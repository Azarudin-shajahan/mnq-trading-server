#!/usr/bin/env python3
"""
Model 9 COT ablation - resolves research-critiquer BLOCKER 1 (COT named-but-off).

The validated combo hardcodes make_data("off", ...). ICT names COT (CFTC commercials)
as a Model 9 weekly-bias input. This measures COT's actual contribution by running the
EXACT production combo (OTE r2 + Turtle r3, maxrisk 30, one trade/week/book) three ways:
  off     = price-range-expansion bias only (current production)
  confirm = COT adds a bias on price-neutral weeks (veto disabled)
  veto    = COT also neutralizes weeks where it contradicts price (no-lookahead, merge_asof backward)

Imports the engine; touches NO validated code. Prints n/wr/pf/pnl/maxDD/$ + per-year per mode.
Decision: if COT improves pf/pnl with no added DD -> wire into production; else reword the
claim to "COT built + ablated, off in production (no edge)".
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import pandas as pd
import model9_oneshot_engine as E


def combo(data):
    o = E.backtest(dict(E.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = E.backtest(dict(E.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    c = pd.concat([o, t]).sort_values("date").reset_index(drop=True)
    return c


def report(mode, c):
    s = E.stats(c)
    eq = c.pnl.cumsum() if len(c) else pd.Series([0])
    dd = (eq - eq.cummax()).min()
    py = E.peryear(c)
    neg = [f"{y}:{v[3]}" for y, v in py.items() if v[3] != "inf" and float(v[3]) < 1.0]
    print(f"\ncot={mode:7} | n={s['n']:3} wr={s['wr']:4} pf={s['pf']:5} "
          f"pnl={s['pnl']:7}pt maxDD={dd:6.0f}pt  ${s['pnl']*E.NQ_PT:>8,.0f}/1NQ")
    print("   yr pf: " + " ".join(f"{y}:{v[3]}" for y, v in py.items()))
    if neg:
        print("   sub-1 years: " + " ".join(neg))
    return dict(mode=mode, n=s["n"], pf=s["pf"], pnl=s["pnl"], dd=round(float(dd), 1))


def main():
    print("loading data...", flush=True)
    df5m, fvgs, news = E.load_all()
    print(f"5m bars: {len(df5m):,} | 4h FVGs: {len(fvgs)} | news days: {len(news)}", flush=True)
    print("\n=== MODEL 9 COMBINED (OTE r2 + Turtle r3) - COT ABLATION on NQ ===")
    out = []
    for mode in ["off", "confirm", "veto"]:
        data = E.make_data(mode, df5m, fvgs, news)
        out.append(report(mode, combo(data)))
    base = next(r for r in out if r["mode"] == "off")
    print("\n=== DELTA vs off (the production default) ===")
    for r in out:
        if r["mode"] == "off":
            continue
        print(f"  {r['mode']:7}: dPnL {r['pnl']-base['pnl']:+.1f}pt  "
              f"dN {r['n']-base['n']:+d}  pf {base['pf']}->{r['pf']}  dDD {r['dd']-base['dd']:+.1f}pt")
    print("\nVERDICT INPUT: COT helps only if dPnL>0 AND dDD<=0 (no worse drawdown).")


if __name__ == "__main__":
    main()
