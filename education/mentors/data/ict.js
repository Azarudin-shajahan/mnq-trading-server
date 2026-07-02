/* ICT deep-guide content. window.GUIDE, loaded by guide.js. Faithful transcription of
   NotebookLM answers from ICT notebooks (Charter dd17ad76… + Core b2c21c14…, @InnerCircleTrader).
   Bounded to ICT's teaching core (the vocabulary the other mentors build on). No fabrication. */
window.GUIDE = {
  id: "ict",
  name: "ICT",
  tagline: "the SUBSTRATE — PD arrays, liquidity, killzones, OTE, Power-of-3 (teaching core)",
  sections: [
    { id:"thesis", title:"Core thesis", html:`
<p class='nc'>This guide covers ICT's teaching core — the vocabulary the other four mentors build on — not the full 600+ lecture archive.</p>
<p>ICT's core thesis: market movements are not driven by buying and selling pressure but by a precise, <b>time-based algorithm</b> engineered to seek liquidity and rebalance inefficiency. On a strict "time first, then price" protocol, the price engine perpetually cycles between sweeping <b>external range liquidity</b> (the buy/sell stops resting above old highs / below old lows) and returning to <b>internal range liquidity</b> (FVGs and order blocks) to rebalance the displacement caused by those stop runs. This creates a continuous price-delivery continuum: the algorithm traps retail on the wrong side of false breakouts during specific time macros, neutralizes their stops, then drives price the opposite way to offer smart money an offset at the next opposing liquidity pool. Every phase — Accumulation, Manipulation, Distribution — is chained to the clock.</p>` },

    { id:"model", title:"The market model", html:`
<p>Markets are delivered by an automated engine, time first then price, perpetually seeking liquidity to trap retail and rebalancing inefficiency to offer smart money an offset. Read the market as a sequence of algorithmic behaviors.</p>
<h3>Step 1 — Liquidity (BSL/SSL and ERL/IRL)</h3>
<ul>
<li><b>External Range Liquidity (ERL):</b> stop orders outside the current range — <b>Buy-Side Liquidity (BSL)</b> = buy stops above old highs; <b>Sell-Side Liquidity (SSL)</b> = sell stops below old lows.</li>
<li><b>Internal Range Liquidity (IRL):</b> structural inefficiencies inside the range — FVGs and order blocks.</li>
</ul>
<p>The cycle: price moves IRL → ERL and ERL → IRL. Sweep an old high (ERL) and it immediately seeks a discount FVG/OB (IRL) to rebalance.</p>
<h3>Step 2 — Premium, discount, equilibrium</h3>
<p>Identify the high and low of the lookback (e.g. the 20-day IPDA range). <b>Equilibrium</b> = the 50% midpoint. In a <b>premium</b> (upper half) you only look for shorts (targeting discount); in a <b>discount</b> (lower half) you only look for longs (targeting premium).</p>
<h3>Step 3 — Power of 3 (AMD) and killzones</h3>
<p>Institutional delivery runs a daily <b>Power of 3</b>: Accumulation, Manipulation, Distribution. Hunt only in the killzones — <b>London Open (2:00–5:00 AM ET)</b> and <b>New York Open (7:00–10:00 AM ET)</b>. Wait for the <b>Judas Swing</b>: manipulation opposite your bias (if bullish, price drops below the open) to raid liquidity and trap breakout traders.</p>
<h3>Step 4 — Market Structure Shift (MSS) on displacement</h3>
<ul>
<li><b>Prerequisite:</b> a valid MSS only occurs <i>after</i> a liquidity raid — price must first run an old high/low to purge stops.</li>
<li><b>Displacement:</b> price then reverses with extreme energy, breaking a recent short-term high (longs) / low (shorts).</li>
<li><b>The wick rule:</b> an MSS does <i>not</i> require a candle body to close beyond the swing — a wick piercing the structure is sufficient.</li>
<li><b>The imbalance:</b> the displacement must be aggressive enough to leave a fair value gap.</li>
</ul>
<h3>Step 5 — high-probability PD arrays</h3>
<ul>
<li><b>Fair Value Gap:</b> a 3-candle imbalance; in a bearish FVG the upper half is "balanced" — the true sensitivity is in the lower half (and vice versa for bullish). High-probability FVGs break away from a range and don't overlap old choppy price.</li>
<li><b>Order Block:</b> the last down-close candle before an expansion swing — but it <i>must</i> be coupled with an FVG that forms right after. Sensitivity is at the open or the mean threshold (the 50% midpoint of the body).</li>
<li><b>Breaker:</b> a failed order block — a bearish breaker forms on High → Low → Higher High (raiding BSL) then a break below the low; the last down-close candle between the two highs becomes the breaker.</li>
</ul>
<h3>Step 6 — Optimal Trade Entry (OTE)</h3>
<ul>
<li><b>The 62% rule:</b> anchor the fib from the low to the high of the displacement swing; OTE keys off the exact 62% retracement (prioritized over 70.5% / 79%).</li>
<li><b>Entry buffer:</b> don't enter exactly at 62% — for longs, a buy limit at 62% <b>+ 5 pips</b>; for shorts, a sell limit at 62% <b>− 5 pips</b> (to account for spread).</li>
<li><b>Stop:</b> 5 pips below the anchor swing low (longs) / 5 pips above the anchor swing high (shorts).</li>
<li><b>Management:</b> don't move the stop to break-even until the position reaches exactly <b>75% of the profit objective</b>.</li>
<li><b>Forex vs index futures:</b> the "+5 pip" entry buffer and the "10/20/30 pip" liquidity-run figures are <i>forex-specific</i>. Index futures (MNQ) are measured in points/handles and the corpus gives no exact point equivalent — treat them as "a few ticks past the level" and "a small sweep beyond the old high/low", not literal pips.</li>
</ul>` },

    { id:"glossary", title:"Concept glossary", html:`
<h3>Fair Value Gap (FVG)</h3>
<p>A range where one side of liquidity is exclusively offered, leaving a liquidity void on lower timeframes. <b>Nuance:</b> price gravitates back to fill the gap — but if an order block within the gap supports price, it may not fill completely, leaving a "breakaway gap" signalling extreme strength.</p>
<h3>Order Block</h3>
<p>A bullish OB is the lowest down-close candle (most range between open/close) near support, validated when a later candle trades through its high; a bearish OB is the last up-close candle before a down move. <b>Nuance:</b> focus on the candle <i>bodies</i> (open/close), not wicks — the crucial metric is the "mean threshold," the 50% midpoint of the body; a valid OB shouldn't let price trade through this midpoint.</p>
<h3>Breaker</h3>
<p>A failed order block that flips to support/resistance on return. <b>Nuance:</b> a true breaker must be born from a stop run (turtle soup) that traps traders at an extreme — after the violent reversal, price stops at the breaker rather than returning to the extreme order block, stranding retail waiting for a deeper retracement.</p>
<h3>Mitigation Block</h3>
<p>A short-term swing where an MSS occurs <i>without</i> taking an old extreme (a failure swing, M/W pattern). <b>Nuance:</b> orders placed on that short-term swing are trapped "underwater" — smart money returns price to the last down/up candle to mitigate those losses to zero before driving in the intended direction.</p>
<h3>Liquidity (BSL / SSL)</h3>
<p>Pending orders resting in the market — BSL = buy stops above old highs, SSL = sell stops below old lows. <b>Nuance:</b> smart money treats these not as support/resistance but as targets to pair large orders against — driving price below an old low to trigger sell stops so they can accumulate longs at a discount (and vice versa).</p>
<h3>ERL / IRL</h3>
<p>External Range Liquidity is outside the range (buy stops above / sell stops below); Internal Range Liquidity is inside (liquidity voids, FVGs, order blocks). <b>Nuance:</b> the algorithm moves price like a pendulum between them — the highest-probability trades enter at IRL (a discount OB inside a range) and exit at ERL (above the old high where buy stops rest).</p>
<h3>Equilibrium</h3>
<p>The exact 50% midpoint of a defined swing. <b>Nuance:</b> it dictates fair value — below 50% is a "discount" (buy), above is a "premium" (sell); consolidations constantly seek to return to this mean.</p>
<h3>OTE 62–79% (Optimal Trade Entry)</h3>
<p>A deep discount/premium retracement between the 62%, 70.5%, and 79% fib levels of an impulse swing. <b>Nuance:</b> it works because it highlights the deepest discount/premium for the algorithm — only valid strictly below equilibrium (longs) or above (shorts), and it should overlap an FVG or order block.</p>
<h3>Displacement</h3>
<p>A sudden, rapid, impulsive swing moving aggressively away from equilibrium, consolidation, or an order block. <b>Nuance:</b> it's the fingerprint of institutional sponsorship — if the reaction at a level is lethargic and lacks energetic expansion, there's no smart money participation; abandon the trade.</p>
<h3>MSS (Market Structure Shift)</h3>
<p>Price breaking a significant short-term high (bullish) or low (bearish) following an impulse. <b>Nuance:</b> most potent immediately after a stop run (turtle soup) into a higher-timeframe PD array — once it occurs, retracements back into the new range are treated as safe entries.</p>
<h3>Judas Swing</h3>
<p>A false, protractionary move counter to the true daily direction, engineered to trick breakout traders and trigger stops. <b>Nuance:</b> highly time-sensitive — typically initiates at the 00:00 GMT open, the midnight NY open, or the 8:30 AM news embargo lift; smart money uses the fake expansion to accumulate its true positions.</p>
<h3>Killzone</h3>
<p>Specific high-volume windows where institutional order flow dominates — London 1:00–5:00 AM NY, New York 7:00–10:00 AM NY, London Close 10:00 AM–12:00 PM NY. <b>Nuance:</b> the day's high or low predominantly forms within these windows; a setup outside a killzone has far lower odds of institutional sponsorship.</p>
<h3>Power of 3</h3>
<p>The algorithmic blueprint of the daily Open-High-Low-Close: bullish day = open near the low, decline (Judas swing), expand higher, close near the high; bearish day = open near the high, rally (Judas), expand lower, close near the low. <b>Nuance:</b> on anticipated bullish days you must buy <i>at or below</i> the daily open; on bearish days sell <i>at or above</i> it.</p>` },

    { id:"timing", title:"Timing & sessions", html:`
<p>ICT originally taught the killzones in a <b>forex</b> context; for <b>index futures</b> (S&amp;P / Nasdaq / Dow e-minis — what applies to MNQ) he shifts the focus to the 9:30 equities open. The corpus distinguishes the two, so they're sorted below.</p>
<h3>Forex killzones (ICT's original framing)</h3>
<ul>
<li><b>London Open Killzone — 1:00–5:00 AM ET</b> (some lectures quote 2:00–5:00 with opening range 1:30–2:00; the 1:00-vs-2:00 difference is forex-killzone framing / DST, not an index distinction). The prime "Judas Swing" session that traps retail before the true daily high/low; algorithmic sweet spot <b>3:30 AM ET</b>.</li>
<li><b>New York Killzone — 7:00–10:00 AM ET</b> (purist 7:00–9:00, extends to 10:00 specifically for forex).</li>
<li><b>London Close Killzone — 10:00 AM–12:00 PM ET.</b></li>
</ul>
<h3>Index-futures sessions (indices — what applies to MNQ)</h3>
<ul>
<li><b>NY AM session — 8:30–11:00 AM ET.</b> For futures, 7:00–9:30 is just pre-market ahead of the 9:30 bell. The true day high/low tends to form <b>9:30–10:30</b>; for AM index SMT, compare relative highs/lows between <b>5:00 AM and the 9:30 open</b>.</li>
<li><b>AM Opening Range — strictly 9:30–10:00 AM ET.</b> The algorithm leaves the <b>1st Presented FVG</b> (the first 1-minute FVG at 9:31 or later with true breakaway displacement — never the 9:30 candle itself), extended forward as a reference all day.</li>
<li><b>NY PM session — 1:00–4:00 PM ET.</b> The PM trend heats up ~<b>2:00 PM</b>; the true PM high/low forms in the final hour <b>3:00–4:00 PM</b>. The <b>PM Opening Range (1:30–2:00)</b> sets the afternoon (find its 1st Presented FVG).</li>
</ul>
<h3>Universal windows (all asset classes)</h3>
<ul>
<li><b>Midnight Opening Range (00:00–00:30 ET):</b> sets the daily-range boundary markers and founds the daily Power of 3; the algorithm refers back to the first displacement (FVG) inside it. Projecting standard deviations (−0.5, −1, −2.5) off this 30-minute range projects the daily high/low.</li>
<li><b>7:00 AM ET algo fire-up:</b> algorithms across all asset classes come online (universal NY-open opening range 7:00–7:30); gauge the narrative from what liquidity was taken at <b>6:30 AM</b>.</li>
<li><b>Silver Bullet hours — 10:00–11:00 AM &amp; 2:00–3:00 PM ET</b> (not distinguished by instrument): there has never been a day without an FVG in the 10:00 AM hour; in low-resistance conditions a new FVG forms in <i>every</i> 15-minute quarter.</li>
<li><b>NY Lunch macro (11:30 AM–1:30 PM ET):</b> sneaky and stagnant — beginners avoid it; experienced traders use the first swing high after a marked 10:00 AM as the lunch-retracement draw.</li>
<li><b>Final-hour macros:</b> the <b>2:50–3:10 PM</b> macro and the <b>Final Hour of RTH macro (3:15–3:45 PM)</b>, setting the final liquidity run into the 3:50 PM Market-On-Close algorithm.</li>
<li><b>Universal 20-minute macros:</b> the last 10 minutes before and first 10 minutes after the top of the hour (e.g. 9:50–10:10, 10:50–11:10) — the algorithm spools price to form the leading candles that break structure and validate PD arrays.</li>
</ul>` },

    { id:"setups", title:"Signature setups, step-by-step", html:`
<h3>1. NY AM V-Shape / Optimal Trade Entry (OTE)</h3>
<ul>
<li><b>Context:</b> stalked in the NY killzone (7:00–10:00 AM ET), looking for a retracement against London's momentum.</li>
<li><b>Trigger:</b> price retraces into the exact 62% fib of the dealing range.</li>
<li><b>Entry:</b> a limit at 62% <b>+ 5 pips</b> (longs) / <b>− 5 pips</b> (shorts) for spread.</li>
<li><b>Stop:</b> exactly 5 pips below the anchor swing low (longs) / above the anchor swing high (shorts); don't move to break-even until 75% of the profit objective.</li>
<li><b>Target:</b> first partials at the day's anchor high/low, then 10/20/30 pips beyond the previous day's range into external liquidity.</li>
<li><b>Nuance:</b> draw the fib using candle <b>bodies</b> to capture core volume — ignore the wicks.</li>
</ul>
<h3>2. Silver Bullet</h3>
<ul>
<li><b>Context:</b> time-based continuation strictly within the 10:00–11:00 AM or 2:00–3:00 PM ET hour.</li>
<li><b>Trigger:</b> a displacement swing that leaves an FVG within that 60-minute window.</li>
<li><b>Entry:</b> a limit as price retraces into the FVG, targeting the gap extreme or its consequent encroachment (midpoint).</li>
<li><b>Stop:</b> beyond the local swing extreme that preceded the displacement gap.</li>
<li><b>Target:</b> opposing session liquidity, or standard deviations mapped from the 30-minute opening range.</li>
<li><b>Nuance:</b> it's algorithmically time-bound — there has never been a day where an FVG didn't form in the 10:00 AM hour; if you missed the 9:30 opening range, wait for 10:00.</li>
</ul>
<h3>3. Judas Swing / Turtle Soup</h3>
<ul>
<li><b>Context:</b> the manipulation phase of the daily Power of 3, launching in the London or NY open.</li>
<li><b>Trigger:</b> price drives opposite your true bias, running 10/20/30 pips above an old high (BSL) or below an old low (SSL) to trap breakout traders.</li>
<li><b>Entry:</b> immediate execution into the stop hunt as it sweeps external liquidity — stepping in as retail stops trigger.</li>
<li><b>Stop:</b> above the highest sweep wick (shorts) / below the lowest sweep wick (longs).</li>
<li><b>Target:</b> price cycling back inside the range to opposing IRL (a discount FVG/OB) or the opposite side.</li>
<li><b>Nuance:</b> wicks do the damage, bodies tell the truth — a valid turtle soup sees long wicks pierce the pools while the bodies close back inside the dealing range, confirming smart money stepped in as counterparty.</li>
</ul>
<h3>4. MSS + FVG Entry (the 2022 model)</h3>
<ul>
<li><b>Context:</b> 5m→1m within an index macro (e.g. 8:30–11:00 AM ET); a clear liquidity raid on an old high/low must have just occurred.</li>
<li><b>Trigger:</b> aggressive displacement reversing from the pool that causes a rapid MSS and leaves an FVG (at/above equilibrium for shorts; at/below for longs).</li>
<li><b>Entry:</b> a limit at the anatomy of the 3-candle gap — the high of the discount low (shorts) / the low of the premium high (longs).</li>
<li><b>Stop:</b> at the extreme of the 3-candle gap (removing the 5-pip buffer).</li>
<li><b>Target:</b> ride the expansion from the entry PD array to an opposing PD-array objective (premium FVG → discount FVG / old session low).</li>
<li><b>Nuance:</b> a valid MSS does <b>not</b> require a body close beyond the swing — a wick breaking structure with heavy displacement is sufficient.</li>
</ul>` },

    { id:"example", title:"Worked example", html:`
<p>A 5-minute NASDAQ chart, 9:20 AM ET. Higher-timeframe daily flow is bearish, so the ultimate draw is the SSL below yesterday's low. But the algorithm cycles IRL↔ERL, so it must engineer a trap first — mark the relative equal highs from pre-market as external BSL above.</p>
<h3>Step 1 — the liquidity sweep &amp; Power of 3 (9:30)</h3>
<p>The bell rings; sit on your hands. The market shoots up, smashing the pre-market highs — the <b>Judas Swing</b> (Power-of-3 manipulation), raiding BSL and tricking breakout buyers. The wicks pierce the highs to trigger stops, but the bodies respect the institutional levels — smart money is accumulating shorts into the retail buy stops.</p>
<h3>Step 2 — displacement &amp; MSS (9:45–9:55)</h3>
<p>Immediately after purging buy stops, price drops with heavy displacement, violently breaking a recent short-term swing low. <b>Nuance:</b> a valid MSS must be preceded by a liquidity raid, and does not require a body close below the swing — a wick with rapid displacement is sufficient.</p>
<h3>Step 3 — the Silver Bullet FVG &amp; OTE (10:00)</h3>
<p>The displacement leaves a 3-candle bearish FVG. At 10:00 we enter the Silver Bullet window and wait for price to retrace up into that inefficiency. <b>Nuance 1:</b> in a bearish FVG the upper half is balanced — the true inefficiency is the lower half. <b>Nuance 2:</b> anchor the fib from the displacement high down to the low using candle <i>bodies</i>, ignoring wicks.</p>
<h3>Step 4 — exact entry &amp; stop</h3>
<p>Key on the 62% level (over 70.5%/79%); note it aligns inside the lower half of the bearish FVG. Place a <b>sell limit at 62% − 5 pips</b>; the moment it's placed, the stop goes exactly <b>5 pips above the anchor swing high</b>.</p>
<h3>Step 5 — target &amp; management</h3>
<p>At 10:10 price taps the limit at the lower half of the FVG, stalls at the consequent encroachment (50% midpoint), and falls toward the SSL below yesterday's low. Manage mechanically: at 25% of objective reduce stop risk 25%; at 50% reduce 50%; at exactly <b>75%</b> — and only then — move the stop to break-even. Hold the final portion until price sweeps 10/20/30 pips below the old daily low, completing ERL → IRL → ERL delivery.</p>` },

    { id:"nuances", title:"Nuances you must not miss", html:`
<h3>Focus on candle bodies, not wicks</h3>
<p>Bodies represent true institutional volume; wicks often represent erroneous, spread-driven retail action. Look for liquidity resting just above/below the <i>bodies</i> of previous highs and lows.</p>
<h3>The "classic chart pattern" trap</h3>
<p>Double tops, bull flags, head-and-shoulders are engineered market-maker traps to build pools of retail stops — smart money drives price through them to absorb that liquidity and pair its own orders.</p>
<h3>Misunderstanding market efficiency</h3>
<p>Retail buys breakouts; smart money <b>fades</b> them. In a bearish HTF trend, any short-term move above an old high is an engineered run on buy stops to let banks sell short at a premium.</p>
<h3>The 80% ADR rule for New York</h3>
<p>Don't trade the NY killzone every day — if London already fulfilled 80%+ of the 5-day Average Daily Range, move to the sidelines and skip NY; it will likely chop or catch you in an unpredictable reversal.</p>
<h3>The "London Lunch" squeeze</h3>
<p>The 5:00–7:00 AM NY window (London Lunch) frequently creates a sharp retracement/consolidation that squeezes open profits — always take partial profits before 5:00 AM NY.</p>
<h3>Use the correct "True Day" open</h3>
<p>Don't use 00:00 GMT to frame the Power-of-3 Judas Swing for London/NY day trading — the True Day always begins at <b>midnight New York time</b>.</p>
<h3>The "lethargic response" warning</h3>
<p>At a PD array, monitor the immediate reaction — if it's lethargic, stalling, or lacks dynamic expansion, institutional sponsorship is absent; reduce risk or abandon the trade.</p>
<h3>Mean-threshold violations</h3>
<p>The mean threshold is the 50% mark of the order block's <i>body</i>; a valid, sponsored OB should never see price close or significantly trade beyond that midpoint.</p>
<h3>Divergence phantoms (the indicator trap)</h3>
<p>Price has zero awareness of your indicators — market makers use indicator divergences (e.g. Stochastic) as "phantoms" to trap retail into picking a top while smart money makes one more run on the stops.</p>
<h3>The higher-timeframe arm-wrestling match</h3>
<p>Never trade a 15m/1h setup that opposes the Daily/Weekly order flow — in a timeframe "arm wrestling match," the higher timeframe always wins.</p>
<h3>The fear of taking partial profits</h3>
<p>Scale out at logical low-hanging objectives — demanding your whole position hit the final HTF objective usually turns a winner into a stop-out.</p>` },

    { id:"grounding", title:"Grounding & sources", html:`
<p>This guide is transcribed faithfully from ICT's NotebookLM notebooks — Charter Models (<code>dd17ad76…</code>) and Core Content 2016–17 (<code>b2c21c14…</code>), built from the <b>@InnerCircleTrader</b> channel. It is deliberately <b>bounded to ICT's teaching core</b> (PD arrays, liquidity, killzones, OTE, Power-of-3, MSS — the vocabulary the other four mentors build on), not the full 600+ lecture archive. Every claim traces to a NotebookLM answer grounded in that corpus; the bracketed <code>[n]</code> citations in the underlying answers map to individual source videos. Nothing here is imported from outside the corpus. Note: ICT taught killzones in a <b>forex</b> context and index-futures sessions around the 9:30 equities open — the Timing section sorts them by instrument class (index-futures = what applies to MNQ). The London 1:00–5:00 vs 2:00–5:00 AM difference is within his forex-killzone framing (and DST adjustment), not a forex-vs-futures split. The "5 pip" entry buffer and "10/20/30 pip" liquidity-run figures are forex-specific; index futures use points/handles (no exact equivalent given in the corpus).</p>` }
  ]
};
