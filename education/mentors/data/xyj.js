/* XYJ (TheMMXMTrader) deep-guide content. window.GUIDE, loaded by guide.js. Faithful
   transcription of NotebookLM answers from the XYJ notebook (53f6731e…, @XYJtrades). No fabrication. */
window.GUIDE = {
  id: "xyj",
  name: "XYJ",
  tagline: "MMXM · the Lathyrus Model — ERL↔IRL, strength switching, 2-stage CiC reversals",
  sections: [
    { id:"thesis", title:"Core thesis", html:`
<p>TheMMXMTrader's core thesis: all market expansion requires the formation of a <b>swing</b>, and every swing inherently acts as a <b>Market Maker Model (MMXM)</b> designed to distribute liquidity between <b>Internal Range Liquidity (IRL)</b> — fair value gaps — and <b>External Range Liquidity (ERL)</b> — old swing highs/lows. He mechanicalizes delivery through the "Universal Model": price moves IRL→ERL for trend continuations, ERL→IRL for HTF retracements, or ERL→ERL for order-paired reversals — the critical nuance being that every <i>true swing</i> delivers price to the opposing side of its range, distinguishing it from untradable <b>failure swings</b>. Because institutional liquidity is dispersed unevenly, correlated assets in a triad (ES/NQ/YM) desynchronize to manipulate traders; to survive you use <b>strength switching</b> to mechanically validate the end of manipulation — observing when the asset that sweeps the extreme absorbs paired liquidity and suddenly reverses with relative strength, forcing the triad to resynchronize. To execute without guessing, the <b>Lathyrus Model</b> (and its intraday "Twitter Model" variant) is a rigid 5-step framework: define a clear ERL/IRL draw, align with the daily protraction profile (e.g. short <i>above</i> the midnight open on a bearish day), identify a HTF key level, demand a mechanical Crack in Correlation (CiC — an SMT or PSP) to confirm the extreme, and enter on a lower-timeframe Change in State of Delivery (CISD).</p>` },

    { id:"model", title:"The market model", html:`
<p>Market expansion requires a swing, and every swing point acts as an MMXM whose one mechanical purpose is to distribute liquidity between two pools: <b>ERL</b> (old swing highs/lows) and <b>IRL</b> (FVGs / inefficiencies).</p>
<h3>Step 1 — the Universal Model (ERL ↔ IRL)</h3>
<ul>
<li><b>IRL → ERL (trend continuation):</b> price retraces into a gap and expands to sweep an old high/low.</li>
<li><b>ERL → IRL (retracement):</b> price sweeps an external extreme and retraces back inside to rebalance a gap.</li>
<li><b>ERL → ERL (order-paired reversal):</b> price manipulates one side to pair orders, then reverses to the opposing side.</li>
</ul>
<p><b>Nuance:</b> ranges are defined by the space between swing formations, and <b>every true swing delivers price to the opposing side of the range</b>. A swing that fails to deliver is a <i>failure swing</i> — no institutional sponsorship; don't trade away from it.</p>
<h3>Step 2 — protraction vs expansion</h3>
<p>Every candle is read on two axes, time and price, and splits into two phases: the <b>protraction phase</b> (the initial deviation past the open — the manipulation wick) and the <b>expansion phase</b> (the true delivery — the body toward the draw). <b>Nuance:</b> there's a strict inverse relationship — <b>the smaller the wick, the more time and range the candle has to expand.</b> If price hits a level but forms a massive wick late in the candle's life, do NOT trade it as a reversal (C2) — wait for it to close and trade the next candle (C3) as a continuation.</p>
<h3>Step 3 — strength switching &amp; the triad</h3>
<p>Never trust a reversal extreme just because price hit a level — validate it with the correlated triad (ES/NQ/YM). Correlated assets normally expand in sync; when they fall out of sync, the market is manipulating. Per <b>Liquidity Dispersal Theory</b>, market makers don't inject liquidity evenly, creating relative strength/weakness. <b>Strength switching:</b> when the asset manipulating deepest into the range pairs orders, it suddenly reverses with relative strength while the previously leading asset shows weakness. A <b>Precision Swing Point (PSP)</b> is the prime example — the manipulating asset sweeps an extreme but its candle closes as the opposing colour, proving a mechanical strength shift at the reversal. <b>Nuance:</b> you can almost never trade away from a failure swing — the <i>only</i> exception is an undeniable strength switch (a PSP or 2-stage SMT) proving liquidity has dispersed to reverse the market.</p>
<h3>Step 4 — the Lathyrus execution model (5 components)</h3>
<ol>
<li><b>Draw on Liquidity:</b> define the objective first (external high/low or internal gap). No target = no trade.</li>
<li><b>Protraction Profile:</b> daily bias from price vs the daily open (18:00) — bullish requires open, manipulate <i>low</i> (protraction wick), expand <i>high</i>.</li>
<li><b>Key Level:</b> the manipulation wick must trade into a HTF key level — a 4H FVG or a 1H order-paired swing.</li>
<li><b>Crack in Correlation (CiC):</b> the extreme must be validated by divergence — an unconfirmed reversal (C2) requires a <b>two-stage CiC</b> (e.g. an SMT confirming a PSP); a continuation (C3) out of a fresh gap needs only a one-stage CiC (an SMT fill).</li>
<li><b>Lower-timeframe reversal signature:</b> drop to the execution chart (15m/5m/3m) and require a <b>CISD</b> — a V-shaped displacement that leaves a fresh FVG to enter from.</li>
</ol>` },

    { id:"glossary", title:"Concept glossary", html:`
<h3>MMXM (Market Maker Model)</h3>
<p>A universal delivery mechanism distributing liquidity between internal and external pools — the formation of a swing (reversal, reaccumulation/redistribution, liquidation). <b>Nuance:</b> continuations away from the reversal extreme form a <b>"model within a model"</b> — a lower-timeframe MMXM sponsored entirely by the higher-timeframe MMXM's draw.</p>
<h3>ERL (External Range Liquidity)</h3>
<p>Old swing highs and lows. <b>Nuance:</b> a true swing always delivers price to the opposing side of the range; if price reverses without sweeping the opposing ERL/IRL, it's a failure swing with no institutional sponsorship.</p>
<h3>IRL (Internal Range Liquidity)</h3>
<p>Fair value gaps and inefficiencies. <b>Nuance:</b> true expansion doesn't offer deep retracements — a valid continuation gap must form near the open and stay in the upper half (equilibrium) of the previous candle's range; a gap deep in the discount of a continuing expansion is a manipulation signature.</p>
<h3>CiC / Change-in-Candle / C2</h3>
<p>CiC = a mechanical divergence between triad assets (SMT, PSP, or consecutive-candle divergence) used to validate a swing. C2 = the "reversal" phase of an MMXM formed at the extreme. <b>Nuance:</b> CiCs follow a strict equation — at the unconfirmed reversal (C2) you need the maximum <b>n = 2</b> CiCs; for a continuation (C3) opening in a gap you need <b>n − 1</b> (one CiC); by the time you execute the LTF CISD you need <b>zero</b>. And if C2 has a massive wick or lacks time to form a body, abandon the C2 reversal and trade the C3 continuation.</p>
<h3>2-Stage Reversal (True Reversal)</h3>
<p>A swing extreme validated by two distinct stages of CiC inside a key level (an SMT confirming a PSP, a PSP confirming an SMT, or a two-stage SMT). <b>Nuance:</b> <b>if a two-stage CiC is not present, it is NOT a true reversal</b> — never trade a reversal just because price tapped a level; with only a one-stage CiC, wait for the candle to close and trade the next sequence as a continuation.</p>
<h3>Strength Switching</h3>
<p>A signature proving manipulation is ending, rooted in Liquidity Dispersal Theory — the asset trading deepest into the extreme absorbs paired liquidity and suddenly reverses with relative strength (closing as a PSP), forcing the triad to resync. <b>Nuance:</b> it's the <i>only</i> way to safely trade away from a failure swing.</p>
<h3>Protraction Profile</h3>
<p>The study of a candle's wick (manipulation phase) relative to its open to determine session dynamics. <b>Nuance:</b> a strict binary — "if London does this, then New York does that." If London manipulates cleanly into a HTF array (Classic/Delayed protraction), NY expands safely away; if London <i>fails</i> to manipulate, NY engineers a "Judas Swing" to sweep the London lows before the true expansion.</p>
<h3>Expansion Phase</h3>
<p>The true delivery of price — the candle body driving toward the draw, distinct from the protraction wick. <b>Nuance:</b> strict inverse proportion between wick depth and expansion body — the smaller the manipulation wick, the more time/range left to expand.</p>
<h3>Seek &amp; Destroy</h3>
<p>An asymmetric consolidation (broadening formation) that violently sweeps both highs and lows without clear direction. <b>Nuance:</b> despite looking like a two-way reversal, it's mechanically a <b>continuation</b> signature — it engineers liquidity on both sides so you trade the retracement leg back into it before the HTF trend resumes.</p>
<h3>Premium/Discount Sequence (APD)</h3>
<p>A framework applied to a dealing range to gauge continuation probability via equilibrium. <b>Nuance:</b> it's primarily an <b>invalidation tool during expansion</b> — expansion doesn't offer deep retracements, so if price drops past equilibrium into the deep discount of an expanding continuation candle, the expansion is invalidated (a manipulation signature).</p>
<h3>Leading / Lagging Asset</h3>
<p>Uneven liquidity dispersal decouples the triad — the "leading" asset trades closest to / sweeps the draw; the "lagging" asset is weakest and furthest from it. <b>Nuance:</b> to trade a lagging asset as it catches up, wait for the "Ideal Sequence" — the leading asset must <i>fail</i> to reverse, print a Strength Switch PSP (a weak close), and leave a gap; the lagging asset then forms an SMT Fill inside it.</p>
<h3>Lathyrus</h3>
<p>XYJ's mentorship and the rigid 5-component daily framework: Draw on Liquidity · Protraction Profile · Key Level · Crack in Correlation · Lower-Timeframe Reversal Signature. <b>Nuance:</b> success relies on a strict <b>Plan → Execute → Review</b> loop — never strategy-hop; mastery comes from mechanically executing this exact sequence hundreds of times and severing emotion from the logical trading mind, not from a magic indicator.</p>` },

    { id:"timing", title:"Timing & sessions", html:`
<p>XYJ trades a rigid schedule built on session profiling and the candle's mechanical lifecycle, governed by the binary "if London does this, then New York does that."</p>
<h3>Operating windows</h3>
<ul>
<li><b>6:00 PM (18:00) — the anchor:</b> the daily open, used to study the daily protraction profile (the manipulation wick is measured against it; e.g. wait for an open-low to frame longs on a bullish day).</li>
<li><b>London manipulation window (~12:00–3:00 AM classic / 2:00–8:00 AM delayed protraction):</b> the primary manipulation phase. If London cleanly manipulates into a HTF PD array (Classic/Delayed protraction), NY expands safely away from it.</li>
<li><b>6:00 AM — the decoupled move:</b> the open of a new 4H cycle, notorious for "decoupled expansion" (Algorithm 1) where triad assets move opposite to manipulate.</li>
<li><b>9:30 AM (equities open):</b> a massive volatility injection. If London <i>failed</i> to manipulate, NY uses 9:30 to engineer a violent Judas Swing — sweeping the London lows to trap traders before reversing. If 6 AM decoupled, 9:30 is often where the reversal trigger forms.</li>
<li><b>10:00 AM — the resync / continuation window:</b> if 6 AM decoupled, this is where the leading asset fails to manipulate further, forcing the triad to resync and catch up — prime for continuations.</li>
<li><b>2:00 &amp; 2:30 PM (macro / FOMC):</b> a two-stage driver — wait out the 2:00 manipulation (often a PSP/SMT), then use the 2:30 open to confirm the true continuation away from the trap.</li>
</ul>
<h3>Filtering reversals by time &amp; price</h3>
<p>Every candle is read on time and price. Whether a C2 reversal is tradable follows a strict inverse proportion between wick and body:</p>
<ul>
<li><b>Price filter (wick size):</b> a small C2 wick → trade it aggressively as a reversal expansion; a massive wick puts your invalidation (stop) too far away → do NOT trade C2, let it close and trade C3.</li>
<li><b>Time filter (time remaining):</b> if the V-shape reversal forms near the end of the HTF candle's lifespan, there's insufficient time for an expansion body → wait for C3 to open, form a small opposing wick, and expand.</li>
</ul>
<h3>Timing expansions — reversals vs continuations</h3>
<ul>
<li><b>Reversals (C2):</b> the least-confirmed phase — demand the max confluence, a <b>two-stage CiC</b> (SMT confirming a PSP) at a key level; a one-stage divergence or an oversized wick filters it out.</li>
<li><b>Continuations (C3):</b> the highest-probability sequence (structure already established) — wait for the C2 to close and print a new FVG, then for C3 to retrace into the upper half (equilibrium) of the previous candle; you need only a <b>one-stage CiC</b> (an SMT fill in the gap).</li>
</ul>
<p><b>Nuance:</b> expansion doesn't offer deep retracements — if a C3 continuation drops deep past equilibrium into the previous candle's discount, the expansion is invalidated.</p>` },

    { id:"setups", title:"Signature setups, step-by-step", html:`
<h3>1. The Lathyrus 80% Model (the "Twitter Model", ERL↔IRL)</h3>
<ul>
<li><b>Context:</b> a repeatable daily setup, strong in extended consolidations — the Daily engages an ERL (PDH/PDL); the Hourly forms an internal retrace into a discount/premium IRL gap.</li>
<li><b>Trigger:</b> a 15m SMT between triad assets inside the hourly gap, paired immediately with a 15m Market Structure Shift (MSS).</li>
<li><b>Entry:</b> on the retest of the newly created 15m FVG left by the MSS displacement.</li>
<li><b>Stop:</b> a candle-body closure through the first candle of the entry FVG.</li>
<li><b>Target:</b> the opposing IRL or an obvious opposing swing pool — typically 2R–2.5R.</li>
<li><b>Nuance:</b> use the daily/midnight open as a filter — short <i>above</i> the midnight open, long <i>below</i> it.</li>
</ul>
<h3>2. The 2-Stage CiC True Reversal (Candle 2)</h3>
<ul>
<li><b>Context:</b> price reaches a HTF key level (4H gap, Daily ERL) to order-pair and reverse to the opposing side.</li>
<li><b>Trigger:</b> the extreme validated strictly by a <b>two-stage CiC</b> (SMT confirming a PSP, PSP confirming an SMT, or a two-stage SMT).</li>
<li><b>Entry:</b> drop to 15m/5m/3m; wait for a V-shape displacement + CISD that leaves a fresh gap.</li>
<li><b>Stop:</b> at the true invalidation — the extreme wick of the reversal.</li>
<li><b>Target:</b> the opposing side of the HTF dealing range, or a static 2R.</li>
<li><b>Nuance:</b> reversals require the most confirmation — if only a one-stage CiC forms, or the HTF wick is exaggerated / lacks time to close as an expansion body, do NOT trade C2; trade the C3 continuation.</li>
</ul>
<h3>3. MMXM Continuation (Type 1 / IRL→ERL)</h3>
<ul>
<li><b>Context:</b> the highest-probability sequence — a true reversal (C2) is established and has expanded away; C3 opens and retraces into a newly formed FVG.</li>
<li><b>Trigger:</b> a <b>one-stage CiC</b> (n−1) inside the new HTF gap.</li>
<li><b>Entry:</b> on the execution TF (5m/3m) you need <i>zero</i> additional CiCs — just wait for the LTF reversal signature (CISD / V-shape) inside the gap.</li>
<li><b>Stop:</b> below the true invalidation — the swing low within the HTF continuation gap.</li>
<li><b>Target:</b> the opposing external objective (the "internal model draw" or failure swings left behind).</li>
<li><b>Nuance:</b> it's a "model within a model" — and the valid continuation gap <i>must</i> sit in the upper half (equilibrium) of C2's range, else it's invalidated.</li>
</ul>
<h3>4. Strength-Switch / Lagging-Asset ("Ideal Sequence")</h3>
<ul>
<li><b>Context:</b> the triad desynchronizes; the leading asset trades deep into the extreme but <i>fails to reverse</i>, entering a new phase (consolidation/retrace).</li>
<li><b>Trigger:</b> the leader prints a <b>Strength Switch PSP</b> (trades into a high but closes as a weak down-close) and leaves a gap; the lagging asset then forms an <b>SMT Fill</b> inside that gap.</li>
<li><b>Entry:</b> an LTF CISD/MSS on the <i>lagging</i> asset as it catches up.</li>
<li><b>Stop:</b> below the invalidation of the newly formed swing.</li>
<li><b>Target:</b> the SMT break — the exact key level/high the leading asset previously tapped.</li>
<li><b>Nuance:</b> you can't trade a laggard just because it hasn't hit the high — the leader must print a sudden weakness (Strength Switch PSP) and leave a gap to prove liquidity dispersal.</li>
</ul>
<h3>5. Seek &amp; Destroy Session</h3>
<ul>
<li><b>Context:</b> often the overnight/London session — an asymmetric broadening formation sweeping both highs and lows, price typically high in a daily premium.</li>
<li><b>Trigger:</b> after sweeping external liquidity, wait for an aligned HTF open (10:00 / 10:30 AM 90-minute open); the market must print a sequential SMT or two-stage CiC (a PSP) at the engineered high to confirm the local top.</li>
<li><b>Entry:</b> on a "true CISD" — a mechanical closure through the single candle that formed the sequential SMT on a low TF (2m/1m).</li>
<li><b>Stop:</b> statically above the engineered highs of the manipulation.</li>
<li><b>Target:</b> the Logical Liquidity Target (equilibrium) or the engineered overnight lows (often 5.5R+).</li>
<li><b>Nuance:</b> despite the erratic sweeps, Seek &amp; Destroy is mechanically a <b>continuation</b> — you trade the retracement leg back into engineered liquidity before the HTF trend resumes.</li>
</ul>
<h3>6. Continuation Framework (qualifying gaps)</h3>
<ul>
<li><b>Context:</b> a true reversal exists; you're framing C3/C4 continuations by trading strictly out of gaps.</li>
<li><b>Trigger:</b> qualify the swing via one of three variants — CiC <i>at</i> a gap (SMT Fill), CiC <i>in</i> a gap (PSP closure), or CiC at <i>and</i> in a gap (two-stage SMT + PSP inside it).</li>
<li><b>Entry:</b> wait for the LTF to shift internal→external inside the HTF gap (CISD).</li>
<li><b>Stop:</b> in the discount of the current expanding candle.</li>
<li><b>Target:</b> the opposing side of the dealing range.</li>
<li><b>Nuance:</b> filter continuation gaps by the Premium/Discount of the <i>current</i> candle — keep your stop safely in the discount of the expanding candle, not in a premium where it's unprotected.</li>
</ul>` },

    { id:"example", title:"Worked example", html:`
<p>XYJ teaches that reversals are the least-confirmed phase — the highest-conviction setup is the <b>Type 1 Continuation (IRL→ERL)</b>: trading C3 away from a confirmed C2 true reversal, a "model within a model."</p>
<h3>Step 1 — confirm the true reversal</h3>
<p>Wednesday, HTF daily chart. Price sweeps the external high; we wait for mechanical confirmation. We see the leading asset form an SMT inside an advanced-premium FVG, immediately followed by a PSP closure — a two-stage CiC (PSP confirming an SMT). Wednesday's high is locked as a <b>True Reversal (C2)</b>. We have sponsorship to trade lower; leave the charts.</p>
<h3>Step 2 — the wait &amp; premium/discount filter (profiling C3)</h3>
<p>Thursday: the new daily candle (C3) opens at 18:00. Amateurs blindly short the open; we don't. Into the 6:00 AM and 9:30 AM windows we map the expanding candle's range and see price retrace up, printing a fresh 30m FVG. <b>Nuance:</b> expansion doesn't offer deep retracements — for a valid continuation this 30m gap <i>must</i> sit at/near equilibrium (upper half) of the current expanding candle; if price pushes deep into premium above it, the expansion is invalidated. Our gap sits at EQ.</p>
<h3>Step 3 — the trigger (one-stage CiC)</h3>
<p>9:30 AM. Because C3 already has structure confirmed by Wednesday's high, the Equation of Confirmation needs n−1 = one CiC. At the bell YM pushes up into our 30m gap; NQ and ES fail to reach as high — an <b>SMT Fill</b> (one-stage divergence) exactly inside the gap. Sponsorship confirmed.</p>
<h3>Step 4 — execution (zero CiCs)</h3>
<p>Drop to the 5m/3m. <b>Nuance:</b> by this timeframe you need <i>zero</i> more CiCs — hunting a 3m SMT here is noise; you're trading the phase of price. The 5m V-shapes away from the SMT Fill: a 5m candle violently displaces down, closing its body through the prior up-close candles — our <b>CISD</b>. Execute the short on that 5m CISD close.</p>
<h3>Step 5 — management &amp; targeting</h3>
<p>Stop above the true invalidation — the high of the swing wick just created inside the 30m gap (protected in the discount of the expanding candle). Target the opposing external draw (the failure swings / lows at the bottom of the range); set a static 2R (up to 2.5R). Don't touch it — let the "model within a model" deliver into the lows to hit 2R.</p>` },

    { id:"nuances", title:"Nuances you must not miss", html:`
<h3>1. Filter C2 reversals by time AND price</h3>
<p>Never trade a reversal just because price hit a key level — filter C2 by the inverse wick/body proportion. <b>Price:</b> a small wick is safe to trade as a reversal; a massive wick puts your stop too far away → don't trade C2, wait for it to close and trade C3. <b>Time:</b> if the LTF V-shape forms near the very end of C2's lifespan there's not enough time for an expansion body → wait for the next candle.</p>
<h3>2. Protraction profiling (London → New York)</h3>
<p>Anchor protraction to a daily open (18:00 / midnight). "If London does this, then New York does that": if London manipulates cleanly into a HTF array, NY expands away (Classic/Delayed protraction); if London <i>fails</i> and expands toward your draw early, anticipate a <b>Judas Swing</b> — NY sweeps the London lows at the equities open before the true expansion.</p>
<h3>3. Don't trade random candle ranges</h3>
<p>Applying C1-C2-C3 range theory to random chart levels without anchoring to a HTF key level (a 4H gap / daily swing) is "garbage" — swings only deliver to the opposing side when they originate from true institutional levels.</p>
<h3>4. Don't trade choppy consolidations as reversals</h3>
<p>Price doesn't linger at true key levels. If price reaches a HTF gap and prints a choppy consolidation instead of a violent V-shape, it's engineering liquidity — don't trade it; that consolidation will almost certainly be swept again to form the true swing.</p>
<h3>5. Don't trade away from failure swings</h3>
<p>A failure swing (a reversal that fails to order-pair the opposing pool) is a red flag — trading away from it is very low probability. The only exception is a mechanically verified strength switch (a PSP) proving institutional liquidity has dispersed to reverse.</p>
<h3>6. Don't misuse premium/discount</h3>
<p>The most common mistake is using P/D in the wrong phase. Use it for entries during a <i>retracement</i>; during an <i>expansion</i>, equilibrium is strictly an invalidation tool — a continuation that deeply retraces past equilibrium is invalidated.</p>
<h3>7. Psychology — the windfall trap &amp; "set and delete"</h3>
<p>Beware the "windfall trader" who stacks small wins but can't accept a loss — they ignore an MSS against their bias, average down, and blow the account (an "elevator down" equity curve). Once you break one rule, the "caveman brain" prioritizes revenge trading; sever it with <b>"set and delete"</b> — set the limit, stop, and static TP (e.g. 2R), then close the broker app until the next day. Time diffuses the emotion and forces you to realize the model's true statistical expectancy.</p>` },

    { id:"grounding", title:"Grounding & sources", html:`
<p>This guide is transcribed faithfully from the XYJ NotebookLM notebook (<code>53f6731e…</code>), built from the <b>@XYJtrades</b> YouTube channel (TheMMXMTrader / the Lathyrus Model) — 31 of 34 sources ingested (14 videos + 1 stream + 16 shorts; 3 shorts, two of them motivational, could not be transcribed by NotebookLM). Every claim traces to a NotebookLM answer grounded in that corpus; the bracketed <code>[n]</code> citations in the underlying answers map to individual source videos. Nothing here is imported from outside the corpus.</p>` }
  ]
};
