#!/usr/bin/env python3
"""Per-DAY risk of the M9+M5+Reversal book vs prop-firm limits, to find the max safe MNQ size.

reversal_vs_book.py aggregates WEEKLY (for the merge return/DD). This aggregates DAILY to check
the two limits that actually breach a $50K EOD account (propfile.md):
  - DLL  (daily loss limit)        = $1,000  (TopStep optional / Apex-EOD / MFFU-Builder soft-pause)
  - maxDD (max EOD trailing draw)  = $2,000
Equal-risk ($100/1R). Reversal at the robust maxrisk=30. Read-only.

CAVEAT: uses REALIZED per-trade PnL aggregated by exit-date -> it is a LOWER BOUND on intraday DLL
exposure (open drawdown before a win is not modeled). Appropriate for EOD trailing DD; for the
intraday DLL the true figure is somewhat worse, mostly for wider-SL (reversal/M9) trades.
"""
import sys

sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import pandas as pd
import model9_oneshot_engine as M9
import model5_intraday_engine as M5
import reversal_engine as REV

DLL = 1000.0     # $/day loss limit, $50K EOD account
MAXDD = 2000.0   # $ max EOD trailing drawdown, $50K
MNQ_PT = 2.0     # $/index-point on 1 MNQ (micro)


def eq_risk(tr):
    tr = tr.copy()
    tr["risk"] = (tr.entry - tr.sl).abs()
    tr["usd"] = (tr.pnl / tr.risk) * 100.0
    return tr


def daily(tr):
    return eq_risk(tr).groupby("date").usd.sum()


def report(name, s):
    eq = s.cumsum()
    dd = (eq - eq.cummax()).min()
    print(f"  {name:9} days={len(s):>4} worst_day=${s.min():>7,.0f} "
          f"dailyMaxDD=${dd:>7,.0f} days<-$1k={int((s < -DLL).sum()):>2} total=${s.sum():>8,.0f}")
    return s.min(), dd


def main():
    print("Building M9 combo + M5 scalp + Reversal(maxrisk=30), DAILY aggregation...\n", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    o = M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    m9 = pd.concat([o, t]).reset_index(drop=True)
    m5 = M5.backtest(dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny"), "nq")
    rev = REV.backtest(dict(REV.DEFAULTS, tp="r1", exit="session", bias="off", session="ny", maxrisk=30), "nq")

    d9, d5, dr = daily(m9), daily(m5), daily(rev)
    idx = d9.index.union(d5.index).union(dr.index)
    book = d9.reindex(idx, fill_value=0) + d5.reindex(idx, fill_value=0) + dr.reindex(idx, fill_value=0)

    print("--- per engine (equal-risk $100/1R) ---")
    report("M9", d9)
    report("M5", d5)
    report("Reversal", dr)
    print("\n--- BOOK M9+M5+Rev ---")
    wd, dd = report("book@$100", book)
    report("book@$200", book * 2)

    print("\nWorst 5 book days ($100/1R unit):")
    for d, v in book.nsmallest(5).items():
        print(f"  {d.date()}  ${v:>7,.0f}  (M9 ${d9.get(d, 0):>6,.0f} | M5 ${d5.get(d, 0):>6,.0f} | Rev ${dr.get(d, 0):>6,.0f})")

    s_dll, s_dd = DLL / abs(wd), MAXDD / abs(dd)
    s = min(s_dll, s_dd)
    binding = "DLL (daily)" if s_dll < s_dd else "maxDD (trailing)"
    print(f"\n=== MAX SAFE SIZE  ($50K EOD: DLL ${DLL:,.0f}/day, maxDD ${MAXDD:,.0f}) ===")
    print(f"  worst day ${wd:,.0f} -> DLL allows {s_dll:.2f}x | dailyMaxDD ${dd:,.0f} -> DD allows {s_dd:.2f}x")
    print(f"  MAX SAFE SCALE = {s:.2f}x  (binding: {binding})  =>  ${s * 100:,.0f}/1R unit")
    print(f"  at that size: worst day ${wd * s:,.0f}, maxDD ${dd * s:,.0f}")
    print(f"\nMNQ framing (MNQ = ${MNQ_PT:.0f}/pt): reversal maxrisk=30pt = ${30 * MNQ_PT:.0f} risk/1 MNQ. "
          f"A ${s * 100:,.0f}/1R unit ~= {s * 100 / (30 * MNQ_PT):.1f} MNQ on a 30pt SL "
          f"/ {s * 100 / (15 * MNQ_PT):.1f} MNQ on a 15pt SL (caps: MFFU 40 micros, TopStep 50).")


if __name__ == "__main__":
    main()
