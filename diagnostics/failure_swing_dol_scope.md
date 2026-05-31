# Scope — Failure-Swing DOL as TP target (GxT Stage 0.5 lever)

## Hypothesis
The 62T PERFECT engine sets TP = the FAR side of the FVG (`gap_top` bull / `gap_bot`
bear) — i.e. it only targets a full gap-fill. GxT instead targets the **Draw on
Liquidity = the nearest failure-swing cluster** (stacked equal highs/lows), which
is usually BEYOND the gap. Testing whether targeting the failure-swing DOL instead
of gap-fill changes net P&L.

**Why it might help:** of the 62 trades, only 24 are WIN; **23 BE + 15 EXP** = 38
trades that filled little/none before session end. A reachable real-liquidity
target beyond the gap could convert some BE/EXP -> WIN, and lift R on existing wins.
**Why it might hurt:** a farther TP can let a current gap-fill WIN round-trip back
to the fixed SL -> turns WIN into LOSS (this is the key risk to watch; DD could
leave $0).

## What changes vs what's held fixed
- **CHANGE only the TP target.** Entry (`gap_bot`+tick), SL, and ALL gates
  (nq-leads, h4-direction, holiday, cutoff, max-gap, driver-model) stay identical
  -> runs on the SAME 62 entries -> directly comparable to baseline.
- New TP = nearest failure-swing cluster beyond `gap_top` (bull)/`gap_bot` (bear) in
  trade direction; **fallback to gap_top/bot if no cluster found** (isolates effect).

## Mechanization
- **Swings:** fractal on 1H resample (primary), k=2 bars each side. (5m as a
  sensitivity-only variant — report, don't decide on it.)
- **Failure-swing cluster:** >=2 swing highs (bull) within `cluster_tol[inst]` of
  each other; cluster level = the extreme (equal-highs price). Isolated swing =
  "relevant swing" = NOT a target.
- **Target pick (bull):** nearest failure-swing-high cluster with level > gap_top;
  cap search to the session/day range (no targets miles away). Bear = mirror.
- **`cluster_tol[inst]` = fixed, tick-derived, NOT swept** (overfit guard):
  e.g. NQ 4pt, ES 1pt, YM 8pt, GC 1.0, RTY 1.0 (calibrate to tick x small k,
  per-instrument like the Asia GAP_BOUNDS pattern).

## Implementation
- New `find_failure_swing_dol(df, inst, date, direction, gap_top, gap_bot)` ->
  target price or None.
- New `--tp failure-swing` branch at engine line ~1202 (alongside full/half).
- New per-instrument `cluster_tol` dict.
- Re-run the 62T PERFECT config with `--tp failure-swing`.

## Metrics & baseline
Baseline 62T PERFECT (`--tp full`): **PF inf | WR 100% | DD $0 | Net $289 | 24W/23BE/15EXP**.
Report: WR, net, DD, avg R, EXP/BE counts, per-instrument, and a **per-trade delta**
(which BE/EXP converted to WIN, which WIN round-tripped to LOSS), + per-year split.

## Decision criteria
- **Combine-viable** only if DD stays **$0** (no new losses) AND net >= $289.
- **Funded-stage candidate** if net materially higher even with some DD.
- **Reject** (keep gap-fill TP) if it adds losses without a commensurate net gain,
  or net < $289. Document either way.

## Overfit guards
- Fixed tick-derived `cluster_tol` (no sweep), single swing config (1H,k=2).
- Entries unchanged -> result cannot be gamed via entry selection.
- Low N (62) -> report per-trade so every conversion is inspectable; per-year stability.

## Effort
~1 function + 1 TP branch + 1 dict + one re-run. ~30-45 min build+run.

## Locked-work boundary
This touches ONLY the TP target on existing entries. It does NOT re-open drivers,
PSP, C2-continuation, or limit-order entries (all tested & locked). Stays behind
`--tp failure-swing` (default `full` unchanged).

## RESULT (2026-05-31) — SAFE but NOT robustly +EV; funded-stage-only, NOT adopted
Built `--tp failure-swing` (+ `find_failure_swing_dol`, `FS_CLUSTER_TOL`, `--fs-tf`,
`--fs-tol-mult`). Entries/SL/gates held fixed (same 62). Sensitivity sweep:

| tf / tol | Net | W/BE/EXP | vs $289 |
|----------|-----|----------|---------|
| 1h / 1.0   | $312 | 19/27/16 | +$23 |
| 5min / 1.0 | $335 | 16/30/16 | +$46 (best) |
| 30min / 1.0| $239 | 14/31/17 | -$50 (BELOW baseline) |
| 1h / 0.5   | $326 | 20/26/16 | +$37 |
| 1h / 2.0   | $328 | 18/27/17 | +$39 |

ALL variants: WR 100% / DD $0 / 0 losses (feared win->SL round-trip never happened).
**Verdict:** SAFE in every config, but NOT robustly +EV — swing-TF swings it
non-monotonically and 30min goes net-NEGATIVE vs gap-fill; tolerance barely matters
(not the overfit lever). Win-count drops (24->14-20) = P&L concentrated = ADVERSE for
TopStep consistency rule. **Keep `--tp full`; failure-swing is OFF-by-default,
funded-stage-only at best. Do NOT sweep further.**
