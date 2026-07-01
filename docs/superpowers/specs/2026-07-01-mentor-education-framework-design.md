# Mentor-Education "The Framework" page — Spec

> Status: APPROVED via clickable mockup (2026-07-01). Building v1.
> Supersedes the heavier `2026-06-20-mentor-education-mindmap.md` (mastery/spaced-rep/simulator deferred).
> Ground truth: `docs/mentor_setup_catalog.md`, `mentor_mindmap/data.json`, verdict tiers in memory `gotchas.md`/`session_state.md`, TTrades qmd corpus.

## 1. Intent
A self-contained education page that teaches how the whole 5-mentor corpus (ICT / Daye / GxT / TTrades / Dexter)
converges into ONE way to frame a setup with no guessing. User is buying a funded account and will trade only
valid high-probability setups; this page is to (a) understand the unified framework, (b) see how each mentor
reads the market / which sessions / what setups, (c) learn every concept with no gaps, (d) self-check understanding.
EDUCATION tool (learn the method), distinct from the trading cockpit (read the live market) — shares only the
verdict-grading honesty layer.

## 2. Locked decisions
- Scope = Learn + framework + self-check. DEFER two-track mastery %, SM-2 spaced repetition, chart-replay simulator.
- Structure = unified-framework-FIRST; mentors + sessions are lenses on top.
- Location = separate `education/` page, ONE link from `project_dashboard.html`.
- Self-check = in-page quiz + reveal + localStorage progress (no live NotebookLM in v1).

## 3. Verdict-honesty layer (runs through everything)
Every concept / setup / mentor claim carries a badge from OUR backtests:
- 🟢 PROVEN (v8.18 62T core) · 🟡 UNVALIDATED (taught, not proven here) · 🔴 DEAD (net-negative/lookahead/null) · ⚪ MECHANIC (refinement).

## 4. The six views
1. **The Frame** (landing) — the 7-stage convergence pipeline (HTF bias → session/killzone → liquidity sweep →
   CISD/MSS+displacement → PD-array entry → protected-swing stop → target). Click a stage → meaning + concepts used +
   per-mentor vocabulary + verdict.
2. **Read It Live** (interactive walk-through) — a step-by-step decision wizard: answer HTF bias / session / sweep /
   CISD / PD-array → outputs the framed setup with entry-stop-target guidance AND an explicit verdict, including
   "no trade / skip" when the inputs don't line up (e.g. London, or missing displacement). Grounded in the LOCKED
   rules (--no-london, V-shape-is-the-edge, CE-entry harmful, etc.).
3. **Concept Library** — Layer-0 PD arrays (11) + Layer-1 mechanics (14); each = definition · how-to-spot · bull/bear ·
   place-in-frame · mentor vocabulary · verdict. Completeness = "nothing missed".
4. **Mentor Lenses** — per mentor: owned layer, philosophy, sessions, signature setups, vocabulary→frame mapping.
5. **Session Playbook** — interactive/filterable render of `mentor_setup_catalog.md`, verdict-colored.
6. **Self-Check** — quizzes: concept recall + mentor/session + framing SCENARIO; reveal + localStorage coverage/gap readout.

## 5. Tech / architecture
- `education/index.html` + `styles.css` + `app.js` + `data.js` (content as `window.EDU`, embedded so it works both
  double-clicked `file://` and served — avoids the `fetch()` CORS block on `file://`). Vanilla JS, zero backend.
- Progress in `localStorage` (`edu_progress_v1`).
- `build_dashboard.py` gets one link to `education/index.html` so it's reachable from the dashboard.
- Content curated from existing artifacts (no live NotebookLM in v1).

## 6. Out of scope (v1)
Mastery %, SM-2 spaced repetition, chart-replay practice simulator, live NotebookLM "ask deeper". Schema leaves room.

## 7. Verification
- Every claim traces to an existing artifact / recorded verdict (no unsourced assertions).
- Verdicts sourced from recorded backtests, not re-derived.
- Walk-through outputs must match the LOCKED engine rules (memory `gotchas.md`).
