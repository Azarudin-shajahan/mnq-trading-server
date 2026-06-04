# Critique — Reversal engine refinement (maxrisk=20 filter)

**Date:** 2026-06-04 (Session 38) · **Judge:** independent read-only subagent (re-ran both diagnostics) · **Artifact:** `backtest/reversal_engine.py` + `diagnostics/reversal_maxrisk_sweep.py` + `diagnostics/reversal_vs_book.py`

## VERDICT: REVISE
Numbers reproduce and the merge improvement is real, but the headline rests on a single tuned threshold and a mixed PF surface; several honesty disclosures are missing.

## FINDINGS
- **[BLOCKER] maxrisk=20 is a cliff, not a plateau.** Judge re-ran finer: `maxrisk=22` breaks every-year-positive (2020 pf 0.94); `25` also (2020 0.96). Only `20` clears the every-year bar -> single tuned threshold. The "plateau at 25/30/15" argument referred to ret/DD magnitude, not the every-year gate. **Fix:** re-sweep fine (~26-34) to find a *contiguous* every-year-positive band; adopt a threshold inside it (candidate `maxrisk=30`: every-year-positive min 1.13, 164 trades, merge 85.5) OR scope the claim as "20 is the single every-year-positive point; 2020 is the marginal year." The **slot itself is robust** (3-engine > 2-engine at 20/25/30) - only the standalone every-year headline is fragile.
- **[BLOCKER] PF surface mixed.** Cited "PF 3.14" = equal-risk *weekly* PF; engine `show()` raw trade-level PF = 2.23; the per-year pf column is raw. **Fix:** label every PF/number with its surface (raw-trade vs equal-risk-weekly); don't mix in one line.
- **[WARN] SL anchored to all-day range** (running max/min from 00:00 IST, incl. pre-killzone bars), not killzone-scoped. NOT lookahead (contemporaneous), but undisclosed. **Fix:** document; note maxrisk=20 thereby selects days whose whole range-to-entry is <=20pt.
- **[WARN] WR 72.8% is a 5m-bar UPPER BOUND.** 51/103 trades have a bar where SL+TP both breach; resolved SL-first (correct convention) but 36 labeled WIN are optimistic vs 1m. **Fix:** disclose; recommend a 1m re-run (same method used to isolate the GxT 2024-03-19 ES loss).
- **[WARN] 2026 = partial year**, 2 trades, 9.99 sentinel -> annotate partial in any "every year positive" line.
- **[WARN] Merge magnitude is threshold-sensitive:** 3-engine return/DD = 102.4 / 101.8 / 85.5 at maxrisk 20 / 25 / 30. Present all three, not just the peak.
- **[NIT]** Sweep not strictly monotonic above 40 (50:4.8 < 60:5.9); peaks at 20, turns back at 15 -> reinforces "20 is the optimum" (the BLOCKER), not a plateau.
- **[NIT]** Grounding clean: qmd `ict_transcripts` "turtle soup" 91% match incl. live-execution videos. Mechanic is canonical ICT, not invented.

## GROUNDING CHECKS RUN (judge, independent)
- Both diagnostics re-run -> reproduce exactly (sweep off->20: 5.1->23.5; merge 77.5->102.4, maxDD -$500, corr -0.08).
- maxrisk 22/25 standalone -> break 2020 every-year-positive; 30 holds (min 1.13). Merge at 25->101.8, 30->85.5 (both still earn slot).
- Lookahead: find_reversal entry=cl[k], SL=running max/min<=k, pdh/pdl via .shift(1) -> clean. walk_intraday SL-first, ambiguity post-entry only.
- qmd grounding for turtle soup confirmed.

## Resolution status (updated 2026-06-04)
- **BLOCKER 1 RESOLVED with data:** fine sweep found a CONTIGUOUS every-year-positive band **28/30/32** (min yr pf ~1.13); 26 (2020:0.96) and 34 (2023:0.96) fail -> a real plateau, not a cliff. **Adopted maxrisk=30** (band center, 164 trades). `reversal_vs_book.py` set to 30.
- **BLOCKER 2 RESOLVED:** surfaces labeled -> raw-trade PF **1.46**, equal-risk-weekly PF **2.12**.
- **Robust merge (maxrisk=30):** M9+M5 77.5 -> M9+M5+Rev **85.5** (+10%), maxDD flat -$600, corr **0.01**, +$4,800. Earns a slot (modest, robust) - NOT the overfit 20-peak (102.4).
- **WARNs disclosed:** SL anchored to full-day range (00:00 IST, not killzone start); WR 64.6% is a 5m-bar UPPER BOUND -> **1m re-run is the open validation step**; 2026 partial year (2 trades).
- **STATUS:** ~~blockers cleared; candidate~~ -> **FAILED (cross-index audit 2026-06-04).**

## CROSS-INDEX AUDIT 2026-06-04 -> VERDICT: FAILED (fatal lookahead)
- The 1m re-run exposed a **fatal entry-timing lookahead**. The reversal enters at the reclaim CLOSE `cl[k]` of the 5m bar starting at `emins`; that close is only known at `emins+5`. The original 1m walk started at `emins`, letting pre-signal 1m bars "hit TP" -> the "0 win->loss flips / WR holds" claim was a lookahead artifact.
- **Corrected (enter at `emins+5`, verified both by the judge and independently):** NQ PF 1.46->**0.94** (WR 63.9->49.4%, 23 wins were lookahead); YM PF 1.47->**0.76** (WR 66.3->42.6%, 40 wins lookahead). 5m mins confirmed start-labeled @5-min spacing.
- **CONSEQUENCE:** the reversal has **no executable edge**. The maxrisk filter was tuning a 5m entry-bar lookahead. ALL dependent results are INVALID: the 94.8 book merge, the NQ+YM cross-index, the $286/$200-unit daily-risk sizing. **Reversal SHELVED. Do NOT add to the book. Do NOT commit as validated.**
- **ESCALATION (top priority):** `walk_intraday` starts the sim at the entry bar `k` for **Model 9 and Model 5 too**. If their entries are also close-based (vs a resting OTE *limit* fill), the SAME lookahead inflates the production book. MUST re-run M9/M5 with correct (next-bar / limit-fill) entry timing on 1m before trusting any production number. The whole edge is in question until this is checked.
