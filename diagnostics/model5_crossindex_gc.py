#!/usr/bin/env python3
"""Cross-index the validated M5 OTE-scalp to GC (gold) -- GxT-cross-check finding.

GxT's cross-check (gxt_execution_posts.csv) showed GC is his #1 traded instrument, but
our scalp book is NQ+YM only (ES/RTY tested DEAD). Same-mechanic extension test.

CRITICAL (RTY lesson, see gotchas): min_imp is an ABSOLUTE-point threshold. GC trades
~1875 vs NQ ~13830, so a fixed min_imp silently over/under-filters. We sweep min_imp
across the FAIR %-of-price band (0.05-0.20% of GC's median), plus points just outside,
so an "alive only when over-filtered / tiny-n" artifact (what killed RTY) is visible.

Verdict gate (honest): GC earns a slot only if it is every-year-positive at FAIR
selectivity (not just the over-filtered tail) AND diversifies Book C (low daily corr).
Even then it is EMPIRICAL (the M5 scalp was validated on indices; GC = translation
hypothesis) -- NOT ICT-grounded -> would need /research-critiquer before "validated".

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import numpy as np   # noqa: E402
import pandas as pd  # noqa: E402
import model9_oneshot_engine as M9   # noqa: E402
import model5_intraday_engine as M5  # noqa: E402

R_USD = 100.0
SCALP = dict(M5.DEFAULTS, entry="ote", tp="r1", exit="kz", session="ny")
GC_MED = 1875.3
# min_imp points: below band, the 0.05-0.20% fair band, above band
SWEEP = [0.5, 0.94, 1.4, 1.88, 2.8, 3.75, 5.6]   # pts (0.94=0.05%, 1.88=0.10%, 3.75=0.20%)


def eq(tr):
    tr = tr.copy()
    tr["risk"] = (tr.entry - tr.sl).abs()
    tr["usd"] = (tr.pnl / tr.risk) * R_USD
    return tr


def pf_year(tr):
    s = eq(tr)
    gp = s.usd[s.usd > 0].sum(); gl = -s.usd[s.usd < 0].sum()
    pf = round(gp / gl, 2) if gl > 0 else float("inf")
    yr = {}
    s["y"] = pd.to_datetime(s.date).dt.year
    for y in sorted(s.y.unique()):
        sy = s[s.y == y]; g2 = -sy.usd[sy.usd < 0].sum()
        yr[int(y)] = round((sy.usd[sy.usd > 0].sum() / g2) if g2 > 0 else 999.0, 2)
    everyyr = all(v >= 1.0 for v in yr.values())
    return pf, int(len(tr)), round(s.usd.sum(), 0), yr, everyyr


def daily(tr):
    s = eq(tr)
    return s.groupby("date").usd.sum()


def main():
    print("loading + running M5 OTE-scalp on GC (min_imp sweep, %-of-price normalized)...", flush=True)
    print("GC median ~%.0f -> fair band 0.05-0.20%% = %.2f-%.2f pts\n" % (GC_MED, GC_MED*0.0005, GC_MED*0.002))
    print("  %-10s %-6s %-7s %-9s %-7s  %s" % ("min_imp", "%price", "PF", "n", "everyYr", "per-year PF"))
    rows = {}
    for mi in SWEEP:
        tr = M5.backtest(dict(SCALP, min_imp=mi), "gc")
        if len(tr) == 0:
            print("  %-10.2f %-6.3f  (no trades)" % (mi, mi/GC_MED*100)); continue
        pf, n, tot, yr, ey = pf_year(tr)
        rows[mi] = tr
        band = "FAIR" if 0.94 <= mi <= 3.75 else ""
        print("  %-10.2f %-6.3f %-7s %-9d %-7s  %s %s"
              % (mi, mi/GC_MED*100, pf, n, "YES" if ey else "no", yr, band))

    # diversification vs Book C (M9 + 0.5*M5nq + 0.5*M5ym), at the mid-band GC config
    mid = 1.88
    if mid in rows:
        print("\n=== diversification check (GC @min_imp=%.2f vs Book C daily) ===" % mid)
        data = M9.make_data("off", *M9.load_all())
        m9 = pd.concat([M9.backtest(dict(M9.DEFAULTS, entry="ote", tp="r2", maxrisk=30), data),
                        M9.backtest(dict(M9.DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data)]
                       ).reset_index(drop=True)
        dnq = daily(M5.backtest(dict(SCALP), "nq"))
        dym = daily(M5.backtest(dict(SCALP), "ym"))
        d9 = daily(m9); dgc = daily(rows[mid])
        idx = d9.index.union(dnq.index).union(dym.index).union(dgc.index)
        bookC = (d9.reindex(idx, fill_value=0) + 0.5*dnq.reindex(idx, fill_value=0)
                 + 0.5*dym.reindex(idx, fill_value=0))
        g = dgc.reindex(idx, fill_value=0)
        corr = bookC.corr(g)
        overlap = ((bookC != 0) & (g != 0)).sum()
        print("  daily corr(GC, Book C) = %.3f  | same-day overlap = %d days  | GC trading days = %d"
              % (corr, overlap, (g != 0).sum()))

        # decisive: does GC EARN a slot? return/DD with vs without, SAME total scalp budget
        def rdd(s):
            eqc = s.cumsum(); dd = (eqc - eqc.cummax()).min()
            return (s.sum() / abs(dd) if dd else float("nan")), dd
        anq = dnq.reindex(idx, fill_value=0); aym = dym.reindex(idx, fill_value=0); a9 = d9.reindex(idx, fill_value=0)
        bookC_gc = a9 + (anq + aym + g) / 3.0   # split the 1-unit scalp budget THREE ways
        print("\n=== does GC earn a slot? (daily equal-risk, SAME total scalp budget) ===")
        for nm, s in [("Book C  (M9 + 0.5*(nq+ym))", bookC),
                      ("Book C+GC (M9 + (nq+ym+gc)/3)", bookC_gc)]:
            r, dd = rdd(s)
            print("  %-30s return/DD %6.1f   maxDD $%7.0f   total $%7.0f" % (nm, r, dd, s.sum()))
        print("  -> GC earns a slot only if Book C+GC return/DD > Book C OR maxDD materially lower.")

    print("\nVERDICT GUIDE: GC qualifies only if every-year-positive across the FAIR band "
          "(0.94-3.75pt), not just the over-filtered tail (the RTY trap), AND daily corr is "
          "low. If PF is good only at min_imp>=3.75 with small n -> over-filter artifact = DEAD. "
          "If it qualifies it is EMPIRICAL (gate via /research-critiquer before 'validated').")


if __name__ == "__main__":
    main()
