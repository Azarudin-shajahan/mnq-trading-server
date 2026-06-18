# SSMT → PSP → 1m PD-array engine — design spec

**Date:** 2026-06-14
**Status:** design (pending implementation plan)
**Engine file (to build):** `backtest/ssmt_psp_engine.py`

## 1. Purpose & motivation

Test the **multi-timeframe top-down ICT/GxT model** as the source material actually
specifies it, for the first time. The model:

> 6H SSMT (HTF cross-asset divergence) → 15m PSP (MTF strength-switch confirmation)
> → 1m order-flow shift via CISD + PD-array entry → target the first opposing swing
> ("low-hanging fruit") → stop behind the CISD-protected swing.

### Why this is NOT a re-run of the dead SSMT engines
We have killed SSMT twice (`ss_trigger_engine.py`, `ss_continuation_engine.py`) — but
both were **single-decision-timeframe gates** on prior-day-high/low sweeps with a same-bar
companion check. Our own backlog flags the real model was never built:
- **Item 144:** the live system "enters a market order at the SMT signal candle close …
  **Completely skips steps 2-4**" (shift → first-swing → retrace). "Cannot be tested as a
  scoring tweak — **requires a new state machine**." → deferred.
- **Item 133 (GxT Aligned Sequence — LTF model nested inside HTF model = GxT's
  highest-conviction setup):** the live system "scores each timeframe's signals
  independently with **no check** for whether the LTF entry matches the HTF model." → deferred.

So "SSMT is DEAD" applies to the **degenerate single-TF form only**. The nested HTF→MTF→LTF
cascade with proper resolution at each level has never been built or tested. This spec builds
exactly that.

### Corpus grounding (the model is a 3-tradition synthesis)
- **GxT Item 133** — nested LTF-inside-HTF Universal Sequence (the cascade).
- **GxT Item 134 (Order Pairing)** — target = nearest opposing swing (standard) vs full-range
  opposing **failure swing** (aggressive). Governs the `--target` flag.
- **Daye (Item 144)** — SMT → structure shift → first post-shift swing = engineered TP →
  retrace into FVG/Breaker/True-Open → enter on the retrace.
- **TTrades (Items 056 / 042)** — **Protected Swing** = a swing confirmed by a **CISD**
  (Change in State of Delivery). CISD = price **closes beyond the *opening price of the first
  candle* of the opposing leg** that created the swing. Stop goes just beyond the protected
  swing, not a fixed tick.

## 2. Trade logic (bullish case; bearish is the exact mirror)

1. **6H SSMT — bias + protected reference.**
   On CME-session-anchored 6H candles (anchor = 18:00 ET), NQ sweeps a prior **6H swing low**
   (low < a prior 6H pivot low) while **either ES or YM fails** to sweep its equivalent low →
   bullish SSMT divergence. The swept 6H low and the divergence timestamp `ssmt_ts` are recorded.
2. **15m PSP — Stage-1 confirmation (strength switch).**
   After `ssmt_ts`, the first 15m candle where NQ closes **opposite color** to the same
   companion (NQ bearish close / companion bullish close) → `psp_ts`. PSP must occur within a
   bounded window after the SSMT (config `psp_window_h`, default 24h) or the setup expires.
2b. **Stage-2 secondary SMT — GxT two-stage validation (ablatable, default ON).**
   GxT's documented standard setup needs **two** divergence stages, not one (Item 127: Stage 1
   SMT/PSP at a key level **+** Stage 2 = a *secondary* Swing SMT or Strength-Switch PSP). After
   `psp_ts`, require a **secondary SSMT on a configurable timeframe** (`--stage2-tf`, default 90m —
   the layer the content creator described) in the **same bias direction**, within the same
   window → `stage2_ts`. If `--stage2 off`, this layer is skipped (1-stage mode) for ablation.
   The 1m entry search then starts at `stage2_ts` (or `psp_ts` when stage2 is off).
3. **1m order-flow shift (CISD) + PD-array entry.**
   After `psp_ts`, on 1m: a **bullish CISD** confirms the OFS — price closes **above the open
   of the first down-candle of the down-leg that made the most recent 1m swing low**. That same
   displacement leg:
   - prints the **first opposing swing high after the shift** → this is the **TP target**
     (low-hanging fruit), and
   - leaves a **PD array** (FVG / IFVG / OB / breaker) in the bias direction.
   Enter a **limit on the retrace into the first valid PD array** (proximal edge by default).
3b. **Key-level / nested-FVG gate (GxT Item 133, ablatable, default `either`).**
   GxT's "key level" is *an FVG **or** a swing H/L* (Item 127), and its highest-conviction setup
   nests the LTF entry **inside an HTF FVG** (Item 133: "drop to a lower TF and find an *internal
   FVG* at the entry point"). So the chosen 1m entry must satisfy a key-level context per
   `--key-level`: `htf-fvg` = the entry price is nested inside an HTF FVG on `--key-level-tf`
   (default 1h); `swing` = the entry is within `--key-level-tol` pts of the swept SSMT swing;
   `either` = nested-FVG OR near-swing. This implements the "SMT-in-gap vs at-swing" hierarchy
   (Item 2) as a measurable gate rather than baking one branch in.
4. **Stop — CISD-protected swing.**
   `sl = protected_swing_low - buffer`, where the protected swing low is the 1m swing low the
   CISD reversed from (default), or the 6H SSMT low (`--sl ssmt`, wider).
5. **Target.** `--target nearest-swing` (default, the first post-shift opposing swing) or
   `--target failure-swing` (GxT order-pairing: opposing range failure swing, larger).

One setup per SSMT event (no re-entry on the same 6H divergence).

## 3. PD-array definitions (each an ablatable detector, bullish form)

- **FVG** — 3-candle imbalance: `low[i+1] > high[i-1]`. Entry zone = `[high[i-1], low[i+1]]`;
  limit at proximal edge (nearest price on the retrace = gap top).
- **IFVG (inverse FVG)** — a prior **bearish** FVG that price displaces up through and **closes
  above**; it flips to bullish support. Entry zone = the old bearish gap.
- **OB (order block)** — the **last down-close candle** before the up-displacement leg that
  produced the CISD. Entry zone = that candle's `[low, open]` (or body).
- **Breaker** — the down-candle(s) at the **swept swing low** (failure swing); once structure
  shifts up (CISD), that candle acts as support. Entry zone = its body.

First valid array (earliest forming, in bias direction, fully above SL) wins. `--arrays`
toggles the active set so each can be isolated.

## 4. Components (isolated, testable; in `backtest/ssmt_psp_engine.py`)

| Function | Responsibility | Returns |
|---|---|---|
| `resample_tf(df_et, rule, anchor)` | resample 1m→any TF (6H, 90m, …), CME-anchored; **proper IST→America/New_York tz convert** (precedent: `diagnostics/org_driver_falsifier.py` — fixed-offset IST is wrong for an exact ET anchor) | per-inst OHLC |
| `pivots(highs, lows, n=3)` | n-bar fractal swing highs/lows | index arrays |
| `find_6h_ssmt(df6h, inst, companions, upto_ts)` | NQ sweeps a prior 6H pivot, companion(s) per `--companion` do not | `(bias, protected_level, ssmt_ts)` or `None` |
| `find_15m_psp(df15, inst, comp, after_ts, window_h)` | first opposite-color 15m close after SSMT (Stage 1) | `psp_ts` or `None` |
| `find_secondary_smt(df_tf, inst, companions, bias, after_ts, window_h)` | Stage-2 same-bias SSMT on `--stage2-tf` (default 90m) after the PSP | `stage2_ts` or `None` |
| `htf_fvgs(df_tf, bias, upto_ts)` | active bias-direction FVG zones on `--key-level-tf` formed before the entry | `[(lo, hi), …]` |
| `passes_key_level(entry, bias, fvg_zones, swing_level, mode, tol)` | nested-FVG / near-swing key-level gate (GxT Item 133/127/2) | `bool` |
| `is_displacement(o,h,l,c, idx, frac)` | candle idx body/range ≥ frac (ICT displacement existence rule) | `bool` |
| `htf_bias(df_tf, upto_ts, n)` | HTF structural bias from last two pivots (HH/HL=bull, LL/LH=bear) — TTrades Item 53 | `"bull"/"bear"/"none"` |
| `in_macro(ts_et, windows)` + `MACRO_WINDOWS` | entry inside an algorithmic macro window | `bool` |
| `prior_day_levels(df_et)` | per-date prior-day high/low (PDH/PDL "easiest draw") | `{date:(pdh,pdl)}` |
| `find_cisd_entry(df1m, after_ts, bias, arrays, sl_mode)` | bullish/bearish CISD → first PD array → entry/sl/target/protected swing | `(entry, sl, tp, target_swing, entry_ts)` or `None` |
| (reuse) `walk_limit_1m`-style 1m fill + walk | resolve fill + exit on **1m, from the bar after fill** | `(outcome, pnl)` |
| `stats` / `peryear` | reuse M9 reporting | metrics |

Reused helpers from `model5_intraday_engine.py` / `model9_oneshot_engine.py`:
`_load_1m`, the 1m fill/walk pattern, `in_kz`, `stats`, `peryear`. New 6H resample +
SSMT/PSP/CISD detectors are written fresh.

## 5. Rigor gates (non-negotiable — from the project graveyard)

1. **1m fill resolution**, walk from the bar **after** the limit fills — no entry-bar lookahead
   (M5 / Asia-1H-FVG lesson).
2. **No-lookahead everywhere** (see the plan's "Lookahead Safety Invariants"): fractal pivots are
   only usable once confirmed (`j + n < i`); HTF events (6H/90m SSMT, 15m PSP) fire at bar **close**
   = label + timeframe, not the label; the 1m limit goes live only from `confirm_idx + 1` (after the
   CISD close), never at the PD-array bar; the TP is **causal** (the impulse peak observed before the
   fill, or a prior-day PDH/PDL) — never a swing that forms after entry.
3. **Random-direction null (≥500 seeds)** — mandatory for any directional driver (ORG lesson).
   The model must beat the null distribution (report its percentile), not just post a per-year PF.
4. **Tail test** — drop the top-3 winners; if PF collapses below ~1.0 it is tail-noise
   (SSMT-v2 lesson).
5. **Per-year breakdown** — "every-year-positive on 2020–2024" is the bar.
6. **Data provenance** — develop on `MULTI_1min/15min_IST_2020_2024.csv` + the 2020_2024 6H
   resample (these truly end 2024-12-31). **Keep 2025+ sealed** as the only clean holdout. No
   "validated" claim before a 2025 holdout run AND a `/research-critiquer` PASS.

## 6. CLI / ablation flags

| Flag | Default | Purpose |
|---|---|---|
| `--exec {nq, failure-swing}` | (run **both**) | trade NQ vs the asset that didn't sweep (test Daye's claim) |
| `--companion {es, ym, either}` | `either` | which companion defines SSMT + PSP divergence |
| `--stage2 {secondary-smt, off}` | `secondary-smt` | GxT two-stage validation: require a Stage-2 secondary SMT after the PSP (ablate to `off` = 1-stage) |
| `--stage2-tf` | `90min` | timeframe for the Stage-2 secondary SMT (the creator's 90m) |
| `--key-level {swing, htf-fvg, either}` | `either` | nested-FVG gate: entry inside an HTF FVG vs near the swept swing vs either (GxT Item 133/127) |
| `--key-level-tf` | `1h` | timeframe whose FVG the 1m entry must nest inside |
| `--key-level-tol` | `20` | pts tolerance for the `swing` key-level branch |
| `--displacement {on, off}` | `on` | require the structure-shift/FVG leg to be a real displacement (strong body) — ICT "no FVG without displacement" |
| `--disp-frac` | `0.5` | min body/range fraction for a displacement candle |
| `--htf-bias {off, 1d, 4h}` | `1d` | gate SSMT direction against HTF daily/4h structural bias (TTrades 3-TF alignment, Item 53) |
| `--macro {session, precise}` | `session` | broad NY killzone vs precise algorithmic macro windows (ICT macros) |
| `--arrays fvg,ifvg,ob,breaker` | all | which 1m PD arrays may trigger (ablate noise) |
| `--target {nearest-swing, pdh-pdl, failure-swing}` | `nearest-swing` | first-swing low-hanging fruit / prior-day H-L "easiest draw" / GxT order-pairing |
| `--sl {local, ssmt}` | `local` | CISD-protected 1m swing vs wider 6H SSMT low |
| `--anchor-et HH:MM` | `18:00` | 6H CME-session anchor |
| `--psp-window-h N` | `24` | max hours SSMT→PSP before expiry |
| `--session {ny, all}` | `ny` | entry killzone gate |
| `--pivot-n N` | `3` | fractal pivot strength |

## 7. Success criteria (what makes it "alive")

A configuration is a candidate **only if it clears ALL** of:
- beats the random-direction null (entry-direction edge, not just any-direction movement);
- survives drop-top-3 (PF stays > ~1.0 without the top 3 trades);
- every-year-positive 2020–2024;
- holds up on the **sealed 2025 holdout** (PF and per-year sign retained);
- passes `/research-critiquer` (independent reproduction).

Otherwise it is logged honestly to gotchas as another dead end and not deployed. Even a PASS is
**in-sample / necessary-not-sufficient** until live-demo OOS (per the data-provenance reframe).

## 7b. Fidelity gates (added after a full corpus re-audit)

The cascade order matches the source (SMT→MSS/CISD→retrace→first-swing→protected stop). The
re-audit surfaced four book-required conditions, all added as ablatable gates:
- **Displacement** (`--displacement`) — ICT: an FVG/shift is only tradable if it forms on
  displacement; the structure-shift candle must be strong-bodied (`is_displacement`).
- **HTF bias alignment** (`--htf-bias`) — TTrades Item 53 3-TF alignment: block an SSMT whose
  direction opposes the daily/4h structural bias (`htf_bias`).
- **Macro-time precision** (`--macro precise`) — ICT macros (e.g. 9:50–10:10 ET) beyond the broad
  NY killzone (`in_macro`).
- **PDH/PDL target** (`--target pdh-pdl`) — TTrades "easiest draw" baseline (`prior_day_levels`).

**Ablation runs BOTH ways** (per decision): (A) **forward selection** — start from the minimal
cascade that produces trades, add one gate at a time, measure marginal contribution; (B)
**all-on then ablate** — every gate ON (max GxT fidelity), remove one at a time. (A) avoids the
near-zero-trade trap; (B) gives the strict-fidelity baseline. Report both.

## 7c. Dual-spine architecture (decision 2026-06-17: build BOTH, ablate)

The TTrades-corpus gap-pass found two distinct spines that SHARE most machinery. Build both behind
`--spine` and let the data choose:

- **Spine A — `smt-cascade` (GxT/Daye; the original spec above):** 6H SSMT → 15m PSP → 90m Stage-2
  SSMT → 1m CISD/PD-array entry. SMT divergence IS the trigger.
- **Spine B — `c2c3-closure` (TTrades-native Fractal Model):** a **daily candle closure** sets bias;
  on the swing TF a **C2 closure** (sweep the prior candle + close **back inside** its range =
  reversal closure) — or, if C2 fails, a **C3 closure** (close over/engulf the C2 body *without*
  sweeping) — anticipates the expansion candle; entry on the exec TF inside **Equilibrium**
  (discount for longs / premium for shorts) via the 1m T-Spot IFVG. **SMT is an optional confluence
  toggle here, not the trigger.**

**Shared machinery — write once, both spines use it:** the 1m CISD entry + PD-array fill
(`find_cisd`, `pd_arrays_*`, `walk_setup`), the **CISD-protected-swing** stop, the target system
(first-swing / PDH-PDL / failure-swing), the killzone/macro gates, the **swing-significance filter**,
and **`lookahead_guard`**. Only the *setup-selecting trigger* differs.

New components for Spine B:
- `candle_closure(o,h,l,c, i, bias)` → `"c2" | "c3" | "continuation" | None`. Reversal closure =
  sweep prior candle high/low + close back inside its range; C3 = close over/engulf the C2 body
  with no sweep; continuation = sweep + close beyond.
- `equilibrium(prev_o, prev_h, prev_l, prev_c)` → 50% level; `in_discount(price, eq)` /
  `in_premium(price, eq)`.
- `relevant_swing(...)` → swing-significance: failure (too close, < range-expansion separation) vs
  relevant; 3-HTF-candle lookback; **valid swing = POI + a valid C2/C3 closure** (applies to BOTH spines).

New flags: `--spine {smt-cascade, c2c3-closure}` (ablation runs both); `--eq-zone {on, off}`
(require premium/discount entry, Spine B default on); `--swing-sig {on, off}` (significance filter,
both spines); TF nest via `--tf-bias/--tf-swing/--tf-exec` (default TTrades **D/4H/15m** for Spine B;
6H/90m/1m for Spine A).

**Ablation:** Spine A vs Spine B head-to-head on identical data, each through the SAME
null / drop-top-3 / 2025-holdout / `lookahead_guard` gates; report which spine (if either) clears
all success criteria. Neither is assumed superior.

## 8. Out of scope (YAGNI for v1)

- Partials / runners (book mentions "partials at B pool" — single clean TP first).
- Gold/oil/RTY cross-index (indices triad only: nq/es/ym).
- True-Open entry zone (FVG/IFVG/OB/breaker cover the entry; add later if needed).
- **Wickless-candle fake-SMT filter** (GxT Item 128 — a wickless candle at the SMT level = fake,
  expect revisit). A real GxT filter; add as an ablatable gate in v2 if the core shows edge.
- **Two-Stage-PSP alternative** (GxT Item 127 — PSP-first when there's no SMT at the level).
  v1 fixes Stage-1 = PSP, Stage-2 = secondary SMT; the swapped ordering is a v2 option.
- **FVG-inside-expansion entry / Model 12** (ICT Item 88 — enter the FVG that forms *inside* the
  expansion swing, not at the OB). v1's first-PD-array proximal entry is a coarse proxy; the
  Model-12 refinement is a v2 option once the nested-FVG gate proves useful.
- Live wiring / Railway (research engine only).
