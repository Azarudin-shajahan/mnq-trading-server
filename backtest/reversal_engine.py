#!/usr/bin/env python3
"""
ICT Reversal / Turtle-Soup engine - factory (b): the structurally-different edge.

DIRECTION is set by a FAILED liquidity raid (sweep of a prior-day pool + reclaim), INDEPENDENT
of the weekly bias - the one axis M9 (swing) / M5 (scalp) / M8 (selective) never explore (they
all trade in the weekly-bias direction). Tests whether a non-bias-aligned edge exists to add a
genuinely new diversification axis to the book.

  bull: price sweeps prior-day LOW then closes back ABOVE it (failed sell-side raid) -> LONG.
  bear: price sweeps prior-day HIGH then closes back BELOW it (failed buy-side raid) -> SHORT.
Entry = the reclaim close; SL = beyond the raid extreme; TP = fixed R or opposite prior-day pool.
Optional --bias with|against to intersect with the weekly bias (default off = pure reversal).
Reuses model5_intraday_engine (M5) helpers + model9 loaders/stats.
"""
import sys
import argparse
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import numpy as np
import pandas as pd
import model9_oneshot_engine as M9
import model5_intraday_engine as M5

SL_BUF = M5.SL_BUF
PT = M5.PT


def find_reversal(mins, hi, lo, cl, pdh, pdl, sess):
    """First failed-raid reclaim during the killzone. Returns (k, dir, entry, sl)."""
    cmin, cmax = np.inf, -np.inf
    swept_lo = swept_hi = False
    for k in range(len(mins)):
        cmin = min(cmin, lo[k]); cmax = max(cmax, hi[k])
        if not M5.in_kz(mins[k], sess):
            continue
        if lo[k] <= pdl:
            swept_lo = True
        if swept_lo and cl[k] > pdl:                 # failed sell-side raid -> long
            return k, "bull", cl[k], cmin - SL_BUF
        if hi[k] >= pdh:
            swept_hi = True
        if swept_hi and cl[k] < pdh:                 # failed buy-side raid -> short
            return k, "bear", cl[k], cmax + SL_BUF
    return None


def backtest(cfg, inst="nq"):
    df5 = M9._load(M9.M5, inst)
    _w, bias_map = M9.build_weekly_bias("off", inst)
    pdh_map, pdl_map = M5.prior_day_levels(df5)
    by_date = {d: g.reset_index(drop=True) for d, g in df5.groupby("date")}
    days_ok = {"tuethu": {1, 2, 3}, "monwed": {0, 1, 2}, "all": {0, 1, 2, 3, 4}}[cfg["days"]]
    trades = []
    for d in sorted(by_date):
        if d.dayofweek not in days_ok:
            continue
        pdh, pdl = pdh_map.get(d), pdl_map.get(d)
        if pdh is None or pdl is None or np.isnan(pdh) or np.isnan(pdl):
            continue
        g = by_date[d]
        res = find_reversal(g["mins"].values, g["high"].values, g["low"].values,
                            g["close"].values, pdh, pdl, cfg["session"])
        if not res:
            continue
        k, bias, entry, sl = res
        risk = abs(entry - sl)
        if risk <= 0 or (cfg["maxrisk"] and risk > cfg["maxrisk"]):
            continue
        if cfg["bias"] != "off":                     # intersect with weekly bias
            wb = bias_map.get(M5.week_start(d), "neutral")
            if cfg["bias"] == "with" and bias != wb:
                continue
            if cfg["bias"] == "against" and bias == wb:
                continue
        if cfg["tp"] == "prevday":                   # mean-reversion to opposite pool
            tp = pdh if bias == "bull" else pdl
            if not ((bias == "bull" and tp > entry) or (bias == "bear" and tp < entry)):
                continue
        else:
            mult = float(cfg["tp"][1:])
            tp = entry + mult * risk if bias == "bull" else entry - mult * risk
        exit_df = g
        if cfg["exit"] == "kz":
            kze = M5.kz_end_of(g["mins"].values[k])
            j = k
            while j + 1 < len(g) and g["mins"].values[j + 1] < kze:
                j += 1
            exit_df = g.iloc[:j + 1]
        out, pnl = M5.walk_intraday(exit_df, k, entry, sl, tp, bias)
        R = abs(entry - tp) / risk
        trades.append({"date": d, "dir": bias, "entry": round(entry, 2), "sl": round(sl, 2),
                       "tp": round(tp, 2), "R": round(R, 2), "out": out, "pnl": round(pnl, 2),
                       "emins": int(g["mins"].values[k])})
    return pd.DataFrame(trades)


DEFAULTS = dict(days="all", session="ny", bias="off", tp="r1", exit="kz", maxrisk=0)


def show(name, tr):
    s = M9.stats(tr)
    extra = ""
    if len(tr):
        eq = tr.pnl.cumsum(); dd = (eq - eq.cummax()).min()
        extra = (f" maxDD={dd:.0f}pt ${s['pnl']*M9.NQ_PT:,.0f}/1NQ | yr pf: "
                 + " ".join(f"{y}:{v[3]}" for y, v in M9.peryear(tr).items()))
    print(f"{name}: n={s['n']} wr={s['wr']}% pf={s['pf']} pnl={s['pnl']}pt avgR={s['avgR']}{extra}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="nq")
    ap.add_argument("--days", default="all", choices=["tuethu", "monwed", "all"])
    ap.add_argument("--session", default="ny", choices=["both", "ny", "london"])
    ap.add_argument("--bias", default="off", choices=["off", "with", "against"])
    ap.add_argument("--tp", default="r1", choices=["prevday", "r1", "r1.5", "r2", "r3"])
    ap.add_argument("--exit", dest="exit_mode", default="kz", choices=["session", "kz"])
    ap.add_argument("--maxrisk", type=float, default=0)
    ap.add_argument("--scan", action="store_true", help="sweep tp x exit configs")
    args = ap.parse_args()
    base = dict(DEFAULTS, days=args.days, session=args.session, bias=args.bias,
                tp=args.tp, exit=args.exit_mode, maxrisk=args.maxrisk)
    print(f"REVERSAL engine | inst={args.inst} days={args.days} session={args.session} bias={args.bias}")
    if args.scan:
        for tp in ["r1", "r1.5", "r2", "prevday"]:
            for ex in ["kz", "session"]:
                show(f"tp={tp:7} exit={ex:7}", backtest(dict(base, tp=tp, exit=ex), args.inst))
    else:
        show(f"tp={args.tp} exit={args.exit_mode} bias={args.bias}",
             backtest(base, args.inst))


if __name__ == "__main__":
    main()
