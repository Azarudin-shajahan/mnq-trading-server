/* The Framework — content data. Curated from mentor_setup_catalog.md,
   mentor_mindmap/data.json, and recorded backtest verdicts (memory gotchas/session_state).
   Embedded as window.EDU so the page works both double-clicked (file://) and served. */
window.EDU = {
/* Verdict tiers = EVIDENCE tier, not truth. Green (FORWARD-VALIDATED) is deliberately EMPTY:
   nothing here has been validated live or out-of-sample yet. The 62T V-shape core is IN-SAMPLE
   only (n=62, zero-loss = a fragile/overfit-prone sample) — never size up on it.
   Verdicts are from the 2020-01-02 -> 2026-05-26 backtest window. $ figures are backtest pts
   @ $0.50/pt (live = $2.00/pt). */
_meta: { verdict_asof:"2020-01-02 -> 2026-05-26 backtest (in-sample; no OOS/forward)", pt_note:"backtest $ @ $0.50/pt; live = $2.00/pt" },
verdicts: { g:"FORWARD-VALIDATED", s:"IN-SAMPLE", a:"UNVALIDATED", r:"DEAD (our engine)", w:"MECHANIC" },

frame: [
 {n:"01", t:"HTF Bias", verdict:["s","the h4-direction-gate is in production v8.18 (NY_AM)."],
  meaning:"Which direction is the higher timeframe drawing price? Decide this before anything else — it is the permission slip for the whole day. No clean bias = no trade.",
  concepts:["Draw on Liquidity","Candle Profiling","Premium/Discount + EQ","Power of 3"],
  mentors:[["TTrades","mechanical daily-bias — close beyond prior day's range = continuation; sweep + close-back = reversal (fractal C2)."],
   ["Daye","which quarter are we in? Dealing range + True Open define the phase."],
   ["GxT","IRL → ERL: internal range liquidity is drawing toward external liquidity."],
   ["ICT","HTF PD array + Power-of-3 phase (accumulation vs distribution)."],
   ["Dexter","is the PO3 already stretched to a 2–2.5 SD terminus? that caps continuation."]]},
 {n:"02", t:"Session / Killzone", verdict:["s","NY AM & PM are our in-sample edge; London 🔴 net-negative in our engine (--no-london LOCKED); Asia 🔴 dilutive."],
  meaning:"The edge only lives in specific windows. Only act inside the NY AM (09:30–11:00) and NY PM (13:30–16:00) killzones. Outside them, you are eye-training, not trading.",
  concepts:["Sessions / Killzones","True / Midnight Open"],
  mentors:[["All","NY AM 09:30–11:00 and NY PM 13:30–16:00 are the tradeable killzones."],
   ["ICT","Silver Bullet hour (10:00–11:00 / 14:00–15:00) sits inside the killzone."],
   ["Daye","treats each session as its own Q1→Q4 cycle."]]},
 {n:"03", t:"Liquidity Sweep", verdict:["s","the early liquidity raid is step 1 of the V-shape edge."],
  meaning:"Price raids an obvious pool — equal highs/lows, the session extreme, PDH/PDL — running stops. This is the fuel; the reversal comes after the raid, not before.",
  concepts:["Liquidity (BSL/SSL)","Draw on Liquidity","Relevant / Failure Swings"],
  mentors:[["ICT","buy-side / sell-side raid; the 09:30 'Judas' swing."],
   ["GxT","sweep of IRL before the ERL delivery."],
   ["Daye","the Manipulation leg of Accumulation-Manipulation-Distribution."],
   ["Dexter","manipulation push to the standard-deviation extreme."]]},
 {n:"04", t:"CISD / MSS + Displacement", verdict:["s","this displacement is what the whole edge keys on."],
  meaning:"After the sweep, price shifts market structure with a decisive displacement leg back through the origin. This is the confirmation that the raid was a trap and the reversal is real.",
  concepts:["CISD / MSS","Displacement","SMT Divergence"],
  mentors:[["GxT","2-stage PSP + CISD, confirmed by the SMT triad (NQ vs ES vs YM)."],
   ["TTrades","CISD — change in state of delivery; 'let the wick form, trade the body'."],
   ["ICT","MSS — market structure shift on displacement."]]},
 {n:"05", t:"PD-Array Entry", verdict:["s","the V-shape retrace IS the edge — but CE / mid-gap entry 🔴 is actively harmful."],
  meaning:"Enter on the retrace into the first-presented FVG / order block / breaker — the OTE 62–79% zone (70.5% sweet spot). Do NOT enter at the gap midpoint (consequential-encroachment) — that catches knives and breaks the edge.",
  concepts:["FVG","Order Block","Breaker","OTE","Inversion FVG"],
  mentors:[["ICT","first-presented FVG / OTE sweet spot 70.5%."],
   ["TTrades","T-Spot order block / CISD retest."],
   ["GxT","limit on the LTF FVG after the PSP forms."]]},
 {n:"06", t:"Protected-Swing Stop", verdict:["s","the tight structural stop is what makes the R work."],
  meaning:"Stop one tick beyond the swing extreme that formed the setup — the structure that must NOT break for the idea to remain valid. Because the SL sits below the entry bar's own low, the entry bar can't stop you out.",
  concepts:["Protected Swings","Relevant / Failure Swings"],
  mentors:[["TTrades","protected swing behind the CISD."],
   ["ICT","one tick beyond the 0% swing / the FVG candle."]]},
 {n:"07", t:"Target", verdict:["a","first-opposing / full target holds in-sample; far fixed SD targets 🟡 often never hit."],
  meaning:"Exit at the first opposing liquidity / SD projection / 2R / PDH-PDL. Take the meat of the move; don't hold for a distant fixed target that rarely prints.",
  concepts:["SD Projection","Liquidity (ERL)","Power of 3"],
  mentors:[["ICT","opposing swing / -0.5 / -1 / -1.5 SD."],
   ["Dexter","2–2.5 SD projection (extending to 3.5–4)."],
   ["GxT","failure swings / PDH-PDL / a fixed 2R."]]}
],

pd_arrays: [
 {t:"FVG (Fair Value Gap)", v:"s", d:"A 3-candle imbalance where candle 1 and candle 3 wicks don't overlap, leaving candle 2's range unfilled. Price tends to return to rebalance it.",
  spot:"Find 3 candles where there's a clean gap between C1's wick and C3's wick.", bb:"Bullish = BISI (gap below price, expect support). Bearish = SIBI (gap above, expect resistance).", step:"Step 05 — entry"},
 {t:"Inversion FVG (IFVG)", v:"a", d:"An FVG price traded fully through; its polarity flips — a bullish FVG that fails becomes resistance and vice-versa.",
  spot:"An FVG that gets closed through, then retested from the opposite side.", bb:"Failed bullish FVG → bearish IFVG (resistance), and vice-versa.", step:"Step 05 — entry"},
 {t:"Order Block (OB)", v:"s", d:"The last opposing candle before a displacement move — the institutional origin of the leg.",
  spot:"Last down-candle before an up-move (bullish OB); last up-candle before a down-move (bearish OB).", bb:"Bullish OB = demand below; bearish OB = supply above.", step:"Step 05 — entry"},
 {t:"Breaker", v:"a", d:"A failed order block: a swing gets taken, price breaks back through, and the OB is retested from the other side.",
  spot:"OB that gets violated, then price returns to it from the opposite direction.", bb:"Bullish breaker under price = support; bearish breaker above = resistance.", step:"Step 05 — entry"},
 {t:"Mitigation Block", v:"w", d:"Like an OB but forms after a failed continuation — price returns to mitigate trapped positions.",
  spot:"Origin of a move that follows a failed push, where trapped traders get relieved.", bb:"Direction follows the mitigating move.", step:"Step 05 — refinement"},
 {t:"Rejection Block", v:"w", d:"A cluster of wicks marking strong rejection; entry is taken off the wick extremes rather than the bodies.",
  spot:"Prominent wicks (not bodies) rejecting a level.", bb:"Long off bullish wick rejection; short off bearish.", step:"Step 05 — refinement"},
 {t:"Propulsion Block", v:"w", d:"An order block nested on top of a prior order block, adding propulsion to the move.",
  spot:"OB that sits directly on an earlier OB.", bb:"Amplifies the parent OB's direction.", step:"Step 05 — refinement"},
 {t:"BPR (Balanced Price Range)", v:"a", d:"The overlap of a bullish FVG and a bearish FVG — a doubly-inefficient zone that reacts strongly.",
  spot:"Where a bullish and bearish FVG occupy the same price range.", bb:"Reaction can go either way; direction set by higher-TF bias.", step:"Step 05 — entry"},
 {t:"Volume Imbalance", v:"w", d:"A gap between two candle BODIES (open-to-close) while wicks touch — a thin, magnetic zone.",
  spot:"Body-to-body gap with overlapping wicks.", bb:"Filled in the direction of delivery.", step:"Step 05 — refinement"},
 {t:"Liquidity Void", v:"w", d:"A near one-sided, vertical move with little two-way trade; price often returns to fill it.",
  spot:"A steep single-direction range on the chart.", bb:"Fills against the void's direction.", step:"Step 03 — target/context"},
 {t:"Unicorn (Breaker + FVG)", v:"a", d:"A breaker and an FVG overlapping inside the OTE zone — a high-confluence entry.",
  spot:"Breaker and FVG stacked in the 62–79% retrace.", bb:"Direction of the breaker.", step:"Step 05 — entry"}
],

mechanics: [
 {t:"Liquidity (BSL/SSL, ERL/IRL)", v:"s", d:"Where stops rest: buy-side above highs, sell-side below lows; internal-range vs external-range liquidity.",
  spot:"Equal highs/lows, session extremes, PDH/PDL, old swing points.", bb:"Price is drawn toward the nearest / most obvious pool.", step:"Steps 01, 03, 07"},
 {t:"Displacement", v:"s", d:"A fast, one-directional move that leaves inefficiency (an FVG) — a signature of institutional intent.",
  spot:"A large-bodied candle or run that gaps price and breaks structure.", bb:"Up displacement = bullish intent; down = bearish.", step:"Step 04"},
 {t:"CISD / MSS", v:"s", d:"Change in State of Delivery / Market Structure Shift — price breaks the swing that caused the move, confirming a reversal.",
  spot:"After a sweep, the first break of the opposing short-term swing on displacement.", bb:"Bullish CISD after a low sweep; bearish after a high sweep.", step:"Step 04"},
 {t:"SMT Divergence", v:"a", d:"Correlated assets disagree at a high/low (NQ makes a higher high, ES doesn't) — non-confirmation of the move.",
  spot:"Compare NQ vs ES vs YM at the raid extreme.", bb:"Bullish SMT at a low; bearish at a high.", step:"Step 04 (confluence)"},
 {t:"Premium / Discount + Equilibrium", v:"s", d:"The 50% of a dealing range is equilibrium; buy in discount (lower half), sell in premium (upper half).",
  spot:"Draw a fib on the dealing range; note the 50% line.", bb:"Discount = look long; premium = look short.", step:"Step 01"},
 {t:"OTE (Optimal Trade Entry)", v:"s", d:"The 62–79% retrace of a displacement (70.5% sweet spot) — the entry window for the V-shape.",
  spot:"Fib the displacement leg; the 62–79% band is the OTE.", bb:"Long OTE on an up displacement; short on a down.", step:"Step 05"},
 {t:"SD Projection", v:"a", d:"Standard-deviation extensions of the manipulation leg, used to project targets.",
  spot:"Measure the manip leg; project -1/-1.5/-2.5 SD.", bb:"Targets sit against the entry direction.", step:"Step 07"},
 {t:"Power of 3 / AMD", v:"a", d:"Accumulation → Manipulation → Distribution within a candle or session — the daily/session lifecycle.",
  spot:"Consolidation, then a stop-run, then the real expansion.", bb:"Trade the Distribution leg after the Manipulation.", step:"Steps 01, 03"},
 {t:"Sessions / Killzones", v:"s", d:"The time windows where the algorithm delivers price. NY AM & PM are the proven edge.",
  spot:"09:30–11:00 (AM), 13:30–16:00 (PM) ET; Silver Bullet hours inside them.", bb:"Only act inside a tradeable killzone.", step:"Step 02"},
 {t:"True / Midnight Open (ICT)", v:"a", d:"ICT reference opens (00:00 midnight, 08:30, session opens) that anchor premium/discount for the day. NOTE: Daye's 'True Open' is a different, more specific idea — see the Quarterly Theory group below.",
  spot:"Mark the midnight open and session opens.", bb:"Longs below the open, shorts above (MMXM logic).", step:"Steps 01, 05"},
 {t:"Relevant / Failure Swings", v:"a", d:"Which swing points matter for structure vs which failed to hold — cleans up MSS reading.",
  spot:"Distinguish a swing that got respected from one that failed.", bb:"Trade from relevant swings; failure swings become targets.", step:"Steps 03, 06"},
 {t:"Protected Swings", v:"s", d:"The swing that must hold for a setup to remain valid — defines stop placement.",
  spot:"The extreme that formed the setup, behind the CISD.", bb:"Stop 1 tick beyond it.", step:"Step 06"},
 {t:"Candle Profiling", v:"a", d:"Reading candle open/close/wick to infer the phase (the TTrades fractal C1→C2→C3 model).",
  spot:"C1 sweeps, C2 closes back inside, C3 expands.", bb:"Bias follows the C2 close direction.", step:"Step 01"},
 {t:"Wick Analysis", v:"a", d:"A shallow opposing wick on the sweep candle 'supports expansion' — the transferable wick-filter (frac ≤0.33).",
  spot:"Measure the opposing wick vs the candle range.", bb:"Small opposing wick favors continuation of the body.", step:"Step 04 (filter)"}
],

/* Quarterly Theory & Time (Daye) — grounded in ict_extraction/Daye_Quarterly_Theory_Study_Guide.md */
timing: [
 {t:"Quarterly Theory (fractal quarters)", v:"a",
  d:"Daye's foundation: TIME drives price, and every cycle splits into 4 equal quarters — the same structure repeating at every scale (fractal).",
  spot:"Yearly → 3 months each (Q1 Jan-Mar … Q4 Oct-Dec) · Monthly → 1 week each · Weekly → 1 day (Q1 Mon, Q2 Tue, Q3 Wed, Q4 Thu; Fri = its own function) · Daily → 6h (Q1 Asia, Q2 London, Q3 New York, Q4 Afternoon) · 90-min → ~22.5min each.",
  bb:"The quarter you're in tells you the PHASE — see the AMDX card.", step:"Steps 01–02 — bias & timing"},
 {t:"AMDX cycle (the 4 phases)", v:"a",
  d:"What each quarter DOES: A = Accumulation (Q1), M = Manipulation (Q2), D = Distribution (Q3), X = Reversal or Continuation (Q4). (XAMD is the shifted variant.)",
  spot:"Q1 builds a range → Q2 runs stops (the manipulation / Judas) → Q3 delivers the real move → Q4 reverses or continues.",
  bb:"Trade the Distribution (Q3) AFTER the Q2 manipulation — not during accumulation.", step:"Steps 01–04"},
 {t:"True Open (Daye)", v:"a",
  d:"The algorithmic starting price for Q2 of any cycle — the reference the algo manipulates AROUND (the Judas swing forms at/near it). It is NOT the calendar open.",
  spot:"True Year = open of the 1st Monday of April · True Month = open of the 2nd Monday · True Week = Monday 6:00 PM ET · True Day = 12:00 AM (midnight) · NY session = 7:30 AM ET · Afternoon = 1:30 PM ET.",
  bb:"Bull bias → look to BUY below the True Open. Bear bias → look to SELL above it (it's your premium/discount 50% line).",
  use:"How to hunt with it: (1) mark the session's True Open (NY AM = 7:30 ET; daily = midnight). (2) Set HTF bias FIRST. (3) Wait for the Judas swing — price runs the WRONG side of the TO (below it on a bull day to grab sell-stops; above it on a bear day) = the manipulation. (4) Enter as price REVERSES back through the TO, confirmed by CISD/displacement (+ SMT). (5) Only long below the TO (discount) / short above (premium). (6) Best when the TO overlaps an HTF FVG/OB = a 'Precision Level'. Stop beyond the Judas extreme; target the opposite liquidity. For reversals use the Revolving True Open (Q4 open) with Q3→Q4 SMT.",
  step:"Steps 01 & 05 — anchor"},
 {t:"Revolving True Open", v:"a",
  d:"The opening price of Q4 within a cycle. Used mainly when Sequential SMT appears between Q3 and Q4 — it signals a high-probability reversal.",
  spot:"Mark the open of the 4th quarter (e.g. the 1:30 PM Afternoon open for the daily cycle).",
  bb:"Short below a bearish revolving TO (with SMT); long above a bullish one.", step:"Step 01 — reversal anchor"},
 {t:"Timeframe synchronization", v:"a",
  d:"Each cycle must be read on its PAIRED timeframe so lower-cycle noise doesn't distort the bias.",
  spot:"Yearly → Weekly TF · Monthly → Daily · Weekly → 4H · Daily → 1H · 90-min → 5m · Micro → 1m.",
  bb:"Use the paired TF to define the quarter; the LTF to execute inside it.", step:"Step 01"},
 {t:"Defining Range & the Thirds rule (Q1)", v:"a",
  d:"Q1 of any cycle dictates the quarters that follow. Overextended Q1 → expect Q2 to consolidate; tight-range Q1 → expect Q2 to expand.",
  spot:"Split Q1 into thirds; omit the 1st third (distortion), read T2 & T3 to predict Q2.",
  bb:"Tight Q1 = lean for expansion; wide Q1 = lean for consolidation.", step:"Step 01 — bias"},
 {t:"Sequential SMT (Q3→Q4)", v:"a",
  d:"Daye's key nuance: SMT divergence is only valid when it occurs between Q3 and Q4 of a cycle. SMT in Q1/Q2 is a 'fake SMT' trap.",
  spot:"Crack in correlation (NQ vs ES vs YM) specifically at the Q3→Q4 transition, at an HTF level.",
  bb:"Bullish sequential SMT at a low = reversal up; bearish at a high = reversal down.", step:"Step 04 — confirmation"}
],

/* Mentor Models & Named Vocabulary — every named model the page uses.
   Grounded in GxT_Execution_Spec.md, Daye study guide, mentor_setup_catalog.md, FULL_EXTRACTION_CLEAN.md */
models: [
 {t:"V-Shape Signature (our edge)", v:"s",
  d:"The core reversal shape and OUR proven edge (the 62T). After a liquidity sweep, price displaces sharply back through 2+ opposing candles within ~3 time-steps, forming a 'V' (or inverted V).",
  spot:"Sweep of a level → fast displacement back through it within ~3 bars (GxT: '≥2 opposing candles in 3 time-steps').",
  bb:"V (down-then-up) = long; inverted-V (up-then-down) = short. WITHOUT the V-shape, a first-touch limit collapses WR from ~100% to ~26% — the V IS the edge.", step:"Steps 04–05 — the trigger"},
 {t:"Universal Sequence (GxT)", v:"a",
  d:"GxT's core formula: IF price manipulates Internal Range Liquidity (IRL) via an SMT at a refined key level (gap/swing), THEN it targets External Range Liquidity (ERL).",
  spot:"IRL sweep + SMT while inside an HTF FVG (1H/4H) = the high-probability entry.",
  bb:"Long when the IRL sweep is a low with bullish SMT; short at a high.", step:"Steps 01, 03, 05"},
 {t:"PSP — Precision Swing Point (GxT)", v:"a",
  d:"A swing point CONFIRMED by candle closure (not just a wick). Bullish PSP = a bearish candle followed by a bullish candle that sweeps the prior low and closes back inside the range.",
  spot:"Two-candle closure that sweeps then closes back in; enter on the 2nd ('reversal') candle's close, aligned with 4H bias.",
  bb:"Bullish PSP at a low = long; bearish PSP at a high = short.", step:"Step 04 — confirmation"},
 {t:"CSD (GxT's name for CISD)", v:"s",
  d:"Change in State of Delivery — a candle CLOSURE that displaces through the most recent opposing candle or PD-array. GxT's 'CSD' is the same idea as ICT's CISD / MSS.",
  spot:"First close that breaks the opposing short-term structure after a sweep.",
  bb:"Bullish CSD after a low sweep; bearish after a high.", step:"Step 04"},
 {t:"Two-Stage SMT & Strength Switch (GxT)", v:"r",
  d:"GxT's laggard-entry model: Stage 1 = lead asset A sweeps but B fails (SMT confirmed); Stage 2 = when A reaches its objective, the LAGGING asset C prints a CSD ('strength switch') → enter C.",
  spot:"Lead index hits target → laggard prints a CSD against it.",
  bb:"Enter the laggard in the reversal direction after the switch. ⚠️ 🔴 on our data — single-TF SSMT / strength-switch is tail-noise (dead OOS). Learn it; don't trade it standalone.", step:"Step 04 — confluence"},
 {t:"TTFM — TTrades Fractal Model", v:"a",
  d:"TTrades' mechanical daily-bias on a fractal candle: C1 sweeps the prior candle's high/low, C2 closes back inside (sets bias), C3/C4 expand. 'Let the wick form, trade the body.'",
  spot:"On daily/4H: prior-range sweep (C1) → close-back-inside (C2) → expansion (C3).",
  bb:"C2 closes back up = bullish bias; back down = bearish.", step:"Step 01 — bias"},
 {t:"IC-CISD — Intracandle CISD (TTrades)", v:"a",
  d:"An early CISD that forms on a lower TF (M5/M15) INSIDE a higher-TF candle before it closes — lets you enter the HTF move early instead of waiting for the 1H/4H candle to complete.",
  spot:"Wait for C3/C4 of the HTF candle, then take the first M5/M15 CISD inside it.",
  bb:"Direction of the intracandle CISD.", step:"Steps 04–05"},
 {t:"T-Spot (TTrades)", v:"a",
  d:"TTrades' 'trigger spot' — the specific order block / retest zone where the M5 CISD confirms and you execute. The precise entry point inside the TTFM sequence.",
  spot:"The CISD order block that price retests after the structure shift.",
  bb:"Long off a bullish T-spot OB; short off a bearish one.", step:"Step 05 — entry"},
 {t:"Silver Bullet (ICT / TTrades)", v:"a",
  d:"A TIME-boxed model: inside a fixed 1-hour window (AM 10:00–11:00, PM 14:00–15:00 ET), take the first-presented FVG after a sweep/MSS. It's a timing wrapper, not a bias.",
  spot:"1st FVG that forms inside the Silver Bullet hour.",
  bb:"Direction of the sweep + MSS that precedes the FVG. Standalone far-target version is 🟡; best as a timing overlay on the proven V-shape.", step:"Steps 02 & 05"},
 {t:"Venom (ICT)", v:"a",
  d:"An 8:00–9:30 ET model: liquidity swept by a single candle that leaves a CIBI/BISI imbalance; enter on the 'Venom' order-block candle open, targeting the opposing 8–9:30 extreme.",
  spot:"Single-candle sweep in the 8–9:30 window that leaves an imbalance.",
  bb:"Bearish Venom after a high sweep; bullish after a low.", step:"Steps 03–05"},
 {t:"MMXM — Market Maker Buy/Sell Model (ICT)", v:"a",
  d:"The full cycle: consolidation → manipulation to an HTF PD array → a 2-stage accumulation (buy model) or distribution (sell model) that delivers price to the opposite side.",
  spot:"Consolidation, a manip leg to a PD array, then a low-risk entry after the smart-money reversal (SMR).",
  bb:"Buy model at a discount low; sell model at a premium high.", step:"Steps 01–05 (full-day framework)"},
 {t:"Judas Swing (ICT)", v:"a",
  d:"A false move at/near a session open (midnight, 8:30, session True Open) designed to trap traders — a stop-hunt before the real move. It IS the manipulation leg.",
  spot:"Rally above the open then decline (bearish), or dip below then rally (bullish), right after the open.",
  bb:"Fade it: short the rally above the open in a bear bias; long the dip in a bull bias.", step:"Step 03 — the sweep"},
 {t:"Turtle Soup (ICT)", v:"a",
  d:"A false-breakout reversal: price makes a MINOR false break of a prior short-term high/low, then quickly reverses. You fade the failed breakout when HTF bias agrees.",
  spot:"Minor break of an old swing high/low that immediately fails and closes back inside.",
  bb:"Sell the false break above a high (bear bias); buy the false break below a low (bull bias).", step:"Steps 03–04"},
 {t:"Devil's Mark (Dexter)", v:"a",
  d:"Dexter's reversal signature: a candle opens and expands with NO opposing wick into an HTF array / 2–2.5 SD terminus (+SMT), then reverses to 'print the missing wick' back toward the candle-open price.",
  spot:"No-wick expansion into an SD extreme, then a reversal displacement.",
  bb:"Short a no-wick push into premium; long into discount.", step:"Steps 03 & 07"}
],

mentors: [
 {id:"ttrades", name:"TTrades", owns:"owns BIAS",
  phil:"Reads the market as a fractal. The daily candle sweeps the prior range (C1), closes back inside (C2), then expands (C3). Mechanical daily-bias sets direction; the mantra is 'let the wick form, trade the body.'",
  ses:"NY continuation; HTF candle opens (10:00, 14:00 ET).",
  setups:[["Fractal Model C2 reversal","a"],["IC-CISD (intracandle)","a"],["Unicorn (Breaker+FVG)","a"],["TTFM continuation","a"]],
  vocab:"Mechanical daily-bias → Frame step 1 · CISD → step 4 · protected swing → step 6."},
 {id:"daye", name:"Daye", owns:"owns TIMING",
  phil:"Quarterly Theory: time is fractal and cyclical. Every range (yearly down to session) splits into 4 quarters running Accumulation → Manipulation → Distribution → Reversal. He answers WHEN — he sets the stage.",
  ses:"Frames each session as its own Q1–Q4 cycle; NY AM 'Q3-of-Q3' sweet spot.",
  setups:[["Q1 Asian Dynamic S/R","a"],["Daily Q2 London Stop Hunt","a"],["Q3-of-Q3 Sweet Spot","a"],["Q4 Afternoon Reversal","a"]],
  vocab:"Quarter / phase → Frame steps 1–2 · manipulation → step 3 · True Open → step 5 anchor."},
 {id:"gxt", name:"GxT", owns:"owns ENTRY",
  phil:"The Universal Sequence: internal range liquidity draws to external (IRL→ERL); a 2-stage PSP/CISD with an SMT triad confirms; you take the precise entry. He answers WHAT / WHERE — he calls the shot.",
  ses:"NY AM & PM reversals off the 6:00 / 10:00 ET opens.",
  setups:[["6am NY Reversal → 10am cont.","a"],["NY AM V-shape (shared)","s"],["Driver Pairing","r"],["Lagging-asset SMT","r"]],
  vocab:"IRL→ERL → steps 1 & 3 · 2-stage PSP/CISD → step 4 · LTF FVG limit → step 5."},
 {id:"ict", name:"ICT", owns:"the SUBSTRATE",
  phil:"The source vocabulary everyone else builds on: PD arrays, liquidity, killzones, OTE, Power of 3. Reads price as algorithmic delivery seeking liquidity, then rebalancing inefficiency.",
  ses:"All killzones (London, NY AM, Lunch, NY PM, Silver Bullet hours).",
  setups:[["NY AM V-shape / OTE","s"],["Silver Bullet","a"],["Venom","a"],["MMXM","a"],["SMC Opening-Range Gap","r"]],
  vocab:"Provides the words for every frame step; OTE + PD arrays → step 5."},
 {id:"dexter", name:"Dexter", owns:"owns TARGETS",
  phil:"Power-of-3 and standard-deviation projections. Price accumulates, manipulates to a 2–2.5 SD terminus, then reverses. Strong on where the move ends and on time-based reversals (Tuesday, EOM/EOQ).",
  ses:"HTF candle opens (10:00 & 14:00 ET); calendar reversals.",
  setups:[["10am PO3 Expansion","a"],["Devil's Mark Reversal","a"],["Tuesday Reversal","a"],["EOM/EOQ Range Scalp","a"]],
  vocab:"SD terminus → step 1 bias & step 7 target · PO3 manipulation → step 3."},
 {id:"xyj", name:"XYJ", owns:"the MMXM SYNTHESIS",
  phil:"TheMMXMTrader / the Lathyrus Model. Every swing is a Market Maker Model distributing liquidity ERL↔IRL; correlated assets desynchronize and 'strength switching' validates the reversal. A rigid 5-step daily checklist (draw · protraction profile · key level · Crack-in-Correlation · LTF CISD) removes guessing.",
  ses:"18:00 anchor; London 02:00–05:00 manipulation; 06:00 decoupled; 09:30 Judas/trigger; 10:00 resync/continuation; 14:00 macro.",
  setups:[["Lathyrus 80% Model","a"],["2-Stage CiC True Reversal","a"],["MMXM Continuation (C3)","a"],["Strength-Switch / Lagging Asset","a"],["Seek & Destroy","a"]],
  vocab:"ERL↔IRL → steps 1 & 3 · protraction profile → step 1 bias · 2-stage CiC/PSP → step 4 · LTF CISD → step 5."}
],

/* Per-mentor coverage matrix + cross-mentor gap-fill. Grounded in GxT_vs_Daye_CrossMap.md,
   Daye QT study guide, GxT_Execution_Spec.md, mentor_setup_catalog.md, layer-ownership map.
   c = full | partial | none. Gaps fill from authorities[step] (never a dead source). */
coverage: {
 authorities: { 1:"ttrades", 2:"daye", 3:"ict", 4:"gxt", 5:"gxt", 6:"ict", 7:"gxt" },
 mentors: {
  ttrades: { dead:[], steps:{
   1:{c:"full",own:"mechanical daily-bias: close beyond the prior day's range = continuation, sweep + close-back = reversal (fractal C1→C2→C3)"},
   2:{c:"partial",own:"trades the NY continuation window",note:"doesn't define killzone/quarter timing rigorously"},
   3:{c:"full",own:"C1 sweeps the prior candle's high/low; 'let the wick form, trade the body'"},
   4:{c:"full",own:"CISD; IC-CISD (intracandle CISD); trade the body of the shift"},
   5:{c:"partial",own:"T-Spot order block / CISD retest",note:"lighter on FVG/OTE 62–79% precision"},
   6:{c:"full",own:"protected swing behind the CISD"},
   7:{c:"full",own:"PDH/PDL, 2R, next HTF liquidity"} }},
  daye: { dead:[
    {step:4,label:"Sequential-SMT cascade as a standalone driver",tier:"r",why:"= our ssmt_psp_engine — dead on the sealed 2025-26 holdout"},
    {step:7,label:"Far SD-projection-only targets",tier:"a",why:"far/projected targets lowered net vs the tight first-target in our tests"}
   ], steps:{
   1:{c:"full",own:"which quarter/phase (AMDX); True Open premium/discount; the dealing range"},
   2:{c:"full",own:"daily quarters (Q1 Asia … Q4 Afternoon); True Opens select which session to hunt"},
   3:{c:"full",own:"the Manipulation leg (Q2); the Judas swing at the True Open"},
   4:{c:"partial",own:"displacement/CSD off a PD-array at a True-Open level; sequential SMT (Q3→Q4)",note:"less mechanical on the precise CISD trigger"},
   5:{c:"partial",own:"enter at NWOG/NDOG/BPR/FVG at the True Open",note:"lighter on OTE / first-presented-FVG precision"},
   6:{c:"full",own:"protected swing = the sweep-leg extreme (+ SD/fib offset)"},
   7:{c:"partial",own:"opposite dealing-range liquidity; the Magneto level; SD projection",note:"leans on far SD-projection targets"} }},
  gxt: { dead:[
    {step:4,label:"Two-stage strength-switch / laggard-SMT entry",tier:"r",why:"single-TF SSMT dead OOS (tail noise); the cascade failed the holdout"},
    {step:4,label:"News driver-pairing bias",tier:"r",why:"all driver levers closed; --driver-news had zero effect"},
    {step:7,label:"3R/4R far R-multiple targets",tier:"a",why:"far targets dilutive vs the tight first-target"}
   ], steps:{
   1:{c:"full",own:"direction via candle profiling (open-low = bull / open-high = bear) + the IRL→ERL draw"},
   2:{c:"partial",own:"session windows (6am / 10am / London reversal)",note:"borrows which session/quarter to hunt from Daye's clock"},
   3:{c:"full",own:"sweep of IRL before the ERL delivery"},
   4:{c:"full",own:"CSD + V-shape signature; 2-stage PSP; SMT triad (NQ/ES/YM)"},
   5:{c:"full",own:"SMT-in-gap; limit on the LTF FVG after the PSP (Universal Model)"},
   6:{c:"full",own:"protected swing = the manipulation-leg low (+ body-closure offset)"},
   7:{c:"full",own:"External Range Liquidity / unestablished extreme; 2R; asset-sync exit"} }},
  ict: { dead:[
    {step:5,label:"SMC Opening-Range Gap fade",tier:"r",why:"ORG driver falsified — 16th percentile of the random-direction null"}
   ], steps:{
   1:{c:"full",own:"HTF PD array + Power-of-3 phase; premium/discount"},
   2:{c:"full",own:"killzones (London / NY AM / Lunch / NY PM); Silver Bullet hours; midnight open"},
   3:{c:"full",own:"BSL/SSL; the Judas swing; turtle soup; draw on liquidity"},
   4:{c:"full",own:"MSS (market structure shift) on displacement; SMT"},
   5:{c:"full",own:"FVG / OB / breaker + OTE 62–79% — the full PD-array vocabulary"},
   6:{c:"full",own:"one tick beyond the swing / the FVG candle"},
   7:{c:"full",own:"opposing swing / -0.5 / -1 / -1.5 SD"} }},
  dexter: { dead:[
    {step:7,label:"Far fixed 2–2.5 SD-only targets",tier:"a",why:"far-SD-only is dilutive here; pair it with the tight first-opposing target"},
    {step:4,label:"Standalone PO3 cascade",tier:"a",why:"unvalidated on our data"}
   ], steps:{
   1:{c:"partial",own:"PO3 SD-terminus (is continuation already capped?); time-based bias (Tuesday / EOM)",note:"no mechanical daily-bias / direction"},
   2:{c:"partial",own:"HTF candle opens (10:00 / 14:00 ET); calendar reversals",note:"no killzone / quarter timing"},
   3:{c:"partial",own:"manipulation to the SD extreme; no-wick expansion (Devil's Mark)",note:"lighter on liquidity-pool naming"},
   4:{c:"partial",own:"reversal displacement (prints the missing wick) + SMT",note:"no mechanical CISD trigger"},
   5:{c:"partial",own:"OB end-of-manip / 1st FVG / inversion FVG at the 10am open",note:"lighter on OTE precision"},
   6:{c:"partial",own:"stop beyond the manipulation / SMR extreme",note:"borrows the protected-swing framing"},
   7:{c:"full",own:"PO3 2–2.5 SD projection (→ 3.5–4); the SD terminus"} }}
 }
},

sessions: [
 {name:"Asian Range", time:"20:00–00:00 ET", star:false, rows:[
  ["Q1 Dynamic S/R","Daye","a"],["Lazy Man's Asian Breakout","ICT","r"],["Asia Reversal → London Cont.","GxT","a"]]},
 {name:"London Open Killzone", time:"02:00–05:00 ET", star:false, rows:[
  ["London Silver Bullet","ICT · TT","r"],["London Reversal → NY Cont.","GxT","r"],["Daily Q2 London Stop Hunt","Daye","a"],["Classic Protraction","TT","a"]]},
 {name:"Pre-Market / NY Open", time:"07:00–09:30 ET", star:false, rows:[
  ["Pre-Market Liquidity Run","ICT","a"],["6am NY Reversal → 10am Cont.","GxT","a"]]},
 {name:"NY AM Killzone", time:"09:30–11:00 ET", star:true, rows:[
  ["NY AM V-shape Sweep-Reversal (OTE)","ICT · GxT · TT","s"],["AM Opening-Range 1st-FVG","ICT · TT","a"],
  ["AM Silver Bullet","ICT · TT","a"],["ICT Venom","ICT","a"],["Q3-of-Q3 Sweet Spot","Daye","a"],
  ["10am PO3 Expansion","Dexter","a"],["SMC Opening-Range Gap","ICT","r"]]},
 {name:"NY Lunch Macro", time:"11:30–13:30 ET", star:false, rows:[
  ["Lunch Macro Reversal","ICT · Daye · TT","a"]]},
 {name:"NY PM Killzone", time:"13:30–16:00 ET", star:true, rows:[
  ["PM continuation / reversal","ICT · Daye · GxT","s"],["Q4 Afternoon Reversal","Daye","a"],
  ["PM Silver Bullet","ICT","a"],["Final Hour / MOC Macro","ICT · TT","a"]]},
 {name:"News / Driver Macros", time:"08:30 · 10:00 · 14:00 ET", star:false, rows:[
  ["High-Impact News Reversal","Daye · DX","a"],["NFP/JOLTS Framework","Dexter","a"],["Driver Pairing","GxT","r"]]}
],

quiz: [
 {type:"Concept recall", q:"What is a Fair Value Gap, and how do you tell bullish from bearish?",
  a:"A 3-candle imbalance where candle 1's and candle 3's wicks don't overlap, leaving candle 2's range unfilled. Bullish = BISI (gap below price, acts as support on a return). Bearish = SIBI (gap above, acts as resistance). Price tends to return to rebalance it."},
 {type:"Concept recall", q:"Why is entering at the FVG midpoint (consequential encroachment) a mistake in our framework?",
  a:"Because the edge is the V-shape retrace into the FIRST-presented FVG / OTE 62–79% zone. In-sample backtests show CE / mid-gap entry is actively harmful (it flips the 62T from net +$366 to a loss; note: backtest pts @ $0.50/pt, live = $2.00/pt) — it catches knives instead of waiting for the structural entry. Enter the array, not its middle."},
 {type:"Mentor / session", q:"It's the London Open killzone (03:00 ET). Whose setups fire here, and which should you take?",
  a:"Daye's Daily Q2 London Stop Hunt (🟡) and TTrades' Classic Protraction (🟡) are taught; ICT's London Silver Bullet and GxT's London Reversal are 🔴. On OUR data London is net-negative — --no-london is LOCKED. Answer: none to auto-trade. London is eye-training only; wait for NY AM."},
 {type:"Mentor / session", q:"Which mentor owns which layer of the frame?",
  a:"TTrades = BIAS (mechanical daily-bias / fractal). Daye = TIMING (Quarterly Theory / when). GxT = ENTRY (Universal Sequence / precise shot). ICT = the SUBSTRATE (vocabulary everyone builds on). Dexter = TARGETS (PO3 / SD projections). Risk sizing is ours."},
 {type:"Framing scenario", q:"10:15 ET. Price ran the Asian session low, then displaced sharply up leaving a clean FVG, and NQ shows SMT vs ES. Frame it — our best setup, or skip?",
  a:"This is our IN-SAMPLE edge — the highest-quality framing we have. HTF bias up (1) · NY AM killzone (2) · swept the Asian low (3) · displacement + SMT = CISD (4) · enter the retrace into the 1st FVG / OTE 70.5% (5) · stop 1 tick below the swing low (6) · target the first opposing swing (7). This is the v8.18 62T V-shape core. BUT 'in-sample' means it's never been validated live or OOS — treat it as a demo-only framing, not a green light to size up."},
 {type:"Framing scenario", q:"Same setup, same time — but it's the London killzone (03:30 ET) instead of NY AM. What changes?",
  a:"Skip. The structure is identical but the SESSION gate fails: London is 🔴 net-negative on our data (--no-london LOCKED). A perfect-looking pattern in the wrong window is still a no-trade. Session (step 2) is a hard gate, not a nice-to-have."}
],

/* interactive walk-through: a linear decision wizard. Each step has options;
   an option can set outcome flags or short-circuit to a verdict. */
walk: [
 {id:"bias", q:"1 — HTF bias: which way is the higher timeframe drawing price?", help:"Daily-bias (close vs prior range), quarter/phase, IRL→ERL.",
  opts:[
   {label:"Long (drawing up)", set:{dir:"long"}},
   {label:"Short (drawing down)", set:{dir:"short"}},
   {label:"Unclear / conflicting", stop:{v:"w", title:"No trade — no bias", body:"Without a clean HTF bias you have no permission slip. Sitting out IS the correct read. Come back when the daily/4H picture is one-directional."}}
  ]},
 {id:"session", q:"2 — Session: which killzone are you in right now?", help:"Only NY AM & NY PM are the proven edge.",
  opts:[
   {label:"NY AM (09:30–11:00 ET)", set:{ses:"NY AM", sesv:"s"}},
   {label:"NY PM (13:30–16:00 ET)", set:{ses:"NY PM", sesv:"s"}},
   {label:"London (02:00–05:00 ET)", stop:{v:"r", title:"Skip — London is a hard gate", body:"London is net-negative on our data (--no-london is LOCKED). A perfect pattern here is still a no-trade. Watch it to train your eye; wait for NY AM."}},
   {label:"Asian range (20:00–00:00 ET)", stop:{v:"r", title:"Skip — Asia is dilutive", body:"Asia has unfilterable losses and dilutes the edge (funded-stage only, never for the combine). No entry here."}},
   {label:"Lunch (11:30–13:30 ET)", stop:{v:"a", title:"Caution — Lunch macro only", body:"Lunch is 🟡 unvalidated. At most a small macro-reversal read; not a core setup. Prefer to wait for NY PM."}}
  ]},
 {id:"sweep", q:"3 — Liquidity sweep: has price raided an obvious pool in your direction's favor?", help:"Equal highs/lows, session extreme, PDH/PDL — the stop-run that fuels the reversal.",
  opts:[
   {label:"Yes — a clean sweep just happened", set:{sweep:true}},
   {label:"No sweep yet", stop:{v:"w", title:"Wait — no fuel yet", body:"No liquidity raid = no reason for the reversal. Don't anticipate the sweep; let it run the stops first, THEN look for the shift."}}
  ]},
 {id:"cisd", q:"4 — CISD / MSS + displacement: did price shift structure back through the origin with a displacement leg?", help:"The confirmation the raid was a trap. SMT (NQ vs ES/YM) is a bonus.",
  opts:[
   {label:"Yes — displacement + structure shift (SMT confirms)", set:{cisd:true, smt:true}},
   {label:"Yes — displacement + structure shift (no SMT)", set:{cisd:true, smt:false}},
   {label:"No clean shift yet", stop:{v:"w", title:"Wait — unconfirmed", body:"Without the CISD/MSS displacement you only have a sweep — which often just continues. The displacement back through the origin is the trigger. No shift, no trade."}}
  ]},
 {id:"entry", q:"5 — PD-array entry: is there a first-presented FVG / OB / breaker to retrace into (OTE 62–79%)?", help:"Enter the array on the retrace — NOT the gap midpoint.",
  opts:[
   {label:"Yes — clean 1st-presented FVG / OB in the OTE zone", set:{entry:true}},
   {label:"Only a mid-gap / CE fill available", stop:{v:"r", title:"Skip — don't chase the midpoint", body:"CE / mid-gap entry is actively harmful in backtests (flips the 62T to a loss). If there's no clean first-presented array in the OTE, pass. Wait for the retrace or the next setup."}},
   {label:"No array — price ran away", stop:{v:"w", title:"Missed — let it go", body:"No retrace into a PD array = no entry. Chasing an extended move breaks the R. Mark it, wait for the next setup; there's always another."}}
  ]}
],
// terminal verdict when all 5 steps pass (dir/ses/sweep/cisd/entry all set)
walkResult: {
 title:"Matches our in-sample edge — framing only",
 lines:[
  "Direction: {dir} · Session: {ses}",
  "Step 3 — enter the retrace into the first-presented FVG / OTE 70.5% zone.",
  "Step 6 — stop 1 tick beyond the swing extreme that formed the setup (protected swing).",
  "Step 7 — target the first opposing swing / -1 to -1.5 SD; take the meat, don't hold for a distant fixed target.",
  "{smtline}"
 ]}
};
