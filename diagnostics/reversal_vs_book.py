#!/usr/bin/env python3
"""
(b) decision: does the independent-direction REVERSAL engine add to the M9+M5 book?
Reversal direction = failed liquidity raid (NOT weekly bias) - the one axis M9/M5 lack.
Edge is modest (PF ~1.20) but if its independent direction DECORRELATES and complements
the bias-aligned book, it can still add a diversification axis. Equal-risk ($100/1R).
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import numpy as np
import pandas as pd
import model9_oneshot_engine as M9
import model5_intraday_engine as M5
import reversal_engine as REV

R_USD = 100.0


def eq_risk(tr):
    tr = tr.copy(); tr["risk"] = (tr.entry - tr.sl).abs(); tr["usd"] = (tr.pnl / tr.risk) * R_USD
    return tr


def weekly_date(tr):
    tr = tr.copy(); tr["week"] = tr["date"].apply(M5.week_start)
    return tr.groupby("week").usd.sum()


def pf_dd(s):
    gp = s[s > 0].sum(); gl = -s[s < 0].sum()
    pf = round(gp / gl, 2) if gl > 0 else float("inf")
    eq = s.cumsum(); return pf, (eq - eq.cummax()).min()


def main():
    print("building M9 combo / M5 scalp / Reversal (r1, session, NY)...", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    o = M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    m9 = eq_risk(pd.concat([o, t]).reset_index(drop=True))
    w9 = m9.groupby("week").usd.sum()                # M9 trades already carry a 'week' column
    m5 = eq_risk(M5.backtest(dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny"), "nq"))
    rev = eq_risk(REV.backtest(dict(REV.DEFAULTS, tp="r1", exit="session", bias="off", session="ny"), "nq"))
    w5 = weekly_date(m5); wr = weekly_date(rev)

    idx = w9.index.union(w5.index).union(wr.index)
    a9 = w9.reindex(idx, fill_value=0.0); a5 = w5.reindex(idx, fill_value=0.0); ar = wr.reindex(idx, fill_value=0.0)
    book = a9 + a5                                   # the validated 2-engine book

    print("\n=== REVERSAL vs the M9+M5 book ===")
    print(f"trades: M9={len(m9)} M5={len(m5)} Rev={len(rev)}")
    print(f"corr  M9-Rev: {a9.corr(ar):.2f} | M5-Rev: {a5.corr(ar):.2f} | (M9+M5)-Rev: {book.corr(ar):.2f}")

    def line(nm, s):
        pf, dd = pf_dd(s); r = s.sum() / abs(dd) if dd else float("nan")
        return f"  {nm}: total ${s.sum():>8,.0f} PF {pf:>5} maxDD ${dd:>7,.0f} return/DD {r:>5.1f}"
    print(line("Reversal   ", ar))
    print(line("M9+M5      ", book))
    print(line("M9+M5+Rev  ", book + ar))
    r2 = book.sum() / abs(pf_dd(book)[1]); r3 = (book + ar).sum() / abs(pf_dd(book + ar)[1])
    print(f"\nVERDICT: Reversal earns a slot if (M9+M5)-Rev corr < 0.4 AND 3-engine return/DD "
          f"({r3:.1f}) >= 2-engine ({r2:.1f}). Independent direction may complement despite modest PF.")


if __name__ == "__main__":
    main()
