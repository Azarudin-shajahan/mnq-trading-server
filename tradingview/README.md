# Fractal Model (TTFM Clone)

A faithful open re-implementation of TTrades' closed-source "Fractal Model [Pro+]"
TradingView indicator, built from the ttrades.com 94-article corpus and the published
Toodegrees breakdown video.

**PASSIVE charting/learning tool only.** Uses `indicator()`, no `strategy()`, no webhooks,
no signal authority. Per the project's cockpit-plan v2, the validated Python engine is
the only thing that says "setup now." NOT a trading edge -- the faithful fractal model
backtests dead standalone (IS PF ~1.14, 2 down years). This indicator is for learning to
READ the model, not for generating entries.

---

## The model in one paragraph

The Fractal Model describes a four-candle HTF sequence. C1 is the prior candle whose
extreme (high or low) holds liquidity. C1's extreme is swept by price (the manipulation
leg). C2 is the candle that swept C1 and then CLOSES back inside C1's range (back above
the swept low for bullish, mirror for bearish; a wick-only sweep is NOT a C2) --
the reversal candle. A T-Spot zone marks the anticipated wick area during the C3 period.
C3 is the expansion candle that closes through C2's extreme in the reversal direction,
confirming the swing. C4 is the continuation. A Change in State of Delivery (CISD) on
the LTF (inside the HTF C2 candle) provides the precision entry level. Candle EQ (50%
of the prior HTF candle wick-to-wick) and STDV projections (anchored to the manipulation
leg) frame targets. An Ideal Formation (marked with *) is when C2/C3 closure also closes
through the entire opposing LTF candle series, creating a protected swing on the spot.
Label lifecycle: gray = forming/valid, orange = consolidation warning (did not fail
within the next HTF candle), red = failed (price returned to the initial sweep extreme).
On red, projections, EQ, sweep line, and T-Spot cease plotting for that formation.

---

## Feature map

- **HTF candle panel**: right-of-price candle display (count 0-40, size, offset);
  bull/bear/wick colors; HTF open line; vertical HTF period dividers; previous HTF
  high/low lines (default off); previous-candle EQ line; time labels (24h/AM-PM,
  optional custom IANA timezone); drawing type On Chart / HTF Candle / Both.

- **Pairing ladder**: auto-detection from chart TF or preset selection --
  1m-1s, 5m-15s, 15m-1m, 30m-3m, 1H-5m, 4H-15m, Daily-1H, Weekly-4H, Monthly-Daily.
  Fully custom HTF/LTF pair also available. 1S and 15S rungs are guarded (require a
  seconds-capable chart). TF mismatch (chart TF > model LTF) disables CISD and
  projections and shows a warning in the info table.

- **Formation state machine**: per-direction (bullish/bearish) state tracking --
  WATCHING -> SWEPT -> C2_CLOSED -> CONFIRMED (C3/C4 tracking) -> gray/orange/red.
  History cap 0-40 formations (each = 1 bull + 1 bear instance). Object recycling
  respects Pine's 500-line/box/label budgets.

- **C1 sweep line**: drawn at the C1 extreme; color configurable.

- **LTF CISD engine**: walks LTF bars inside the HTF C2 candle; finds the consecutive
  opposing-close run containing the swing extreme; CISD level = open of the first candle
  of that run. Rendered dashed (pending) until an LTF candle closes through it (solid).
  Optional early-C2 CISD preview (before HTF close, off by default, flagged as preview).

- **Candle EQ + T-Spot**: EQ = 50% of prior HTF candle wick-to-wick range; T-Spot = the
  expansion-side half of C2's range drawn across the next HTF period (bull: upper half;
  bear: lower half). Both color-configurable; toggleable independently.

- **STDV projections**: anchor = manipulation leg (C2 open to sweep extreme); Wick or Body
  mode; default levels -1, -1.5, -2, -2.5, -4, -4.5; fully custom comma-separated
  negative levels; labels toggle. Note: high History values with many levels approach
  Pine's 500-line budget -- reduce one if levels stop rendering.

- **Formation liquidity rays**: prior HTF highs/lows aligned with a valid model drawn as
  target rays. Default style: dotted, width 1, black; off by default.

- **Session time filters**: three configurable session windows (defaults 02:00-05:00,
  08:00-11:00, 13:30-16:15); apply-below TF threshold (default 1H); optional custom
  IANA timezone; all three filters off by default.

- **Auto Bias 1/2**: gates LTF formations by the direction of the model one or two rungs
  up the pairing ladder (e.g., on 5m-1H: AB1 = 15m-4H direction, AB2 = 1H-Daily).

- **SMT divergence**: off by default; Automatic mode detects NQ/ES pairs from the chart
  symbol root; Custom mode lets you specify up to two symbols and an inverse-correlation
  flag. The ONLY place `request.security` is used -- confirmed HTF values only
  (lookahead_off + [1]/[2] offsets = last completed candles, non-repainting). Labels
  and alerts independently toggled.

- **Info table**: bottom-right (configurable), shows Asset, Chart TF, Pairing, HTF
  countdown, Bias, Filter, SMT state; each row individually toggleable.

- **Alerts**: master toggle in General group; individual toggles per event type (C2, C3,
  CISD confirmed, early-C2 CISD preview, SMT). To receive alerts, create ONE TradingView
  alert with condition "Any alert() function call" on this indicator.

---

## Settings summary

| Group | Key settings | Notable defaults |
|---|---|---|
| Warnings | Show warnings/errors toggle | On |
| General | Alerts (master), History, Fractal pairing, C2/C3/C4 show, Custom HTF/LTF, Bias | History=1; Fractal=Automatic; Bias=Neutral |
| HTF Candles | Count, size (bars/candle), offset, bull/bear/wick colors, open line, vertical lines, L/H lines, prev EQ, drawing type | Count=4; Offset=10 (bump to 17+ for a second stacked instance) |
| HTF Candle Time Labels | Show, format, custom timezone | 24h; NY default |
| Model Style | TTFM labels, label size, C1 sweep + color, CISD bull/bear + colors, candle EQ + color, T-Spot bull/bear + colors, early C2 CISD (+ its own alert), C3 closure mode | Early CISD=Off; C3=Body break |
| SMT Divergence | Enable, alerts, labels, mode Auto/Custom, symbol 1/2, inverse | All off; Auto=NQ/ES |
| Projections | Enable, labels, type, color, levels string | On; Wick; -1,-1.5,-2,-2.5,-4,-4.5 |
| Formation Liquidity | Enable, color | Off; black dotted |
| Time Filter | Enable, apply-below TF, Filter 1/2/3 windows, custom timezone | All off; 02-05/08-11/13:30-16:15 NY |
| Info Table | Show, size, location, asset/TF/pairing/countdown/bias/filter/SMT row toggles | On; Small; Bottom Right |
| Warnings | Errors/mismatch display | On |

---

## The learning workflow (Quiz / Check)

TTrades teaches a specific study loop with the indicator:

1. Pick a past session and navigate to it in TradingView bar replay.
2. Before advancing bars: read the HTF candle panel and form your own hypothesis about
   where C1's liquidity sits, which direction a sweep might come from, and whether a C2
   is forming.
3. Advance bars one at a time. The indicator's labels appear on confirmed closes -- you
   see the same signal the indicator would have produced in real time (no hindsight).
4. After each closure, compare your read to the label: Did you call the C2? Did you
   identify the CISD level before the LTF confirmed it?
5. Use the orange/red failure lifecycle as a lesson: orange = "you were in consolidation,
   not a clean expansion"; red = "the model failed, no targets."

Because all state transitions in this implementation happen on confirmed bar closes (see
non-repaint section below), bar replay is an honest quiz -- labels will not retroactively
appear or move as you advance.

---

## Non-repaint guarantees

All formation state transitions occur on `barstate.isconfirmed` using `[1]`-history
(previous completed bar values) only. HTF closures are processed on the first bar of
the new HTF period using the completed prior HTF bar data -- no intra-bar HTF lookahead.
CISD confirmation requires an LTF candle to close (not just touch) through the level.
SMT uses `request.security` with `lookahead = barmerge.lookahead_on` combined with
`[1]/[2]` offsets -- the standard non-repainting idiom that returns only the last
COMPLETED HTF candles of the pair symbol (independently review-verified to be
temporally aligned with the chart-side HTF candles).

Two intentionally forward-looking elements exist (mirroring the real tool's behavior):
- **Early C2 CISD preview**: off by default; when enabled, shows the CISD level before
  the HTF candle closes, labeled as preview. This is the only intra-bar visual.
- **Info table countdown**: shows bars remaining until HTF close. Not a signal.

Both are clearly flagged in settings and match the real TTFM's design intent.

---

## Known deltas vs the real TTFM [Pro+]

From the 2026-07-16 parity audit (video -n31VuAijzo, frames vs MNQ1! 5m replay):

| # | Delta | Status |
|---|---|---|
| 1 | Label rendering: ours use filled label boxes (state colors gray/orange/red); real TTFM uses small plain gray text for C2/C3/C4. Color semantics are identical; it is a style difference. | Open -- revisit in polish pass if screen parity desired |
| 2 | Exact red-state failure label text (e.g., "FAILED" vs "X" vs custom wording) not verified against a live red formation in video | Open -- unverified |
| 3 | Sub-minute rungs (1S, 15S) guarded: require a seconds-capable chart; behavior on a standard chart is a warning, not a crash | By design |
| 4 | Same-date pixel parity deferred: the video formation date (likely 2025-10-15) is beyond TradingView 5m bar-replay depth; element-for-element table comparison queued for a recent-date replay | Deferred to Task 14 round 2 |
| 5 | Formation Liquidity default style fixed to dotted/black per audit (was solid orange in early draft) | Fixed in Task 9 |

No detection-rule mismatches were found: C2 closure semantics (sweep + close back inside
C1 body), T-Spot zone placement, CISD dashed-to-solid lifecycle, and red-state cease rule
all matched the video narration and frame evidence.

---

## Files

```
tradingview/ttfm_clone.pine                                    -- the indicator (~810 lines)
docs/superpowers/specs/2026-07-09-ttfm-clone-indicator-design.md  -- design spec (approved 2026-07-09)
docs/superpowers/plans/2026-07-10-ttfm-clone-indicator.md         -- implementation plan + grounded detection rules
docs/audits/2026-07-16-ttfm-phase1-parity-gate.md                 -- parity audit vs video frames
```
