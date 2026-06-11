#!/usr/bin/env python3
"""Execution stress: slippage + commission floor (Fable's #2, 2026-06-11).

"C18" is an archived JUDGE-era baseline not reproducible from current code; the
live-relevant strategies are the 62T v8.18 COMBINE config and BOOK C (the funded
book whose kill-criteria are frozen). This stresses both with adverse fills +
commission and -- for Book C -- re-maps against its OWN frozen kill thresholds, so
we learn BEFORE the demo whether execution drag ALONE can breach the kill line
(separate from edge decay).

Model (analytic fill-level adverse, the standard quick stress -- not a re-simulation):
  adverse slippage = `ticks` worse on EACH fill (entry + exit) = 2*ticks*0.25 pts/trade;
  round-trip `commission` $ per trade. A BE trade becomes a small loss; a marginal win
  can flip. Applied to the realized trades (does not retrigger stops mid-trade).

Modes:
  --book-c (default): pull Book C trades from the frozen engines, stress in R-units,
    re-bootstrap the 12-week distribution at each slippage level, compare median/5th
    PF + R-sum against diagnostics/book_c_kill_criteria.json. Flags the slippage level
    at which the stressed MEDIAN 12-wk window would itself look like a kill.
  --log CSV: stress a trade log (e.g. backtest/mnq_trade_log_v8_18_perfect62.csv) and
    print the net-$/PF/maxDD floor at 0/1/2-tick slippage (LIVE $/pt by default).

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_c_kill_criteria as KC  # reuse engine configs + weekly_stats + bootstrap + R_USD

TICK = 0.25                  # NQ/MNQ index-point tick
KILL_JSON = os.path.join(HERE, "book_c_kill_criteria.json")


def book_c_legs():
    """Run the frozen Book C engines once; keep entry/sl/pnl/date per leg trade."""
    print("running frozen Book C engines (once)...", flush=True)
    df5m, fvgs, news = KC.M9.load_all()
    data = KC.M9.make_data("off", df5m, fvgs, news)
    m9 = pd.concat([KC.M9.backtest(dict(KC.M9.DEFAULTS, **c), data) for c in KC.M9_LEGS]
                   ).reset_index(drop=True)
    m5nq = KC.M5.backtest(dict(KC.M5.DEFAULTS, **KC.M5_SCALP), "nq")
    m5ym = KC.M5.backtest(dict(KC.M5.DEFAULTS, **KC.M5_SCALP), "ym")
    return {"m9": m9, "m5nq": m5nq, "m5ym": m5ym}


def stressed_weekly(legs, ticks, commission, pt_value):
    """Apply per-trade slippage+commission in R-units, weight, aggregate weekly (KC fmt)."""
    slip_pts = 2.0 * ticks * TICK
    frames = []
    for name, tr in legs.items():
        risk = (tr["entry"] - tr["sl"]).abs()
        risk = risk.where(risk > 0, np.nan)
        gross_R = tr["pnl"] / risk
        slip_R = slip_pts / risk
        comm_R = commission / (risk * pt_value)
        net_R = (gross_R - slip_R - comm_R) * KC.WEIGHTS[name]
        frames.append(pd.DataFrame({"date": pd.to_datetime(tr["date"]),
                                    "usd": net_R * KC.R_USD}).dropna())
    return KC.weekly_stats(pd.concat(frames).reset_index(drop=True))


def book_c_mode(args):
    kill = json.load(open(KILL_JSON))["KILL_CRITERIA"] if os.path.exists(KILL_JSON) else None
    pf_kill = kill["primary_PF_below"] if kill else None
    rsum_kill = kill["primary_Rsum_below"] if kill else None
    legs = book_c_legs()
    print("\n=== Book C execution stress (commission $%.2f RT, $%.0f/pt, 12wk bootstrap) ==="
          % (args.commission, args.pt_value))
    if kill:
        print("   frozen kill line (in-sample 5th pct): 12wk PF < %.2f OR R-sum < %.2f"
              % (pf_kill, rsum_kill))
    print("   %-9s %-22s %-22s  %-10s" % ("slippage", "12wk PF 5/50/95", "12wk Rsum 5/50/95", "full PF"))
    breach_level = None
    for ticks in range(0, args.max_ticks + 1):
        wk = stressed_weekly(legs, ticks, args.commission, args.pt_value)
        pf, rs, _ = KC.bootstrap(wk, window=12, n=args.n, block=4, seed=KC.SEED)
        pf5, pf50, pf95 = (np.percentile(pf, p) for p in (5, 50, 95))
        r5, r50, r95 = (np.percentile(rs, p) for p in (5, 50, 95))
        fpf = (wk["gp"].sum() / wk["gl"].sum()) if wk["gl"].sum() > 0 else float("inf")
        flag = ""
        if kill and (pf50 <= pf_kill or r50 <= rsum_kill):
            flag = "  <-- MEDIAN window now looks like a KILL"
            breach_level = breach_level if breach_level is not None else ticks
        print("   %-9s %5.2f /%5.2f /%5.2f      %6.1f /%6.1f /%6.1f      PF %.2f%s"
              % ("%dtk" % ticks, pf5, pf50, pf95, r5, r50, r95, fpf, flag))
    print("\n   VERDICT: %s" % (
        "execution drag alone can breach the kill line at %d-tick slippage" % breach_level
        if breach_level is not None else
        "kill line NOT reachable by execution drag alone up to %d-tick slippage "
        "(a kill in the demo would indicate genuine edge decay, not just costs)" % args.max_ticks))


def log_mode(args):
    df = pd.read_csv(args.log)
    if "pts" not in df.columns:
        sys.exit("log needs a signed-favorable 'pts' column")
    print("=== trade-log execution stress: %s (n=%d, $%.0f/pt live, commission $%.2f RT) ==="
          % (os.path.basename(args.log), len(df), args.pt_value, args.commission))
    print("   %-9s %-9s %-12s %-12s %-10s" % ("slippage", "PF", "net $", "maxDD $", "exp $/trade"))
    for ticks in range(0, args.max_ticks + 1):
        net_pts = df["pts"] - 2.0 * ticks * TICK
        net_usd = net_pts * args.pt_value - args.commission
        gp = net_usd[net_usd > 0].sum()
        gl = -net_usd[net_usd < 0].sum()
        pf = (gp / gl) if gl > 0 else float("inf")
        eqc = net_usd.cumsum()
        dd = (eqc - eqc.cummax()).min()
        print("   %-9s %-9.2f $%-11.0f $%-11.0f $%-9.2f"
              % ("%dtk" % ticks, pf, net_usd.sum(), dd, net_usd.mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", help="stress a trade-log CSV (else Book C mode)")
    ap.add_argument("--commission", type=float, default=1.00, help="round-trip $ per trade")
    ap.add_argument("--pt-value", dest="pt_value", type=float, default=2.0, help="live $/pt (MNQ)")
    ap.add_argument("--max-ticks", dest="max_ticks", type=int, default=2)
    ap.add_argument("--n", type=int, default=20000, help="bootstrap resamples (Book C mode)")
    args = ap.parse_args()
    if args.log:
        log_mode(args)
    else:
        book_c_mode(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
