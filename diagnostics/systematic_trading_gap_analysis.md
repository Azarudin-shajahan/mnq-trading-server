# Systematic / CTA practice vs this project — gap analysis (2026-06-19)

External research pass ("how OTHER automated traders mechanize"), aimed process-first,
then a lighter scan of published systems. Goal: surface better ways to mechanize
the bias / sizing / validation layers, and any genuinely new structural approach.

## TL;DR
- No new *edge* (the direction-signal lever stays CLOSED — published systems converge on the
  same sweep/reclaim = V-shape this project already trades).
- Real gaps are in *engineering*: (1) volatility targeting, (2) forecast-combination /
  weak-signal ensemble sizing, (3) walk-forward validation (data-permitting), and
  (4) a regime filter that makes the "runner" archetype COMPLEMENTARY instead of useless.
- The project has already independently reinvented the *validation* discipline (random-direction
  nulls, drop-top-3, lookahead guard, sealed holdout = Lopez de Prado / Carver spirit).

## Our approach vs the systematic/CTA philosophy
This project = ONE hand-crafted, high-WR, all-or-nothing mean-reversion scalp (v8.18).
The CTA world runs the inverse: a PORTFOLIO of many weak, uncorrelated, continuous signals,
vol-targeted. The contrast is the source of the gaps below.

| Layer | This project | Systematic/CTA (Carver et al.) | Action |
|---|---|---|---|
| Sizing | Fixed-R | Volatility targeting (constant cash-at-risk; size ~ 1/vol) | Build into risk_sizer.py |
| Signal | One binary config (on/off) | Forecast combination: many weak signals, each a continuous forecast (std long-run = 10), combined then vol-targeted | Treat v8.18 + mech-bias + regime as an ensemble |
| Bias use | conf 1/2/3 GATES the trade | Forecast strength SCALES position size (continuous) | Wire conf -> size, not gate |
| Validation | One sealed holdout (now burned by config search) | Walk-forward (rolling), Walk-Forward Efficiency = OOS/IS annual return, want > 50-60% | Adopt if trade count allows |

### Key sizing/ensemble facts
- Vol targeting smooths the equity curve and cuts drawdowns by holding RISK constant, not
  position size constant (Carver, ex-AHL PM).
- Forecast-combination literature: equal weighting usually beats estimated "optimal" weights
  — errors in estimating weights exacerbate the ensemble. So combine simply; don't optimize weights.
- Carver's failure modes (all things this project should keep avoiding): over-complication,
  over-optimism on returns, excessive risk, trading too often.

## The genuinely NEW structural idea: a vol-regime filter
Strongest finding from the comparison. Established result:
- Mean reversion works in LOW-vol / range; trend works in EXPANDING vol. The two are
  STRUCTURALLY NEGATIVELY CORRELATED (when one gets run over, the other thrives).
- v8.18 is a mean-reversion scalp (V-shape sweep-reversal = reversion). The mentors' big-R
  "lagging-asset catchup" runners are TREND/EXPANSION trades.
- Therefore they are not competitors and the runner is not "useless" — they are
  complementary regimes. You don't convert the scalp into a runner (proven non-convertible);
  you run a SEPARATE trend arm in the regime where the scalp underperforms, gated by a vol filter.
- Evidence already in hand: 2025-12-16 was an expansion/trend day — luffy ran YM to +10R while
  v8.18's reversion scalp EXPIRED. A vol-regime filter would have routed that day to a trend arm,
  not the scalp. This is the kind of "new approach surfaced by comparison" the search aimed at.

Caveat: this is a HYPOTHESIS to test, not a result. It must clear the same gates (lookahead guard,
null, forward) before any belief. And WFO/regime work needs more data than 62 trades/6yr provides
at the scalp's frequency — feasibility check required.

## Published-systems scan (lighter net)
- Retail automated NQ/ES systems publicly converge on breakout + "sweep then reclaim key level
  with conviction" = the V-shape this project trades (e.g. Steady Turtle's sweep/reclaim).
  Confirms the edge is real and shared; yields no new direction-driver.
- Public "73% WR / +$17k" type claims are unverifiable and in-sample-flavored (same caveat as our
  own numbers). Do not anchor on them.
- Universal caveat repeated everywhere: over-leverage = mathematical ruin; "you can't flip a switch
  and be profitable" — execution + risk discipline matter more than the signal. Matches our gotchas.

## Sources
- Carver, Systematic Trading — frameworks/forecasts + vol targeting: the7circles.uk reviews
- Forecast combination / ensemble weighting (equal-weight robustness): arxiv 2506.04677 and 2025 ensemble surveys
- Walk-forward vs single holdout: quantinsti, algotrading101, QuantConnect docs
- Regime (trend vs reversion, vol-conditioned): arxiv 2501.16772; Elite Trader / Alvarez Quant threads
- Retail automated NQ/ES systems scan: highstrike, quantvps, Steady Turtle (Medium)
