/* Daye Mentorship (@DayeMentorship_) deep-guide content. window.GUIDE, loaded by guide.js.
   Faithful transcription of NotebookLM answers from the @DayeMentorship_ notebook
   (e2649cc6…, 69 videos). No fabrication. This is the fuller MENTORSHIP rendering of Daye's
   Quarterly Theory — see the "Daye" guide for the base channel; §7 lists the confirmed differences. */
window.GUIDE = {
  id: "dayement",
  name: "Daye Mentorship",
  tagline: "The full Quarterly-Theory mentorship — Sequential SMT, Precision Swing Points, True Opens & the algorithmic clock",
  sections: [
    { id:"thesis", title:"Core thesis", html:`
<p>The mentorship's founding claim is that <b>"time comes before price"</b> and <b>"nothing in price is random"</b> — price delivery is scheduled by an algorithm across fractal <b>quarters of time</b>, so you read the clock first and the chart second. Every cycle (yearly down to a 90-minute session) is split into four quarters running <b>Accumulation → Manipulation → Distribution → Reversal/Continuation (AMD)</b>, and each quarter has a fixed algorithmic job. Direction is not guessed from structure: the market <b>only ever reverses when a "Sequential SMT" (a crack in correlation between related assets) forms at a quarter boundary</b> — without it, price just trends in a straight line. Traditional order blocks and breakers are called <b>"illusions"</b> that fail unless anchored to time-based divergence. The entire method is a rigid, checklist-driven pursuit of one thing: a higher-timeframe Sequential SMT confirmed by a lower-timeframe one, executed at a <b>True Open</b> in the <b>Q3-of-Q3</b> New-York window, with a Fibonacci-standard-deviation stop.</p>
<p><b>Relationship to the base Daye channel:</b> this is the same Quarterly-Theory system taught on <code>@QuaterlytheoryDaye</code>, rendered in far more depth — more named models, more advanced SMT variants, and a few rules made stricter (see <a href="#nuances">§ Nuances</a>).</p>` },

    { id:"model", title:"The market model", html:`
<h3>Fractal cycles → fixed timeframes</h3>
<p>Each cycle must be read on its own timeframe or the setup is invalid: <b>yearly → weekly TF · monthly → 4H/Daily · weekly → 1H · daily → 15m · 90-minute → 5m · micro (scalp) → 1m</b>.</p>
<h3>The quarters (AMD) and their jobs</h3>
<ul>
<li><b>Q1 — Accumulation:</b> consolidates and accumulates orders. Rule: <i>omit the first third of Q1</i>; use the 2nd and 3rd thirds (T2/T3) to predict what Q2 will do. The Q1 opening price acts as dynamic support/resistance.</li>
<li><b>Q2 — Manipulation:</b> the false move / stop-hunt (the "Judas swing"). Contains the cycle's <b>True Open</b>.</li>
<li><b>Q3 — Distribution:</b> distributes the positions built in Q1/Q2 — the real directional trend. Usually the easiest to trade.</li>
<li><b>Q4 — Reversal/Continuation:</b> "Q4 is known for reversals." A reversal in Q4 gives birth to continuation in the next Q1; for Q4 to reverse it <i>must</i> have Sequential SMT.</li>
</ul>
<h3>Order flow & PD-array hierarchy</h3>
<p>Order flow is set strictly by SMT aligning with higher-timeframe targets. HTF PD arrays are ranked by how well they hold price: <b>1. Balanced Price Ranges</b> (two overlapping FVGs) &gt; <b>2. Fair Value Gaps</b> &gt; <b>3. Liquidity Pools</b> (old highs/lows). Bias needs price in premium/discount relative to the True Opens — in a bear market you want <b>Stacked True Opens</b> (a lower-TF True Open sitting <i>above</i> a higher-TF True Open = extreme premium).</p>
<h3>Three forms of SMT (the reversal engine)</h3>
<ul>
<li><b>Sequential SMT</b> — divergence between consecutive quarters (Q3↔Q4, Mon-high↔Tue-high). Relies on <b>closures, not wicks</b>: "the algorithm sees the closes… wicks are gaps." Weekly Sequential SMT needs a <b>1-hour close</b> beyond the prior day's extreme.</li>
<li><b>Intermarket SMT</b> — compare a correlated <b>Triad</b>: Index (ES / NQ / YM), Forex (DXY / EUR / GBP), Rates (30y / 10y / 5y). Rule: "the asset that makes the lower high usually falls more."</li>
<li><b>Hidden Sequential SMT</b> — divergence measured on candle <i>bodies only</i> (wicks removed); signals an explosive impending reversal.</li>
</ul>` },

    { id:"glossary", title:"Concept glossary", html:`
<h3>Sequential SMT</h3><p>The exclusive mechanic behind reversals — a crack in correlation occurring precisely at a quarter boundary, measured by closes not wicks. No Sequential SMT ⇒ no reversal.</p>
<h3>Intermarket SMT / the Triads</h3><p>Divergence across three correlated assets (Index ES/NQ/YM · Forex DXY/EUR/GBP · Rates 30y/10y/5y). A true macro reversal is when the Triads crack correlation simultaneously.</p>
<h3>Hidden Sequential SMT</h3><p>Divergence read on candle bodies only — one asset closes beyond a prior quarter's lowest close while its pair fails to. An advanced, high-conviction reversal signal.</p>
<h3>Precision Swing Point (PSP)</h3><p>A swing validated by <i>closure</i>, not structure: at the same time, one asset prints an up-close swing high while its correlated pair prints a down-close. The wick of a PSP behaves like a high-probability gap.</p>
<h3>Precision Candle / Precision Breaker</h3><p><b>Precision Candle</b> = a single candle whose close contradicts the correlated asset (even without a swing). <b>Precision Breaker</b> = a breaker block validated by a PSP, making it high-probability.</p>
<h3>True Open & Stacked True Opens</h3><p>The static Q2 opening price of any cycle — buy below it, sell above it. Macro opens: True Year = <b>January 1st</b> (the yearly Q1 open) · True Month = the open one week into the monthly cycle (the 2nd Monday when the cycle opens on the first Monday) · True Week = Monday 6:00 PM · True Day = 12:00 AM midnight. <b>Stacked True Opens</b> = a lower-TF open sitting above/below a higher-TF open = extreme premium/discount.</p>
<h3>Revolving True Open</h3><p>The Q4 opening price. Because Q4 is built for reversals, it acts as a rigid line to catch extreme tops/bottoms.</p>
<h3>Precision Levels</h3><p>Invisible entry bands formed by <b>stacking a True Open with the wick/high of a Precision Swing Point</b>; overlapping NWOG/NDOG gaps sharpen them.</p>
<h3>The Magneto Effect</h3><p>When an opposing Sequential SMT forms, it cancels the previous SMT and turns that old level into a magnetic draw on liquidity — price is pulled back to it.</p>
<h3>SMT Fill</h3><p>One asset fully fills a Fair Value Gap while its correlated pair fails to reach its equivalent gap — an immediate reversal signal / precise entry trigger.</p>
<h3>Symmetrical highs / lows</h3><p>Clean equal highs/lows where all correlated assets moved together with <i>no</i> divergence — used as the primary draw on liquidity.</p>
<h3>Doubling Theory</h3><p>Introduced as the "parent" of Quarterly Theory — fractal-of-time divergence stretching beyond a week/day (e.g. month-to-month sequential divergence, January reflecting onto February).</p>
<h3>The "Joker" / Distortion week</h3><p>A 13th partial week appended to every 12-week quarter — coded to trap traders and run liquidity both sides before the new cycle begins.</p>
<h3>Base of truth (Economic Calendar)</h3><p>ForexFactory red-folder news is the "injection of liquidity" that forces price; the news itself is a smoke screen. The day with the most USD red folders usually forms the high/low of the week.</p>` },

    { id:"timing", title:"Timing & sessions", html:`
<h3>The algorithmic clock</h3>
<p>The mentorship frames the algorithm on <b>UTC+2 ("Switzerland time")</b>, making EST 6 hours behind algorithmic midnight. The daily cycle runs four 6-hour sessions (EST):</p>
<ul>
<li><b>Q1 — Asian:</b> 6:00 PM – 12:00 AM (accumulation)</li>
<li><b>Q2 — London:</b> 12:00 AM – 6:00 AM (manipulation / stop-hunt)</li>
<li><b>Q3 — New York:</b> 6:00 AM – 12:00 PM (distribution)</li>
<li><b>Q4 — Afternoon:</b> 12:00 PM – 6:00 PM (reversals; anchored by the 1:30 PM Revolving True Open)</li>
</ul>
<h3>The "Sweet Spot" (Q3 of Q3)</h3>
<p><b>9:00 AM – 10:30 AM EST</b> is the single best time to trade — the distribution phase of the distribution session. Enter with Sequential SMT below the New-York True Open.</p>
<h3>Best days</h3>
<p><b>Thursday</b> is the highest-probability day (Thursday = Q4 of the week = reversals); Wednesday is second. Mondays and Tuesdays with no high-impact news are treated as low-probability "time distortion" days to avoid. In this rendering the weekly cycle runs <b>Monday→Thursday (Q1→Q4)</b>, with <b>Friday an isolated "blank"/reset day (TGIF)</b> that returns price into the weekly range.</p>` },

    { id:"setups", title:"Signature setups, step-by-step", html:`
<h3>"One Shot One Kill" — the two-stage Sequential SMT</h3>
<ol>
<li><b>Stage 1 — HTF setup:</b> Sequential SMT on a higher-TF cycle (e.g. the weekly cycle on the 1H) — e.g. ES takes yesterday's high, NQ fails to.</li>
<li><b>Stage 2 — confirmation:</b> drop to the execution TF (15m for the daily cycle) and wait for a <b>Precision Swing Point</b> — the pair's closures contradict.</li>
<li><b>Stage 3 — trigger:</b> enter on the <b>True-Open cross</b> (price trades back through the session/day True Open) <i>or</i> the <b>SMT Fill</b> (one asset fills an FVG, the pair fails). Execute on the wick of the PSP or the FVG during the mismatch.</li>
<li><b>Stop:</b> Fibonacci from the liquidity-run swing low→high; place at <b>1 standard deviation</b> beyond the extreme (or <b>0.5 SD</b> for a tight "cheeky" stop).</li>
<li><b>Target:</b> the symmetrical highs/lows (draw on liquidity) or the opposing Sequential SMT — "enter on SMT, exit on SMT." Minimum <b>3R</b>.</li>
</ol>
<h3>The Stage-4 (Advanced 4-Stage) Setup</h3>
<p>An intricate sequence: (1) HTF Sequential SMT, (2) a mid-TF cycle showing <i>no</i> SMT, (3) a lower-TF Sequential SMT forming a Precision Swing Point.</p>
<h3>The Monday Expansion Model ("Monday One Shot One Kill")</h3>
<p>Sequential SMT forming between the prior week's Friday and the current Monday ⇒ Monday becomes an explosive expansion day that forms the high or low of the week.</p>
<h3>The CPI Trading Model</h3>
<p>CPI direction is set days beforehand: if Sequential SMT forms the Tuesday/Wednesday prior, the CPI release simply expands aggressively in the pre-established SMT direction.</p>
<h3>The Q4 Afternoon Reversal</h3>
<p>Q3 expands aggressively, price breaks back below the 1:30 PM Revolving True Open with a Q3↔Q4 Sequential SMT ⇒ afternoon reversal.</p>` },

    { id:"example", title:"Worked example", html:`
<p>A NY→Afternoon (Q3→Q4) short on the index Triad, walked through end to end:</p>
<ol>
<li><b>Context:</b> transition from the New-York session (Q3) into the Afternoon session (Q4) of a 90-minute cycle. Q4 is programmed for reversals, and two Sequential SMTs are "colliding" — a 90-minute-cycle SMT aligned with an immediate micro-cycle SMT.</li>
<li><b>HTF Sequential SMT:</b> as Q4 begins, <b>NASDAQ pushes up to run the prior Q3 highs but the S&P 500 fails to break its high</b> — a clear Q3↔Q4 Sequential SMT.</li>
<li><b>Draw on liquidity:</b> the target is the "stage-one buy" FVG left open during the original run-up (the accumulation phase of a Market-Maker Sell Model).</li>
<li><b>Precision confirmation:</b> on the 1-minute micro cycle, the micro true open forms <i>directly above</i> the <b>Revolving True Open</b> (the Q4 open). Because the Revolving True Open formed during the SMT, it is rigid resistance.</li>
<li><b>Entry trigger:</b> price briefly wicks above the micro true open, is capped by the Revolving True Open, and the entry fires on the <b>1-minute close</b> as price fails the high and collapses back below the true open.</li>
<li><b>Stop:</b> Fibonacci from the 1-minute swing low→high of the failed run; stop at <b>1 SD</b> above the swing high (or <b>0.5 SD</b> "cheeky").</li>
<li><b>Take-profit:</b> held through distribution; first TP as price drops back into the "stage-one buy" FVG of the Market-Maker Sell Model.</li>
</ol>` },

    { id:"nuances", title:"Nuances you must not miss", html:`
<ul>
<li><b>Closures, not wicks.</b> Sequential SMT is measured on closes — "the algorithm sees the closes; wicks are gaps." Weekly SMT needs a <b>1H close</b> beyond the prior day's extreme.</li>
<li><b>The True-Open filter is non-negotiable.</b> A long is invalid unless price is trading <i>below</i> the cycle's True Open (short: above). SMT on the wrong side of the True Open "is just the market playing with you."</li>
<li><b>No SMT ⇒ no reversal.</b> Price only turns on a crack in correlation; otherwise it trends. For Q4 to reverse it must have Sequential SMT.</li>
<li><b>Trade the weakest link.</b> Execute the asset that <i>failed</i> to sweep — it harbors the true pressure and expands hardest.</li>
<li><b>Omit the first third of Q1</b>; use T2/T3 to project Q2.</li>
<li><b>Multi-TF confirmation:</b> a HTF Sequential SMT is not an entry by itself — it must be followed by a lower-TF Sequential SMT.</li>
</ul>
<h3>Where this mentorship differs from the base Daye channel (verified)</h3>
<p>Both teach the identical core system; these four points are genuine deltas, confirmed against the <code>@QuaterlytheoryDaye</code> corpus:</p>
<ul>
<li><b>Algorithmic timezone:</b> the mentorship frames the clock on <b>UTC+2 / "Switzerland time."</b> The base channel explicitly says the algorithm runs on <b>GMT</b>. (Both still trade the same 9:00–10:30 AM EST window.)</li>
<li><b>Target rule:</b> the mentorship pushes a <b>minimum 3R</b>; the base channel explicitly says there is <i>no</i> fixed minimum — "even two works."</li>
<li><b>The "Joker" week:</b> the mentorship formalizes a named <b>13th "Joker" week</b> per quarter; the base channel uses the looser "distortion week" idea with no 13th-week / Joker label.</li>
<li><b>Doubling Theory</b> is presented here as the parent of Quarterly Theory; it does not appear in the base-channel corpus.</li>
<li><b>True Year Open:</b> the mentorship anchors it to <b>January 1st</b> (the yearly Q1 open); the base channel uses the <b>first Monday of April</b>. (Both still share the Monday-6PM True Week and the midnight True Day.)</li>
</ul>
<p class="nc"><b>Project note (our backtests, in-sample):</b> this is the same converged QT/SMC method — no new standalone edge. The two-stage Sequential-SMT cascade = our <code>ssmt_psp_engine</code> (dead on the sealed 2025-26 holdout); the hardened 3R-minimum target is the payoff-transfer that <i>degraded</i> the tight first-target entries in our tests. A study asset, not an engine change.</p>` },

    { id:"grounding", title:"Grounding & sources", html:`
<p>Every claim above is transcribed from the <b>@DayeMentorship_</b> YouTube channel — all <b>69 videos</b> ingested into a dedicated NotebookLM notebook (<code>e2649cc6</code>): the "Lesson 1–45 Concept" series, "Lesson 1–12 April," and the June–August daily Market-Overview / Price-Action sessions. Answers were pulled with grounded queries (methodology, execution, signature models, worked example) and transcribed faithfully — nothing invented; where the corpus was silent it is left out.</p>
<p>This is the fuller <b>mentorship</b> rendering of Daye's Quarterly Theory. For the base channel see the <a href="daye.html">Daye guide</a>; the four verified differences are listed in <a href="#nuances">§ Nuances</a>. Cross-checks were run directly against the <code>@QuaterlytheoryDaye</code> "source of truth" notebook (<code>3f9d9752</code>).</p>` }
  ]
};
