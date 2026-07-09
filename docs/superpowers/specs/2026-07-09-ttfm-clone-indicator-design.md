# TTFM Clone Indicator — Design Spec

**Date:** 2026-07-09
**Status:** Approved by user (brainstorming session 2026-07-09)
**Branch:** `ttfm-clone-indicator`
**Deliverable:** `tradingview/ttfm_clone.pine` (Pine v6, single indicator)

## 1. Purpose & Non-Goals

Build **"Fractal Model (TTFM Clone)"** — a single Pine v6 indicator replicating **Fractal Model [Pro+] (TTrades)** (built by Toodegrees, invite-only) feature-for-feature, as a **passive charting / learning tool**.

**Non-goals (hard constraints):**
- NO `strategy()`, NO webhooks, NO signal authority. The validated Python engine remains the ONLY live trigger (mentor-cockpit-plan v2).
- NOT an edge. The faithful fractal model backtested dead standalone (IS PF ~1.14, 2 down years). This is for charting, study, and the TTrades "Quiz/Check" learning workflow.
- NO use of the protected/pirated TTFM Pine source. Grounding = public docs + our corpus only.

**Why buildable without their source:** the ttrades.com full guide + TradingView script description + Toodegrees product page = a complete FEATURE spec; the 98-article TTrades corpus + our Python mechanization (`backtest/ssmt_psp_engine.py` Spine B c2c3-closure) = the DETECTION rules.

## 2. Grounding Sources (every rule must cite one)

| Source | What it provides |
|---|---|
| `Trading/TTrades_Articles/ttrades-fractal-model-indicator-full-guide.md` | Complete settings-panel / feature spec |
| TV script page `XdwK9qQQ-Fractal-Model-Pro-TTrades` | Label state machine (gray/orange/red), failure semantics, default projections [-1,-2,-2.5,-4,-4.5], non-repainting guarantee, TF-mismatch warning |
| toodegrees.trade/indicators/fractal-model | Feature confirmation, framework components |
| `ttrades-ideal-formation-high-probability-swing-points.md` (NEW, ripped 2026-07-09) | Ideal Formation = C2/C3 closure that ALSO closes through the opposing candle series → protected swing; key levels = opposing-series open + confirmation-candle EQ |
| `understanding-candle-2-closures-within-the-fractal-model.md`, `how-to-trade-candle-2-ttrades-fractal-model.md` | C2 closure definition |
| `candle-3-closure-a-complete-guide...md`, `how-to-trade-candle-3-in-the-fractal-model.md` | C3 closure / expansion |
| `ttrades-fractal-model-candle-4.md` | C4 continuation |
| `understanding-the-change-in-state-of-delivery-cisd.md`, `how-change-in-the-state-of-delivery-confirms-swing-points.md` | CISD = close through the opening price of the opposing candle series |
| `protected-swings-understanding-trends-and-invalidations.md`, `stop-loss-mastery-using-protected-swings...md` | Protected swing definition |
| `understanding-t-spot-pdf.md` (+ NotebookLM TTrades nb `2a6deaec-…` if the stub is too thin) | T-Spot geometry |
| `standard-deviation-projections.md` (+ `...combined-with-amd...md`) | STDV projection anchoring (manipulation leg, wick vs body) |
| `timeframe-alignment-how-to-align-higher-and-lower-time-frames-for-precision-entries.md` | Canonical pairing ladder |
| `using-equilibrium-in-continuations.md` | EQ (50% of prior HTF candle) usage |
| Qvintrix clone description (TV `vHXyBEfF`) | Leaked nuance: C3 confirm = strict body break OR 50% threshold (we expose both as a setting) |
| fadi's open-source "ICT HTF Candles" (TradingView, open license) | Structural reference for local HTF aggregation + right-offset candle rendering. Reference only — we write our own code. |

Rule: anything the corpus cannot pin down exactly is resolved from the NotebookLM TTrades corpus / published videos BEFORE coding, or explicitly marked `// INTERPRETATION:` in source.

## 3. Architecture (Approach A — approved)

Single Pine v6 file, internally sectioned:

1. **Settings** — groups mirroring the real TTFM panel 1:1 (§6).
2. **HTF engine** — HTF candles aggregated LOCALLY from chart-TF bars (running OHLC accumulation; no `request.security` for model logic). Fully causal by construction; provides the intra-HTF LTF candle series that CISD needs.
   - Canonical auto-pairing ladder: 3m→30m, 5m→1H, 15m→4H, 1H→Daily, 4H→Weekly, Daily→Monthly. Presets + fully custom pairing.
   - TF-mismatch safeguard: chart TF > model LTF ⇒ CISD/projections disabled + warning row in info table (HTF candles stay visible) — same behavior as the real one.
3. **Detection library** — pure functions: sweep, C2/C3/C4 closure, opposing-series identification, CISD level + confirmation, protected-swing test, EQ, T-Spot, STDV anchors, formation liquidity.
4. **Formation state machine** — per direction (bull/bear), `Formation` UDT instances.
5. **Rendering layer** — all drawings, labels, table; history cap 0–40; drawing-budget recycling (TV object caps).
6. **Alert layer** (Phase 2) — `alert()` events for formation/early-CISD/SMT.

### SMT exception
The SMT module (Phase 2) is the ONE place `request.security` is required (other symbols). It requests CONFIRMED HTF values only (`lookahead=barmerge.lookahead_off`, mirrored series), never intra-bar.

## 4. Formation State Machine

States per formation: `WATCHING → SWEPT → C2_CLOSED → CONFIRMED(C3/C4 tracking) → {VALID(gray), CONSOLIDATION(orange), FAILED(red)}`

- **C1** = previous HTF candle; its high/low = liquidity (sweep line drawn on the extreme).
- **Sweep**: price trades beyond the C1 extreme (bull: below C1 low).
- **C2 closure**: the HTF candle that swept closes back beyond C1's body against the sweep direction. Toggleable display per C2/C3/C4.
- **LTF CISD**: opening price of the opposing LTF candle series that formed the HTF wick; line drawn PENDING (dashed), converts to SOLID when an LTF candle CLOSES through it. "Early C2 CISD" setting shows it before HTF close, labeled preview.
- **C3**: expansion candle; C3 closure setting: strict body break (default) or 50% threshold.
- **C4**: continuation display.
- **Ideal Formation flag**: C2/C3 closure that ALSO closes through the entire opposing series (= protected swing created). Marked distinctly (label suffix `★`).
- **Label states (exact TTFM semantics):**
  - **gray** — model valid / forming, stable conditions
  - **orange** — didn't fail within the NEXT HTF candle → consolidation/range warning
  - **red** — FAILED: price returned to the initial sweep extreme without forming the HTF swing → projections, EQ, sweep line, T-Spot for that formation CEASE plotting
- **Non-repaint law**: every state transition happens on `barstate.isconfirmed` only. Only deliberate previews: Early C2 CISD + info-table countdown (both flagged, mirroring the real tool).

## 5. Drawings & Levels

- HTF candles right of price: count (default 4, up to 40), size, offset (default stackable at 17), body/border/wick colors, time labels (24h/AMPM, custom tz).
- HTF open line, vertical HTF period lines, previous HTF L/H lines (default off), **previous-candle EQ** (50% wick-to-wick).
- Drawing type: On Chart / HTF candle / Both (per the guide).
- C1 sweep line; bullish/bearish CISD lines (independent styling); candle EQ line; **T-Spot** zones (anticipated wick area; exact geometry grounded per §2); C2/C3/C4 labels w/ size setting.
- **STDV projections**: anchor = manipulation leg, Wick or Body calculation; default levels −1, −2, −2.5, −4, −4.5; custom levels (negative numbers); labels toggle.
- **Formation liquidity**: prior HTF highs/lows aligned with a valid model, drawn as target rays.
- History: 0–40 previous formations (each = 1 bullish + 1 bearish); object recycling beyond TV caps (`max_lines_count=500`, `max_boxes_count=500`, `max_labels_count=500`).

## 6. Settings Panel (mirrors the real TTFM guide 1:1)

Groups: Warnings/Errors toggle · General (Alerts enable, History, Fractal preset/Automatic/Custom, C2/C3/C4 toggles, Custom Fractal, Bias: Neutral/Bullish/Bearish/Auto Bias 1/Auto Bias 2) · HTF Candles (count/size/offset/colors, HTF Open, Vertical Lines, L/H Lines, Previous EQ, Drawing Type) · HTF Candle Time Labels · Model Style (TTFM labels, C1 sweep, CISD both directions, Candle EQ, T-Spot, Early C2 CISD + its alert) · SMT Divergence (enable, alerts, labels, mode Auto/Custom, secondary pair, inverse) · Standard Deviation Projections (enable, labels, type Wick/Body, custom levels) · Formation Liquidity · Time Filter (enable, Apply Below TF, Filter 1/2/3 windows) · Info Table (show, size, location, selections: asset/TF/pairing/countdown/bias/filter/SMT) · Calculation (Calculated Bars limit).

**Auto Bias 1/2**: gate LTF formations by the direction of the model one/two rungs up the pairing ladder (e.g., on 1H↔5m: AB1 = 4H↔15m model direction, AB2 = Daily↔1H).

**SMT defaults**: Automatic mode = NQ↔ES for index futures (chart symbol root detected); Custom mode = user symbols, secondary pair, inverse-correlation flag.

## 7. Build Phases

- **Phase 1 (core model):** HTF engine + pairing ladder + state machine + sweep/C2/C3/C4 + CISD + EQ + labels + history + basic info table + TF-mismatch warning. Verify on MNQ 5m↔1H.
- **Phase 2 (modules):** T-Spot, STDV projections, formation liquidity, SMT, time filters, Auto Bias 1/2, Early C2 CISD, alerts, full info table, warnings, calculated-bars limit, polish.

Each phase: compile → on-chart verify → ground-truth comparison before the next.

## 8. Verification (ground truth = videos + docs, approved)

1. **Compile loop:** `tv` CLI into a NEW script slot. GOTCHAS enforced: `tv pine get` backup before ANY edit; `tv pine compile` AUTO-SAVES + bumps version; never open/compile against JUDGE or S-series scripts; verify with `tv state` after compile (title-match can update the wrong study).
2. **Ground-truth comparison:** frame-extract published videos that show the real TTFM live (full-guide video May 9 2026, "How To Use SMT Divergence – TTrades Fractal Model", Toodegrees/TTrades breakdown `youtube.com/watch?v=-n31VuAijzo`) via the local video pipeline; reproduce same symbol/date/TF on our chart; compare drawings element-by-element (sweep line, CISD level, labels, EQ, projections).
3. **Non-repaint proof:** TradingView bar-replay across formations; drawings must be identical replayed vs. historical. (Pine analog of `lookahead_guard`: future bars must not move past drawings.)
4. **Reading values for checks:** Pine tables render to CANVAS — use the canvas-tag + `#id` screenshot recipe (gotchas) or `tv screenshot --region chart`.

## 9. Risks / Open Items

- **T-Spot exact geometry** — corpus stub is thin (3KB PDF page). Resolve from NotebookLM TTrades notebook / videos before coding; else mark `// INTERPRETATION:`.
- **Sweep qualifier ambiguity** (does C2 sweep require LTF close-back or HTF wick only) — resolve from the C2 articles; expose as setting if genuinely ambiguous.
- **Parity ceiling**: without their source, edge-case behavior may differ; video comparison bounds this but can't eliminate it.
- **Pine object caps** with History=40 × 2 directions × ~10 drawings each — recycling design required from day 1.
- Repo hygiene: commit NAMED files only (`tradingview/ttfm_clone.pine`, this spec, plan); never `git add -A`.
