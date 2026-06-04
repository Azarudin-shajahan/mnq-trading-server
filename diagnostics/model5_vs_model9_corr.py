#!/usr/bin/env python3
"""
3-ENGINE diversification test: Model 9 (swing) / Model 5 (scalp) / Model 8 (selective).
All three reuse the OTE entry + weekly bias - the question is whether their different
target/hold/frequency wrappers produce UNCORRELATED P&L (earn a portfolio slot) or are
redundant. Pairwise Pearson corr of equal-risk WEEKLY P&L + all merge combinations.

Equal-risk normalize each trade: realized R-mult (pnl/|entry-sl|) x $100 (scale-free).
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import numpy as np
import pandas as pd
import model9_oneshot_engine as M9
import model5_intraday_engine as M5

R_USD = 100.0


def eq_risk(tr):
    tr = tr.copy()
    tr["risk"] = (tr.entry - tr.sl).abs()
    tr["usd"] = (tr.pnl / tr.risk) * R_USD
    return tr


def weekly(tr, wk_from_date=False):
    if wk_from_date:
        tr = tr.copy(); tr["week"] = tr["date"].apply(M5.week_start)
    return tr.groupby("week").usd.sum()


def pf_dd(s):
    gp = s[s > 0].sum(); gl = -s[s < 0].sum()
    pf = round(gp / gl, 2) if gl > 0 else float("inf")
    eq = s.cumsum(); dd = (eq - eq.cummax()).min()
    return pf, dd


def main():
    print("building Model 9 combo (NQ)...", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    o = M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    m9 = eq_risk(pd.concat([o, t]).reset_index(drop=True))

    print("building Model 5 scalp (OTE r1, kz-exit, NY)...", flush=True)
    m5 = eq_risk(M5.backtest(dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny"), "nq"))

    print("building Model 8 selective (OTE fixed-25, one-per-week, monwed, NY)...", flush=True)
    m8 = eq_risk(M5.backtest(dict(M5.DEFAULTS, entry="ote", tp="fixed", tp_pts=25.0,
                                  days="monwed", one_per_week=True, session="ny"), "nq"))

    w9 = weekly(m9); w5 = weekly(m5, True); w8 = weekly(m8, True)
    idx = w9.index.union(w5.index).union(w8.index)
    a9 = w9.reindex(idx, fill_value=0.0)
    a5 = w5.reindex(idx, fill_value=0.0)
    a8 = w8.reindex(idx, fill_value=0.0)

    print("\n=== 3-ENGINE DIVERSIFICATION (M9 swing / M5 scalp / M8 selective) ===")
    print(f"trades: M9={len(m9)} M5={len(m5)} M8={len(m8)}")
    print("\nPearson corr of equal-risk WEEKLY P&L:")
    print(f"  M9-M5: {a9.corr(a5):.2f} | M9-M8: {a9.corr(a8):.2f} | M5-M8: {a5.corr(a8):.2f}")

    def line(name, s):
        pf, dd = pf_dd(s)
        r = s.sum() / abs(dd) if dd else float("nan")
        return f"  {name}: total ${s.sum():>8,.0f} PF {pf:>5} maxDD ${dd:>7,.0f} return/DD {r:>5.1f}"

    print("\n=== MERGE TEST (equal-risk $100/trade) ===")
    for nm, s in [("M9 alone   ", a9), ("M5 alone   ", a5), ("M8 alone   ", a8),
                  ("M9+M5      ", a9 + a5), ("M9+M8      ", a9 + a8), ("M5+M8      ", a5 + a8),
                  ("M9+M5+M8   ", a9 + a5 + a8)]:
        print(line(nm, s))
    r2 = (a9 + a5).sum() / abs(pf_dd(a9 + a5)[1])
    r3 = (a9 + a5 + a8).sum() / abs(pf_dd(a9 + a5 + a8)[1])
    print(f"\nVERDICT: M8 earns a slot if M5-M8 corr < 0.4 AND 3-engine return/DD ({r3:.1f}) "
          f"> 2-engine M9+M5 ({r2:.1f}). Else redundant with M5 (OTE-scalp core saturated -> pivot to (b)).")


if __name__ == "__main__":
    main()
