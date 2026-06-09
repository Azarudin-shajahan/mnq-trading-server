"""
Databento RTY (Russell 2000 e-mini) 1-min OHLCV download.

Adds rty_open/high/low/close/volume columns to the 1-MINUTE MULTI files
(MULTI_1min_IST_2020_2024.csv, MULTI_1min_IST_2025.csv) so Model 5's 1m
fill-resolver (walk_limit_1m) can resolve RTY at the true limit fill instead
of the conservative 5m k+1 floor. RTY 5m is already in the 5m MULTI files;
only 1m was missing.

Usage:
  export DATABENTO_API_KEY=db-XXXX
  python3 databento_download_rty.py --cost-only                 # free estimate, no credits
  python3 databento_download_rty.py --confirm --max-cost 8.00   # download + merge (aborts if cost > max)
"""
import os, sys, argparse
import pandas as pd

DATA_DIR        = os.path.expanduser("~/mnq_trading/data")
DATASET         = "GLBX.MDP3"
SYMBOL          = ["RTY.v.0"]        # continuous front-month, same .v.0 convention as CL/GC
SCHEMA_1M       = "ohlcv-1m"
IST_OFFSET      = pd.Timedelta(hours=5, minutes=30)
TARGET_1M_FILES = ["MULTI_1min_IST_2020_2024.csv", "MULTI_1min_IST_2025.csv"]
COLS            = ["rty_open", "rty_high", "rty_low", "rty_close", "rty_volume"]

SEGMENTS = [
    ("2020-01-01", "2022-01-01", "2020-2021"),
    ("2022-01-01", "2024-01-01", "2022-2023"),
    ("2024-01-01", "2026-01-01", "2024-2025"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--cost-only", action="store_true")
ap.add_argument("--confirm", action="store_true", help="proceed with the paid download (non-interactive)")
ap.add_argument("--max-cost", type=float, default=8.00, help="hard abort if estimated cost exceeds this")
args = ap.parse_args()

try:
    import databento as db
except ImportError:
    print("ERROR: pip3 install databento --break-system-packages")
    sys.exit(1)

key = os.environ.get("DATABENTO_API_KEY")
if not key:
    print("ERROR: export DATABENTO_API_KEY=db-XXXX")
    sys.exit(1)

client = db.Historical(key)

print("Checking RTY 1-min cost (free metadata call)...")
total_cost = 0.0
for start, end, label in SEGMENTS:
    c = client.metadata.get_cost(dataset=DATASET, symbols=SYMBOL, schema=SCHEMA_1M,
                                 stype_in="continuous", start=start, end=end)
    print("  [%s] $%.4f" % (label, c))
    total_cost += c
print("\nTotal estimated cost: $%.4f   (max allowed $%.2f)" % (total_cost, args.max_cost))

if args.cost_only:
    sys.exit(0)

if total_cost > args.max_cost:
    print("ABORT: estimated $%.4f exceeds --max-cost $%.2f. Not downloading." % (total_cost, args.max_cost))
    sys.exit(2)

if not args.confirm:
    print("Dry run (no --confirm). Re-run with --confirm to download.")
    sys.exit(0)

all_dfs = []
for start, end, label in SEGMENTS:
    print("\nDownloading RTY %s..." % label)
    data = client.timeseries.get_range(dataset=DATASET, symbols=SYMBOL, schema=SCHEMA_1M,
                                       stype_in="continuous", start=start, end=end)
    df = data.to_df()
    df = df.rename(columns={"open": "rty_open", "high": "rty_high", "low": "rty_low",
                            "close": "rty_close", "volume": "rty_volume"})
    df["timestamp"] = pd.to_datetime(df.index).tz_localize(None) + IST_OFFSET
    df = df[["timestamp"] + COLS]
    all_dfs.append(df)
    print("  %s rows" % format(len(df), ","))

rty_df = (pd.concat(all_dfs).drop_duplicates("timestamp")
          .sort_values("timestamp").reset_index(drop=True))
print("\nTotal RTY 1m rows: %s | %s -> %s" % (format(len(rty_df), ","),
      rty_df.timestamp.min(), rty_df.timestamp.max()))

for fname in TARGET_1M_FILES:
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        print("  skip (missing): %s" % fname)
        continue
    print("\nMerging into %s..." % fname)
    multi = pd.read_csv(path, parse_dates=["timestamp"])
    for col in COLS:
        if col in multi.columns:
            multi.drop(columns=[col], inplace=True)
    merged = multi.merge(rty_df, on="timestamp", how="left")
    filled = merged["rty_high"].notna().sum()
    print("  %s/%s rows with RTY data" % (format(filled, ","), format(len(merged), ",")))
    merged.to_csv(path, index=False)
    print("  Saved -> %s" % path)

print("\nDone. RTY 1m now available to Model 5's walk_limit_1m resolver.")
