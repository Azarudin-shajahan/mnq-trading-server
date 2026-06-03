# Critique — ICT Model 9 "One Shot One Kill" engine

Produced by the `research-critiquer` routine (independent read-only Claude subagent), 2026-06-03.
Artifact audited: `model9_oneshot_result.md` + `backtest/model9_oneshot_engine.py` + `/tmp/m9_multi.log`.

VERDICT: REVISE

SUMMARY: Directionally sound (OTE/turtle edge real, min_imp sweep present, concentration caveat
disclosed) but two BLOCKERs: (1) COT is named as a weekly-bias input but `cot="off"` in every
validated run and was never ablated; (2) "every year positive" is false for the cross-index claim
(ES 2024 PF 0.67 / 2025 0.89; YM and RTY 2020 sub-1) — it holds for NQ only.

FINDINGS:
- [BLOCKER] COT named in spec ("weekly bias = range-expansion + COT") but DEFAULTS `cot="off"`;
  `--combo`/`--multi` hardcode `make_data("off", ...)`; the LAST-STONE sweep iterates
  entry x tp x maxrisk x news only — COT mode is NOT swept. Same grounding-vs-code gap the rubric
  exists to catch. Fix: ablate cot=off/veto/confirm and report delta, OR reword to "COT built but
  off in production; not tested as a toggle."
- [BLOCKER] "EVERY YEAR POSITIVE" is contradicted by the log: ES 2024 PF 0.67, 2025 0.89; YM 2020
  0.78 / 2023 0.81 / 2026 0.85; RTY 2020 0.80. Holds for NQ only (all years >=1.05). Fix: scope the
  claim strictly to NQ; flag RTY 2020 sub-1 and ES/YM weak years; qualify the "edge GENERALIZES"
  cross-index language.
- [WARN] Reproduce command absent from the claims doc. Fix: add `--combo` (NQ) and `--multi`
  (cross-index) commands with data paths.
- [WARN] News-filter ablation directionality ambiguous: code `news=True` = trade ONLY on news days
  (day-selector, line 275-276), not "avoid news". Spec says "news gate degraded performance" — clarify
  which direction was tested.
- [WARN] No execution corpus exists for ICT Model 9 (no X-posts equivalent to GxT). Rubric B requires
  acknowledging the taught-vs-traded gap rather than silently skipping it.
- [NIT] `walk_to_friday` "be" can report a small float as breakeven (label cosmetic; PnL honest).
- [NIT] RTY uses `load_daily` 4h-resample fallback (disclosed, not quantified).

GROUNDING CHECKS RUN:
1. qmd "one shot one kill OTE 70.5" -> zero hits. OTE-as-70.5%-impulse-retrace NOT confirmed in
   `ict_transcripts` text (possible interpolation).
2. qmd "COT commitment traders model 9" -> Month-07 One Shot One Kill transcript (LBlK6JB0QS0, 92%)
   names COT/CFTC -> COT IS a taught Model 9 input, sharpening BLOCKER 1.
3. DEFAULTS line 391-393 `cot="off"`; `--combo` (466) and `--multi` (446) pass `make_data("off")`.
4. /tmp/m9_multi.log: ES 2024 0.67 / 2025 0.89, YM 2020 0.78 confirmed.
5. Sweep lines 529-534: entry x tp x maxrisk x news only; cot not swept.

RUBRIC COVERAGE: A:flag(COT) B:flag(no exec corpus) C:ok(FVG-CE falsified; news dir ambiguous=WARN)
D:flag(BLOCKER on every-year-positive; sweep+DD+concentration otherwise ok) E:ok(fade diagnosed,
scaling rejected) F:flag(no reproduce command).

---

## RE-VERIFICATION 2026-06-03 -> VERDICT: PASS

Generator addressed all findings; independent re-check confirms:
- BLOCKER 1 (COT): RESOLVED with data. Ablation `diagnostics/model9_cot_ablation.py` ran the exact
  production combo (OTE r2 + turtle r3, maxrisk30) three ways: off PF1.47/1380pt/DD-174 (every yr
  >=1.05) BEATS confirm 1.38/1309/DD-188 and veto 1.44/1258/DD-165 (veto breaks 2023->0.98). COT
  adds no edge; `off` is correct and now backed. Method sound (reuses make_data cot_mode, merge_asof
  backward = no lookahead).
- BLOCKER 2 (every-year-positive): RESOLVED. Scoped to NQ-only; RTY 2020 (0.80), ES 2024/25
  (0.67/0.89), YM sub-1 years flagged in the cross-index section.
- WARNs (reproduce cmd / news directionality / no-exec-corpus): all RESOLVED in the claims doc.
STILL OPEN: none. Loop closed: REVISE -> fix-with-data -> PASS.
