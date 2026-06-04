#!/usr/bin/env python3
"""Sweep --maxrisk (wide failed-raid filter) on the validated reversal config to test
whether equal-risk weekly return/DD lifts from ~5 toward ~10+ - the bar (session_state)
to re-test merging the reversal engine into the M9+M5 book. Read-only: runs
reversal_engine.backtest at varying maxrisk; changes nothing in the engine or production.
"""
import sys

sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import reversal_engine as REV
import model9_oneshot_engine as M9
import reversal_vs_book as RVB  # reuse eq_risk / weekly_date / pf_dd

BASE = dict(REV.DEFAULTS, tp="r1", exit="session", bias="off", session="ny", days="all")


def row(label, tr):
    s = M9.stats(tr)
    if not len(tr):
        print(f"{label:>8}  n=0")
        return
    wk = RVB.weekly_date(RVB.eq_risk(tr))
    _pf, dd = RVB.pf_dd(wk)
    rdd = wk.sum() / abs(dd) if dd else float("nan")
    yr = " ".join(f"{y}:{v[3]}" for y, v in M9.peryear(tr).items())
    print(f"{label:>8}  n={s['n']:>3} wr={s['wr']:>4}% pf={s['pf']:>4} "
          f"tot=${wk.sum():>7,.0f} maxDD=${dd:>7,.0f} ret/DD={rdd:>5.1f} | yr pf {yr}")


def main():
    print("REVERSAL maxrisk sweep (tp=r1 exit=session bias=off NY, NQ) - equal-risk $100/1R weekly\n")
    for mr in [0, 60, 50, 40, 35, 30, 25, 20, 15]:
        row("off" if mr == 0 else str(mr), REV.backtest(dict(BASE, maxrisk=mr), "nq"))


if __name__ == "__main__":
    main()
