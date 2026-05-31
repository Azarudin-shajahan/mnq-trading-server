# Scope - 4H Profiling-Sequence Selector (GxT if-then) as a gate on the 62 entries

## Hypothesis
GxT's if-then: the REVERSAL (manipulation) is put in on ONE 4H leg; the next leg
EXPANDS (continues). Rule: *if 02:00 (London) manipulates -> 06:00 (NY-AM)
continues; if 06:00 manipulates -> 10:00 (NY-PM) continues.* So a fresh V-shape
REVERSAL entry is only valid on the leg that actually manipulates; a reversal
entry on a LATER leg (after the manipulation already happened earlier that day)
is "late" and should be skipped. Test this as a GATE on the existing 62 entries.

## What it is / is NOT
- IS: a binary session-SELECTOR layered on the current FVG-reversal entries
  (keep / drop), using 4H leg classification. NOT a new entry type.
- NOT the 10am DRIVER entry (that = --driver-v2, already tested net-negative).
- NOT the single-bar --h4-direction-gate (that only checks NY-AM 4H direction;
  this adds the cross-leg manipulation->continuation SEQUENCE).

## Mechanical definitions (fixed thresholds - NOT swept, overfit guard)
4H legs (NY time, map to engine IST 4H bars at impl): 02:00=London, 06:00=NY-AM,
10:00=NY-PM. For each leg's 4H candle compute body=|close-open|, range=high-low,
upper/lower wick.
- **Manipulation candle (reversal):** swept one side then closed back ->
  opposing wick >= 40% of range AND close in the opposing 50% of range.
  manipulation_up = long LOWER wick + close in top half; mirror for down.
- **Expansion candle (continuation):** body >= 50% of range AND opposing wick
  <= 25% of range (fluid-motion open, small wick) - reuse the engine's existing
  wick convention (compute_quality_score uses wick_threshold=0.20) for consistency.
- Else: neutral.

## Gate logic (per existing entry, in session S, direction D, day Day)
1. Map S -> its 4H leg (pre_market/ny_am -> NY-AM 06:00 leg; ny_pm -> NY-PM 10:00 leg).
2. Look at PRIOR leg(s) that day. If a prior leg already printed a
   **manipulation candle in direction D** (the reversal was already established),
   then S is "continuation territory" -> a fresh V-shape REVERSAL entry here is
   LATE -> **SKIP**.
3. Otherwise (this leg is itself the manipulation, no earlier reversal printed)
   -> **KEEP**.
(Net effect: enforce "one reversal per daily sequence, on the leg that manipulates.")

## Held fixed vs changed
- CHANGE: add the profiling-sequence gate only. Entries, SL, TP (gap-fill), and
  all existing gates (nq-leads, h4-direction, holiday, cutoff, max-gap) unchanged.
- Runs on the SAME 62 entries -> measures purely keep/drop.

## Metrics & baseline
Baseline 62T PERFECT: **PF inf | WR 100% | DD $0 | Net $289 | 24W/23BE/15EXP**.
Report: trades KEPT vs DROPPED (and WHICH - win/BE/EXP of each dropped), net, DD,
WR, PF, per-session, per-instrument, per-year. Key: did it drop dead trades
(BE/EXP) while keeping all 24 WINs, or did it cut into wins?

## Decision criteria
- 62T is already 100% WR / $0 DD, so the ONLY way this helps = drop BE/EXP (dead
  trades) while keeping ALL 24 wins -> higher PF/efficiency, net >= $289.
- If it drops ANY of the 24 wins -> net-negative -> REJECT (same fate as
  --c3-gate / --erl-gate / --driver-gate / --smt-gate).
- Document either way.

## Overfit guards
- Fixed wick/body thresholds (40% / 50% / 25%), reuse existing 0.20 wick conv;
  NO sweep. Binary keep/drop. Entries unchanged -> cannot be gamed via entries.
- Report per-trade so every drop is inspectable; per-year stability.

## Implementation sketch
- `classify_4h_leg(df_4h, leg_open_ts, inst) -> manip_up/manip_down/exp_*/neutral`.
- `profiling_sequence_ok(df_4h, date, session_label, trade_dir, inst) -> bool`.
- New flag `--profiling-gate`; stat `profiling_gate_skip`. Apply before append.
- **KEY IMPL RISK:** mapping engine sessions -> NY 4H legs precisely (pre_market
  straddles the London/NY-AM 4H boundary; df_4h bar alignment to NY 02/06/10 opens
  must be verified, EDT/EST aware). Get this exact or the gate is noise.

## Prior (expectation, not result)
WEAK. Every added FILTER on 62T PERFECT has SUBTRACTED (c3/erl/driver/smt gates
all removed good trades w/o improving 100% WR). Base rate says this trims trades,
likely cutting wins -> net-negative. But it is genuinely UNTESTED as a selector.

## Effort
~2 functions + 1 gate + flag + one run. ~30-45 min build+run.

## Locked-work boundary
GATE on existing entries only (keep/drop). Does NOT add driver entries (--driver-v2
locked), does NOT touch failure-swing or limit-order/C2 work (all locked). Stays
behind `--profiling-gate`, default OFF; production configs untouched.

## RESULT (2026-05-31) — net-NEGATIVE, REJECT (5th filter to fail on 62T PERFECT)
Built `--profiling-gate` (+ `classify_4h_candle`, `profiling_sequence_skip`,
`_PROF_LEGS`). Baseline 62T/$289 -> **49T/$226 (-$63, -22%)**. Dropped 13 trades =
7 EXPIRED + 2 BE + **4 WINS**, incl the single biggest trade **2024-10-30 ny_am NQ
+$39.25**. DD stayed $0.
**Verdict:** REJECT — dropped wins, not just dead weight (tripped the decision rule).
5th structural filter to fail on 62T PERFECT (after c3/erl/driver/smt gates) ->
LOCKED: the core's wins are NOT separable from its BE/EXP by any filter.
**Caveat:** engine 4H bars are IST-aligned (12/16/20 IST), ~30min off GxT's NY
02/06/10 legs; tested the approximation. Base rate (5 filters failed, cut a $39 win)
says don't chase a NY-aligned re-resample. `--profiling-gate` stays OFF by default.
