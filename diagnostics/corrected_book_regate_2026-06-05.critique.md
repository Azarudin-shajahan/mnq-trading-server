# Corrected M9+M5 Book - Re-gate (lookahead-completeness)

Date: 2026-06-05 (initial) | RECONCILED 2026-06-08 (Session 38c)

**Scope note**: the dispatched independent judge STALLED (infra, 600s) mid-finding on the lead "reversal
commit only added emins, did not fix walk_intraday(exit_df, k) to k+1". The initial verdict (2026-06-05)
completed that lead by code inspection but got the reversal provenance BACKWARDS - it claimed the recorded
0.94/0.76 was the "un-fixed inflated" number. The 2026-06-08 re-run + reading reversal_refinement.critique.md
corrected this: 0.94/0.76 is the 1m-resolved CORRECT number; the ENGINE SOURCE was the laggard (still 5m-k
-> produced the inflated 1.46). This block is the reconciled verdict and supersedes the earlier reversal
BLOCKER.

```
VERDICT: PASS (production book M9+M5) | reversal record CONFIRMED dead; engine source patched to match.

SUMMARY: The production book (M9 OTE/turtle + M5 OTE-scalp) is correctly lookahead-fixed and its corrected
  numbers stand. Reversal is CONFIRMED dead (0.94/0.76, validated by the 1m re-run on the maxrisk=30
  candidate) and stays SHELVED. The only real defect was that reversal_engine.py SOURCE had never been
  patched (commit c0de8c2 only added the emins field) and still produced the inflated 5m-k 1.46; it is now
  patched to k+1 and reproduces ~0.91-0.95 NQ / 0.85-0.89 YM at 5m, consistent with the 1m 0.94/0.76.
  Record and code now agree.

FINDINGS:
  [RESOLVED] reversal_engine.py:89 walked from k (entry bar), not k+1. Commit c0de8c2 touched it by only
    3 lines (the emins field). FIX APPLIED 2026-06-08: walk from k+1 with a bounds guard (entry = reclaim
    CLOSE cl[k] -> next-bar exec; mirrors M9 turtle / M5). Re-run at the recorded maxrisk=30 config:
    NQ pf 0.91-0.95 (n=164), YM 0.85-0.89 (n=115), NEGATIVE P&L, every-year-positive broken -> reproduces
    the validated 1m 0.94/0.76. Reversal DEAD, stays shelved. The maxrisk filter that had "rescued" it was
    overfit to the 5m entry-bar lookahead (reversal_refinement.critique.md line 34).

  [CORRECTION] The 2026-06-05 draft called 0.94/0.76 "the un-fixed inflated number, mislabeled corrected."
    That was BACKWARDS: 0.94/0.76 is the 1m-CORRECTED number (reversal_refinement.critique.md, enter
    emins+5). The un-fixed 5m-k number was 1.46/1.47. The engine source - not the record - was the error.
    Methodological note: the unfiltered maxrisk=0 5m scan (PF ~1.15) briefly looked alive but is a
    different (looser) population AND a 5m upper bound; not a refutation of the 1m dead number.

  [WARN] model9_oneshot_engine.py:339,365 FVG close-back branch still uses fut=[day5m.iloc[k:]] (k, not
    k+1) -> retains the entry-bar lookahead. NOT production (production M9 = OTE/turtle @303, correct k+1)
    and FVG-CE is already falsified (PF<=0.96), so no production claim is affected. Fix-or-document before
    any future --entry fvg run.

GROUNDING CHECKS RUN (direct code inspection + re-run):
  - M5 walk_limit_1m (model5_intraday_engine.py:129-158): 1m fill window [emins,emins+5), SL-first from the
    true fill, then 5m from k+1. No new lookahead. PRODUCTION = CLEAN.
  - M9 OTE/turtle (model9_oneshot_engine.py:303): fut=[day5m.iloc[k+1:]] -> k+1. CLEAN.
  - Reversal (reversal_engine.py): find_reversal entry=cl[k] (close); exit walk patched to k+1; re-run at
    maxrisk=30 reproduces 0.94/0.76 (n=164/115, negative). DEAD - confirmed, not refuted.
  - Provenance of 0.94/0.76: reversal_refinement.critique.md (2026-06-04) - 1m re-run, enter emins+5,
    23 NQ / 40 YM wins were lookahead; the maxrisk filter was tuning that lookahead.
  - NOT RE-RUN this pass: M9+M5 corrected headline (1.34 / 1.38 / 1.71, book return/DD 26.1), the min_imp
    sweep, every-year-positive post-fix table, A/B grounding. Still open for a full rubric pass.

BOTTOM LINE: production decision unaffected (M9+M5 clean). Reversal dead + shelved (the record was right).
Engine source now patched to reproduce the validated number - code and record finally agree.
```
