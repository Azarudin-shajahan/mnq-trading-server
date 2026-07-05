# Mentor Model Playbook — Design Spec

> Date: 2026-07-05 · Branch: `mentor-education-framework` · Status: design (pre-plan)
> Supersedes nothing; extends the education dashboard (`~/mnq_trading/education/`).

## 1. Goal

Provide one canonical, filterable enlistment of **all 33 mentor models** derivable from the
NotebookLM corpus, each rendered with a **complete tradable field-set**, verdict-honest, grouped
by mentor — as a new 9th view ("Model Playbook") in the education dashboard. For education/study:
a learner can scan every model any mentor teaches and see exactly how to trade it, alongside our
honest backtest verdict.

The 33 models (from each guide's section-5 "signature setups"):
TTrades 4 · Daye 4 · GxT 4 · ICT 4 · Dexter 6 · XYJ 6 · Daye Mentorship 5 = **33**.

## 2. Locked scope decisions (AskUserQuestion, 2026-07-05)

1. **Format** = a new "Model Playbook" view in the education dashboard (9th nav item), searchable +
   filterable, auto-rolled into the offline mobile bundle + PWA.
2. **Fields** = full trading spec (11 fields, §4).
3. **Source** = reuse the already-audited guide section-5 data + `docs/mentor_setup_catalog.md`
   (faithful post-audit 2026-07-05; NO new NotebookLM calls, NO re-audit).
4. **Grouping** = by mentor (7 groups), with Session + Verdict filter chips.

## 3. Current state (why this is needed)

- `education/data.js` `mentors[]` already lists each mentor's setups as **chips** (name + verdict
  tag `a`/`s`/`r`) — labels only, no tradable detail.
- The full detail (Trigger / Entry / Stop / Target / Nuance) lives in each guide's section-5 as
  **prose HTML** (`education/mentors/data/<id>.js`, `window.GUIDE.sections[id="setups"]`), which
  cannot be filtered or sorted.
- There is **card-drift** between the two: e.g. the ICT `data.js` card lists Venom / MMXM /
  SMC-Opening-Range-Gap, while the audited ICT guide §5 details Judas-Swing/Turtle-Soup + MSS-2022.
- So no single surface enlists all 33 models with complete, consistent, filterable tradable fields.
  This spec builds that surface and reconciles the drift.

## 4. Data model — `education/models.js`

New file `education/models.js` exposing `window.MODELS = [ ... ]` (same load pattern as `window.EDU`
in `data.js` and `window.GUIDE` in the guide files). One object per model:

```js
{
  id:        "ttrades-unicorn",        // <mentorkey>-<slug>, stable anchor
  mentor:    "TTrades",                // display name
  mentorKey: "ttrades",                // ttrades|daye|gxt|ict|dexter|xyj|dayement
  name:      "Unicorn (Breaker + FVG)",
  session:   "London 02:00 / NY AM 09:30 ET",  // human-readable time-of-day (ET)
  sessionKey:"ny-am",                  // asia|london|ny-am|lunch|ny-pm|news|htf-open|dow (for filter)
  htf:       "1H POI in the draw direction",   // HTF context / bias precondition
  trigger:   "5m stop-hunt displaces through the breaker, leaving an FVG",
  entry:     "Limit at the 5m breaker-block start",
  stop:      "Opposite side of the breaker",
  target:    "2R / HTF ERL",
  tfs:       "1H POI -> 5m execution",  // timeframe nest
  tools:     ["breaker block","FVG","liquidity sweep"],  // PD-arrays / concepts used
  verdict:   "a",                       // s|a|r|w — REUSE window.EDU.verdicts codes (OUR evidence)
  example:   "NQ sweeps the Asia low, breaks the 1H breaker, retraces into the 5m FVG ...",
  guideId:   "ttrades"                  // links back to the full mentor guide (mentors/ttrades.html)
}
```

**11 rendered fields**: Mentor · Name · Session/time · HTF context · Trigger · Entry · Stop ·
Target · Timeframes · Tools · Verdict (+ one-line example, + guide link).

**Authoring**: hand-curated (33 records) from each guide's section-5 + the setup catalog. NOT
runtime HTML-parsing of the guides (prose is inconsistent; curation lets us reconcile drift and fill
fields the guides state loosely, e.g. HTF/tfs/tools). Any field a source does not cover is set to the
literal string `"not covered in corpus"` — never fabricated (enforced project rule).

`verdict` — REUSE the existing `window.EDU.verdicts` code system (so the model cards render with the
same `chip()` helper and CSS as the rest of the dashboard):
`{ g:"FORWARD-VALIDATED", s:"IN-SAMPLE", a:"UNVALIDATED", r:"DEAD (our engine)", w:"MECHANIC" }`.

Mapping (grounded in OUR backtests, NOT mentor claims):
- `g` (FORWARD-VALIDATED) — **deliberately EMPTY**. Nothing is forward/OOS-validated. Do NOT tag any
  model `g`.
- `s` (IN-SAMPLE) — our in-sample production edge. Exactly **2** models: the NY-AM V-shape
  sweep-reversal (OTE) and the NY-PM continuation (= v8.18 62T core). Any mentor's rendering of the
  NY-AM V-shape maps to `s`.
- `a` (UNVALIDATED) — taught & plausible, never independently validated here (or only marginal). The
  majority of the 33.
- `r` (DEAD) — our backtests found it net-negative / lookahead-artifact / null-failing (e.g. driver
  pairing, single-TF strength-switch/Lathyrus, Son's/30-sec model, London-leg setups).

## 5. The view

New `<section class="view" id="models">` and a nav button **"Model Playbook"** inserted between
"Session Playbook" and "Self-Check" in `index.html`.

`renderModels()` in `app.js` (matching the existing per-view render functions):
- **Default layout**: grouped by mentor — 7 collapsible groups, each header shows the mentor name +
  model count (e.g. "Dexter (6)").
- **Filter chips**: Mentor · Session · Verdict, plus a text search box (matches name / trigger /
  tools). Filters compose (AND). "All" resets each dimension.
- **Model card**: renders all 11 fields as labelled rows; verdict as a colored badge
  (green/yellow/red dot + label); a "Full guide ->" link to the mentor's guide page
  (`mentors/<guideId>.html`).
- Reuses existing CSS variables / card styling from `styles.css`; adds only what's needed for the
  filter bar + verdict badges (append, do not restructure existing CSS).

## 6. Honesty layer (non-negotiable)

Every model card shows its verdict chip (via the existing `chip()` helper). A persistent banner at
the top of the view:

> "Verdicts grade OUR backtest EVIDENCE, not the mentors' claims. FORWARD-VALIDATED is deliberately
> empty — nothing here is proven live/OOS. IN-SAMPLE (only 2 models) = our in-sample edge (the v8.18
> 62T, never size up on it); UNVALIDATED = taught but not gated here; DEAD = net-negative in our
> engine. This is a learning catalog, not a signal source."

Consistent with the tiering used across the rest of the dashboard (`data.js` verdict tags, the
Concept Library, Session Playbook).

## 7. Integration & mobile

- `index.html`: add the nav button + `<section id="models">`; bump the base asset `?v=` cache-bust
  and add `<script src="models.js?v=N">`.
- `app.js`: register the `models` view in the view-switch wiring; add `renderModels()`.
- `data.js`: reconcile the `mentors[].setups` chips so they match the 33 audited guide models
  (fixes the ICT/others card-drift). No other `data.js` changes.
- `diagnostics/build_bundle.js`: add `models.js` to the inlined ids/assets and include the Model
  Playbook markup so the offline single-file `education/mentor-guides.html` carries the view; then
  regenerate the bundle.
- `sw.js`: add `models.js` to the cached assets; bump the SW cache version.
- No backend. Vanilla JS. Works `file://` or served. Consistent with the existing app.

## 8. Verification

Headless-browser check (project standard):
1. 9 nav buttons render; "Model Playbook" switches to `#models`.
2. 33 model cards render across 7 mentor groups with correct counts (4/4/4/4/6/6/5).
3. Each filter (Mentor / Session / Verdict) narrows the set correctly; search narrows by
   name/trigger/tools; filters compose.
4. Exactly 2 cards carry the `s` (IN-SAMPLE) verdict chip (NY-AM V-shape OTE, NY-PM continuation);
   0 cards carry `g` (FORWARD-VALIDATED stays empty).
5. Each "Full guide ->" link points to an existing `mentors/<id>.html`.
6. `build_bundle.js` regenerates; the offline `mentor-guides.html` opens and shows the Model
   Playbook view.
7. `models.js` is syntactically valid (`node -c` / load check).

## 9. Scope guardrails (YAGNI)

- No editing/authoring UI, no per-model deep pages (the mentor guides already serve that; each card
  links out to its guide).
- No new NotebookLM calls, no re-audit — content is already audited (2026-07-05).
- No CSS/JS restructuring beyond what the new view needs; append, don't refactor unrelated code.
- Named-file commits only, on `mentor-education-framework`. Never `git add -A`.

## 10. Files touched

New:
- `education/models.js`
- `docs/superpowers/specs/2026-07-05-mentor-model-playbook-design.md` (this doc)

Modified:
- `education/index.html` (nav + section + script + ?v bump)
- `education/app.js` (view wiring + `renderModels()`)
- `education/data.js` (reconcile `mentors[].setups` chips to the 33 audited models)
- `education/sw.js` (cache models.js + version bump)
- `diagnostics/build_bundle.js` (inline models.js + view) -> regenerates `education/mentor-guides.html`

## 11. Non-goals / open follow-ups

- The 🟢/🟡/🔴 counts are a RESEARCH catalog; only the 2 green models are tradable-with-our-proof.
  This surface does not change the real lever (first 1-lot live-demo fill of Book C).
- PWA install-to-home-screen deploy stays user-gated (Netlify Drop of `education/`, https).
