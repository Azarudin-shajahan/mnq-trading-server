#!/usr/bin/env python3
"""Book C pre-registered KILL-CRITERION harness (Fable's go-live gate, 2026-06-10).

Purpose: turn the live demo into a REAL out-of-sample test instead of one more
selection draw. Book C (M9 + 0.5*M5-NQ + 0.5*M5-YM) is 100% in-sample / never held
out (see the DATA-PROVENANCE LEAK gotcha). Before the first demo trade we FREEZE the
config and pre-register the threshold below which forward performance falsifies the
edge -- no parameter rescue, no "regime" excuse, no re-tuning on demo data.

Method (Fable's design):
  - Block-bootstrap 12-week segments from the IN-SAMPLE Book C equity curve to get the
    null distribution of a 12-week window's PF and R-sum FOR A GENUINE Book C edge.
  - KILL if realized forward PF (or R-sum) over a same-length window falls below the
    in-sample 5th percentile.
  - Secondary tripwire: forward trade frequency deviating >2x from in-sample
    expectation falsifies the signal-generation PIPELINE, independent of P&L.

Two modes:
  build (default) -- run the frozen engines, bootstrap, write the pre-registration:
      diagnostics/book_c_kill_criteria.json   (machine: weekly arrays + thresholds + hash)
      diagnostics/BOOK_C_KILL_CRITERIA.md      (human: the committed pre-registration record)
  score           -- evaluate a forward demo trade log against the frozen criteria
      python3 book_c_kill_criteria.py --score demo_trades.csv
      demo CSV columns: date,entry,sl,pnl,leg   (leg in {m9,m5nq,m5ym})

ASCII-only source (this Python 3.10 rejects U+2014 in literals).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import model9_oneshot_engine as M9   # noqa: E402
import model5_intraday_engine as M5  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "book_c_kill_criteria.json")
MD_PATH = os.path.join(HERE, "BOOK_C_KILL_CRITERIA.md")

R_USD = 100.0            # equal-risk unit (matches the portfolio diagnostic)
WEIGHTS = {"m9": 1.0, "m5nq": 0.5, "m5ym": 0.5}   # Book C leg weights (FROZEN)
WINDOW_WEEKS = 12        # demo evaluation window
N_BOOT = 20000           # bootstrap resamples
BLOCK_WEEKS = 4          # circular block length (preserves serial correlation)
SEED = 20260610          # frozen so thresholds are reproducible

# FROZEN Book C config (exactly the validated half-budget portfolio).
M9_LEGS = [dict(entry="ote", tp="r2", maxrisk=30),
           dict(entry="turtle", tp="r3", maxrisk=30)]
M5_SCALP = dict(entry="ote", tp="r1", exit="kz", session="ny")


def _weighted_usd(tr, weight):
    """Per-trade equal-risk USD at the Book C leg weight. Needs entry/sl/pnl."""
    risk = (tr["entry"] - tr["sl"]).abs()
    usd = (tr["pnl"] / risk) * R_USD * weight
    out = pd.DataFrame({"date": pd.to_datetime(tr["date"]), "usd": usd})
    return out


def build_book_c_trades():
    """Run the frozen engines, return a dated per-trade weighted-USD frame for Book C."""
    print("loading data + running frozen Book C engines...", flush=True)
    df5m, fvgs, news = M9.load_all()
    data = M9.make_data("off", df5m, fvgs, news)
    m9_parts = [M9.backtest(dict(M9.DEFAULTS, **cfg), data) for cfg in M9_LEGS]
    m9 = pd.concat(m9_parts).reset_index(drop=True)
    m5nq = M5.backtest(dict(M5.DEFAULTS, **M5_SCALP), "nq")
    m5ym = M5.backtest(dict(M5.DEFAULTS, **M5_SCALP), "ym")
    legs = {"m9": m9, "m5nq": m5nq, "m5ym": m5ym}
    frames = [_weighted_usd(legs[k], WEIGHTS[k]) for k in legs]
    counts = {k: int(len(legs[k])) for k in legs}
    allt = pd.concat(frames).reset_index(drop=True)
    print("trades: " + " ".join("%s=%d" % (k, counts[k]) for k in counts)
          + " | total=%d" % len(allt))
    return allt, counts


def weekly_stats(trades):
    """Aggregate per-trade weighted USD into one row per CALENDAR week.

    Full weekly calendar index (zero-filled quiet weeks) so a 12-week bootstrap
    window mirrors a real 12 calendar weeks of demo (quiet weeks included).
    Columns: gp (gross profit), gl (gross loss, positive), rsum (weighted R), count (raw).
    """
    t = trades.copy()
    t["week"] = t["date"].dt.to_period("W-SUN").dt.start_time
    g = t.groupby("week")
    gp = g["usd"].apply(lambda s: s[s > 0].sum())
    gl = g["usd"].apply(lambda s: -s[s < 0].sum())
    rsum = g["usd"].sum() / R_USD
    count = g["usd"].count()
    wk = pd.DataFrame({"gp": gp, "gl": gl, "rsum": rsum, "count": count})
    # week keys are W-SUN period start_times (Mondays); step the full index by 7 days
    # from the same anchor so reindex aligns (date_range freq='W-SUN' would land on
    # Sundays and zero everything out).
    full = pd.date_range(wk.index.min(), wk.index.max(), freq="7D")
    wk = wk.reindex(full, fill_value=0.0)
    wk["count"] = wk["count"].astype(int)
    return wk


def _block_indices(n_weeks, window, block, rng):
    """Circular block bootstrap: contiguous blocks until >= window, trimmed."""
    idx = []
    while len(idx) < window:
        start = rng.integers(0, n_weeks)
        idx.extend([(start + j) % n_weeks for j in range(block)])
    return idx[:window]


def bootstrap(wk, window=WINDOW_WEEKS, n=N_BOOT, block=BLOCK_WEEKS, seed=SEED):
    rng = np.random.default_rng(seed)
    gp = wk["gp"].to_numpy(float)
    gl = wk["gl"].to_numpy(float)
    rs = wk["rsum"].to_numpy(float)
    ct = wk["count"].to_numpy(float)
    nw = len(wk)
    pf = np.empty(n)
    rsum = np.empty(n)
    cnt = np.empty(n)
    for i in range(n):
        ix = _block_indices(nw, window, block, rng)
        sgp, sgl = gp[ix].sum(), gl[ix].sum()
        pf[i] = (sgp / sgl) if sgl > 0 else 999.0   # inf -> cap; only the LOW tail matters
        rsum[i] = rs[ix].sum()
        cnt[i] = ct[ix].sum()
    return pf, rsum, cnt


def _pctiles(a):
    return {str(p): round(float(np.percentile(a, p)), 4) for p in (1, 5, 25, 50, 75, 95)}


def build():
    trades, counts = build_book_c_trades()
    wk = weekly_stats(trades)
    in_start = str(trades["date"].min().date())
    in_end = str(trades["date"].max().date())
    n_weeks = len(wk)
    pf, rsum, cnt = bootstrap(wk)

    pf_kill = round(float(np.percentile(pf, 5)), 4)
    rsum_kill = round(float(np.percentile(rsum, 5)), 4)
    cnt_med = float(np.percentile(cnt, 50))

    weekly_arr = [{"week": str(ix.date()), "gp": round(float(r["gp"]), 4),
                   "gl": round(float(r["gl"]), 4), "rsum": round(float(r["rsum"]), 6),
                   "count": int(r["count"])} for ix, r in wk.iterrows()]

    record = {
        "name": "Book C kill criteria (pre-registered)",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "WARNING": ("Book C is 100% in-sample (engines default to data through "
                    "2026-05-26; never held out). This bootstrap baseline INCLUDES the "
                    "burned 2025-2026 window on purpose (it is the best estimate of a "
                    "real edge's 12-week behaviour). The DEMO is the only clean OOS."),
        "frozen_config": {
            "book": "Book C = M9(ote/r2 + turtle/r3, maxrisk=30) + 0.5*M5-NQ + 0.5*M5-YM",
            "m9_legs": M9_LEGS, "m5_scalp": M5_SCALP, "weights": WEIGHTS,
            "R_USD": R_USD, "m9_cot": "off",
        },
        "in_sample": {"start": in_start, "end": in_end, "calendar_weeks": n_weeks,
                      "trade_counts": counts, "total_trades": int(len(trades))},
        "bootstrap": {"method": "circular block", "n": N_BOOT, "block_weeks": BLOCK_WEEKS,
                      "window_weeks": WINDOW_WEEKS, "seed": SEED},
        "in_sample_12wk_distribution": {
            "PF_percentiles": _pctiles(pf),
            "Rsum_percentiles": _pctiles(rsum),
            "tradecount_percentiles": _pctiles(cnt),
        },
        "KILL_CRITERIA": {
            "primary_PF_below": pf_kill,
            "primary_Rsum_below": rsum_kill,
            "note": ("KILL Book C if a >=8-week demo window's realized PF OR R-sum "
                     "(re-scored at the demo's exact week-length via --score) falls "
                     "below the in-sample 5th percentile for that length. No re-tuning."),
            "secondary_tripwire_tradecount": {
                "expected_per_12wk_median": round(cnt_med, 1),
                "kill_if_outside": [round(cnt_med / 2.0, 1), round(cnt_med * 2.0, 1)],
                "note": "Frequency >2x off in-sample expectation falsifies the pipeline.",
            },
            "demo_protocol": ("Freeze config (this file). Run 8-12 weeks demo at min "
                              "size, target >=40-60 trades across M9+M5-NQ+M5-YM. "
                              "Score with --score. PASS != validated; it only clears "
                              "the one pristine OOS gate."),
        },
        "_weekly": weekly_arr,
    }
    # Integrity hash over the canonical content (excludes the hash field itself).
    record["sha256"] = hashlib.sha256(
        json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()

    with open(JSON_PATH, "w") as f:
        json.dump(record, f, indent=2)
    _write_md(record)
    print("\n=== Book C in-sample 12-week bootstrap (n=%d) ===" % N_BOOT)
    print("  PF   5th/50th: %.2f / %.2f   -> KILL if forward PF   < %.2f"
          % (np.percentile(pf, 5), np.percentile(pf, 50), pf_kill))
    print("  Rsum 5th/50th: %.2f / %.2f   -> KILL if forward Rsum < %.2f"
          % (np.percentile(rsum, 5), np.percentile(rsum, 50), rsum_kill))
    print("  trades/12wk median %.0f  (tripwire outside [%.0f, %.0f])"
          % (cnt_med, cnt_med / 2, cnt_med * 2))
    print("\nwrote %s" % JSON_PATH)
    print("wrote %s" % MD_PATH)
    print("FROZEN sha256: %s" % record["sha256"][:16])


def _write_md(rec):
    kc = rec["KILL_CRITERIA"]
    d = rec["in_sample_12wk_distribution"]
    lines = [
        "# Book C -- Pre-Registered Kill Criteria",
        "",
        "_Generated %s. FROZEN before the first demo trade. sha256 `%s`._" %
        (rec["generated"], rec["sha256"][:16]),
        "",
        "> %s" % rec["WARNING"],
        "",
        "## Frozen config",
        "- %s" % rec["frozen_config"]["book"],
        "- m9_cot=off, R_USD=%.0f, weights=%s" %
        (rec["frozen_config"]["R_USD"], rec["frozen_config"]["weights"]),
        "- In-sample: %s -> %s (%d calendar weeks, %d trades %s)" %
        (rec["in_sample"]["start"], rec["in_sample"]["end"],
         rec["in_sample"]["calendar_weeks"], rec["in_sample"]["total_trades"],
         rec["in_sample"]["trade_counts"]),
        "",
        "## Bootstrap",
        "- %s, n=%d, block=%d weeks, window=%d weeks, seed=%d" %
        (rec["bootstrap"]["method"], rec["bootstrap"]["n"], rec["bootstrap"]["block_weeks"],
         rec["bootstrap"]["window_weeks"], rec["bootstrap"]["seed"]),
        "- 12wk PF percentiles: %s" % d["PF_percentiles"],
        "- 12wk R-sum percentiles: %s" % d["Rsum_percentiles"],
        "- 12wk trade-count percentiles: %s" % d["tradecount_percentiles"],
        "",
        "## KILL CRITERIA (no re-tuning, no regime excuse)",
        "1. **Primary** -- KILL if a demo window's realized **PF < %s** OR **R-sum < %s** "
        "(re-scored at the demo's exact week-length via `--score`, 5th percentile)." %
        (kc["primary_PF_below"], kc["primary_Rsum_below"]),
        "2. **Secondary tripwire** -- KILL the pipeline if trade frequency is outside "
        "**%s** per 12 weeks (median %.0f, >2x deviation)." %
        (kc["secondary_tripwire_tradecount"]["kill_if_outside"],
         kc["secondary_tripwire_tradecount"]["expected_per_12wk_median"]),
        "",
        "## Demo protocol",
        "- %s" % kc["demo_protocol"],
        "",
        "## Scoring forward results",
        "```bash",
        "python3 diagnostics/book_c_kill_criteria.py --score demo_trades.csv",
        "# demo_trades.csv columns: date,entry,sl,pnl,leg   (leg in m9/m5nq/m5ym)",
        "```",
    ]
    with open(MD_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


def score(csv_path):
    if not os.path.exists(JSON_PATH):
        sys.exit("No frozen criteria at %s -- run build first." % JSON_PATH)
    rec = json.load(open(JSON_PATH))
    # Integrity check.
    stored = rec.get("sha256")
    chk = dict(rec)
    chk.pop("sha256", None)
    if hashlib.sha256(json.dumps(chk, sort_keys=True, default=str).encode()).hexdigest() != stored:
        print("WARNING: criteria file hash mismatch -- it was edited after freezing.")

    df = pd.read_csv(csv_path)
    need = {"date", "entry", "sl", "pnl", "leg"}
    if not need.issubset(df.columns):
        sys.exit("demo CSV needs columns %s" % need)
    df["date"] = pd.to_datetime(df["date"])
    df["w"] = df["leg"].map(WEIGHTS)
    if df["w"].isna().any():
        sys.exit("leg must be one of %s" % list(WEIGHTS))
    risk = (df["entry"] - df["sl"]).abs()
    df["usd"] = (df["pnl"] / risk) * R_USD * df["w"]
    weeks = df["date"].dt.to_period("W-SUN").nunique()
    span_weeks = max(1, int(np.ceil((df["date"].max() - df["date"].min()).days / 7)) + 1)
    demo_weeks = max(weeks, span_weeks)

    gp = df["usd"][df["usd"] > 0].sum()
    gl = -df["usd"][df["usd"] < 0].sum()
    real_pf = (gp / gl) if gl > 0 else float("inf")
    real_rsum = df["usd"].sum() / R_USD
    real_count = int(len(df))

    # Re-bootstrap thresholds at the demo's ACTUAL week-length from the frozen weekly arrays.
    wk = pd.DataFrame(rec["_weekly"])
    wk_stats = pd.DataFrame({"gp": wk["gp"], "gl": wk["gl"],
                             "rsum": wk["rsum"], "count": wk["count"]})
    pf_b, rs_b, ct_b = bootstrap(wk_stats, window=demo_weeks,
                                 n=rec["bootstrap"]["n"], block=rec["bootstrap"]["block_weeks"],
                                 seed=rec["bootstrap"]["seed"])
    pf_kill = float(np.percentile(pf_b, 5))
    rsum_kill = float(np.percentile(rs_b, 5))
    cnt_med = float(np.percentile(ct_b, 50))
    cnt_lo, cnt_hi = cnt_med / 2.0, cnt_med * 2.0

    pf_fail = real_pf < pf_kill
    rsum_fail = real_rsum < rsum_kill
    cnt_fail = not (cnt_lo <= real_count <= cnt_hi)
    killed = pf_fail or rsum_fail

    print("=== Book C demo scoring (%d trades over ~%d weeks) ===" % (real_count, demo_weeks))
    print("  realized: PF %.2f | R-sum %.2f | trades %d" % (real_pf, real_rsum, real_count))
    print("  thresholds @%dwk (in-sample 5th pct): PF >= %.2f | R-sum >= %.2f"
          % (demo_weeks, pf_kill, rsum_kill))
    print("  freq band @%dwk: [%.0f, %.0f] (median %.0f)" % (demo_weeks, cnt_lo, cnt_hi, cnt_med))
    print("  PF: %s | R-sum: %s | frequency: %s"
          % ("FAIL" if pf_fail else "ok", "FAIL" if rsum_fail else "ok",
             "TRIPWIRE" if cnt_fail else "ok"))
    print("  VERDICT: %s" % ("KILL (edge falsified -- do NOT re-tune)" if killed
          else ("PASS primary; PIPELINE TRIPWIRE -- investigate frequency" if cnt_fail
                else "PASS (clears the OOS gate; not 'validated')")))
    return 1 if killed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", metavar="DEMO_CSV", help="evaluate a forward demo trade log")
    args = ap.parse_args()
    if args.score:
        return score(args.score)
    build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
