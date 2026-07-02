# Mentor Deep-Guides (per-mentor teaching curriculum) — Spec

> Status: design APPROVED via brainstorming (2026-07-02b). Awaiting spec review before writing-plans.
> Sub-project of the mentor-education page. Related: `2026-07-01-mentor-education-framework-design.md`, `reference_mentor_yt_corpus` (memory).
> Ground truth: the per-mentor NotebookLM notebooks (live pull). NOT the on-disk second-hand extractions.

## 1. Intent
Give each mentor (TTrades / Daye / GxT / ICT / Dexter) a deep, self-contained teaching guide so the user can
learn that mentor's whole method WITHOUT watching the videos. This is a DEPTH upgrade beyond the short "Mentor
Lenses" cards already on the education page. "Concise without missing any nuance" resolved to a **deep curriculum**
per the locked decision below. These guides teach the method faithfully; they are DELIBERATELY verdict-free (see §3).

## 2. Locked decisions (AskUserQuestion, 2026-07-02b)
1. **Depth** = Deep curriculum (~4k words/mentor: concepts + nuances + step-by-step setups + worked examples).
2. **Structure** = Per-mentor standalone pages under `education/mentors/`.
3. **Sourcing** = Live NotebookLM pull, authoritative. NOT the on-disk extractions (those are second-hand).
4. **Verdicts** = NONE inside the guides. Pure faithful teaching; the backtest verdict grading stays in the other
   education views. (This deliberately reverses the base page's "verdict layer throughout" rule for these guides.)

## 3. Source-of-truth rule (hard constraint)
Every claim in a guide must trace to a NotebookLM answer from THAT mentor's notebook(s). Nothing fabricated,
nothing imported from general ICT/SMC knowledge. If a notebook cannot answer a section, the guide marks it
"not covered in this mentor's corpus" rather than filling the gap. Citations returned by NotebookLM (`[n]` refs
mapping to source videos) are preserved in the Grounding section. This extends the banked
"corpus-grounded, never fabricated" rule from the base page.

## 4. Per-mentor page — the 8-section spine (identical for all five, so they're comparable)
1. **Core thesis** — how this mentor sees the market, in a paragraph.
2. **The market model** — their foundational lens (TTrades fractal C1/C2/C3 · Daye Quarterly Theory AMDX ·
   GxT Universal Sequence IRL→ERL · ICT algorithmic delivery / PD arrays · Dexter PO3 + SD).
3. **Concept glossary** — every term they use, defined faithfully. This is where "no missing nuance" lives.
4. **Timing / sessions** — when they operate and why.
5. **Signature setups, step-by-step** — each setup as context → trigger → entry → stop → target, with the
   must-not-miss nuances.
6. **Worked example** — a narrated read of the setup forming, from the corpus.
7. **Nuances you must not miss** — the pitfalls (NotebookLM surfaces these naturally, per the Dexter calibration).
8. **Grounding** — which notebook/videos the guide is built from; NotebookLM citations preserved.

## 5. Content generation (the NotebookLM pull)
- For each mentor, a fixed set of ~7 deep "teaching-guide" questions (one per content section 1–7) asked against
  that mentor's notebook with `notebooklm ask -n <nbid> "..." --json` to capture cited answers.
- The returned answers are transcribed into the content file, lightly edited for flow and consistency — faithful
  to the returned text, not rewritten from outside knowledge.
- CLI facts (verified 2026-07-02): `notebooklm` v0.3.4 at `~/bin/notebooklm`; auth confirmed via a real
  `source list` call (the `auth check` command lies — presence only). `ask` has NO `--new` flag (errors); it
  resumes the last conversation by default; `--json` adds source IDs. If auth expires mid-run, re-auth via the
  skill's browser login (`/tmp/nlm_login.py` + `touch /tmp/nlm_save_signal`).
- **Per-mentor notebook IDs:** TTrades `2a6deaec-1a3a-42bf-983a-106433d1c253`, Daye
  `3f9d9752-ba37-4244-b780-0d79800de15c`, GxT `d34cdc19-f682-4bfa-9e3b-44d5bc2e792b`, Dexter
  `84499947-bc7c-44df-bce0-04e36a8db068`.
- **ICT (bounded):** ICT is spread across 6 notebooks / 600+ videos, so a literally-complete ICT guide is
  unbounded. Scope ICT to its TEACHING CORE — PD arrays, liquidity, killzones, OTE, Power-of-3, MSS, and the
  models the other four build on — querying the 2–3 densest ICT notebooks (Charter Models `dd17ad76…`,
  Core 2016-17 `b2c21c14…`, Extended `cc301409…`). Same 8-section depth, bounded concept set. This bounding is
  deliberate and stated on the page (ICT guide = "the teaching core the other mentors build on", not every lecture).

## 6. Tech / architecture
- New dir `education/mentors/` with `ttrades.html`, `daye.html`, `gxt.html`, `ict.html`, `dexter.html`.
- Shared `education/mentors/guide.css` (reuses the base page's color tokens so it feels native) and
  `education/mentors/guide.js` (tiny renderer: sticky table-of-contents from the section list, section anchors,
  prev/next-mentor nav, "← Back to Framework").
- Per-mentor content in `education/mentors/data/<id>.js` as `window.GUIDE = { id, name, sections:[{title, html}...],
  grounding:[...] }` — the same embed pattern as `window.EDU` (works `file://` and served, no `fetch()` CORS issue).
- The existing Mentor Lenses view (`app.js` `showMentor`) gets a "📖 Full guide →" link per mentor to
  `mentors/<id>.html`. Each guide page has a "← Back to Framework" link to `../index.html`.
- Cache-bust: bump `?v=N` on the base page's asset links after any shared JS/CSS edit (banked rule).
- Vanilla JS, zero backend. No change to `build_dashboard.py` beyond what already links the education page.

## 7. Build order
- **Phase 0** — scaffolding: `guide.css`, `guide.js`, a template page, the Lenses "📖 Full guide →" links,
  cache-bust bump. Verify headless.
- **Phase 1** — generate + build **Dexter** end-to-end (smallest corpus, already calibrated). USER reviews the
  look/feel before mass production.
- **Phase 2** — the other four (TTrades, Daye, GxT, ICT) on the locked template.

## 8. Out of scope
- No verdict/backtest layer inside the guides (§2.4).
- No live "ask deeper" widget on the page (content is pre-generated static prose).
- No mastery %, spaced repetition, or practice simulator (still deferred, as in the base page).
- No change to the trading engine, cockpit, or verdict data.

## 9. Verification
- Every claim traces to a NotebookLM answer from that mentor's notebook; unsourced assertions are a bug.
- Sections a notebook can't answer are marked "not covered in this mentor's corpus", never fabricated.
- All five pages render headless with no console errors; TOC, anchors, prev/next nav, and back-link work.
- ICT guide is explicitly labelled as the bounded teaching core, not a complete ICT archive.
