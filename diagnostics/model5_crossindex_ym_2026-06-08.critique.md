# Model 5 OTE-scalp cross-index to ES/YM/RTY — research-critiquer verdict (2026-06-08)

Independent read-only critiquer (general-purpose subagent) audited the claim that Model 5
(`--entry ote --tp r1 --exit kz --session ny`) cross-indexes to **YM** as a validation-grade edge.

## VERDICT: REVISE

SUMMARY: YM numbers reproduce and the robustness sweep holds every-year-positive, but the
"validated" label is gated by: (1) the Obsidian spec still cites the pre-lookahead-fix PF 3.84
NQ baseline (corrected = 1.71); (2) the cross-index has NO ICT-source grounding (spec says Model 5
was taught on FOREX; indices = "translation hypothesis"; no YM/ES/RTY in spec or 493 transcripts);
(3) the SD-confluence ("Grail") ablation is still open (same standing item as NQ; parallel to the
Model 9 COT rule). Plus an undisclosed YM max-DD spike and an unstated NQ-YM PF quality gap.

## BLOCKERS (must clear before "validated")
1. **Stale spec baseline.** `ICT_Model5_IntradayVolExpansion_Spec.md` BACKTEST RESULT block still
   says PF 3.84 + "research-critiquer PASS (no lookahead)" (now known-wrong) + return/DD ~60.
   Corrected NQ baseline is **1.71** (recorded only in `model5_scalp_result.md`, never propagated
   to the spec). Any diversifier math normalized against 3.84 is on a superseded surface.
   -> Update spec to PF 1.71; re-derive any diversifier return/DD against corrected numbers.
2. **Cross-index ungrounded.** YM "validation-grade" is a backtest-only empirical finding. Spec
   explicitly flags indices as a translation hypothesis; qmd of 493 ICT transcripts returns no
   Model 5 x YM/ES/RTY content. -> Record YM as an EMPIRICAL cross-index observation (the OTE
   *mechanic* is ICT-grounded via Model 9; the *instrument scope* is not). Keep the translation
   caveat. Do not label "validated" on methodology grounds.
3. **SD-confluence ablation open** (engine line 14: "SD-confluence filter = TODO, off-by-default").
   Named discretionary component, untested across all instruments. -> Run the SD off/CBDR/Asian
   ablation on NQ (primary) at minimum before PASS (same discipline as Model 9 COT).

## WARNS
- **YM max-DD spike**: at min_imp=64.5pt (0.15% of price) maxDD = -552pt vs -293/-316pt at
  neighboring sweep points — a 1.9x mid-band spike, undisclosed. -> Disclose; find the driving
  year; confirm not a regime crack.
- **NQ-YM PF gap**: at matched scale-normalized filters YM 1.47-1.63 vs NQ 1.68-1.79 (~10-15%
  lower). Honest YM floor is the weakest sweep point ~1.41, not the 1.64 headline. -> State the gap.

## What the critiquer INDEPENDENTLY confirmed (clean)
- YM baseline reproduced exactly: pf 1.64, n 632, every-yr 1.22-2.35.
- Scale-normalized sweep: YM every-year-positive at all 5 settings (independently re-run).
- Engine lookahead-clean: only exit path is `walk_limit_1m` (L231); its fallback walks from `k+1`
  (L158), never `k`. No residual entry-bar lookahead.
- NQ-YM daily-PnL correlation = -0.022 (465 overlapping trade-days) — diversification claim holds.

## Generator reconciliation notes (2026-06-08)
- ACCEPT all 3 blockers + 2 warns as valid.
- Core empirical finding STANDS and is unchanged: YM cross-indexes (robust, every-year-positive,
  ~0 corr with NQ); ES fails at every filter; RTY's 1.76 was an overfit artifact of min_imp=20 being
  ~1%-of-price (at fair selectivity RTY fails every-year, now 1m-resolved). The REVISE is about the
  "validated"/production LABEL and documentation hygiene, NOT the numbers.
- Same-direction metric reconciliation: critiquer reported 88% (same trade DIRECTION/bias — expected,
  shared weekly bias); generator reported 58% (same P&L SIGN). Different quantities, both correct;
  the diversification conclusion rests on the -0.02 P&L correlation, which both confirmed.
- ES & RTY are now RECORDED NEGATIVE results (do not re-run as cross-index candidates).

## Status
YM = real empirical edge, **NOT yet "validated"** (REVISE). Clear blockers 1-3 to re-gate.

## RESOLUTION (2026-06-09) — all 3 blockers addressed
- **BLOCKER 1 (stale spec)**: FIXED 2026-06-08 — spec corrected to PF 1.71 + correction banner supersedes the inflated 3.84 block.
- **BLOCKER 2 (ungrounded cross-index)**: ADDRESSED — YM recorded as an EMPIRICAL cross-index observation (OTE *mechanic* ICT-grounded via M9; *instrument scope* empirical), NOT labeled "validated"; translation-hypothesis caveat retained.
- **BLOCKER 3 (SD-confluence ablation open)**: DONE 2026-06-09 — built `--sd {off,confirm,veto}` in `model5_intraday_engine.py` (off-by-default, no-lookahead) + `diagnostics/model5_sd_ablation.py`. NQ: **off 1.71 / confirm 1.66 / veto 1.75** (confirm < off < veto = OPPOSITE of "the Grail"); band-robust (10-25%) + ref-robust (CBDR/Asian/flout). **NON-ADDITIVE → stays OFF like COT.**
- WARNs (maxDD spike at min_imp=64.5; NQ-YM PF gap, floor ~1.41) — floor IS stated in result memory; spike magnitude + PF-gap number were NOT (caught by the re-gate below; now added 2026-06-09).

**Net**: REVISE blockers cleared. YM = cleared-REVISE **EMPIRICAL** edge (half-budget add-candidate).

## INDEPENDENT RE-GATE — VERDICT: PASS (2026-06-09)
Ran a **separate-context** read-only `/research-critiquer` (Explore subagent) that independently **reproduced every number** (not just re-read the claims): YM PF 1.64/n632 exact; scale-normalized min_imp sweep (17/20/35/52/64.5/70pt ≈ 0.05–0.20% of price) **every-year-positive at all 6 points**, band 1.41–1.64 confirmed, floor 1.41 at 0.15% confirmed; source-traced lookahead-clean (`walk_limit_1m` 1m fill → `k+1` fallback, never the 5m entry bar k); SD ablation off/confirm/veto = 1.71/1.66/1.75 exact (confirm<off → NON-additive, partition 1293+1340=2633 clean); Book C return/DD 31.7 vs A 26.1, maxDD -$769 vs -$900, every-year-better, corr 0.20/-0.01/0.11 all exact; EMPIRICAL label consistent across spec+result+critique, no improper "validated"/"ICT-grounded" tag.
- **2 surviving WARNs (disclosure only, not blockers)**: (1) maxDD spike at min_imp=64.5 = -552pt (1.9x the -269/-334 neighbors) was named only in this critique, NOT in result memory/spec → **NOW disclosed in result memory 2026-06-09**; (2) NQ-YM PF gap ~10-20% at matched selectivity (YM floor 1.41 vs NQ 1.64-1.85) was implicit → **NOW stated as a number in result memory 2026-06-09**.
- **NIT**: Book C 2026 return/DD ratio (11.3 vs 4.2 = 2.69x) is a partial-year optic; 2020-2025 (6 full yrs) are cleanly better — do not cite the 2.69x as representative.
**RE-GATE DECISION**: closes prior REVISE → **PASS**. YM = formally-gated **EMPIRICAL** half-budget diversifier (Book C). The improvement over Book A flows from DIVERSIFICATION (corr 0.11/-0.01), not additive capacity, and YM is ~15-20% lower quality than the NQ scalp — preserve both caveats in any production decision.
