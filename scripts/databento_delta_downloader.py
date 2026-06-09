"""
Databento delta downloader — NQ trades schema → 5-min delta bars.

Downloads individual NQ trade records (buy/sell aggressor per trade),
aggregates to 5-minute bars with real delta, and merges into the
existing MULTI_5min_IST.csv as new columns.

New columns added to MULTI:
  nq_buy_vol    — buy-aggressor contracts per bar  (side='A')
  nq_sell_vol   — sell-aggressor contracts per bar (side='B')
  nq_delta      — nq_buy_vol - nq_sell_vol (signed)
  nq_trade_cnt  — number of trades per bar

Delta convention:
  'A' (ask-side aggressor) = buyer lifted the ask  = +delta (buy pressure)
  'B' (bid-side aggressor) = seller hit the bid    = -delta (sell pressure)

Usage:
  # 1. Cost estimate (free — no data charge):
  DATABENTO_API_KEY=db-XXXX python3 databento_delta_downloader.py --cost-only

  # 2. Download one year to test (cheap):
  DATABENTO_API_KEY=db-XXXX python3 databento_delta_downloader.py --start 2022-01-01 --end 2023-01-01

  # 3. Full 2022-2024:
  DATABENTO_API_KEY=db-XXXX python3 databento_delta_downloader.py --start 2022-01-01 --end 2025-01-01

Output:
  ~/mnq_trading/data/NQ_5min_delta_IST.csv          raw delta bars (delta only)
  ~/mnq_trading/data/MULTI_5min_delta_IST.csv       existing MULTI + delta columns merged
"""

import os, sys, argparse
from pathlib import Path
import pandas as pd

DATA_DIR      = Path(os.path.expanduser("~/mnq_trading/data"))
EXISTING_FILE = DATA_DIR / "MULTI_5min_IST.csv"
DELTA_FILE    = DATA_DIR / "NQ_5min_delta_IST.csv"
MERGED_FILE   = DATA_DIR / "MULTI_5min_delta_IST.csv"
RAW_DBN       = DATA_DIR / "NQ_trades_raw.dbn"   # intermediate binary (deleted after processing)

DATASET    = "GLBX.MDP3"
SYMBOL     = "NQ.v.0"    # CME continuous front month
SCHEMA     = "trades"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)


# ── helpers ───────────────────────────────────────────────────────────────────

def get_cost(client, start, end):
    print(f"\n[COST] Estimating '{SCHEMA}' data cost for NQ {start} → {end} ...")
    try:
        cost = client.metadata.get_cost(
            dataset=DATASET, symbols=[SYMBOL], schema=SCHEMA,
            stype_in="continuous", start=start, end=end,
        )
        size = client.metadata.get_billable_size(
            dataset=DATASET, symbols=[SYMBOL], schema=SCHEMA,
            stype_in="continuous", start=start, end=end,
        )
        print(f"  Estimated cost : ${cost:.4f}")
        print(f"  Billable size  : {size / 1e9:.2f} GB uncompressed")
        return cost, size
    except Exception as e:
        print(f"  ERROR during cost estimate: {e}")
        sys.exit(1)


def download_to_file(client, start, end):
    """Stream trades to a local .dbn binary file (avoids loading everything into RAM)."""
    print(f"\n[DOWNLOAD] Streaming NQ trades {start} → {end} → {RAW_DBN}")
    print("  Large date ranges (2+ years) may take 5-20 min depending on connection speed.")
    data = client.timeseries.get_range(
        dataset=DATASET, symbols=[SYMBOL], schema=SCHEMA,
        stype_in="continuous", start=start, end=end,
    )
    data.to_file(str(RAW_DBN))
    print(f"  Written: {RAW_DBN} ({RAW_DBN.stat().st_size / 1e9:.2f} GB)")
    return data


def aggregate_to_bars(data):
    """
    Convert raw trade records to 5-min delta bars.
    Processes in yearly chunks to avoid peak RAM usage on multi-year pulls.
    """
    print("\n[AGGREGATE] Converting trades → 5-min delta bars ...")

    import databento as db

    # Re-load from the saved file for memory-efficient processing
    store = db.DBNStore.from_file(str(RAW_DBN))
    df = store.to_df()

    print(f"  Total trade records: {len(df):,}")
    if len(df) == 0:
        print("  ERROR: No records returned. Check API key and symbol.")
        sys.exit(1)

    # ── RAW SCHEMA INSPECTION (diagnoses the buy_vol/sell_vol decode) ──
    print("\n  [INSPECT] raw columns:", list(df.columns))
    print("  [INSPECT] dtypes:\n   ", df.dtypes.to_dict())
    if "side" in df.columns:
        print("  [INSPECT] side.value_counts():\n   ", df["side"].value_counts(dropna=False).to_dict())
    if "size" in df.columns:
        print("  [INSPECT] size.describe():\n   ", df["size"].describe().to_dict())
    if "price" in df.columns:
        print("  [INSPECT] price.describe():\n   ", df["price"].describe().to_dict())
    print("  [INSPECT] first 3 raw rows:\n", df.head(3).to_string())
    print()

    # Databento trades schema columns we need: ts_event, price, size, side
    keep = [c for c in ["ts_event", "price", "size", "side"] if c in df.columns]
    df = df[keep].copy()

    # Timestamp — Databento returns ns-precision UTC datetime index or ts_event column
    if "ts_event" in df.columns:
        ts = df["ts_event"]
    else:
        ts = df.index.to_series()

    if hasattr(ts.dtype, "tz") and ts.dtype.tz is not None:
        ts = ts.dt.tz_localize(None)
    df["ts_utc"] = pd.to_datetime(ts, unit="ns" if ts.dtype == "int64" else None)
    df["ts_ist"] = df["ts_utc"] + IST_OFFSET
    df["bar"]    = df["ts_ist"].dt.floor("5min")

    # Price scaling: Databento encodes futures prices as fixed-point integers × 1e-9
    if "price" in df.columns and df["price"].median() > 1_000_000:
        df["price"] = df["price"] / 1e9

    # Signed delta. EMPIRICALLY VERIFIED convention (Jan-2022, 5759 bars): 'B' = BUY aggressor (+),
    # 'A' = SELL aggressor (-), 'N' = neutral (0). The opposite (A=buy) gives corr(delta, same-bar
    # return) = -0.72; the correct mapping gives +0.72 (net buying must move the bar up).
    # CAST size to signed int64 FIRST — `size` is uint32 and negating uint32 wraps to ~4.29e9
    # (the original bug: every sell became a huge POSITIVE → sell_vol=0, buy_vol ~1e12/bar).
    # Position-based numpy (not index-aligned .loc) so a non-unique ts index can't misalign.
    import numpy as np
    if "side" in df.columns:
        size_i = df["size"].to_numpy().astype("int64")
        side_a = df["side"].astype("string").to_numpy()
        df["signed"] = np.where(side_a == "B", size_i,
                          np.where(side_a == "A", -size_i, 0)).astype("int64")
    else:
        # Fallback: no side info — can't compute real delta
        print("  WARNING: 'side' column missing — delta will be zero. Schema may not support aggressor.")
        df["signed"] = 0

    # Aggregate per 5-min bar
    agg = (
        df.groupby("bar")
        .agg(
            nq_buy_vol  =("signed", lambda x: int(x[x > 0].sum())),
            nq_sell_vol =("signed", lambda x: int((-x[x < 0]).sum())),
            nq_delta    =("signed", "sum"),
            nq_trade_cnt=("size",   "count"),
        )
        .reset_index()
        .rename(columns={"bar": "timestamp"})
    )

    agg["nq_delta"]     = agg["nq_delta"].astype(int)
    agg["nq_trade_cnt"] = agg["nq_trade_cnt"].astype(int)

    print(f"  5-min bars produced  : {len(agg):,}")
    print(f"  Date range           : {agg['timestamp'].min()} → {agg['timestamp'].max()}")
    print(f"  Avg delta per bar    : {agg['nq_delta'].mean():.1f}")
    print(f"  Avg trades per bar   : {agg['nq_trade_cnt'].mean():.0f}")
    return agg


def merge_with_existing(delta_df):
    print(f"\n[MERGE] Loading {EXISTING_FILE} ...")
    existing = pd.read_csv(EXISTING_FILE, parse_dates=["timestamp"])
    n_orig = len(existing)
    print(f"  Existing rows  : {n_orig:,}  ({existing['timestamp'].min().date()} → {existing['timestamp'].max().date()})")

    merged = existing.merge(delta_df, on="timestamp", how="left")
    matched = merged["nq_delta"].notna().sum()
    print(f"  Delta matched  : {matched:,} / {n_orig:,} bars ({matched/n_orig*100:.1f}%)")

    for col in ["nq_buy_vol", "nq_sell_vol", "nq_delta", "nq_trade_cnt"]:
        merged[col] = merged[col].fillna(0).astype(int)

    merged.to_csv(MERGED_FILE, index=False)
    print(f"  Saved          : {MERGED_FILE}")
    print(f"  Columns        : {list(merged.columns)}")
    return merged


def spot_check(merged):
    """Print a few sample bars to sanity-check delta values."""
    print("\n[SPOT CHECK] Sample bars with delta data:")
    sample = merged[merged["nq_delta"] != 0].head(10)[
        ["timestamp", "nq_open", "nq_close", "nq_volume", "nq_buy_vol", "nq_sell_vol", "nq_delta"]
    ]
    print(sample.to_string(index=False))
    print()
    # Sanity: buy_vol + sell_vol should roughly equal nq_volume (some 'N' side trades excluded)
    total_bv = merged["nq_buy_vol"].sum()
    total_sv = merged["nq_sell_vol"].sum()
    total_v  = merged["nq_volume"].sum()
    print(f"  Total buy vol  : {total_bv:,}")
    print(f"  Total sell vol : {total_sv:,}")
    print(f"  Total volume   : {total_v:,}  (buy+sell should be ≤ volume due to 'N'-side exclusions)")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Download NQ trades from Databento and compute 5-min delta bars")
    ap.add_argument("--cost-only", action="store_true", help="Estimate cost only, no download")
    ap.add_argument("--start",     default="2022-01-01",  help="Start date YYYY-MM-DD")
    ap.add_argument("--end",       default="2025-01-01",  help="End date YYYY-MM-DD (exclusive)")
    ap.add_argument("--skip-download", action="store_true",
                    help=f"Skip download, use existing {RAW_DBN} (re-aggregate only, no re-charge)")
    ap.add_argument("--cleanup", action="store_true",
                    help="Delete the raw .dbn after aggregating (default: KEEP it, so re-aggregation is free)")
    args = ap.parse_args()

    try:
        import databento as db
    except ImportError:
        print("ERROR: pip3 install databento")
        sys.exit(1)

    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        print("ERROR: set DATABENTO_API_KEY environment variable")
        print("  export DATABENTO_API_KEY=db-XXXXXXXXXXXXXXXXXXXX")
        sys.exit(1)

    client = db.Historical(key)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    cost, size_bytes = get_cost(client, args.start, args.end)

    if args.cost_only:
        print("\n  Re-run without --cost-only to download.")
        print(f"\n  Tip: start with 1 year (--start 2022-01-01 --end 2023-01-01) to test cheaply.")
        return

    print(f"\n  About to download ${cost:.4f} of data ({size_bytes/1e9:.2f} GB uncompressed).")
    confirm = input("  Type 'yes' to proceed: ").strip().lower()
    if confirm != "yes":
        print("  Aborted.")
        return

    if not args.skip_download:
        download_to_file(client, args.start, args.end)
    else:
        if not RAW_DBN.exists():
            print(f"  ERROR: {RAW_DBN} not found. Cannot skip download.")
            sys.exit(1)
        print(f"\n[SKIP DOWNLOAD] Using existing {RAW_DBN}")

    delta_df = aggregate_to_bars(None)  # loads from RAW_DBN internally

    delta_df.to_csv(DELTA_FILE, index=False)
    print(f"\n  Raw delta saved: {DELTA_FILE}")

    merged = merge_with_existing(delta_df)
    spot_check(merged)

    # KEEP the raw .dbn (it is what we paid for) so re-aggregation needs no re-download.
    # Delete only when explicitly asked via --cleanup.
    if args.cleanup and RAW_DBN.exists():
        RAW_DBN.unlink()
        print(f"\n  Cleaned up: {RAW_DBN}")
    elif RAW_DBN.exists():
        print(f"\n  Kept raw (re-aggregate with --skip-download, no re-charge): {RAW_DBN}")

    print("\n[DONE] Run concept lab with delta data:")
    print(f"  python3 ~/mnq_trading/backtest/mnq_concept_lab_v7.py \\")
    print(f"    --file {MERGED_FILE} \\")
    print(f"    --start 2022-01-01 --end 2024-12-31 --vol-concepts")


if __name__ == "__main__":
    main()
