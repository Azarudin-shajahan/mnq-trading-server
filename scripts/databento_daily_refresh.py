"""Daily incremental NQ/ES/YM bar refresh for the HTF capture loop (architecture B).

Pulls newly-settled ohlcv-1m bars from Databento Historical, converts to naive
IST, appends to a rolling 1-min live store, and re-resamples to 5m + 4h live
files that htf_context / htf_outcomes read. Idempotent: re-running a day is a
no-op (dedup on timestamp). Deliberately writes SEPARATE *_live_IST.csv files -
the frozen historical MULTI files are never mutated (avoids the provenance leak).

Reuses the exact mechanics of databento_download_full.py (GLBX.MDP3, ohlcv-1m,
continuous NQ.v.0/ES.v.0/YM.v.0, IST_OFFSET=+5:30, the same AGG resample).

Usage:
  DATABENTO_API_KEY=db-XXXX python3 databento_daily_refresh.py --cost-only
  DATABENTO_API_KEY=db-XXXX python3 databento_daily_refresh.py            # incremental
  DATABENTO_API_KEY=db-XXXX python3 databento_daily_refresh.py --since 2026-05-27
  python3 databento_daily_refresh.py --self-test                          # no key/network
"""
import os, sys, argparse, datetime
from pathlib import Path
import pandas as pd

DATA_DIR   = Path(os.path.expanduser("~/mnq_trading/data"))
DATASET    = "GLBX.MDP3"
SCHEMA     = "ohlcv-1m"
SYMBOLS    = ["NQ.v.0", "ES.v.0", "YM.v.0"]
PREFIX     = {"NQ.v.0": "nq", "ES.v.0": "es", "YM.v.0": "ym"}
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)
HIST_END   = datetime.date(2026, 5, 26)        # last day of the frozen historical file

LIVE_1M = DATA_DIR / "MULTI_1min_live_IST.csv"
LIVE_5M = DATA_DIR / "MULTI_5min_live_IST.csv"
LIVE_4H = DATA_DIR / "MULTI_4h_live_IST.csv"

AGG = {f"{p}_{k}": a for p in ("nq", "es", "ym")
       for k, a in (("open", "first"), ("high", "max"), ("low", "min"),
                    ("close", "last"), ("volume", "sum"))}


def fetch_1m(client, start, end):
    """Return a naive-IST 1-min MULTI frame for [start, end) (UTC datetimes)."""
    frames = {}
    for sym in SYMBOLS:
        p = PREFIX[sym]
        data = client.timeseries.get_range(
            dataset=DATASET, symbols=[sym], schema=SCHEMA,
            stype_in="continuous", start=start, end=end)
        df = data.to_df().rename(columns={c: f"{p}_{c}" for c in
                                          ("open", "high", "low", "close", "volume")})
        frames[p] = df[[f"{p}_{c}" for c in ("open", "high", "low", "close", "volume")]]
        print(f"  {sym}: {len(frames[p]):,} 1m bars")
    merged = frames["nq"].join(frames["es"], how="inner").join(frames["ym"], how="inner")
    merged.index = merged.index.tz_localize(None) + IST_OFFSET
    merged.index.name = "timestamp"
    return merged


def _resample(df1m, rule):
    cols = {c: a for c, a in AGG.items() if c in df1m.columns}
    out = df1m.resample(rule).agg(cols).dropna(how="all")
    return out.dropna(subset=[c for c in out.columns if c.endswith("_close")][:1])


def append_and_resample(new_1m, live_1m=LIVE_1M, live_5m=LIVE_5M, live_4h=LIVE_4H):
    """Merge new 1m bars into the live store (dedup on timestamp) and rewrite the
    5m + 4h live files. Returns the combined 1m frame."""
    if Path(live_1m).exists():
        existing = pd.read_csv(live_1m, parse_dates=["timestamp"]).set_index("timestamp")
        combined = pd.concat([existing, new_1m])
    else:
        combined = new_1m
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined.index.name = "timestamp"
    combined.to_csv(live_1m)
    _resample(combined, "5min").to_csv(live_5m)
    _resample(combined, "4h").to_csv(live_4h)
    print(f"  live store: {len(combined):,} 1m bars  "
          f"{combined.index[0].date()} -> {combined.index[-1].date()}  "
          f"-> {Path(live_5m).name}, {Path(live_4h).name}")
    return combined


def _is_billing_error(msg):
    """True if a Databento error looks like an out-of-credit / spend-limit block
    (you cap the budget on Databento's side; we only need to surface the block)."""
    m = msg.lower()
    return any(w in m for w in ("credit", "balance", "insufficient", "payment",
                                "billing", "funds", "quota", "spend", "exceeded"))


def _incremental_start():
    """UTC start datetime for the next pull = last live bar + 1min, else gap start."""
    if LIVE_1M.exists():
        last = pd.read_csv(LIVE_1M, parse_dates=["timestamp"])["timestamp"].max()
        return (last - IST_OFFSET + pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")
    return (HIST_END + datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")


def _self_test():
    """Verify append + resample + dedup with synthetic 1m data (no key/network)."""
    import numpy as np
    idx = pd.date_range("2026-05-27 09:30", periods=120, freq="1min", name="timestamp")
    cols = list(AGG.keys())
    a = pd.DataFrame(np.arange(len(idx) * len(cols)).reshape(len(idx), len(cols)) * 1.0,
                     index=idx, columns=cols)
    t1, t5, t4 = (Path("/tmp/_lt_1m.csv"), Path("/tmp/_lt_5m.csv"), Path("/tmp/_lt_4h.csv"))
    for p in (t1, t5, t4):
        p.unlink(missing_ok=True)
    append_and_resample(a, t1, t5, t4)
    # re-run with an overlapping + extended window -> dedup, no duplicate timestamps
    b = a.copy(); b.index = b.index + pd.Timedelta(minutes=60)
    combined = append_and_resample(b, t1, t5, t4)
    assert not combined.index.duplicated().any(), "dedup failed"
    assert len(combined) == 180, f"expected 180 unique 1m bars, got {len(combined)}"
    five = pd.read_csv(t5)
    assert len(five) == 36, f"expected 36 5m bars, got {len(five)}"
    assert list(five.columns) == ["timestamp"] + list(AGG.keys()), "5m schema mismatch"
    for p in (t1, t5, t4):
        p.unlink(missing_ok=True)
    print("databento_daily_refresh self-test: PASS (append + resample + dedup + schema)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-only", action="store_true")
    ap.add_argument("--since", help="override start date YYYY-MM-DD")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        _self_test(); return

    try:
        import databento as db
    except ImportError:
        sys.exit("ERROR: pip3 install databento")
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        sys.exit("ERROR: set DATABENTO_API_KEY (key wiring is the last step).")

    client = db.Historical(key)
    start = (args.since + "T00:00:00") if args.since else _incremental_start()
    # end at yesterday 00:00 UTC: only fully-settled days, and stays inside
    # Databento's available history edge (recent ~15min is not yet licensed/served).
    end = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
    if start >= end:
        print(f"  up to date (start {start} >= end {end}); nothing to pull."); return

    print(f"[COST] {SCHEMA} NQ/ES/YM {start} -> {end}")
    try:
        cost = client.metadata.get_cost(dataset=DATASET, symbols=SYMBOLS, schema=SCHEMA,
                                        stype_in="continuous", start=start, end=end)
        print(f"  estimated cost: ${cost:.4f}")
        if args.cost_only:
            print("  re-run without --cost-only to download."); return
        new_1m = fetch_1m(client, start, end)
    except Exception as e:
        if _is_billing_error(str(e)):
            print(f"LOW_BALANCE: Databento pull blocked - {e}")
            sys.exit(3)                      # wrapper turns this into a notification
        raise

    if len(new_1m) == 0:
        print("  no new bars settled yet."); return
    append_and_resample(new_1m)
    print("[DONE] live files refreshed. Next: htf_outcomes.py --update <date>")


if __name__ == "__main__":
    main()
