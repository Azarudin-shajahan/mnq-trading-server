# ICT Charter Model 9 — One Shot One Kill — Rule Spec (Phase 3 grounding)

> Grounded 2026-06-01 (Session 36) directly from the primary transcript `YIxurbDNrWM` ("Charter Price Action Model 9 — Trade Plan & Algorithmic Theory"), cross-source: `LBlK6JB0QS0` (Mentorship Month 07) + `twIPoG2TZ1o` (Model 9 lecture). Build target: **indices (NQ/ES/YM/RTY)**. Status: rules grounded; **edge UNPROVEN until backtest** (per [[ICT_Engine_Factory_Matrix]] protocol — NotebookLM/transcript = rule truth, backtest = edge truth).

## The model in one line
A **once-or-twice-per-week**, news-day, killzone OTE entry toward a weekly draw-on-liquidity. ICT's "50–75 pips/week" is his forex sizing; on indices the **objective is the liquidity pool itself** (old high/low), not a fixed point count.

## Mechanical spec (5 stages)
1. **Weekly bias (IPDA 20-week range)** — highest high & lowest low of the last **20 weeks** = current dealing range. The **next draw on liquidity** = nearest old high (bull) / old low (bear) price is likely to reach; bias = direction of that draw, confirmed by a PD array (FVG/OB) in that direction.
2. **Catalyst gate (news day)** — only take the setup on a day the economic calendar flags a **high-impact / volatility-injection** event (FOMC, FED speakers, CPI, NFP). This is the "low-resistance liquidity run" trigger. **DEPENDENCY: need a high-impact econ-calendar, not just NFP.**
3. **Day filter** — prefer **Tuesday / Wednesday**; skip Monday (Monday = intel; 70% of weeks Tuesday prints the weekly high/low).
4. **Entry (15-min OTE in killzone)** — during **London-open or NY-open killzone**, wait for a retracement and enter at a **15-min OTE** (fib **62 / 70.5 / 79%** drawn over candle *bodies* of the impulse swing) sitting at a PD-array convergence; alternatively a stop-raid of the killzone extreme. Bullish: retrace lower → long. Bearish: retrace higher → short.
5. **Targets / stops** — objective = the framed draw-on-liquidity (old high/low). Stop = beyond the OTE swing. Management: at +50% of objective trail SL by 25%; at +75% move SL to break-even; scale 80% at first objective, run remainder to next pool.

## Index translation decisions (to lock before coding)
- **Target:** liquidity pool (old 20-week or intermediate old high/low), NOT a fixed point target. Add a minimum-expansion sanity floor only if backtest demands.
- **Killzones (IST):** London open ≈ 12:30–15:00 IST; NY open ≈ 18:00–20:30 IST (DST-shifted) — reuse the engine's existing session map.
- **News calendar:** start with FOMC + NFP + CPI dates; expand if edge is calendar-sensitive. This is the gating dependency.
- **OTE:** 62–79% body-fib of the killzone impulse leg — reuse/extend existing FVG/OTE detection.
- **Overlap check:** distinct from 62T PERFECT (that is FVG-reversal→gap-fill, no weekly-bias/news gate). Model 9 adds the **20-week IPDA bias + news-day gate + OTE-in-killzone** entry — a genuinely new engine, not a re-skin.

## Open questions for the build
1. **News-day data** — source a high-impact calendar (FOMC/CPI/NFP minimum) or test news-gate vs no-gate as a lever?
2. **Weekly bias automation** — 20-week range + draw-on-liquidity is straightforward; PD-array confirmation reuses FVG/OB detection.
3. **Backtest instruments** — NQ first (richest ICT index demos), then ES/YM/RTY.

## Weekly bias — COT layer (grounded from Month 10 + Month 07, added Session 36)
Month 07 (One Shot One Kill) states the weekly bias should be **"confirmed with COT — commercials vs large traders + open interest to confirm smart money."** Month 10 (`9H4iaaQXV5Y`) gives the full method:
- **Source:** CFTC.gov weekly COT (futures-only, short format) — the "institutions report to the government" data. NOT ForexFactory (FF just re-displays CFTC). Available for **ES / NQ / YM** futures = our exact instruments, free, decades of history.
- **Watch COMMERCIALS only** (smart money); ignore large specs (always opposite) + small specs (retail).
- **Net = commercial long − short.** Above zero = buy program; below = sell program.
- **ICT's twist:** compute the **6-month (26wk) and 12-month (52wk) range** of commercial net; position within that range ("COT index") + "nodules" of aggression mark turning points — not just the zero-line read.
- **Extremes reverse:** 12-mo / 2-yr / 4-yr extreme of commercial net → long-term reversal bias.
- **Bias = blend:** (zero-line program) + (6/12-mo range position) + (institutional order flow in price), best when all agree + PD-array confluence.

**Mechanizable core for the engine:** weekly commercial-net series per index → COT index = (net − min)/(max − min) over 26/52-wk lookback → bias = bullish when COT index high / near 52wk extreme long, bearish when low / near extreme short; zero-line sign as a coarser confirm. This becomes Model 9's **weekly-bias gate**, agreeing-or-not with the 20-week draw-on-liquidity. **NEW DATA PULL: CFTC historical COT for ES/NQ/YM** (free, government-sourced — separate from the FF news scrape).

## COMPLETE grounding — all 3 transcripts (Session 36, supersedes the skeleton above)
Read `YIxurbDNrWM` (Charter Trade Plan) + `LBlK6JB0QS0` (Month 07 original) + `twIPoG2TZ1o` (lecture). The original spec (one transcript) was a skeleton. Full model:

### The entry/exit ENGINE — internal ↔ external liquidity polarity (the "coder key", from the lecture)
Every trade is ONE of two forms; "whatever the move starts from, it goes to the opposite side of liquidity":
- **Internal-range entry → external-range target:** enter at FVG / liquidity void / order block; target old high/low / equal highs-lows.
- **External-range entry → internal-range target:** fade a swept equal-high/low (turtle soup); target FVG / equilibrium / order block inside the range.
- **Internal-range liquidity** = FVG, liquidity void, order block (inside dealing range). **External-range liquidity** = old highs/lows, equal highs/lows, double top/bottom (outside).
- **Consequent encroachment (CE)** = FVG *midpoint* = the precise entry/sensitivity level. Daily-FVG-CE stacked over weekly-FVG-CE = high-confluence entry. Style: trade the *bottom* of the gap, let stop run through the *far* side; or limit at CE if watching live.
- **Breaker (precise):** buy-stops cleared above equal highs → distribution → market-structure break → the **largest-range down-close candle** before the up-move = bearish breaker (mitigation entry). Mirror for bullish.

### Full bias stack (weekly) — much more than the 20-week range
1. **Weekly range expansion = primary bias** (institutional order flow on the weekly chart; monthly assists; top-down per Month 12). "Our one-trick pony for directional bias."
2. **IPDA data ranges** — 20-week dealing range AND 20/40/60-*day* ranges (both, different purposes).
3. **COT** — commercials net + 6/12-mo range + extremes (see COT layer above) confirm smart money.
4. **Seasonal tendency** — long-term + short-term seasonal lines must AGREE on direction.
5. **Rates / intermarket gate** — treasuries/Bund trending ⇒ movement permitted; consolidating ⇒ suppressed. (Month 05 "Using 10-Year Notes in HTF Analysis".)
6. **Intermarket asset-sync** — correlated instruments must confirm (DXY+EURGBP for EURUSD; for indices = NQ/ES/YM correlation / SMT = our existing `nq-leads`).
7. **Volatility expansion after consolidation** — enter while quiet, expand into volatility.

### Entry timing / management
- **Day filter:** Mon–Wed (76% odds the weekly high/low forms then); Monday rally is often the **weekly Judas swing** (false rally engineering premium) that forms the weekly high. Scale in across Mon–Wed rather than time the exact high.
- **Entry TF stack:** Weekly (bias) → Daily (definition) → **4H (storyline — "we utilize that for one shot one kill")** → 1H (the liquidity runs). OTE / FVG-CE / breaker entry inside London or NY killzone.
- **Stop to BE trigger (key):** move the OSOK stop to BE ONLY when a lower-TF model (scalp/day-trade) hits ITS objective (a 10/20/30-pt opposing-pool sweep) — never jam to BE early or you're knocked out before the weekly expansion. Friday = aggressive trail toward the opposite extreme.

### Mechanizable core for the NQ engine (Phase 4 build list)
weekly-range-expansion bias (+ COT/seasonal/rates/asset-sync as gating confirms) → on Mon–Wed, in a killzone, take an **internal-range FVG-CE entry** (or external-range turtle-soup entry) in the bias direction → **target the opposite liquidity type** (the draw) → SL beyond the breaker/OTE swing, to-BE only on a lower-TF-objective trigger. News gate (FF calendar) + COT bias (cot_index) are both available as toggles to measure.

## Next (Phase 4)
Translate this spec into a backtest module (own file, like the v8.x engines), NQ first, news-gate as a toggle so we can measure its contribution. Bring first NQ result before scaling to other indices. Do NOT fold into the 62T engine — Model 9 is a separate engine in the factory.
