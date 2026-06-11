#!/usr/bin/env python3
"""NWOG range-week FLAG -- measure only, do NOT merge (Fable's #3, 2026-06-11).

NWOG = New Week Opening Gap. Level = Sunday 18:00 ET futures reopen open (persists all
week). Hypothesis: weeks where price CLINGS to the NWOG level (>= touch_thr daily RTH
touches) are range/chop weeks that concentrate losses; weeks that leave the level and
expand are the trend weeks that pay. This script MEASURES that against Book C's weekly
P&L and reports whether the flag is worth LOGGING alongside demo trades as a candidate
filter. It does NOT add anything to the frozen book (unfreezing pre-demo would repeat
the graveyard pattern -- see the data-leak / ORG gotchas).

Method: NQ 1m, clean 2020_2024 file, exact IST->America/New_York tz convert. Per ET
RTH date -> [low, high]; NWOG level for a week = that week's Sunday 18:00 ET open.
range-week = #RTH days whose [low,high] contains the level >= touch_thr. Book C weekly
R-sum from the frozen kill-criteria engines (KC.weekly_stats). Compare flagged vs
unflagged weeks; report mean R, share of total losses, and correlation.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_c_kill_criteria as KC  # Book C weekly R-sum (same engines as the kill-criteria)

DATA = os.path.join(os.path.expanduser("~"), "mnq_trading/data")
RTH_OPEN, RTH_CLOSE = 9 * 60 + 30, 16 * 60
SUN_OPEN_MIN = 18 * 60                       # 18:00 ET Sunday futures reopen


def load_nq_et(fname, start, end):
    cols = ["timestamp", "nq_open", "nq_high", "nq_low", "nq_close"]
    df = pd.read_csv(os.path.join(DATA, fname), usecols=cols, parse_dates=["timestamp"])
    ts = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df["et_date"] = ts.dt.normalize().dt.tz_localize(None)
    df["et_min"] = ts.dt.hour * 60 + ts.dt.minute
    df["et_dow"] = ts.dt.dayofweek                # Mon=0 .. Sun=6
    df = df[(df["et_date"] >= pd.Timestamp(start)) & (df["et_date"] <= pd.Timestamp(end))]
    return df


def week_key(d):
    return (d - pd.Timedelta(days=int(d.weekday()))).normalize()   # Monday of d's week


def build(args):
    df = load_nq_et(args.file, args.start, args.end)
    # NWOG level: Sunday 18:00 ET open, keyed by the FOLLOWING Monday's week.
    sun = df[(df["et_dow"] == 6) & (df["et_min"] == SUN_OPEN_MIN)]
    nwog = {}
    for _, r in sun.iterrows():
        nwog[week_key(r["et_date"] + pd.Timedelta(days=1))] = float(r["nq_open"])
    # per RTH date high/low
    rth = df[(df["et_min"] >= RTH_OPEN) & (df["et_min"] <= RTH_CLOSE)]
    dh = rth.groupby("et_date").agg(h=("nq_high", "max"), l=("nq_low", "min"))
    dh["wk"] = [week_key(d) for d in dh.index]
    # touches per week
    rows = []
    for wk, g in dh.groupby("wk"):
        lvl = nwog.get(wk)
        if lvl is None:
            continue
        touches = int(((g["l"] <= lvl) & (g["h"] >= lvl)).sum())
        rows.append({"wk": wk, "level": lvl, "rth_days": len(g), "touches": touches,
                     "range_week": touches >= args.touch_thr})
    flags = pd.DataFrame(rows).set_index("wk")

    # Book C weekly R-sum (same engines as kill-criteria)
    print("running Book C engines for weekly R-sum...", flush=True)
    trades, _ = KC.build_book_c_trades()
    wk_bc = KC.weekly_stats(trades)["rsum"]
    wk_bc.index = [week_key(d) for d in wk_bc.index]
    wk_bc = wk_bc.groupby(level=0).sum()

    m = flags.join(wk_bc.rename("rsum"), how="inner").dropna(subset=["rsum"])
    fl = m[m["range_week"]]
    un = m[~m["range_week"]]
    report(m, fl, un, args)


def report(m, fl, un, args):
    def blk(name, d):
        r = d["rsum"]
        return ("  %-12s weeks=%3d  meanR=%6.2f  medR=%6.2f  posWk=%2.0f%%  totR=%7.1f"
                % (name, len(d), r.mean(), r.median(), (r > 0).mean() * 100, r.sum()))
    tot_loss = m.loc[m["rsum"] < 0, "rsum"].sum()
    loss_in_flag = fl.loc[fl["rsum"] < 0, "rsum"].sum()
    corr = m["range_week"].astype(int).corr(m["rsum"])
    print("\n=== NWOG range-week flag vs Book C weekly R (touch_thr=%d, %s..%s) ==="
          % (args.touch_thr, args.start, args.end))
    print("  weeks measured: %d | flagged range-weeks: %d (%.0f%%)"
          % (len(m), len(fl), len(fl) / max(1, len(m)) * 100))
    print(blk("range-week", fl))
    print(blk("trend-week", un))
    print("  point-biserial corr(flag, weeklyR) = %.3f (negative => flag marks worse weeks)"
          % corr)
    print("  share of total LOSS-R inside flagged weeks: %.0f%% (flag captures losses if high)"
          % (loss_in_flag / tot_loss * 100 if tot_loss < 0 else 0))
    diff = un["rsum"].mean() - fl["rsum"].mean()
    verdict = ("WORTH LOGGING as a candidate filter (flagged weeks clearly worse)"
               if (corr <= -0.10 and diff > 0.5) else
               "WEAK / not differentiating -- log if cheap, do not prioritize")
    print("  VERDICT (measure-only): %s" % verdict)
    print("  REMINDER: do NOT merge into the frozen Book C pre-demo; log alongside demo "
          "trades and decide post-OOS.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="MULTI_1min_IST_2020_2024.csv")
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--touch-thr", dest="touch_thr", type=int, default=3)
    ap.add_argument("--sweep", action="store_true", help="sweep touch_thr 2..4")
    args = ap.parse_args()
    if args.sweep:
        for t in (2, 3, 4):
            args.touch_thr = t
            build(args)
    else:
        build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
