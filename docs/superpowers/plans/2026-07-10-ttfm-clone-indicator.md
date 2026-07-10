# TTFM Clone Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tradingview/ttfm_clone.pine` — a single Pine v6 indicator replicating Fractal Model [Pro+] (TTrades) feature-for-feature as a passive charting/learning tool (no strategy(), no webhooks, no signal authority).

**Architecture:** One Pine v6 file with disciplined internal sections: settings → UDTs → TF pairing ladder → local HTF aggregation engine (no `request.security` except SMT) → pure detection functions → per-direction Formation state machine (gray/orange/red lifecycle) → rendering layer with object recycling → modules (projections, liquidity, time filters, auto-bias, SMT, alerts, info table). All state transitions on confirmed data only; HTF closures are processed on the first bar of the new HTF period using only `[1]`-history (time-based, non-repainting).

**Tech Stack:** Pine Script v6 on TradingView; `tv` CLI (CDP) for inject/compile/screenshot; git branch `ttfm-clone-indicator`.

**Spec:** `docs/superpowers/specs/2026-07-09-ttfm-clone-indicator-design.md` (approved 2026-07-09).

---

## Grounded detection rules (resolved 2026-07-10, cite these in code comments)

| Rule | Definition | Source |
|---|---|---|
| C2 closure (bull) | Candle sweeps C1's low (`l < C1.l`) AND **body closes back inside C1's range** (`c > C1.l`). Wick-only sweep is NOT a C2. Close below the swept low = continuation closure, not C2. Mirror for bear. | `understanding-candle-2-closures-within-the-fractal-model.md` + NotebookLM TTrades nb `2a6deaec` (quoted: "take out its previous candle's low and close back above it") |
| C3 closure | Next candle closes beyond C2's extreme in the reversal direction. Setting: strict body break (`c > max(C2.o, C2.c)` bull) or 50%-of-C2-range threshold. | `candle-3-closure-...md`; Qvintrix leak (both modes exposed) |
| C4 | Continuation candle after C3 closure. | `ttrades-fractal-model-candle-4.md` |
| CISD (bull, LTF) | Walk the LTF candles inside the HTF candle; find the consecutive run of down-close candles containing the lowest low; CISD level = **open of the first candle of that run**; confirmed when an LTF candle **closes** above it. Pending = dashed, confirmed = solid. | `understanding-the-change-in-state-of-delivery-cisd.md`, `how-change-in-the-state-of-delivery-confirms-swing-points.md` |
| Ideal Formation ★ | The C2/C3 closure ALSO closes through the opposing HTF candle series (bull: close > open of the first candle of the consecutive down-close HTF run into the low) → protected swing created on the closure candle itself. | `ttrades-ideal-formation-high-probability-swing-points.md` (ripped 2026-07-09) |
| T-Spot (bull) | After a bullish C2 closure: zone = **upper half of C2's wick-to-wick range** (`[EQ(C2), C2.h]`), drawn across the next HTF period; C3's low/wick is expected to form inside it. Bear: lower half. | NotebookLM TTrades nb (quoted: "mark out equilibrium of the previous candle's range wanting to see the upper half of that range support price higher and form the low of candle 3") |
| Candle EQ | 50% of the previous HTF candle's range, wick high to wick low. | `using-equilibrium-in-continuations.md` |
| Label states | gray = valid/forming; orange = didn't fail within the NEXT HTF candle (consolidation); red = FAILED (price returned to the initial sweep extreme without forming the HTF swing) → cease plotting projections/EQ/sweep/T-Spot for that formation. | TV script page `XdwK9qQQ` |
| STDV projections (bull) | Manipulation leg: legHigh = highest point between C2's open and the sweep-low bar, legLow = sweep extreme. Wick mode uses wick extremes, Body mode uses opens/closes. Level −k drawn at `legHigh + k*(legHigh−legLow)`. Defaults −1, −2, −2.5, −4, −4.5. Mirror for bear. | `standard-deviation-projections.md`; TV script page defaults |
| Pairing ladder | 3m→30m, 5m→1H, 15m→4H, 1H→D, 4H→W, D→M. Auto-Bias 1/2 = model one/two rungs above the active pair. | `timeframe-alignment-...md` + full guide |
| Failure of sweep line etc. | On red, that formation's projections/EQ/sweep/T-Spot stop plotting (delete or freeze the drawings). | TV script page `XdwK9qQQ` |

## Working rules for EVERY task

- **Source of truth on disk**: `~/mnq_trading/tradingview/ttfm_clone.pine`. Never edit in the TV editor directly.
- **Compile loop** (after `tv launch`, once per session):
  1. FIRST TIME ONLY: create a NEW Pine script slot named `TTFM Clone` (`tv pine new`; check `tv pine --help` for exact flags). NEVER open JUDGE or any S-series script in the editor.
  2. Before every compile: `tv pine get > /tmp/ttfm_backup_$(date +%s).pine` (auto-save gotcha: `tv pine compile` SAVES and bumps version).
  3. `tv pine set --file ~/mnq_trading/tradingview/ttfm_clone.pine` then `tv pine compile`. Expected: `compiled OK` / no errors.
  4. `tv state` — confirm the updated study is `TTFM Clone` (title-match can hit the wrong study).
  5. Visual check: `tv screenshot --region chart` and Read the PNG.
- **Chart for verification**: MNQ1! **5m** (pairing 5m↔1H auto).
- **Commits**: named files ONLY (`git add tradingview/ttfm_clone.pine`), never `git add -A`. Branch `ttfm-clone-indicator`.
- Pine has no unit-test framework: the test gate per task = clean compile + scripted visual assertion (screenshot shows the described elements on the described bars).

---

## Phase 1 — Core model

### Task 1: Scaffold + full settings panel

**Files:**
- Create: `~/mnq_trading/tradingview/ttfm_clone.pine`

- [ ] **Step 1: Write the scaffold with the complete settings panel** (all groups now, even Phase-2 ones — the panel mirrors the real TTFM 1:1 and later tasks only consume the inputs):

```pine
//@version=6
// TTFM Clone — faithful re-implementation of Fractal Model [Pro+] (TTrades) as a PASSIVE
// charting/learning tool. Grounded in the ttrades.com corpus; see
// docs/superpowers/specs/2026-07-09-ttfm-clone-indicator-design.md. NOT a signal tool.
indicator("Fractal Model (TTFM Clone)", "TTFM Clone", overlay = true,
     max_lines_count = 500, max_boxes_count = 500, max_labels_count = 500)

// ===== 1. SETTINGS =====
// -- Warnings --
bool showWarnings = input.bool(true, "Show warnings / errors", group = "Warnings")

// -- General --
bool  alertsOn   = input.bool(false, "Alerts", group = "General",
     tooltip = "Master enable. Individual alert events are toggled in their own sections.")
int   historyN   = input.int(0, "History", minval = 0, maxval = 40, group = "General",
     tooltip = "How many past formations stay on chart (each = 1 bullish + 1 bearish).")
string fractalMode = input.string("Automatic", "Fractal", group = "General",
     options = ["Automatic", "30m - 3m", "1H - 5m", "4H - 15m", "Daily - 1H", "Weekly - 4H", "Monthly - Daily", "Custom"])
bool  showC2 = input.bool(true,  "C2", inline = "cc", group = "General")
bool  showC3 = input.bool(true,  "C3", inline = "cc", group = "General")
bool  showC4 = input.bool(true,  "C4", inline = "cc", group = "General")
string customHtf = input.timeframe("60", "Custom fractal: HTF", group = "General")
string customLtf = input.timeframe("5",  "Custom fractal: LTF", group = "General")
string biasMode  = input.string("Neutral", "Bias", group = "General",
     options = ["Neutral", "Bullish", "Bearish", "Auto Bias 1", "Auto Bias 2"])

// -- HTF Candles --
int   htfCount  = input.int(4, "HTF candles", minval = 0, maxval = 40, group = "HTF Candles")
int   htfSizePx = input.int(2, "Size (bars per candle)", minval = 1, maxval = 6, group = "HTF Candles")
int   htfOffset = input.int(10, "Offset (bars right of price)", minval = 3, maxval = 100, group = "HTF Candles",
     tooltip = "Bump to 17+ on a second stacked instance.")
color bullBody  = input.color(color.new(#0b9981, 0), "Bull body",  inline = "bc", group = "HTF Candles")
color bullBrdr  = input.color(#0b9981, "border", inline = "bc", group = "HTF Candles")
color bearBody  = input.color(color.new(#d13c50, 0), "Bear body", inline = "rc", group = "HTF Candles")
color bearBrdr  = input.color(#d13c50, "border", inline = "rc", group = "HTF Candles")
color wickColr  = input.color(color.gray, "Wick", group = "HTF Candles")
bool  showHtfOpen  = input.bool(true,  "HTF open line", group = "HTF Candles")
bool  showVLines   = input.bool(true,  "Vertical lines (HTF period)", group = "HTF Candles")
bool  showLHLines  = input.bool(false, "L/H lines (prev HTF high/low)", group = "HTF Candles")
bool  showPrevEQ   = input.bool(true,  "Previous EQ (50% prev HTF candle)", group = "HTF Candles")
string drawType    = input.string("On Chart", "Drawing type", options = ["On Chart", "HTF Candle", "Both"], group = "HTF Candles")
bool  showTimeLbl  = input.bool(true, "Time labels", group = "HTF Candle Time Labels")
string timeFmt     = input.string("24h", "Format", options = ["24h", "AM/PM"], group = "HTF Candle Time Labels")
bool  useCustomTz  = input.bool(false, "Custom timezone", group = "HTF Candle Time Labels")
string customTz    = input.string("America/New_York", "Timezone", group = "HTF Candle Time Labels")

// -- Model Style --
bool  showLabels = input.bool(true, "TTFM labels (C2/C3/C4)", group = "Model Style")
string lblSize   = input.string("Small", "Label size", options = ["Tiny", "Small", "Normal"], group = "Model Style")
bool  showSweep  = input.bool(true, "Candle 1 sweep line", group = "Model Style")
color sweepCol   = input.color(color.orange, "Sweep color", group = "Model Style")
bool  showCisdB  = input.bool(true, "Bullish CISD", inline = "cb", group = "Model Style")
color cisdBCol   = input.color(#0b9981, "", inline = "cb", group = "Model Style")
bool  showCisdS  = input.bool(true, "Bearish CISD", inline = "cs", group = "Model Style")
color cisdSCol   = input.color(#d13c50, "", inline = "cs", group = "Model Style")
bool  showEq     = input.bool(true, "Candle equilibrium", group = "Model Style")
color eqCol      = input.color(color.silver, "EQ color", group = "Model Style")
bool  showTspot  = input.bool(true, "T-Spot", inline = "ts", group = "Model Style")
color tspotBull  = input.color(color.new(#0b9981, 82), "bull", inline = "ts", group = "Model Style")
color tspotBear  = input.color(color.new(#d13c50, 82), "bear", inline = "ts", group = "Model Style")
bool  earlyCisd  = input.bool(false, "Show early C2 CISD (preview, before HTF close)", group = "Model Style")
bool  earlyCisdAlert = input.bool(false, "Early C2 CISD alerts", group = "Model Style")
string c3Mode    = input.string("Body break", "C3 closure mode", options = ["Body break", "50% threshold"], group = "Model Style")

// -- SMT Divergence --
bool   smtOn     = input.bool(false, "Enable SMT?", group = "SMT Divergence")
bool   smtAlerts = input.bool(false, "SMT alerts", group = "SMT Divergence")
bool   smtLabels = input.bool(true,  "Labels", group = "SMT Divergence")
string smtMode   = input.string("Automatic", "SMT mode", options = ["Automatic", "Custom"], group = "SMT Divergence")
string smtSym1   = input.symbol("CME_MINI:ES1!", "Custom symbol 1", group = "SMT Divergence")
bool   smtUse2   = input.bool(false, "Enable secondary pair", group = "SMT Divergence")
string smtSym2   = input.symbol("CBOT_MINI:YM1!", "Custom symbol 2", group = "SMT Divergence")
bool   smtInverse = input.bool(false, "Inverse correlation", group = "SMT Divergence")

// -- Standard Deviation Projections --
bool   projOn    = input.bool(true, "Enable projections", group = "Projections")
bool   projLbls  = input.bool(true, "Labels", group = "Projections")
string projType  = input.string("Wick", "Type", options = ["Wick", "Body"], group = "Projections")
string projLvlsS = input.string("-1,-2,-2.5,-4,-4.5", "Levels (negative, comma-separated)", group = "Projections")

// -- Formation Liquidity --
bool  formLiqOn  = input.bool(false, "Enable formation liquidity", group = "Formation Liquidity")
color formLiqCol = input.color(color.new(color.orange, 30), "Color", group = "Formation Liquidity")

// -- Time Filter --
bool   tfilterOn = input.bool(false, "Enable time filter", group = "Time Filter")
string tfApplyBelow = input.timeframe("60", "Apply below (chart TF <=)", group = "Time Filter")
bool   tf1On = input.bool(false, "Filter 1", inline = "f1", group = "Time Filter")
string tf1   = input.session("0930-1100", "", inline = "f1", group = "Time Filter")
bool   tf2On = input.bool(false, "Filter 2", inline = "f2", group = "Time Filter")
string tf2   = input.session("1330-1600", "", inline = "f2", group = "Time Filter")
bool   tf3On = input.bool(false, "Filter 3", inline = "f3", group = "Time Filter")
string tf3   = input.session("0300-0500", "", inline = "f3", group = "Time Filter")
string tfTz  = input.string("America/New_York", "Filter timezone", group = "Time Filter")

// -- Info Table --
bool   tblOn   = input.bool(true, "Show info", group = "Info Table")
string tblSize = input.string("Small", "Size", options = ["Tiny", "Small", "Normal"], group = "Info Table")
string tblLoc  = input.string("Bottom Right", "Location", group = "Info Table",
     options = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
bool tblAsset  = input.bool(true, "Asset", inline = "t1", group = "Info Table")
bool tblTf     = input.bool(true, "Chart TF", inline = "t1", group = "Info Table")
bool tblPair   = input.bool(true, "Pairing", inline = "t2", group = "Info Table")
bool tblCount  = input.bool(true, "Countdown", inline = "t2", group = "Info Table")
bool tblBias   = input.bool(true, "Bias", inline = "t3", group = "Info Table")
bool tblFilter = input.bool(true, "Time filter", inline = "t3", group = "Info Table")
bool tblSmt    = input.bool(false, "SMT", inline = "t3", group = "Info Table")

// -- Calculation --
int calcBars = input.int(0, "Calculated bars (0 = all)", minval = 0, group = "Calculation")

// ===== 1b. CALC GUARD =====
bool inCalcWindow = calcBars == 0 or (last_bar_index - bar_index) <= calcBars
```

- [ ] **Step 2: Compile.** `tv pine new` (name `TTFM Clone`) → `tv pine set --file ~/mnq_trading/tradingview/ttfm_clone.pine` → `tv pine compile`. Expected: compiles clean (an indicator that draws nothing yet). `tv state` shows study `TTFM Clone`.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): scaffold + full TTFM-parity settings panel"
```

### Task 2: TF pairing ladder + local HTF aggregation engine

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append after section 1b)

- [ ] **Step 1: Append the pairing ladder, TF resolution, warning state, and the HTF aggregation engine:**

```pine
// ===== 2. TYPES =====
type HTFCandle
    float o
    float h
    float l
    float c
    int   tOpen    // open time (ms) of first LTF bar
    int   bStart   // bar_index of first LTF bar
    int   bEnd     // bar_index of last LTF bar

// ===== 3. PAIRING LADDER =====
// Canonical ladder (timeframe-alignment article): 3m→30m, 5m→1H, 15m→4H, 1H→D, 4H→W, D→M
ladderHtf(string ltf) =>
    switch ltf
        "3"   => "30"
        "5"   => "60"
        "15"  => "240"
        "60"  => "D"
        "240" => "W"
        "D"   => "M"
        => na

// Resolve active pairing from the Fractal setting
resolvePair() =>
    string htf = na
    string ltf = na
    if fractalMode == "Automatic"
        ltf := timeframe.period
        htf := ladderHtf(timeframe.period)
    else if fractalMode == "Custom"
        ltf := customLtf
        htf := customHtf
    else
        // preset strings like "1H - 5m"
        [h, l] = switch fractalMode
            "30m - 3m"       => ["30", "3"]
            "1H - 5m"        => ["60", "5"]
            "4H - 15m"       => ["240", "15"]
            "Daily - 1H"     => ["D", "60"]
            "Weekly - 4H"    => ["W", "240"]
            "Monthly - Daily"=> ["M", "D"]
        htf := h
        ltf := l
    [htf, ltf]

[htfStr, ltfStr] = resolvePair()

// TF-mismatch safeguard (real TTFM behavior): chart TF above the model's LTF →
// CISD & projections disabled, warning shown; HTF candles stay visible.
bool pairUnsupported = na(htfStr)
bool tfMismatch = not pairUnsupported and timeframe.in_seconds(timeframe.period) > timeframe.in_seconds(ltfStr)
bool modelEnabled = not pairUnsupported and not tfMismatch and inCalcWindow

// ===== 4. HTF AGGREGATION ENGINE =====
// HTF candles are aggregated locally from chart bars. Fully causal: the completed
// candle is finalized on the FIRST bar of the next HTF period, using only [1]-history.
var array<HTFCandle> htfArr = array.new<HTFCandle>()
var float aggO = na
var float aggH = na
var float aggL = na
var int   aggT = na
var int   aggB = na

bool newHtfPeriod = not pairUnsupported and timeframe.change(htfStr)

// finalize the just-completed HTF candle (values as of bar_index-1)
if newHtfPeriod and not na(aggO)
    array.push(htfArr, HTFCandle.new(aggO, aggH, aggL, close[1], aggT, aggB, bar_index - 1))
    if array.size(htfArr) > 60   // keep a bounded working set (>= 40 history + working room)
        array.shift(htfArr)

// start/continue the running candle
if newHtfPeriod or na(aggO)
    aggO := open
    aggH := high
    aggL := low
    aggT := time
    aggB := bar_index
else
    aggH := math.max(aggH, high)
    aggL := math.min(aggL, low)

int nHtf = array.size(htfArr)
HTFCandle lastHtf = nHtf > 0 ? array.get(htfArr, nHtf - 1) : na
HTFCandle prevHtf = nHtf > 1 ? array.get(htfArr, nHtf - 2) : na
```

- [ ] **Step 2: Add a temporary debug plot to verify aggregation** (removed in Step 5):

```pine
// TEMP DEBUG — remove after verification
plot(nHtf > 0 ? array.get(htfArr, nHtf - 1).c : na, "last HTF close", color.yellow, 2, plot.style_stepline)
```

- [ ] **Step 3: Compile + verify.** On MNQ1! 5m the yellow stepline must equal the 1H closes (cross-check 2-3 values against a 1H chart). Expected: steps change exactly at each top of hour.

- [ ] **Step 4: Verify the mismatch flag.** Switch chart to 15m with Fractal = "1H - 5m": `tfMismatch` should be true (add `plotchar(tfMismatch, "mism", "!", location.top)` temporarily if needed). Switch back to 5m.

- [ ] **Step 5: Remove the debug plots, compile again** (clean), **commit:**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): pairing ladder + causal local HTF aggregation engine"
```

### Task 3: HTF candle panel rendering + extras

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append)

- [ ] **Step 1: Append the HTF panel renderer** (boxes + wick lines right of price, redrawn each HTF close; developing candle drawn from live agg values), the HTF open line, vertical period lines, prev L/H lines, previous EQ, and time labels:

```pine
// ===== 5. HTF CANDLE PANEL =====
var array<box>   htfBoxes  = array.new<box>()
var array<line>  htfWicks  = array.new<line>()
var array<label> htfTimeLbls = array.new<label>()

clearHtfPanel() =>
    while array.size(htfBoxes) > 0
        box.delete(array.pop(htfBoxes))
    while array.size(htfWicks) > 0
        line.delete(array.pop(htfWicks))
    while array.size(htfTimeLbls) > 0
        label.delete(array.pop(htfTimeLbls))

tzActive() => useCustomTz ? customTz : syminfo.timezone

fmtTime(int t) =>
    str.format_time(t, timeFmt == "24h" ? "HH:mm" : "hh:mm a", tzActive())

// slot i = 0..count-1, 0 = oldest displayed; developing candle occupies the last slot
htfSlotX(int i) =>
    bar_index + htfOffset + i * (htfSizePx + 2)

drawHtfCandle(float o, float h, float l, float c, int t, int slot, bool developing) =>
    int x1 = htfSlotX(slot)
    int x2 = x1 + htfSizePx
    int xm = x1 + htfSizePx / 2
    color bod = c >= o ? bullBody : bearBody
    color brd = c >= o ? bullBrdr : bearBrdr
    array.push(htfBoxes, box.new(x1, math.max(o, c), x2, math.min(o, c),
         border_color = developing ? color.new(brd, 40) : brd,
         bgcolor = developing ? color.new(bod, 60) : bod, xloc = xloc.bar_index))
    array.push(htfWicks, line.new(xm, h, xm, math.max(o, c), color = wickColr, xloc = xloc.bar_index))
    array.push(htfWicks, line.new(xm, math.min(o, c), xm, l, color = wickColr, xloc = xloc.bar_index))
    if showTimeLbl
        array.push(htfTimeLbls, label.new(xm, l, fmtTime(t), style = label.style_label_up,
             textcolor = color.gray, size = size.tiny, color = color.new(color.white, 100), xloc = xloc.bar_index))

// model-level drawing helper honoring Drawing Type (On Chart / HTF Candle / Both)
// draws a horizontal level; onChart span = [b1, b2] chart bars; panel span = current panel slots
drawLevel(float price, int b1, int b2, color col, string styl, int width) =>
    array<line> out = array.new<line>()
    lineStyle = styl == "dashed" ? line.style_dashed : styl == "dotted" ? line.style_dotted : line.style_solid
    if drawType != "HTF Candle"
        array.push(out, line.new(b1, price, b2, price, color = col, style = lineStyle, width = width, xloc = xloc.bar_index))
    if drawType != "On Chart"
        array.push(out, line.new(htfSlotX(0), price, htfSlotX(math.max(htfCount - 1, 0)) + htfSizePx, price,
             color = col, style = lineStyle, width = width, xloc = xloc.bar_index))
    out

var line htfOpenLn = na
var line prevEqLn  = na
var line prevHiLn  = na
var line prevLoLn  = na
var array<line> vLines = array.new<line>()

if barstate.islast and htfCount > 0 and not pairUnsupported
    clearHtfPanel()
    int shown = math.min(htfCount - 1, nHtf)   // completed candles shown (last slot = developing)
    for i = 0 to shown - 1
        HTFCandle hc = array.get(htfArr, nHtf - shown + i)
        drawHtfCandle(hc.o, hc.h, hc.l, hc.c, hc.tOpen, i, false)
    drawHtfCandle(aggO, aggH, aggL, close, aggT, shown, true)

    // HTF open line (open of the developing HTF candle, from its first bar to now)
    line.delete(htfOpenLn)
    if showHtfOpen
        htfOpenLn := line.new(aggB, aggO, bar_index + htfOffset, aggO, color = color.gray,
             style = line.style_dotted, xloc = xloc.bar_index)
    // Previous HTF candle levels
    line.delete(prevEqLn), line.delete(prevHiLn), line.delete(prevLoLn)
    if nHtf > 0
        HTFCandle p = array.get(htfArr, nHtf - 1)
        if showPrevEQ
            prevEqLn := line.new(aggB, (p.h + p.l) / 2, bar_index + htfOffset, (p.h + p.l) / 2,
                 color = eqCol, style = line.style_dashed, xloc = xloc.bar_index)
        if showLHLines
            prevHiLn := line.new(p.bStart, p.h, bar_index + htfOffset, p.h, color = color.gray, xloc = xloc.bar_index)
            prevLoLn := line.new(p.bStart, p.l, bar_index + htfOffset, p.l, color = color.gray, xloc = xloc.bar_index)

// vertical period lines drawn once per HTF boundary (persistent, not repainted)
if newHtfPeriod and showVLines and not pairUnsupported
    array.push(vLines, line.new(bar_index, low, bar_index, high, extend = extend.both,
         color = color.new(color.gray, 70), style = line.style_dotted, xloc = xloc.bar_index))
    if array.size(vLines) > 24
        line.delete(array.shift(vLines))
```

- [ ] **Step 2: Compile + visual verify.** Screenshot MNQ1! 5m. Expected: up to 3 completed 1H candles + 1 lighter developing candle right of price, time labels beneath, dotted HTF open line, dashed prev-EQ, dotted vertical lines at each top of hour. Cross-check one HTF candle's OHLC against the 1H chart.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): HTF candle panel + open/EQ/LH/vertical lines + time labels"
```

### Task 4: Formation state machine (sweep, C2/C3/C4, gray/orange/red, labels)

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append)

- [ ] **Step 1: Append the Formation type, pure closure detectors, and the lifecycle driver** that runs at every HTF close:

```pine
// ===== 6. FORMATION STATE MACHINE =====
// States
int ST_C2      = 0   // C2 closed, waiting on C3 (gray)
int ST_C3      = 1   // C3 closed, tracking C4 (gray)
int ST_CONSOL  = 2   // next HTF candle neither expanded nor failed (orange)
int ST_FAILED  = 3   // price returned to sweep extreme before HTF swing formed (red)
int ST_DONE    = 4   // delivered (C4 seen) — kept for history

type Formation
    int   dir            // 1 bull, -1 bear
    int   state
    int   c1Idx          // index into htfArr of Candle 1
    float sweepLevel     // C1 extreme that was swept
    float sweepExtreme   // furthest manipulation price (C2 wick tip)
    float c2O
    float c2H
    float c2L
    float c2C
    int   c2BStart
    int   c2BEnd
    bool  ideal          // protected swing on the closure candle (★)
    float cisdLevel
    bool  cisdConfirmed
    int   cisdRunStartB  // bar_index of first candle of the opposing LTF run
    // drawings
    line  sweepLn
    array<line> cisdLns
    array<line> eqLns
    box   tspotBx
    label lbl
    array<line> projLns
    array<label> projLbls
    array<line> liqLns

var array<Formation> formations = array.new<Formation>()

// bull C2: sweeps C1 low AND body closes back inside C1 range (corpus: wick-only is NOT a C2)
isC2(HTFCandle c1, HTFCandle c2, int dir) =>
    dir == 1 ? (c2.l < c1.l and c2.c > c1.l) : (c2.h > c1.h and c2.c < c1.h)

// C3 closure: close beyond C2 extreme (Body break) or beyond 50% of C2 range (50% threshold)
isC3(Formation f, HTFCandle c3) =>
    float thr = c3Mode == "Body break" ?
         (f.dir == 1 ? math.max(f.c2O, f.c2C) : math.min(f.c2O, f.c2C)) :
         (f.c2H + f.c2L) / 2
    f.dir == 1 ? c3.c > thr : c3.c < thr

// Ideal Formation: closure candle also closes through the opposing HTF candle series
// (bull: consecutive down-close candles into the low; level = open of the FIRST candle of that run)
opposingSeriesOpen(int endIdx, int dir) =>
    // walk back from htfArr[endIdx] while candles oppose `dir`
    float lvl = na
    int i = endIdx
    while i >= 0
        HTFCandle hc = array.get(htfArr, i)
        bool opposing = dir == 1 ? hc.c < hc.o : hc.c > hc.o
        if not opposing
            break
        lvl := hc.o
        i -= 1
    lvl

eraseFormation(Formation f, bool full) =>
    // full = delete everything; else only the "cease plotting on failure" set
    line.delete(f.sweepLn)
    box.delete(f.tspotBx)
    for ln in f.eqLns
        line.delete(ln)
    for ln in f.projLns
        line.delete(ln)
    for lb in f.projLbls
        label.delete(lb)
    if full
        for ln in f.cisdLns
            line.delete(ln)
        for ln in f.liqLns
            line.delete(ln)
        label.delete(f.lbl)

lblSizeConst() => lblSize == "Tiny" ? size.tiny : lblSize == "Small" ? size.small : size.normal

setLabel(Formation f, string txt, color col) =>
    if showLabels
        label.delete(f.lbl)
        int x = (f.c2BStart + f.c2BEnd) / 2
        f.lbl := label.new(x, f.dir == 1 ? f.sweepExtreme : f.sweepExtreme, txt,
             style = f.dir == 1 ? label.style_label_up : label.style_label_down,
             color = color.new(col, 20), textcolor = color.white, size = lblSizeConst(), xloc = xloc.bar_index)

biasAllows(int dir) =>
    biasMode == "Neutral" ? true :
     biasMode == "Bullish" ? dir == 1 :
     biasMode == "Bearish" ? dir == -1 : true   // Auto Bias wired in Task 11

// --- lifecycle driver: runs once per completed HTF candle ---
if newHtfPeriod and modelEnabled and nHtf >= 2
    HTFCandle cur = array.get(htfArr, nHtf - 1)   // just closed
    HTFCandle pre = array.get(htfArr, nHtf - 2)

    // 1) advance existing formations
    for f in formations
        if f.state == ST_C2 or f.state == ST_C3
            bool failed = f.dir == 1 ? cur.l < f.sweepExtreme : cur.h > f.sweepExtreme
            if failed
                f.state := ST_FAILED
                setLabel(f, f.state == ST_FAILED and f.ideal ? "C2 ★" : "C2", color.red)
                eraseFormation(f, false)   // cease projections/EQ/sweep/T-Spot per real TTFM
            else if f.state == ST_C2
                if isC3(f, cur)
                    f.state := ST_C3
                    if showC3
                        setLabel(f, f.ideal ? "C3 ★" : "C3", color.gray)
                else
                    f.state := ST_CONSOL
                    setLabel(f, "C2", color.orange)
            else if f.state == ST_C3
                bool c4cont = f.dir == 1 ? cur.c > cur.o : cur.c < cur.o
                f.state := ST_DONE
                if c4cont and showC4
                    setLabel(f, f.ideal ? "C4 ★" : "C4", color.gray)

    // 2) detect a NEW C2 on the just-closed candle (both directions)
    for dir in array.from(1, -1)
        if isC2(pre, cur, dir) and biasAllows(dir) and (showC2 or showC3 or showC4)
            float seriesOpen = opposingSeriesOpen(nHtf - 2, dir)
            bool idealFlag = not na(seriesOpen) and (dir == 1 ? cur.c > seriesOpen : cur.c < seriesOpen)
            Formation f = Formation.new(
                 dir = dir, state = ST_C2, c1Idx = nHtf - 2,
                 sweepLevel = dir == 1 ? pre.l : pre.h,
                 sweepExtreme = dir == 1 ? cur.l : cur.h,
                 c2O = cur.o, c2H = cur.h, c2L = cur.l, c2C = cur.c,
                 c2BStart = cur.bStart, c2BEnd = cur.bEnd,
                 ideal = idealFlag, cisdLevel = na, cisdConfirmed = false, cisdRunStartB = na,
                 sweepLn = na, cisdLns = array.new<line>(), eqLns = array.new<line>(),
                 tspotBx = na, lbl = na, projLns = array.new<line>(), projLbls = array.new<label>(),
                 liqLns = array.new<line>())
            if showSweep
                f.sweepLn := line.new(pre.bStart, f.sweepLevel, cur.bEnd, f.sweepLevel,
                     color = sweepCol, width = 1, xloc = xloc.bar_index)
            if showC2
                setLabel(f, idealFlag ? "C2 ★" : "C2", color.gray)
            array.push(formations, f)

    // 3) history cap: keep current + historyN per direction
    int keep = (historyN + 1) * 2 + 2
    while array.size(formations) > keep
        Formation old = array.shift(formations)
        eraseFormation(old, true)
```

- [ ] **Step 2: Compile + verify on known formations.** On MNQ1! 5m scroll to a recent NY session; find an hour that swept the prior hour's low and closed back inside (confirm on the 1H chart). Expected: gray `C2` label under that hour's bars + orange sweep line on the prior hour's low; next hour expanding up → label advances to `C3`; a formation whose next candle traded below the sweep wick shows red; an inside next candle shows orange.

- [ ] **Step 3: Bar-replay non-repaint check.** TradingView bar replay from ~3 days back, play through 2-3 formations: labels/lines must appear only at HTF closes and never move afterward.

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): formation state machine (C2/C3/C4, gray/orange/red, ideal flag, sweep line)"
```

### Task 5: LTF CISD engine (pending → confirmed, early C2 preview)

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append; also one insertion inside the Task-4 driver)

- [ ] **Step 1: Append the LTF opposing-run tracker.** It watches chart bars inside the developing HTF candle and maintains the CISD level for each direction (open of the first candle of the consecutive opposing-close run containing the extreme):

```pine
// ===== 7. LTF CISD ENGINE =====
// Tracks, inside the developing HTF candle, the consecutive down-close (up-close) LTF run
// that contains the lowest low (highest high). CISD level = open of the run's first candle.
var float bullCisdLvl = na      // level to close ABOVE (from down-run into the low)
var int   bullRunStartB = na
var float bearCisdLvl = na      // level to close BELOW (from up-run into the high)
var int   bearRunStartB = na
var float runOpenDown = na      // open of current consecutive down-close run
var int   runStartBDown = na
var float runOpenUp = na
var int   runStartBUp = na
var float lowestInHtf = na
var float highestInHtf = na

if newHtfPeriod
    bullCisdLvl := na, bullRunStartB := na, bearCisdLvl := na, bearRunStartB := na
    runOpenDown := na, runOpenUp := na, lowestInHtf := na, highestInHtf := na

if barstate.isconfirmed and modelEnabled
    bool downClose = close < open
    bool upClose   = close > open
    // extend / start runs
    if downClose
        if na(runOpenDown) or not (close[1] < open[1])
            runOpenDown := open
            runStartBDown := bar_index
    else
        runOpenDown := na
    if upClose
        if na(runOpenUp) or not (close[1] > open[1])
            runOpenUp := open
            runStartBUp := bar_index
    else
        runOpenUp := na
    // capture the run that contains the HTF-candle extreme
    if na(lowestInHtf) or low < lowestInHtf
        lowestInHtf := low
        if not na(runOpenDown)
            bullCisdLvl := runOpenDown
            bullRunStartB := runStartBDown
    if na(highestInHtf) or high > highestInHtf
        highestInHtf := high
        if not na(runOpenUp)
            bearCisdLvl := bearRunStartB == na ? runOpenUp : runOpenUp
            bearRunStartB := runStartBUp

// pending/confirmed CISD lines for ACTIVE formations (state C2/C3, this HTF candle)
drawCisd(Formation f) =>
    bool enabled = f.dir == 1 ? showCisdB : showCisdS
    color col = f.dir == 1 ? cisdBCol : cisdSCol
    if enabled and not na(f.cisdLevel)
        for ln in f.cisdLns
            line.delete(ln)
        array.clear(f.cisdLns)
        for ln in drawLevel(f.cisdLevel, f.cisdRunStartB, bar_index,
             f.cisdConfirmed ? col : color.new(col, 40), f.cisdConfirmed ? "solid" : "dashed", 2)
            array.push(f.cisdLns, ln)

if barstate.isconfirmed and modelEnabled
    for f in formations
        if f.state == ST_C2 or f.state == ST_C3
            // adopt the current intra-HTF level while unconfirmed
            if not f.cisdConfirmed
                float lvl = f.dir == 1 ? bullCisdLvl : bearCisdLvl
                int   rsb = f.dir == 1 ? bullRunStartB : bearRunStartB
                if not na(lvl)
                    f.cisdLevel := lvl
                    f.cisdRunStartB := rsb
                if not na(f.cisdLevel)
                    bool crossed = f.dir == 1 ? close > f.cisdLevel : close < f.cisdLevel
                    if crossed
                        f.cisdConfirmed := true
            drawCisd(f)

// Early C2 CISD preview: developing HTF candle has swept prev HTF extreme and an LTF close
// crossed the intra-candle CISD level — shown BEFORE the HTF closes (flagged preview, like real TTFM)
var line earlyLn = na
if earlyCisd and modelEnabled and barstate.isconfirmed and nHtf >= 1
    line.delete(earlyLn)
    HTFCandle p = array.get(htfArr, nHtf - 1)
    bool sweptLo = aggL < p.l and not na(bullCisdLvl) and close > bullCisdLvl
    bool sweptHi = aggH > p.h and not na(bearCisdLvl) and close < bearCisdLvl
    if sweptLo
        earlyLn := line.new(bullRunStartB, bullCisdLvl, bar_index, bullCisdLvl,
             color = color.new(cisdBCol, 50), style = line.style_dotted, width = 2, xloc = xloc.bar_index)
    else if sweptHi
        earlyLn := line.new(bearRunStartB, bearCisdLvl, bar_index, bearCisdLvl,
             color = color.new(cisdSCol, 50), style = line.style_dotted, width = 2, xloc = xloc.bar_index)
```

- [ ] **Step 2: Compile + verify.** On a bullish C2 hour: dashed CISD line at the open of the 5m down-run into the hour's low; turns solid on the first 5m close above it. Enable "Show early C2 CISD" and confirm the dotted preview appears during a developing sweep hour and disappears if invalidated (preview is the ONLY element allowed to do that).

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): LTF CISD engine (pending/confirmed) + early C2 preview"
```

### Task 6: Candle EQ + T-Spot + formation-level rendering polish

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (insert into the Task-4 new-C2 block + append)

- [ ] **Step 1: In the Task-4 driver, right after `array.push(formations, f)` in the new-C2 branch, insert EQ + T-Spot drawing** (T-Spot = expansion-side half of C2's range, drawn across the next HTF period; EQ = 50% of C2 wick-to-wick):

```pine
            // EQ of the closure candle (vital component per corpus)
            float eqLvl = (cur.h + cur.l) / 2
            if showEq
                for ln in drawLevel(eqLvl, cur.bStart, cur.bEnd + (cur.bEnd - cur.bStart + 1), eqCol, "dotted", 1)
                    array.push(f.eqLns, ln)
            // T-Spot: bull = upper half [EQ, C2 high]; bear = lower half [C2 low, EQ];
            // C3's wick expected to form inside it during the NEXT HTF period
            if showTspot
                int spanEnd = cur.bEnd + (cur.bEnd - cur.bStart + 1)
                f.tspotBx := box.new(cur.bEnd + 1, dir == 1 ? cur.h : eqLvl, spanEnd, dir == 1 ? eqLvl : cur.l,
                     bgcolor = dir == 1 ? tspotBull : tspotBear, border_color = color.new(color.gray, 60),
                     xloc = xloc.bar_index)
```

- [ ] **Step 2: Compile + verify.** For a fresh bullish C2: dotted EQ line at the mid of the C2 hour's range + shaded box covering the upper half of that range, spanning the following hour. Confirm the box vanishes on formations that later turn red (Task 4's `eraseFormation(f, false)` already deletes it).

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): candle EQ + T-Spot zone (expansion-side half, corpus-grounded)"
```

### Task 7: Info table (basic) + TF-mismatch warning

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append)

- [ ] **Step 1: Append the info table:**

```pine
// ===== 8. INFO TABLE =====
tblPos() =>
    switch tblLoc
        "Top Left"     => position.top_left
        "Top Right"    => position.top_right
        "Bottom Left"  => position.bottom_left
        => position.bottom_right

tblTxtSize() => tblSize == "Tiny" ? size.tiny : tblSize == "Small" ? size.small : size.normal

fmtCountdown() =>
    int msLeft = time_close(htfStr) - timenow
    int s = math.max(msLeft / 1000, 0)
    str.format("{0,number,00}:{1,number,00}:{2,number,00}", s / 3600, (s % 3600) / 60, s % 60)

var table infoTbl = na
if barstate.islast
    if not na(infoTbl)
        table.delete(infoTbl)
    if tblOn
        infoTbl := table.new(tblPos(), 2, 8, bgcolor = color.new(color.black, 20), border_width = 1)
        int r = 0
        addRow(string k, string v) =>
            table.cell(infoTbl, 0, r, k, text_color = color.gray,  text_size = tblTxtSize())
            table.cell(infoTbl, 1, r, v, text_color = color.white, text_size = tblTxtSize())
            r += 1
        if showWarnings and pairUnsupported
            addRow("⚠", "No ladder pairing for this chart TF — use Custom")
        if showWarnings and tfMismatch
            addRow("⚠", "Chart TF above model LTF — CISD/projections off")
        if tblAsset
            addRow("Asset", syminfo.ticker)
        if tblTf
            addRow("Chart TF", timeframe.period)
        if tblPair
            addRow("Pairing", str.tostring(htfStr) + " ↔ " + str.tostring(ltfStr))
        if tblCount and not pairUnsupported
            addRow("HTF close in", fmtCountdown())
        if tblBias
            addRow("Bias", biasMode)
        if tblFilter
            addRow("Time filter", tfilterOn ? "ON" : "OFF")
        if tblSmt
            addRow("SMT", smtOn ? "ON" : "OFF")
```

- [ ] **Step 2: Compile + verify.** Table bottom-right with asset/TF/pairing/live countdown/bias rows. Switch chart to 15m (Fractal "1H - 5m") → warning row appears, model drawings stop, HTF candles stay. Switch back.

- [ ] **Step 3: Phase-1 gate — ground-truth video comparison.** Frame-extract the real TTFM from the published videos and compare against our chart on the same symbol/date/TF:

```bash
# breakdown video (Toodegrees x TTrades) — shows the indicator on identifiable charts
yt-dlp -f "bv*[height<=1080]" -o /tmp/ttfm_breakdown.mp4 "https://www.youtube.com/watch?v=-n31VuAijzo"
# then: /watch-video /tmp/ttfm_breakdown.mp4  (local whisper+frames), pick 3+ frames where
# symbol/date/TF are readable, replicate each on our chart, screenshot, compare:
# sweep line placement, C2/C3 label positions, CISD level, EQ, T-Spot half, label colors.
```

Expected: element-for-element match on ≥3 independent formations; any mismatch → fix detection before Phase 2 and note the rule correction in the plan's rule table.

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): info table + TF-mismatch warnings (Phase 1 complete)"
```

---

## Phase 2 — Modules

### Task 8: STDV projections

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append helper; insert call in the Task-4 new-C2 block)

- [ ] **Step 1: Append the projection engine:**

```pine
// ===== 9. STDV PROJECTIONS =====
array<float> projLevels() =>
    array<float> out = array.new<float>()
    for s in str.split(projLvlsS, ",")
        float v = str.tonumber(str.trim(s))
        if not na(v) and v < 0
            array.push(out, v)
    out

// manipulation leg measured on the C2 HTF candle:
// wick mode: legHigh=C2.h→legLow=sweep extreme (bull); body mode: opens/closes
drawProjections(Formation f, HTFCandle cur) =>
    if projOn
        float legHi = projType == "Wick" ? cur.h : math.max(cur.o, cur.c)
        float legLo = projType == "Wick" ? cur.l : math.min(cur.o, cur.c)
        float rng = legHi - legLo
        int x1 = cur.bEnd + 1
        int x2 = cur.bEnd + 2 * (cur.bEnd - cur.bStart + 1)
        if rng > 0
            for lv in projLevels()
                float price = f.dir == 1 ? legHi + math.abs(lv) * rng : legLo - math.abs(lv) * rng
                line pl = line.new(x1, price, x2, price, color = color.new(color.blue, 30),
                     style = line.style_dotted, xloc = xloc.bar_index)
                array.push(f.projLns, pl)
                if projLbls
                    array.push(f.projLbls, label.new(x2, price, str.tostring(lv),
                         style = label.style_label_left, textcolor = color.blue,
                         color = color.new(color.white, 100), size = size.tiny, xloc = xloc.bar_index))
```

- [ ] **Step 2: In the Task-4 new-C2 branch (after the T-Spot insert), add:** `drawProjections(f, cur)`

- [ ] **Step 3: Compile + verify.** Bullish C2 → dotted blue levels above the C2 high at −1/−2/−2.5/−4/−4.5 × leg range with left-pointing labels; switch Type to Body and confirm levels tighten. Red formations lose their projections (already handled by `eraseFormation`).

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): STDV projections (wick/body, custom negative levels)"
```

### Task 9: Formation liquidity

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append helper; insert call in the Task-4 new-C2 block)

- [ ] **Step 1: Append + wire:**

```pine
// ===== 10. FORMATION LIQUIDITY =====
// prior HTF highs (bull) / lows (bear) above/below the closure = resting targets
drawFormationLiquidity(Formation f, HTFCandle cur) =>
    if formLiqOn
        int found = 0
        int i = nHtf - 3   // skip C1 and C2
        while i >= 0 and found < 3
            HTFCandle hc = array.get(htfArr, i)
            bool isTarget = f.dir == 1 ? hc.h > cur.c : hc.l < cur.c
            if isTarget
                float price = f.dir == 1 ? hc.h : hc.l
                array.push(f.liqLns, line.new(hc.bEnd, price, cur.bEnd + 12, price,
                     color = formLiqCol, style = line.style_solid, width = 1, xloc = xloc.bar_index))
                found += 1
            i -= 1
```

In the Task-4 new-C2 branch add: `drawFormationLiquidity(f, cur)`

- [ ] **Step 2: Compile + verify** (enable the toggle): orange rays from up to 3 prior 1H highs extending right on a bullish formation.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): formation liquidity target rays"
```

### Task 10: Time filters

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append helper; wire into the Task-4 new-C2 condition)

- [ ] **Step 1: Append:**

```pine
// ===== 11. TIME FILTER =====
inSession(string sess) => not na(time(timeframe.period, sess + ":1234567", tfTz))

timeFilterOk() =>
    if not tfilterOn
        true
    else if timeframe.in_seconds(timeframe.period) > timeframe.in_seconds(tfApplyBelow)
        true   // Apply Below: filter only at/below the selected TF
    else
        bool anyOn = tf1On or tf2On or tf3On
        not anyOn or (tf1On and inSession(tf1)) or (tf2On and inSession(tf2)) or (tf3On and inSession(tf3))
```

- [ ] **Step 2: Wire it:** in the Task-4 new-C2 condition, extend to `... and biasAllows(dir) and timeFilterOk() and ...`

- [ ] **Step 3: Compile + verify.** Enable filter 1 = `0930-1100` NY: formations whose C2 closes outside the window no longer print; inside it they do. Disable → all print again.

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): session time filters (3 windows, apply-below, tz)"
```

### Task 11: Auto Bias 1/2

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append a second aggregation lane; update `biasAllows`)

- [ ] **Step 1: Append a minimal higher-rung closure tracker** (direction only — the HTF-closure part of the model, one/two rungs above the active pair):

```pine
// ===== 12. AUTO BIAS =====
string ab1Htf = ladderHtf(htfStr)                      // one rung up (e.g. 1H↔5m → 4H)
string ab2Htf = na(ab1Htf) ? na : ladderHtf(ab1Htf)    // two rungs up (→ D)

// tiny per-rung aggregator + last C2/C3 direction
type RungState
    float o
    float h
    float l
    float pO
    float pH
    float pL
    float pC
    int   biasDir   // last closure direction: 1 / -1 / 0 none

var RungState ab1 = RungState.new(na, na, na, na, na, na, na, 0)
var RungState ab2 = RungState.new(na, na, na, na, na, na, na, 0)

updateRung(RungState st, string tf) =>
    if not na(tf) and timeframe.change(tf)
        if not na(st.o)
            float cC = close[1]
            if not na(st.pO)
                // C2 closure at this rung sets bias to the reversal direction
                if st.l < st.pL and cC > st.pL
                    st.biasDir := 1
                else if st.h > st.pH and cC < st.pH
                    st.biasDir := -1
                // continuation closure keeps/asserts trend direction
                else if cC > st.pH
                    st.biasDir := 1
                else if cC < st.pL
                    st.biasDir := -1
            st.pO := st.o
            st.pH := st.h
            st.pL := st.l
            st.pC := cC
        st.o := open
        st.h := high
        st.l := low
    else if not na(st.o)
        st.h := math.max(st.h, high)
        st.l := math.min(st.l, low)

updateRung(ab1, ab1Htf)
updateRung(ab2, ab2Htf)
```

- [ ] **Step 2: Replace `biasAllows` (Task 4) with:**

```pine
biasAllows(int dir) =>
    switch biasMode
        "Neutral"     => true
        "Bullish"     => dir == 1
        "Bearish"     => dir == -1
        "Auto Bias 1" => ab1.biasDir == 0 or dir == ab1.biasDir
        "Auto Bias 2" => ab2.biasDir == 0 or dir == ab2.biasDir
        => true
```

Also update the info-table Bias row: `addRow("Bias", biasMode + (biasMode == "Auto Bias 1" ? (ab1.biasDir == 1 ? " ▲" : ab1.biasDir == -1 ? " ▼" : " –") : biasMode == "Auto Bias 2" ? (ab2.biasDir == 1 ? " ▲" : ab2.biasDir == -1 ? " ▼" : " –") : ""))`

- [ ] **Step 3: Compile + verify.** Set Bias = Auto Bias 1 on 5m: only formations matching the 4H closure direction print; table shows ▲/▼. Set Neutral → both directions return.

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): Auto Bias 1/2 via higher-rung closure direction"
```

### Task 12: SMT divergence module

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (append)

- [ ] **Step 1: Append.** The ONLY `request.security` use; confirmed HTF values only (`[1]` + `lookahead_on` = last completed HTF bar, non-repainting):

```pine
// ===== 13. SMT DIVERGENCE =====
autoPair() =>
    string root = syminfo.root
    root == "NQ" or root == "MNQ" ? "CME_MINI:ES1!" :
     root == "ES" or root == "MES" ? "CME_MINI:NQ1!" :
     root == "YM" or root == "MYM" ? "CME_MINI:NQ1!" :
     root == "RTY" or root == "M2K" ? "CME_MINI:ES1!" : "CME_MINI:ES1!"

smtSymbol() => smtMode == "Automatic" ? autoPair() : smtSym1

// last COMPLETED HTF candle of the pair symbol (non-repainting)
[pH1, pL1, pH0, pL0] = request.security(smtSymbol(), htfStr,
     [high[2], low[2], high[1], low[1]], lookahead = barmerge.lookahead_on)
[qH1, qL1, qH0, qL0] = smtUse2 ?
     request.security(smtSym2, htfStr, [high[2], low[2], high[1], low[1]], lookahead = barmerge.lookahead_on) :
     [na, na, na, na]

var array<line>  smtLns  = array.new<line>()
var array<label> smtLbls = array.new<label>()

checkSmt(float oH1, float oL1, float oH0, float oL0, string symName) =>
    if nHtf >= 2
        HTFCandle cur = array.get(htfArr, nHtf - 1)
        HTFCandle pre = array.get(htfArr, nHtf - 2)
        // bullish SMT: chart sweeps prior low, pair does NOT (inverse flag flips the pair test)
        bool pairSweptLow  = smtInverse ? oH0 > oH1 : oL0 < oL1
        bool pairSweptHigh = smtInverse ? oL0 < oL1 : oH0 > oH1
        bool bullSmt = cur.l < pre.l and not pairSweptLow
        bool bearSmt = cur.h > pre.h and not pairSweptHigh
        if bullSmt or bearSmt
            float y1 = bullSmt ? pre.l : pre.h
            float y2 = bullSmt ? cur.l : cur.h
            array.push(smtLns, line.new(pre.bStart, y1, cur.bEnd, y2,
                 color = bullSmt ? cisdBCol : cisdSCol, width = 2, style = line.style_dashed, xloc = xloc.bar_index))
            if smtLabels
                array.push(smtLbls, label.new(cur.bEnd, y2, "SMT " + symName,
                     style = bullSmt ? label.style_label_up : label.style_label_down,
                     color = color.new(color.black, 40), textcolor = color.white, size = size.tiny, xloc = xloc.bar_index))
            if array.size(smtLns) > 20
                line.delete(array.shift(smtLns))
            if array.size(smtLbls) > 20
                label.delete(array.shift(smtLbls))
            true
        else
            false
    else
        false

bool smtFired = false
if smtOn and newHtfPeriod and modelEnabled
    smtFired := checkSmt(pH1, pL1, pH0, pL0, smtSymbol())
    if smtUse2
        smtFired := checkSmt(qH1, qL1, qH0, qL0, smtSym2) or smtFired
```

Update the info-table SMT row: `addRow("SMT", smtOn ? (smtFired ? "DIVERGENCE" : "watching") : "OFF")`

- [ ] **Step 2: Compile + verify.** Enable SMT on MNQ 5m (auto pair ES). Find an hour where NQ swept the prior hourly low but ES held: dashed line connecting the two lows + `SMT` label. Cross-check the ES hourly on a second chart.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): SMT divergence (auto/custom pairs, secondary, inverse)"
```

### Task 13: Alerts

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (small inserts at each event site)

- [ ] **Step 1: Insert `alert()` calls** (all gated by the master `alertsOn`):
  - In the Task-4 new-C2 branch: `if alertsOn` → `alert(syminfo.ticker + " TTFM: " + (dir == 1 ? "Bullish" : "Bearish") + " C2 closure (" + htfStr + ")" + (idealFlag ? " ★ ideal" : ""), alert.freq_once_per_bar)`
  - In the C3-advance branch: `if alertsOn` → `alert(syminfo.ticker + " TTFM: C3 confirmed (" + htfStr + ")", alert.freq_once_per_bar)`
  - In the CISD-confirmation site (Task 5, where `f.cisdConfirmed := true`): `if alertsOn` → `alert(syminfo.ticker + " TTFM: CISD confirmed " + (f.dir == 1 ? "bullish" : "bearish"), alert.freq_once_per_bar)`
  - In the early-CISD site (Task 5, when `sweptLo or sweptHi` becomes true and was false the bar before): `if alertsOn and earlyCisdAlert` → `alert(syminfo.ticker + " TTFM: EARLY C2 CISD (preview)", alert.freq_once_per_bar)`
  - In the SMT site (Task 12, when `smtFired`): `if alertsOn and smtAlerts` → `alert(syminfo.ticker + " TTFM: SMT divergence", alert.freq_once_per_bar)`

- [ ] **Step 2: Compile.** Create one TradingView alert on the indicator ("Any alert() function call") and confirm it fires on the next formation event (or via bar replay is not possible for alerts — confirm live during a session; acceptable to defer the live check).

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine && git commit -m "feat(ttfm): alert events (C2/C3/CISD/early/SMT) behind master toggle"
```

### Task 14: Final QA + docs

**Files:**
- Modify: `tradingview/ttfm_clone.pine` (fixes only)
- Create: `tradingview/README.md`

- [ ] **Step 1: Full-feature pass on MNQ1! 5m:** every settings group toggled on/off one at a time; screenshot each; no runtime errors; object counts stay bounded with History = 40 (scroll 2 weeks of history).
- [ ] **Step 2: Non-repaint proof:** bar replay across ≥5 formations (incl. one red, one orange, one ideal ★). Nothing may move after it prints, except the flagged early-CISD preview and table countdown.
- [ ] **Step 3: Ground-truth video comparison round 2** (same procedure as Task 7 Step 3) including SMT + projections elements this time. Record the comparison table (video frame vs our screenshot, per element) in `docs/audits/2026-07-XX-ttfm-clone-parity.md`.
- [ ] **Step 4: Write `tradingview/README.md`:** what the indicator is (passive TTFM clone, NOT a signal tool, per cockpit-plan v2), the Quiz/Check learning-template workflow (from the full guide), settings summary, known interpretation deltas vs the real TTFM.
- [ ] **Step 5: Commit + push**

```bash
cd ~/mnq_trading && git add tradingview/ttfm_clone.pine tradingview/README.md docs/audits/2026-07-*ttfm-clone-parity.md && git commit -m "feat(ttfm): final QA, parity audit, README" && git push -u origin ttfm-clone-indicator
```

---

## Self-review checklist (done at plan-writing time)

- **Spec coverage:** settings panel 1:1 (T1), HTF engine + safeguards (T2), panel/extras (T3), state machine + label semantics + failure plotting-cease (T4), CISD + early preview (T5), EQ/T-Spot/ideal ★ (T4/T6), info table + warnings (T7), projections (T8), formation liquidity (T9), time filters (T10), auto-bias (T11), SMT (T12), alerts (T13), QA/non-repaint/video parity + README (T7/T14). Calculated-bars limit → `inCalcWindow` (T1) consumed by `modelEnabled` (T2). Drawing type → `drawLevel` helper (T3) used by CISD/EQ.
- **No placeholders:** every code step contains the actual code; the two formerly-open rules (T-Spot, sweep qualifier) are resolved and quoted in the rule table.
- **Type consistency:** `Formation` fields defined in T4 match uses in T5/T6/T8/T9; `HTFCandle` (T2) matches all consumers; `drawLevel` signature (T3) matches T5/T6 calls.
- **Known simplification flagged:** `setLabel` red-state text in T4 keeps the last stage name — verify against video in T7/T14 and adjust if the real one differs (e.g., strikethrough or ✕).
