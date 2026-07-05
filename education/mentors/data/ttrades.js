/* TTrades deep-guide content. window.GUIDE, loaded by guide.js. Faithful transcription of
   NotebookLM answers from TTrades' notebook (2a6deaec…, @TTrades_edu). No fabrication. */
window.GUIDE = {
  id: "ttrades",
  name: "TTrades",
  tagline: "owns BIAS — the fractal daily candle (C1→C2→C3), 'let the wick form, trade the body'",
  sections: [
    { id:"thesis", title:"Core thesis", html:`
<p>TTrades views the market as inherently <b>fractal</b>: every daily candle mechanically constructs an Open-High-Low-Close (OHLC) or Open-Low-High-Close (OLHC) profile out of lower-timeframe structural swings. To set a <b>mechanical daily bias without guessing</b>, you wait for a "Candle 2" (C2) closure — when a daily candle sweeps the extreme high/low of the previous candle into a higher-timeframe point of interest and then <i>closes back inside</i> that previous candle's range. A critical nuance is <b>wick size</b>: a small wick proves the daily extreme formed early, leaving ample range for a smooth directional expansion; a large opposing wick signals range exhaustion, where you conservatively pull targets back to the daily open. Once bias is set, the core execution thesis is to <b>let the wick form, then trade the body</b> of the expanding higher-timeframe candle. To define mechanically when the wick is finished, you drop to an aligned intermediate timeframe (1H/4H) and wait for an intracandle Change in the State of Delivery (CISD) — a decisive close through the opening price of the opposing order block that drove price to the high/low. That intracandle CISD confirms the daily wick is now a <b>protected swing</b>, giving you the green light to drop to an entry timeframe and trade continuations into the aggressive body of the daily candle toward higher-timeframe draws on liquidity.</p>` },

    { id:"model", title:"The market model", html:`
<p>TTrades' foundational model rests on one premise: the market is fractal — the OHLC profile of a higher-timeframe (HTF) daily candle is mechanically built from internal lower-timeframe (LTF) structural swings. The goal is to predict which days will be aggressive, one-sided expansion candles, then drop to lower timeframes to capture the bulk of that move.</p>
<h3>Step 1 — Mechanical daily bias: the C1 → C2 → C3 sequence</h3>
<ul>
<li><b>Candle 1 (C1) — the reference:</b> the previous daily candle that establishes the immediate range.</li>
<li><b>Candle 2 (C2) — the reversal closure:</b> the ultimate reversal signature — the current daily candle sweeps C1's extreme high/low into an HTF point of interest (FVG or older swing), then decisively <b>closes back inside C1's range</b>.</li>
<li><b>The wick-size nuance:</b> a C2 sweep is only tradable for immediate expansion if it has a <b>small wick</b> — proving the reversal happened early, leaving range and time to expand. A <b>large wick</b> (a massive opposing run) has exhausted the daily range: pull targets back to the daily open, or skip and wait for the next day (C3).</li>
<li><b>Candle 3 (C3) — the expansion:</b> once a valid C2 sets direction, C3 is the anticipated expansion continuation — the day to trade aggressively toward the opposing draw on liquidity.</li>
<li><b>Candle 4 (C4) — further continuation:</b> if C3 closes strong (body closes entirely beyond C2's high/low), momentum is extreme and C4 can be another expansion day.</li>
</ul>
<h3>Step 2 — Top-down timeframe alignment</h3>
<p>Never trade the daily expansion blindly. Align three timeframes: an HTF for <b>bias</b> (Daily), a middle TF for <b>structure</b> (4H/1H), and an LTF for <b>entry</b> (15m/5m). True expansion only occurs when all three align in the same direction.</p>
<h3>Step 3 — "Let the wick form, trade the body"</h3>
<p>Never try to catch the absolute top/bottom of a daily move — let the HTF candle's wick form, then trade the body.</p>
<ul>
<li><b>The intracandle CISD (IC-CISD):</b> to define exactly when the HTF wick is finished, drop to your structural timeframe. When the C3 daily candle opens, the LTF initially trends the <i>wrong</i> way to build the wick; wait for it to hit a POI and print an IC-CISD.</li>
<li><b>The mechanical trigger:</b> an IC-CISD is confirmed only when price aggressively <b>closes through the opening price of the opposing order block</b> that drove price to the extreme.</li>
<li><b>Protected swing &amp; entry:</b> that closure converts the extreme into a <b>protected swing</b> — the wick is locked in and shouldn't be violated the rest of the day. With your stop anchored behind it, drop to the entry timeframe and execute continuations into the body toward external liquidity.</li>
</ul>` },

    { id:"glossary", title:"Concept glossary", html:`
<h3>CISD — Change in the State of Delivery</h3>
<p>A shift in trend (bull↔bear): price reaches an important HTF level (a PD array or liquidity sweep), then displaces and closes past the <i>opening price</i> of the opposing candle(s) that drove it there. <b>Nuance:</b> a CISD is not a Market Structure Shift — an MSS needs a close past a swing high/low, whereas a CISD only needs a close past the opening price of the opposing candles (validating a new order block). CISD gets you in much earlier than waiting for a structural break.</p>
<h3>IC-CISD — Intracandle CISD</h3>
<p>A CISD that occurs on a lower timeframe <i>inside</i> a developing HTF candle. <b>Nuance:</b> this is the mechanical definition that confirms an HTF wick has finished forming — once the IC-CISD prints, the wick is locked, giving the green light to trade the expansion of the body.</p>
<h3>Protected Swing (protected high/low)</h3>
<p>A structural high/low expected to stay intact as the trend continues — formed when price hits a POI (sweeps a low, taps an FVG) and then makes a CISD by closing through the opposing candles. <b>Nuance:</b> a swing is <i>not</i> protected just because it looks like a high/low — it must hit an important level AND have the opposing candles closed through. This is your mechanical stop-loss anchor; if a protected swing is closed through, the trade idea is invalidated.</p>
<h3>The T-Spot</h3>
<p>The area where TTrades expects the wick of an HTF expansion candle to form — often in the upper/lower half of the previous candle's range. <b>Nuance:</b> it's an open-ended POI — never blindly place limit orders there; wait for price to drop into the T-Spot and form an LTF confirmation (a 1-minute inversion FVG or an IC-CISD) before trading the expansion out of the zone.</p>
<h3>The Unicorn Model</h3>
<p>An entry pattern combining a breaker block with an overlapping fair value gap. <b>Nuance:</b> to be valid it must begin with a liquidity sweep (stop hunt) forming the breaker (e.g. Low, High, Lower Low, Higher High); the displacement must slice cleanly through the breaker and leave an FVG precisely inside it. Enter at the breaker or wait for the FVG, stop below the breaker low.</p>
<h3>The Fractal Model (TTFM)</h3>
<p>TTrades' foundational top-down strategy, built on the logic that the market can't reverse without forming a swing point — mechanically aligning an HTF bias with a structural TF and an entry TF. <b>Nuance:</b> the goal is never to catch the absolute reversal; it aims to trade "Candle 3" (the continuation expansion) simultaneously across timeframes — a daily C3, an hourly C3, and an LTF protected swing all aligned.</p>
<h3>The Easiest Draw (on liquidity)</h3>
<p>The most obvious high-probability daily targets: the Previous Day High (PDH) and Previous Day Low (PDL). <b>Nuance:</b> unless the market is consolidating, price reaches for the previous day's extreme almost every day — so if the trend is bullish, anticipate the PDH; if price sweeps the PDH and fails to displace (closes back inside), the easiest draw flips and you target the PDL next.</p>
<h3>Weekly Profiles</h3>
<p>Structural blueprints for how the weekly candle develops across its five days (Classic Expansion, Consolidation Reversal, Intraweek Reversal, Midweek Reversal, Thursday Counter). <b>Nuance:</b> don't use them to predict the week in advance — wait for the high/low of the week to actually form and confirm (e.g. a Tuesday C2 closure), then the profile gives you narrative permission to trade the continuations (C3/C4) for the rest of the week.</p>` },

    { id:"timing", title:"Timing & sessions", html:`
<p>For TTrades, <i>when</i> you trade is as strictly ruled as <i>how</i>. He filters out low-probability environments by operating in specific sessions, executing off precise HTF candle opens, and filtering days by weekly profile and news.</p>
<h3>Session — the New York AM focus</h3>
<p>Execution is primarily in the <b>NY AM killzone (8:30–11:00 EST)</b> (a guest-trader variant runs 9:00–11:30). Wait for the 8:30 news embargo to lift or the 9:30 equities open to inject volatility. Inside it sits the stricter <b>Silver Bullet window (10:00–11:00 EST)</b> — if a setup (sweeping the 9:00 hourly candle's extremes) doesn't present in that 60 minutes, no Silver Bullet trade. <b>Nuance:</b> you do not execute in the Asian or London sessions — you use them as <i>data</i> to identify the Accumulation and Manipulation phases; NY is where you catch the Distribution (the clean displacement / large-range body).</p>
<h3>HTF candle opens — the 10:00 AM &amp; 2:00 PM macros</h3>
<p>10:00 and 14:00 EST mark the open of new <b>4-hour candles</b> on index futures. Trade the 4H Power of Three: monitor the open, wait for a shallow run the wrong way, and look for an IC-CISD on a lower timeframe (e.g. 5m) to confirm the reversal. <b>Nuance:</b> the rule is "let the wick form, then trade the body" — never blindly enter exactly at 10:00; wait for the new 4H candle to form its protective wick, then trade the continuation into the body.</p>
<h3>Weekly profile days — the "No Monday" rule &amp; news protocol</h3>
<ul>
<li><b>No Monday:</b> TTrades explicitly avoids Mondays — no prior weekly data, rarely high-impact news, and statistically the smallest daily ranges (under 25% of average). Treat Monday as an accumulation day, pure data for Tue–Fri.</li>
<li><b>High-impact news protocol:</b> avoid trading <i>before</i> the week's first high-impact event (CPI, FOMC, NFP) — pre-news days are prone to consolidation and trapped order flow. News is the trigger that manipulates the range; execute post-release or on the following days.</li>
<li><b>Best day:</b> <b>Thursday</b> is typically highest-probability, as the bulk of the weekly range is distributed following mid-week news.</li>
<li><b>Friday (TGIF):</b> conditional — if the market already expanded three straight days (Tue/Wed/Thu) and hit an HTF objective, don't seek more expansion; look for a "TGIF" fade, anticipating a retrace into the weekly range to form the weekly candle's wick.</li>
</ul>` },

    { id:"setups", title:"Signature setups, step-by-step", html:`
<h3>1. Fractal Model C2 Reversal (TTFM Candle 2)</h3>
<ul>
<li><b>Context:</b> price reaches an HTF POI (old high/low, PDH/PDL, weekly extreme, or HTF FVG).</li>
<li><b>Trigger:</b> the HTF candle sweeps C1's extreme but fails to displace, closing back inside C1's range; then, on an aligned structural TF (e.g. 1H for a daily setup), a CISD confirms — a candle closes through the opening price of the opposing order block that drove price to the extreme.</li>
<li><b>Entry:</b> drop to execution TF (5m/15m); enter on the CISD-confirming close or on a slight retest of that block.</li>
<li><b>Stop:</b> at the absolute swing extreme — the newly confirmed protected high/low.</li>
<li><b>Target:</b> the equilibrium of the HTF range, the opposing PDH/PDL, or a 2R minimum.</li>
<li><b>Nuance (wick size):</b> only trade C2 directly if the HTF candle has a <b>small wick</b>; a massive opposing wick means the range is exhausted — pull targets to the daily open and wait for C3.</li>
</ul>
<h3>2. IC-CISD (Intracandle CISD)</h3>
<ul>
<li><b>Context:</b> a confirmed HTF bias, anticipating an expansion continuation day (C3/C4); executing "let the wick form, trade the body".</li>
<li><b>Trigger:</b> inside the developing HTF candle the LTF trends the wrong way to form the wick, dropping into the T-Spot; the IC-CISD is the LTF shifting back into trend by closing through the opposing order block — locking the HTF wick.</li>
<li><b>Entry:</b> on the close that validates the continuation order block, or a slight retest.</li>
<li><b>Stop:</b> tucked tightly behind the new protected swing.</li>
<li><b>Target:</b> HTF external liquidity (old highs/lows) or a 2R minimum.</li>
<li><b>Nuance (timing):</b> the IC-CISD must form <b>early</b> in the HTF candle's life so there's range left to expand; if it forms near the end of the window, skip it and wait for the next HTF candle.</li>
</ul>
<h3>3. The Unicorn Model (Breaker + FVG)</h3>
<ul>
<li><b>Context:</b> typically in a high-volatility killzone (e.g. the 9:30 NY open) after price taps an HTF POI.</li>
<li><b>Trigger:</b> a structural stop hunt (e.g. High, Low, Higher High) then an aggressive displacement that shifts structure (Lower Low) — slicing cleanly through the last opposite-colored candle (the breaker) and leaving an FVG precisely overlapping it.</li>
<li><b>Entry:</b> at the overlapping zone — a blind limit at the start of the breaker, or a deeper retrace into the FVG for better R:R.</li>
<li><b>Stop:</b> just beyond the breaker/FVG overlap, or at the absolute swing extreme.</li>
<li><b>Target:</b> a fixed 2R, or HTF external liquidity (session highs/lows).</li>
<li><b>Nuance:</b> a random breaker or random FVG is invalid — the displacement candle's FVG must share the same price territory as the breaker's body. Execute emotionlessly: set limit entry, stop, and TP; <b>never accept a break-even trade</b> or trail out of fear — let it hit TP or the stop.</li>
</ul>
<h3>4. TTFM Continuation (Candle 3 / Candle 4)</h3>
<ul>
<li><b>Context:</b> bias locked by a prior C2/C3 closure; trading strictly with trend momentum on an anticipated one-sided expansion day.</li>
<li><b>Trigger:</b> price makes a shallow retrace into a POI (an FVG or short-term liquidity sweep), then aggressively displaces back into trend, closing through the opposing order block to validate a new protected swing.</li>
<li><b>Entry:</b> on the protected-swing-confirming close, or a slight retest of the validated continuation order block.</li>
<li><b>Stop:</b> on the new protected swing extreme.</li>
<li><b>Target:</b> HTF objectives, PDH/PDL, or SD projections (−2 to −2.5 SD); a 2R minimum applies.</li>
<li><b>Nuance:</b> true aggressive expansion needs all three timeframes aligned (Daily C3 + 4H C3 + 15m protected swing); and <b>never</b> take a continuation after a major HTF objective (PDH/PDL) is already hit — that triggers a new phase (consolidation/reversal).</li>
</ul>` },

    { id:"example", title:"Worked example", html:`
<p>TTrades' highest-conviction framework: trading the <b>Candle 3 expansion simultaneously across timeframes</b>. The easiest, most aggressive expansions occur when Daily, 4H, and 15m all align in one direction.</p>
<h3>Step 1 — the anchor (daily bias)</h3>
<p>After the daily close: today's candle traded down, swept below the PDL into a daily FVG, then decisively closed back inside the previous day's range — a classic bullish <b>C2 closure</b>. The daily candle has a <i>small</i> lower wick, proving the reversal happened early and leaving range to expand tomorrow. Bias is locked: tomorrow we exclusively seek the bullish <b>C3 expansion body</b>, target = the easiest draw, the PDH.</p>
<h3>Step 2 — structural alignment (4H)</h3>
<p>The new day begins. We don't buy blindly off the open — "let the wick form, then trade the body." Drop to the 4H: right off the open price dips to a shallow low then aggressively closes over the previous down-close candle, printing a bullish C2 reversal closure on the 4H. Timeframes aligned: Daily C3 + 4H C3. The HTF wick is locked in.</p>
<h3>Step 3 — the trigger (15m IC-CISD)</h3>
<p>Zoom to the 15m execution chart. Price dips to retest a 15m FVG in the lower half of the developing 4H candle (the T-Spot). We wait for the IC-CISD: identify the down-close candles that drove price into the local low; a 15m bullish candle then displaces and closes decisively <i>above their opening price</i>. That closure validates a continuation order block and converts the local low into a <b>protected swing</b>.</p>
<h3>Step 4 — execution &amp; management</h3>
<p>The moment the 15m IC-CISD candle closes, execute a market buy (or a limit on a slight retest of the new order block). Stop goes strictly under the new 15m protected-swing low — a close below it invalidates the whole top-down trend. With Daily/4H/15m aligned, the environment is primed for one-sided expansion: take a fixed 2R to secure gains and hold runners to the PDH. Price expands smoothly, hitting 2R and eventually sweeping the daily liquidity.</p>
<p><b>Nuances:</b> (1) never front-run the IC-CISD — the top reason continuations fail is entering before price closes over the opposing down-close candles; sacrifice the absolute bottom for mechanical confirmation. (2) The IC-CISD must form <b>early</b> in the 4H candle's life; if it forms near the end of the window, skip and wait for the next 4H candle.</p>` },

    { id:"nuances", title:"Nuances you must not miss", html:`
<h3>Overcomplicating PD arrays (analysis paralysis)</h3>
<p>Trying to spot every concept at once — FVGs, order blocks, breakers, OTEs, inversions — clutters the chart and prevents clean execution. <b>Nuance:</b> choose <i>one</i> PD array that makes visual sense to you (e.g. the CISD) and master it, combined with structural highs/lows, into a simple repeatable model.</p>
<h3>Forcing trades on SMT divergence</h3>
<p>Hunting an SMT and using it to blindly force an entry: SMT without displacement and a valid structural model means nothing. <b>Nuance:</b> SMT is strictly added <i>confluence</i> — find the structural framework (e.g. a CISD) first, then check for SMT. Beware "fake SMTs": if the stronger asset sweeps but fails to print a reversal signature and just consolidates, the divergence is fake and the laggard will catch up and sweep too.</p>
<h3>Why continuations fail (the three traps)</h3>
<ul>
<li><b>Trap 1 — it's actually consolidation:</b> an ideal continuation is a swift V-shaped recovery that closes cleanly through the opposing order block; if it takes several sluggish candles (4+) to close through, it's consolidation, not continuation.</li>
<li><b>Trap 2 — forming directly on short-term targets:</b> if the trigger forms exactly as price sweeps a short-term high/low, avoid it — the sweep often induces a reversal to hunt your stop; wait for a fresh continuation after the target clears.</li>
<li><b>Trap 3 — trading after HTF objectives are hit:</b> never take a continuation after a major HTF objective (PDH/PDL) is swept — hitting a major draw exhausts the run and triggers a new phase.</li>
</ul>
<h3>Ignoring wick size on reversal days</h3>
<p>Expecting massive expansion regardless of how the candle opened. <b>Nuance:</b> assess the opposing run (the wick) — a large wick means the candle already burned most of its range/time; pull targets back to the daily open or local liquidity. Aggressive one-sided trends only come from a <i>small</i> wick formed early.</p>
<h3>Stop-loss greed</h3>
<p>Placing the stop at the edge of the OB/FVG body to inflate R:R. <b>Nuance:</b> price often wicks deeper before expanding — anchor the stop at the actual protected-swing extreme; don't chase a 4R trade by putting the stop somewhere vulnerable.</p>
<h3>Trading "random" swing points</h3>
<p>Trading a CISD or order block blindly in the middle of the chart. <b>Nuance:</b> a structural pattern is invalid unless it occurs at an HTF POI — price must first tap an HTF FVG, sweep old external liquidity, or react at an established HTF level.</p>` },

    { id:"grounding", title:"Grounding & sources", html:`
<p>This guide is transcribed faithfully from TTrades' NotebookLM notebook (<code>2a6deaec…</code>), built from his YouTube channel <b>@TTrades_edu</b> (the Fractal Model / TTFM education). Every claim traces to a NotebookLM answer grounded in that corpus; the bracketed <code>[n]</code> citations in the underlying answers map to individual source videos. Nothing here is imported from outside the corpus.</p>` }
  ]
};
