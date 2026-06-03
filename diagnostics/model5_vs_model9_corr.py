#!/usr/bin/env python3
"""
Model 5 (OTE) vs Model 9 (combo) DIVERSIFICATION test - the make-or-break for whether
Model 5 earns a separate slot or is redundant with Model 9.

Both engines inherit the SAME weekly bias -> directionally coupled by construction. This
measures (a) Pearson correlation of equal-risk WEEKLY P&L, (b) directional agreement on
shared weeks, (c) whether merging Model 5 into the Model 9 book improves risk-adjusted return
(return/DD) or just doubles the same edge.

Equal-risk normalize each trade: realized R-mult (pnl/|entry-sl|) x $100, so the comparison
is scale-free (Model 9 maxrisk 30 vs Model 5's wide prevday target).
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


def pf_dd(series_usd):
    gp = series_usd[series_usd > 0].sum(); gl = -series_usd[series_usd < 0].sum()
    pf = round(gp / gl, 2) if gl > 0 else float("inf")
    eq = series_usd.cumsum(); dd = (eq - eq.cummax()).min()
    return pf, dd


def main():
    print("building Model 9 combo (NQ)...", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    o = M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    m9 = eq_risk(pd.concat([o, t]).reset_index(drop=True))

    print("building Model 5 OTE SCALP (r1, kz-exit, NY-only, NQ)...", flush=True)
    m5 = eq_risk(M5.backtest(dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny"), "nq"))

    w9 = weekly(m9)
    w5 = weekly(m5, wk_from_date=True)
    idx = w9.index.union(w5.index)
    a9 = w9.reindex(idx, fill_value=0.0)
    a5 = w5.reindex(idx, fill_value=0.0)

    both = w9.index.intersection(w5.index)
    corr_all = a9.corr(a5)
    corr_both = w9.reindex(both).corr(w5.reindex(both)) if len(both) > 2 else float("nan")

    # directional agreement on shared weeks (sign of weekly P&L)
    same_sign = int((np.sign(w9.reindex(both)) == np.sign(w5.reindex(both))).sum())

    print("\n=== MODEL 5 (OTE) vs MODEL 9 (combo) - DIVERSIFICATION ===")
    print(f"Model 9: {len(m9)} trades, {len(w9)} active weeks | Model 5: {len(m5)} trades, {len(w5)} active weeks")
    print(f"weeks BOTH trade: {len(both)} | weeks only-9: {len(w9.index.difference(w5.index))} "
          f"| weeks only-5: {len(w5.index.difference(w9.index))}")
    print(f"\nPearson corr of equal-risk WEEKLY P&L:")
    print(f"  all weeks (union, 0-filled): {corr_all:.2f}")
    print(f"  shared weeks only:           {corr_both:.2f}")
    print(f"  same-sign weekly P&L on shared weeks: {same_sign}/{len(both)} "
          f"({100*same_sign/max(len(both),1):.0f}%)")

    pf9, dd9 = pf_dd(a9)
    pf5, dd5 = pf_dd(a5)
    merged = a9 + a5
    pfm, ddm = pf_dd(merged)
    r9 = a9.sum() / abs(dd9) if dd9 else float("nan")
    rm = merged.sum() / abs(ddm) if ddm else float("nan")
    print(f"\n=== MERGE TEST (equal-risk, $100/trade) ===")
    print(f"  Model 9 alone:   total ${a9.sum():,.0f} PF {pf9} maxDD ${dd9:,.0f} return/DD {r9:.1f}")
    print(f"  Model 5 alone:   total ${a5.sum():,.0f} PF {pf5} maxDD ${dd5:,.0f}")
    print(f"  MERGED (9+5):    total ${merged.sum():,.0f} PF {pfm} maxDD ${ddm:,.0f} return/DD {rm:.1f}")
    add = "ADDS uncorrelated edge" if rm > r9 + 0.5 else ("REDUNDANT (no return/DD gain)" if rm <= r9 + 0.1 else "marginal")
    print(f"  -> verdict: {add}  (return/DD {r9:.1f} -> {rm:.1f})")
    print(f"\nRULE OF THUMB: corr>0.6 or return/DD flat = redundant (pivot to Model 8). "
          f"corr<0.3 + return/DD up = real diversifier (keep + refine).")


if __name__ == "__main__":
    main()
