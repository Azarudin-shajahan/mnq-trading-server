---
artifact: diagnostics/model5_crossindex_gc.py
audited: 2026-06-12
auditor: independent research-critiquer (separate context, no build involvement)
verdict: PASS
---

# VERDICT: PASS
SUMMARY: GC cross-index numbers reproduce exactly; dilutive verdict is correct and
honest; three WARNs (lower fair-band boundary framing, missing in-sample label in
GC gotchas entry, MFFU Full-GC ban undisclosed) do not block the verdict given the
WARNs are non-production-decision items and the primary production decision (GC does
NOT earn a Book C slot) is unaffected by them.

---

## REPRODUCTION

Ran: `cd ~/mnq_trading && /usr/local/bin/python3 -u diagnostics/model5_crossindex_gc.py`

| min_imp | %price | PF   | n   | everyYr | per-year range |
|---------|--------|------|-----|---------|----------------|
| 0.94    | 0.050  | 1.15 | 594 | no      | 2020:0.96, 2021:1.67, 2022:1.02, 2023:1.19, 2024:1.03, 2025:1.14 |
| 1.40    | 0.075  | 1.20 | 593 | YES     | 2020:1.02, 2021:1.67, 2022:1.09, 2023:1.19, 2024:1.14, 2025:1.14 |
| 1.88    | 0.100  | 1.18 | 577 | YES     | 2020:1.05, 2021:1.48, 2022:1.04, 2023:1.29, 2024:1.12, 2025:1.15 |
| 2.80    | 0.149  | 1.22 | 559 | YES     | 2020:1.24, 2021:1.46, 2022:1.16, 2023:1.23, 2024:1.20, 2025:1.11 |
| 3.75    | 0.200  | 1.18 | 528 | YES     | 2020:1.18, 2021:1.24, 2022:1.26, 2023:1.00, 2024:1.46, 2025:1.00 |
| 5.60    | 0.299  | 1.01 | 433 | no      | 2020:1.03, 2021:1.02, 2022:0.97, 2023:0.88, 2024:1.26, 2025:0.95 |

Corr(GC, Book C): reproduced -0.019 (claimed -0.02 -- rounds correctly).
Slot test: Book C return/DD 27.1 / maxDD -$900 / total $24,383 reproduced exactly.
Book C+GC return/DD 23.6 / maxDD -$867 / total $20,499 reproduced exactly.

**All four headline numbers MATCH the gotchas record exactly.**

Provenance note on claim 1 framing: the *audit spec* characterizes claim 1 as
"every-year-positive across the FAIR band (0.94-3.75 pts)". The actual output shows
0.94pt = everyYr=NO (2020: 0.96). The gotchas entry correctly records this as
"min_imp 1.4-3.75pt" (NOT the full 0.94-3.75 band). The gotchas is accurate; the
audit spec's headline-claim wording was a loose paraphrase, not a generator error.
The PF/n ranges cited (1.18-1.22, 528-593) are correct for the everyYr=YES rows only.

---

## FINDINGS

[WARN] "every-year-positive across the WHOLE fair band" phrasing in gotchas is
       ambiguous. The "fair band" is defined as 0.05-0.20% = 0.94-3.75pt, but
       everyYr is achieved only from 1.40pt upward (0.075%). The parenthetical
       "(min_imp 1.4-3.75pt)" rescues it but the leading "WHOLE fair band" could be
       misread as including 0.94pt. Fix: drop "WHOLE" or replace with
       "across the inner fair band (1.4-3.75pt, 4 of 5 fair-band points)".

[WARN] GC gotchas entry does not carry an "in-sample only / data 2020-2026" label,
       even though the data-provenance leak note (top of gotchas) applies equally
       here. The M5 engine uses MULTI_5min_IST_2020_2025.csv (verified max date
       2026-01-01 for GC columns); 2025 is included in the per-year table and is
       burned. The gotchas does say "EMPIRICAL ... would need /research-critiquer
       before 'validated'" which partially covers this, but the explicit
       "in-sample only, pending live-demo OOS" label present for Book C/62T is
       absent here. Low stakes (GC is explicitly excluded from Book C), but
       should be consistent. Fix: append "All numbers in-sample (2020-2026, per
       data-provenance leak note above)." to the GC gotchas entry.

[WARN] MFFU Full-GC ban not disclosed in the script or gotchas. CLAUDE.md states
       "Full Gold (GC) BANNED -- only Micro Gold (MGC) available" on MFFU Builder
       50K. The diagnostic studies GC (full contract); MGC has different
       tick/point values and different liquidity. The "funded-stage / weaker-book
       candidate" framing for GC as a standalone engine is therefore MFFU-blocked
       without an explicit note. Fix: add a CAVEAT to the gotchas GC entry:
       "MFFU note: Full GC BANNED on Builder 50K (only MGC available); a GC
       standalone engine would need re-run on MGC tick/point scale before any
       funded-account consideration."

[NIT]  At min_imp=3.75 (upper bound of fair band), 2023=1.00 and 2025=1.00 exactly.
       The every-year check uses `>= 1.00` so these pass, but they are zero-profit
       years (flat, not strictly positive). The gotchas records "every yr 1.00-1.67"
       which honestly discloses the 1.00 floor. This is acceptable but readers
       should note the upper bound of the fair band is the weakest point.

[NIT]  Script comment says GC is "GxT's #1 traded instrument". The X execution
       data (gxt_execution_posts.csv) shows GC=9 posts out of 48 total (NQ=8,
       YM=6). GC is #1 by narrow margin, not dominant. The script's claim is
       defensible given the count data, but "among GxT's most-traded" would be
       more accurate than "#1".

---

## GROUNDING CHECKS RUN

**A. Grounding completeness -- "EMPIRICAL / not ICT-grounded" label**
Verified by reading all four M5 ICT source transcripts:
- `bcp19tiJZA0__ICT Charter Price Action Model 5 Supplementary Lesson.md`:
  all examples are forex pairs (GBP/USD cable); gold appears as a CONTEXT signal
  ("watching the gold market because if it was to go higher that would make it
  easy for the dollar to go lower") -- inverse-DXY context, not a direct M5 vehicle.
- `JN_uaDDZ0rc__ICT Charter Price Action Model 5 Day Trading`: taught exclusively
  on GBP/USD (British pound). No gold/GC mentions.
- `NB7Bku099tU__ICT Charter Price Action Model 5 Trade Plan`: forex.
- `2fgXDt3T3XE__ICT Price Action Model 5 Algorithmic Theory`: forex ("Forex LTD demo").

Conclusion: "EMPIRICAL (gold scalp = translation hypothesis, not ICT-grounded)" is
CORRECT. ICT Model 5 is a forex-only model; gold appears only as an intermarket
context signal, never as a direct M5 trade vehicle. GC is LESS grounded than YM:
YM is at least the same asset class (equity index) as NQ where M5 was adapted.
GC is a commodity futures instrument -- a second translation hop away from the
source material. The EMPIRICAL label is if anything understated.

**B. Cross-corpora -- GxT GC taught vs traded**
Verified via gxt_execution_posts.csv (48 real executions):
- GC appears 9 times (plus 1 multi-instrument row "ES,YM,GC"), making it ~19-21%
  of posts -- yes, #1 or co-#1 with NQ (8 posts).
- GxT's GC entries reference "PDL", "4H C3", "10am", "continuation entry", "Daily lows"
  -- these are NOT M5 OTE-scalp signatures; they are GxT's C3/driver pattern using
  higher targets. GxT's GC trading is a DIFFERENT mechanic from our M5 OTE-scalp.
- Conclusion: the cross-corpora motivation (GxT trades GC heavily -> gap to test) is
  legitimate. But GxT's GC = discretionary C3/driver; our M5 = mechanized OTE-scalp.
  The script correctly flags this as a "same-mechanic extension test", not a
  "reproduce GxT's GC" claim.

**C. Anti-pattern falsification**
- Entry mechanic: `backtest()` calls `M9.find_alt_entry(ocfg, bias, ...)` with
  `entry="ote"` -- the validated OTE finder, not a proxy. No new gates added.
  Equal-risk normalization via `eq(tr)` applied before PF. Confirmed in source.
- No un-ablated discretionary layer added. SD is off by default. No COT/driver/PSP.
- RTY-opposite signature test: min_imp=5.60 gives PF=1.01/everyYr=no -- correctly
  falsifies the over-filter artifact hypothesis. Confirmed in reproduction output.

**D. Overfitting**
- min_imp swept across 7 points spanning 0.027%-0.299% of GC price. The %-of-price
  normalization (the RTY lesson) is implemented: `band = "FAIR" if 0.94 <= mi <= 3.75`
  with the band computed as 0.05-0.20% of GC_MED=1875. Confirmed in script lines 29-30.
- Every-year breakdown shown for all points; robustness of the "no every-yr below 1.40"
  observation confirmed by running the engine directly.
- Slot test uses `SAME total scalp budget` (NQ+YM+GC split by 1/3 each vs NQ+YM at 1/2
  each) -- apples-to-apples in risk budget. Confirmed in lines 98, 100-103.
- "Concentration" (GC's 2021 PF=1.67 dominates the mean): at mid-band 1.88pt,
  2021=1.48, 2020=1.05 -- no single-year carry dominates. 2021 is highest but at 1.48
  vs a floor of 1.04-1.15 in other years; this is within a normal distribution for a
  PF~1.18 strategy. No tail-test concern comparable to the SSMT gotcha (3 trades = 100%
  of profit).

**E. Regime vs bug (%-of-price scaling)**
- Scaling verified: SWEEP = [0.5, 0.94, 1.4, 1.88, 2.8, 3.75, 5.6] with
  GC_MED=1875.3. The comment explicitly states "pts (0.94=0.05%, 1.88=0.10%,
  3.75=0.20%)". The fair-band is printed in the output header:
  "GC median ~1875 -> fair band 0.05-0.20% = 0.94-3.75 pts". Not silently curve-fit.
- RTY lesson applied correctly: the over-filter artifact (5.6pt/0.30%) is tested
  and correctly shows the opposite of RTY (GC alive at fair band, dead at over-filter;
  RTY dead at fair band, alive only at over-filter).

**F. Reproducibility & honesty**
- Reproduce command present in gotchas ("Test (2026-06-12, diagnostics/model5_crossindex_gc.py)").
- Numbers reproduced exactly (all four headline claims match).
- Negatives recorded: GC is explicitly labelled dilutive, not production-ready. The
  "do NOT add GC to Book C; do NOT re-run the cross-index" instruction is unambiguous.
- Data window: MULTI_5min_IST_2020_2025.csv runs to 2026-01-01 for GC columns (verified);
  2025 data included in per-year table (2025: 1.14 at mid-band). In-sample, consistent
  with data-provenance leak note, but not explicitly labelled as such in the GC entry.

---

## FINAL JUDGMENT

All four headline claims reproduce. The three WARNs are:
(1) a wording ambiguity in "WHOLE fair band" (lower boundary fails everyYr),
(2) absent "in-sample only" label in the GC-specific gotchas section,
(3) undisclosed MFFU GC ban for any future standalone use.

None of these affect the primary decision ("GC does NOT earn a Book C slot").
The dilutive verdict is arithmetically confirmed (return/DD 27.1->23.6, -13%).
The EMPIRICAL label is if anything understated (further from ICT grounding than YM).
The method is sound: %-of-price normalized sweep, 1m fill resolver (`walk_limit_1m`
called at line 287 for GC as for NQ/YM), equal-risk PF, apples-to-apples slot test.

The WARNs are documentation gaps only. They should be fixed in the gotchas entry
but do not introduce a BLOCKER under the rubric (no ungrounded production claim,
no un-ablated gate, no single-point threshold, no undisclosed DD spike, no
reproduction mismatch).

**VERDICT: PASS** (with three WARNs to apply as documentation fixes)
