#!/usr/bin/env python3
"""
Half-budget M9+M5 portfolio + does M5-YM (empirical scalp) earn a slot as a DIVERSIFIER
of the existing scalp budget (NOT added budget)?

M5-NQ and M5-YM are ~uncorrelated (daily PnL -0.02) but 75% same-day + same-bias, so YM
should not be treated as NEW risk budget; it should SPLIT the one index-scalp unit across
two uncorrelated instruments (free DD reduction at the SAME total budget if the edge is real).

Books (equal-risk $100/1R, weekly P&L):
  A = M9(full) + M5-NQ(full)                 <- current production book
  B = M9 + M5-NQ + M5-YM (all full)          <- naive add = 2x index-scalp risk (reference only)
  C = M9(full) + 0.5*M5-NQ + 0.5*M5-YM       <- YM diversifies the SAME scalp budget as A
Daily aggregation -> worst day + max safe MNQ size vs a $50K EOD account (DLL $1k / maxDD $2k).
Read-only; imports the validated engines.
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import pandas as pd
import model9_oneshot_engine as M9
import model5_intraday_engine as M5

R_USD = 100.0
DLL = 1000.0
MAXDD = 2000.0
MNQ_PT = 2.0


def eq(tr):
    tr = tr.copy()
    tr["risk"] = (tr.entry - tr.sl).abs()
    tr["usd"] = (tr.pnl / tr.risk) * R_USD
    return tr


def weekly(tr, from_date=False):
    if from_date:
        tr = tr.copy()
        tr["week"] = tr["date"].apply(M5.week_start)
    return tr.groupby("week").usd.sum()


def daily(tr):
    return eq(tr).groupby("date").usd.sum()


def pf_dd(s):
    gp = s[s > 0].sum()
    gl = -s[s < 0].sum()
    pf = round(gp / gl, 2) if gl > 0 else float("inf")
    eqc = s.cumsum()
    dd = (eqc - eqc.cummax()).min()
    return pf, dd


def line(nm, s):
    pf, dd = pf_dd(s)
    r = s.sum() / abs(dd) if dd else float("nan")
    return f"  {nm:30} total ${s.sum():>8,.0f}  PF {pf:>5}  maxDD ${dd:>8,.0f}  return/DD {r:>5.1f}"


def main():
    print("building M9 combo + M5-NQ + M5-YM scalps (equal-risk $100/1R)...", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    o = M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data)
    t = M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)
    m9 = eq(pd.concat([o, t]).reset_index(drop=True))
    sc = dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny")
    m5nq = eq(M5.backtest(dict(sc), "nq"))
    m5ym = eq(M5.backtest(dict(sc), "ym"))

    w9 = weekly(m9)
    wnq = weekly(m5nq, True)
    wym = weekly(m5ym, True)
    idx = w9.index.union(wnq.index).union(wym.index)
    a9 = w9.reindex(idx, fill_value=0.0)
    anq = wnq.reindex(idx, fill_value=0.0)
    aym = wym.reindex(idx, fill_value=0.0)

    print(f"\ntrades: M9={len(m9)} M5-NQ={len(m5nq)} M5-YM={len(m5ym)}")
    print("=== weekly equal-risk Pearson corr ===")
    print(f"  M9-M5nq {a9.corr(anq):.2f} | M9-M5ym {a9.corr(aym):.2f} | M5nq-M5ym {anq.corr(aym):.2f}")

    A = a9 + anq
    B = a9 + anq + aym
    C = a9 + 0.5 * anq + 0.5 * aym
    print("\n=== BOOKS (weekly equal-risk) ===")
    print(line("A M9+M5nq (production)", A))
    print(line("B M9+M5nq+M5ym (full=2x scalp)", B))
    print(line("C M9+0.5*(M5nq+M5ym) HALF", C))

    print("\n=== per-year return/DD: A (production) vs C (YM half-budget diversifier) ===")
    yrs = sorted(set(idx.year))
    for nm, s in [("A", A), ("C", C)]:
        cells = []
        for y in yrs:
            sy = s[s.index.year == y]
            _, dd = pf_dd(sy)
            cells.append(f"{y}:{(sy.sum() / abs(dd) if dd else 0.0):.1f}")
        print(f"  {nm} return/DD: " + " ".join(cells))

    d9 = daily(m9)
    dnq = daily(m5nq)
    dym = daily(m5ym)
    di = d9.index.union(dnq.index).union(dym.index)
    bookA_d = d9.reindex(di, fill_value=0) + dnq.reindex(di, fill_value=0)
    bookC_d = d9.reindex(di, fill_value=0) + 0.5 * dnq.reindex(di, fill_value=0) + 0.5 * dym.reindex(di, fill_value=0)
    print("\n=== DAILY (equal-risk $100/1R) ===")
    for nm, bd in [("A book", bookA_d), ("C book", bookC_d)]:
        eqc = bd.cumsum()
        dd = (eqc - eqc.cummax()).min()
        print(f"  {nm:7} worst_day ${bd.min():>7,.0f}  dailyDD ${dd:>8,.0f}  "
              f"days<-$1k {int((bd < -DLL).sum())}  total ${bd.sum():>8,.0f}")

    wd = bookC_d.min()
    eqc = bookC_d.cumsum()
    ddC = (eqc - eqc.cummax()).min()
    s = min(DLL / abs(wd), MAXDD / abs(ddC))
    binding = "DLL (daily)" if DLL / abs(wd) < MAXDD / abs(ddC) else "maxDD (trailing)"
    print("\n=== MAX SAFE SIZE for book C ($50K EOD: DLL $1k/day, maxDD $2k) ===")
    print(f"  worst day ${wd:,.0f} | dailyDD ${ddC:,.0f} -> max scale {s:.2f}x "
          f"(binding {binding}) = ${s * 100:,.0f}/1R unit")
    print(f"  MNQ: a ${s * 100:,.0f}/1R unit ~= {s * 100 / (15 * MNQ_PT):.1f} MNQ on a 15pt SL "
          f"(${15 * MNQ_PT:.0f} risk/1MNQ)")

    rA = A.sum() / abs(pf_dd(A)[1])
    rC = C.sum() / abs(pf_dd(C)[1])
    print(f"\nVERDICT: YM earns a half-budget DIVERSIFIER slot if C return/DD ({rC:.1f}) > A ({rA:.1f}) at the "
          f"SAME total budget, OR C maxDD < A maxDD. If C ~ A -> YM is capacity (sizing headroom), not edge.")


if __name__ == "__main__":
    main()
