# Mentor Model Playbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 9th "Model Playbook" view to the education dashboard that enlists all 33 mentor models with a complete tradable field-set, grouped by mentor, filterable by mentor/session/verdict, verdict-honest — sourced from the already-audited guide section-5 data + the setup catalog.

**Architecture:** A new structured data file `education/models.js` (`window.MODELS`, 33 records) is the single source; a new `renderModels()` in `app.js` renders it into a new `<section id="models">` with filter chips reusing the existing `chip()`/verdict system; the offline mobile bundle and PWA cache are updated to carry it. No backend, vanilla JS, matches the existing `window.EDU` pattern.

**Tech Stack:** Vanilla JS (no framework/deps), static HTML sections, `styles.css`, `diagnostics/build_bundle.js` (Node) for the offline single-file bundle, `sw.js` service worker. Verification via `node --check` + the gstack headless `browse` binary.

**Spec:** `docs/superpowers/specs/2026-07-05-mentor-model-playbook-design.md`

**Branch:** `mentor-education-framework` (already checked out). Named-file commits only; never `git add -A`.

---

## Reference: shared conventions (read once before Task 1)

`app.js` is an IIFE exposing helpers you must reuse:
- `const E = window.EDU;` and `const V = E.verdicts;`
- `const chip = v => '<span class="chip '+v+'">'+V[v]+'</span>';` — renders a verdict chip. **Reuse this.**
- `const $ = s => document.querySelector(s);`
- `const esc = s => String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');`
- `const mcls = name => ...` — returns a mentor color class (`m-tt`, `m-daye`, `m-gxt`, `m-ict`, `m-dx`, `m-all`).
- Views are static `<section class="view" id="X">`; content is rendered once on load via `.innerHTML`.
- `switchView(v)` toggles nav + view `.on` classes; nav buttons use `data-v="<id>"`.

Verdict codes (`window.EDU.verdicts`): `{ g:"FORWARD-VALIDATED", s:"IN-SAMPLE", a:"UNVALIDATED", r:"DEAD (our engine)", w:"MECHANIC" }`. **`g` stays empty — never assign it.**

### The 33-model classification table (authoritative — name · mentorKey · sessionKey · verdict)

Author `models.js` records from this table. `sessionKey` ∈ `{asia,london,ny-am,lunch,ny-pm,news,htf-open,dow}`.

| id | mentor | name | sessionKey | verdict |
|---|---|---|---|---|
| ttrades-c2-reversal | TTrades | Fractal Model C2 Reversal (TTFM) | ny-am | a |
| ttrades-ic-cisd | TTrades | IC-CISD (Intracandle CISD) | htf-open | a |
| ttrades-unicorn | TTrades | Unicorn (Breaker + FVG) | ny-am | a |
| ttrades-ttfm-continuation | TTrades | TTFM Continuation (Candle 3/4) | london | a |
| daye-q1-asian-sr | Daye | Q1 Asian Dynamic S/R | asia | a |
| daye-q2-london-stophunt | Daye | Daily Q2 London Stop Hunt | london | a |
| daye-q3-sweet-spot | Daye | Q3-of-Q3 "Sweet Spot" | ny-am | a |
| daye-q4-afternoon-reversal | Daye | Q4 Afternoon Reversal | ny-pm | a |
| gxt-6am-reversal | GxT | 6:00 AM NY Reversal → 10:00 AM Continuation | ny-am | a |
| gxt-ny-am-vshape | GxT | NY AM V-Shape Reversal | ny-am | s |
| gxt-driver-pairing | GxT | Driver Pairing | news | r |
| gxt-lagging-asset-smt | GxT | Lagging-Asset SMT (Asset Synchronization) | ny-am | r |
| ict-ny-am-ote | ICT | NY AM V-Shape / Optimal Trade Entry (OTE) | ny-am | s |
| ict-silver-bullet | ICT | Silver Bullet | ny-am | a |
| ict-judas-turtle-soup | ICT | Judas Swing / Turtle Soup | ny-am | a |
| ict-mss-fvg-2022 | ICT | MSS + FVG Entry (the 2022 model) | ny-am | a |
| dexter-4h-po3 | Dexter | 4H Power-of-Three Expansion | htf-open | a |
| dexter-mmxm | Dexter | Market Maker Buy/Sell Model (MMXM) | htf-open | a |
| dexter-tuesday-reversal | Dexter | Tuesday Reversal Profile | dow | a |
| dexter-news-nfp-jolts | Dexter | High-Impact News (NFP & JOLTS) | news | a |
| dexter-silver-bullet-zone | Dexter | Silver Bullet Zone Continuation | ny-am | a |
| dexter-devils-mark | Dexter | Devil's Mark Reversal | htf-open | a |
| xyj-lathyrus-80 | XYJ | The Lathyrus 80% Model (ERL↔IRL) | ny-am | r |
| xyj-2stage-cic | XYJ | The 2-Stage CiC True Reversal (Candle 2) | ny-am | r |
| xyj-mmxm-continuation | XYJ | MMXM Continuation (Type 1 / IRL→ERL) | ny-am | a |
| xyj-strength-switch | XYJ | Strength-Switch / Lagging-Asset ("Ideal Sequence") | ny-am | r |
| xyj-seek-destroy | XYJ | Seek & Destroy Session | london | a |
| xyj-continuation-framework | XYJ | Continuation Framework (qualifying gaps) | ny-am | a |
| dayement-one-shot | Daye Mentorship | Two-Stage Sequential SMT (One Shot One Kill) | ny-am | r |
| dayement-stage4 | Daye Mentorship | The Stage-4 (Advanced 4-Stage) Setup | ny-am | r |
| dayement-monday-expansion | Daye Mentorship | Monday Expansion Model | dow | a |
| dayement-cpi | Daye Mentorship | CPI Trading Model | news | a |
| dayement-q4-reversal | Daye Mentorship | Q4 Afternoon Reversal | ny-pm | a |

Counts: TTrades 4 · Daye 4 · GxT 4 · ICT 4 · Dexter 6 · XYJ 6 · Daye Mentorship 5 = **33**. Verdict `s` = exactly 2 (`gxt-ny-am-vshape`, `ict-ny-am-ote`); `g` = 0; `r` = 7; `a` = 24.

`mentorKey` ↔ guide file: ttrades→`ttrades`, daye→`daye`, gxt→`gxt`, ict→`ict`, dexter→`dexter`, xyj→`xyj`, "Daye Mentorship"→`dayement`. Each record's `guideId` = that key; the "Full guide →" link targets `mentors/<guideId>.html`.

### Content sourcing rule (no fabrication)

For each model, fill `htf/trigger/entry/stop/target/tfs/tools/example` by faithfully transcribing from:
1. **Primary:** the mentor's guide section-5, i.e. `education/mentors/data/<guideId>.js`, the `sections` entry with `id:"setups"` — the `<li><b>Trigger:</b>…</li>` etc. for that model.
2. **Secondary (session/target cross-check):** the matching row in `docs/mentor_setup_catalog.md`.

If a field is not stated in either source, set it to the literal string `"not covered in corpus"`. **Never invent** trigger/entry/stop/target values. Keep prose concise (one clause each); strip HTML tags.

---

## Task 1: Create `education/models.js` with all 33 records

**Files:**
- Create: `education/models.js`

- [ ] **Step 1: Write the file skeleton + two fully-worked reference records**

Create `education/models.js`. Use this exact schema. Two records are shown fully worked as the pattern (one `s`, one `r`); author the remaining 31 the same way from the sources named in "Content sourcing rule".

```js
/* Mentor Model Playbook — structured enlistment of all 33 mentor models.
   window.MODELS feeds the "Model Playbook" view (app.js renderModels).
   Sourced from education/mentors/data/<id>.js section-5 + docs/mentor_setup_catalog.md.
   verdict codes reuse window.EDU.verdicts (g/s/a/r/w); g stays empty. NO fabrication —
   fields not in the corpus = "not covered in corpus". */
window.MODELS = [
  { id:"ict-ny-am-ote", mentor:"ICT", mentorKey:"ict", guideId:"ict",
    name:"NY AM V-Shape / Optimal Trade Entry (OTE)",
    session:"NY AM killzone 09:30–11:00 ET", sessionKey:"ny-am",
    htf:"Daily/4H bias set; price into a HTF PD array in the draw direction",
    trigger:"Early-session liquidity raid → MSS/displacement breaks structure",
    entry:"62–79% OTE retrace (70.5% sweet spot) into the 1st-presented FVG/OB",
    stop:"Beyond the swing extreme (0% of the OTE leg)",
    target:"First opposing swing / −0.5/−1/−1.5 SD projection",
    tfs:"Daily/4H bias → 5m/1m execution",
    tools:["liquidity sweep","MSS","displacement","FVG","OTE (Fibonacci)"],
    verdict:"s",
    example:"NQ sweeps the Asia low at 09:35, displaces up through structure, retraces to the 70.5% OTE + FVG, runs to the first opposing swing." },

  { id:"gxt-driver-pairing", mentor:"GxT", mentorKey:"gxt", guideId:"gxt",
    name:"Driver Pairing",
    session:"08:30 / 09:30 ET news drivers", sessionKey:"news",
    htf:"Approaching a high-volatility driver into a HTF swing/draw",
    trigger:"News spike runs into a HTF swing and fails → 2-stage SMT decouples the pair",
    entry:"1–5m V-shape CISD after the spike",
    stop:"Below the driver spike low",
    target:"Failure swings / PDH-PDL / 2R",
    tfs:"1H context → 1–5m execution",
    tools:["SMT divergence","CISD","news driver","liquidity sweep"],
    verdict:"r",
    example:"8:30 print spikes NQ into the PDH, NQ fails while ES makes a higher high (SMT), 1m CISD confirms the short." },

  // … author the remaining 31 records here, same schema, from the sources.
];
```

- [ ] **Step 2: Author the remaining 31 records**

Work mentor-by-mentor through the classification table. For each row, open `education/mentors/data/<guideId>.js`, locate the `id:"setups"` section, find that model's `<li>` block, and map Trigger/Entry/Stop/Target (+ any Context→`htf`, Nuance→fold into `example` or omit). Cross-check `session`/`target` against the matching `docs/mentor_setup_catalog.md` row. Derive `tfs` and `tools` from the same text; if absent, `"not covered in corpus"`. Preserve the classification table's `id`, `name`, `sessionKey`, `verdict` verbatim.

- [ ] **Step 3: Verify syntax**

Run: `node --check ~/mnq_trading/education/models.js`
Expected: no output, exit 0.

- [ ] **Step 4: Verify record count + verdict tallies**

Run:
```bash
cd ~/mnq_trading/education && node -e "require('./models.js'); const M=global.window? global.window.MODELS:null;" 2>/dev/null; \
node -e "global.window={}; require('./models.js'); const M=window.MODELS; \
const by=k=>M.reduce((o,m)=>((o[m[k]]=(o[m[k]]||0)+1),o),{}); \
console.log('total',M.length); console.log('mentor',by('mentorKey')); console.log('verdict',by('verdict'));"
```
Expected: `total 33`; mentor counts `ttrades:4,daye:4,gxt:4,ict:4,dexter:6,xyj:6,dayement:5`; verdict `s:2, r:7, a:24` and **no `g`**.

- [ ] **Step 5: Verify no accidental fabrication placeholders leaked**

Run: `grep -c "not covered in corpus" ~/mnq_trading/education/models.js`
Expected: a small number (0–N). Manually confirm each such field genuinely has no source value — do NOT leave a real field blank.

- [ ] **Step 6: Commit**

```bash
cd ~/mnq_trading && git add education/models.js && \
git commit -m "feat(education): models.js — 33 mentor models, structured tradable fields

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 2: Add the view + nav button + script to `index.html`

**Files:**
- Modify: `education/index.html` (nav ~line 19–27; sections ~line 114–126; scripts ~line 139–141; css ~line 10)

- [ ] **Step 1: Add the nav button**

In `<nav id="nav">`, insert between the "Session Playbook" and "Self-Check" buttons:

```html
  <button data-v="models">Model Playbook</button>
```

- [ ] **Step 2: Add the view section**

After the `<section class="view" id="sessions">…</section>` block and before `<section class="view" id="self">`, insert:

```html
  <section class="view" id="models">
    <h2>Model Playbook</h2>
    <p class="lead">Every model the seven mentors teach — 33 in total — with its full tradable spec. Grouped by mentor. Filter by session or by our backtest verdict.</p>
    <div class="banner">Verdicts grade OUR backtest <b>evidence</b>, not the mentors' claims. FORWARD-VALIDATED is deliberately empty — nothing here is proven live/OOS. <b>IN-SAMPLE</b> (only 2 models) = our in-sample edge (the v8.18 62T — never size up on it); <b>UNVALIDATED</b> = taught but not gated here; <b>DEAD</b> = net-negative in our engine. A learning catalog, not a signal source.</p>
    <div id="modelFilters" class="filters"></div>
    <input id="modelSearch" class="search" placeholder="Search model / trigger / tool…">
    <div id="modelGroups"></div>
  </section>
```

- [ ] **Step 3: Add the script tag + bump cache-busts**

Add `models.js` before `app.js` in the script block, and bump every `?v=10` → `?v=11` (css line 10 + the three script tags):

```html
<link rel="stylesheet" href="styles.css?v=11">
...
<script src="data.js?v=11"></script>
<script src="uses.js?v=11"></script>
<script src="models.js?v=11"></script>
<script src="app.js?v=11"></script>
```

- [ ] **Step 4: Verify the section/nav wiring is present**

Run: `grep -c 'data-v="models"\|id="models"\|models.js?v=11' ~/mnq_trading/education/index.html`
Expected: `3`.

- [ ] **Step 5: Commit**

```bash
cd ~/mnq_trading && git add education/index.html && \
git commit -m "feat(education): Model Playbook nav+section, load models.js, ?v=11

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 3: Implement `renderModels()` + filters in `app.js`

**Files:**
- Modify: `education/app.js` (add a render block before the `/* ---------------- nav ---------------- */` section, ~line 249)

- [ ] **Step 1: Add the render + filter block**

Insert this block inside the IIFE, before the `nav` section. It reuses `E.verdicts`/`chip`/`$`/`esc`/`mcls`.

```js
/* ---------------- Model Playbook ---------------- */
const MODELS = window.MODELS || [];
const MENTOR_ORDER = ["TTrades","Daye","GxT","ICT","Dexter","XYJ","Daye Mentorship"];
const SESSION_LABELS = {asia:"Asia",london:"London","ny-am":"NY AM",lunch:"Lunch","ny-pm":"NY PM",news:"News",'htf-open':"HTF Open",dow:"Day-of-Week"};
let mFilter = {mentor:"all", session:"all", verdict:"all", q:""};

function modelRow(k,v){ return v ? '<div class="row"><div class="k">'+k+'</div><div class="v">'+esc(v)+'</div></div>' : ''; }

function modelCard(m){
  const tools = (m.tools||[]).map(t=>'<span class="tag">'+esc(t)+'</span>').join('');
  return '<div class="card model '+mcls(m.mentor)+'" onclick="this.classList.toggle(\'open\')">'+
    '<h4>'+esc(m.name)+' '+chip(m.verdict)+'</h4>'+
    '<p class="sess">'+esc(m.session)+'</p>'+
    '<div class="more">'+
      modelRow('HTF context', m.htf)+
      modelRow('Trigger', m.trigger)+
      modelRow('Entry', m.entry)+
      modelRow('Stop', m.stop)+
      modelRow('Target', m.target)+
      modelRow('Timeframes', m.tfs)+
      (tools?'<div class="row"><div class="k">Tools</div><div class="v">'+tools+'</div></div>':'')+
      modelRow('Example', m.example)+
      '<div class="row"><div class="k">&nbsp;</div><div class="v"><a href="mentors/'+esc(m.guideId)+'.html">Full guide →</a></div></div>'+
    '</div></div>';
}

function modelMatches(m){
  if(mFilter.mentor!=="all" && m.mentor!==mFilter.mentor) return false;
  if(mFilter.session!=="all" && m.sessionKey!==mFilter.session) return false;
  if(mFilter.verdict!=="all" && m.verdict!==mFilter.verdict) return false;
  if(mFilter.q){ const t=(m.name+' '+m.trigger+' '+(m.tools||[]).join(' ')).toLowerCase(); if(t.indexOf(mFilter.q)<0) return false; }
  return true;
}

function renderModelGroups(){
  const host=$('#modelGroups'); if(!host) return;
  const shown=MODELS.filter(modelMatches);
  let html='';
  MENTOR_ORDER.forEach(mn=>{
    const list=shown.filter(m=>m.mentor===mn);
    if(!list.length) return;
    html+='<div class="mgroup"><h3 class="'+mcls(mn)+'">'+esc(mn)+' <span class="cnt">('+list.length+')</span></h3>'+
      list.map(modelCard).join('')+'</div>';
  });
  host.innerHTML = html || '<p class="lead">No models match these filters.</p>';
}

function renderModelFilters(){
  const host=$('#modelFilters'); if(!host) return;
  const chipBtn=(dim,val,label,cls)=> '<button class="fchip '+(cls||'')+(mFilter[dim]===val?' on':'')+'" data-dim="'+dim+'" data-val="'+val+'">'+label+'</button>';
  let h='<div class="frow"><span class="flab">Mentor</span>'+chipBtn('mentor','all','All');
  MENTOR_ORDER.forEach(mn=> h+=chipBtn('mentor',mn,mn,mcls(mn)) ); h+='</div>';
  h+='<div class="frow"><span class="flab">Session</span>'+chipBtn('session','all','All');
  Object.keys(SESSION_LABELS).forEach(k=> h+=chipBtn('session',k,SESSION_LABELS[k]) ); h+='</div>';
  h+='<div class="frow"><span class="flab">Verdict</span>'+chipBtn('verdict','all','All');
  ['s','a','r'].forEach(v=> h+=chipBtn('verdict',v,V[v],'chip '+v) ); h+='</div>';
  host.innerHTML=h;
  host.querySelectorAll('.fchip').forEach(b=> b.onclick=()=>{ mFilter[b.dataset.dim]=b.dataset.val; renderModelFilters(); renderModelGroups(); });
}

if($('#modelGroups')){
  renderModelFilters();
  renderModelGroups();
  const ms=$('#modelSearch');
  if(ms) ms.addEventListener('input',()=>{ mFilter.q=ms.value.trim().toLowerCase(); renderModelGroups(); });
}
```

- [ ] **Step 2: Verify syntax**

Run: `node --check ~/mnq_trading/education/app.js`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add education/app.js && \
git commit -m "feat(education): renderModels() + mentor/session/verdict filters + search

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 4: Add styles for the filter bar + model cards

**Files:**
- Modify: `education/styles.css` (append at end)

- [ ] **Step 1: Append the styles**

Append to `education/styles.css`. Reuses existing `.card`/`.chip`/`.tag`/`.row` styling; adds only the filter bar, group headers, and model-card session line.

```css
/* --- Model Playbook --- */
#models .banner{background:#fff7e6;border:1px solid #f0d999;border-radius:8px;padding:10px 12px;margin:10px 0;font-size:13px;line-height:1.5}
#models .filters{margin:10px 0}
#models .frow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:6px 0}
#models .flab{font-size:12px;font-weight:600;color:#666;min-width:64px}
#models .fchip{border:1px solid #ccc;background:#fff;border-radius:14px;padding:3px 10px;font-size:12px;cursor:pointer}
#models .fchip.on{background:#1558b0;color:#fff;border-color:#1558b0}
#models .search{width:100%;padding:8px 10px;border:1px solid #ccc;border-radius:8px;margin:6px 0 14px;font-size:14px}
#models .mgroup{margin:0 0 18px}
#models .mgroup h3{border-bottom:2px solid #eee;padding-bottom:4px}
#models .mgroup h3 .cnt{color:#999;font-weight:400;font-size:14px}
#models .card.model .sess{color:#1558b0;font-size:12px;font-weight:600;margin:2px 0 0}
```

- [ ] **Step 2: Verify the block is present**

Run: `grep -c "Model Playbook" ~/mnq_trading/education/styles.css`
Expected: `1`.

- [ ] **Step 3: Commit**

```bash
cd ~/mnq_trading && git add education/styles.css && \
git commit -m "style(education): Model Playbook filter bar + card styles

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 5: Reconcile the `data.js` mentor-card setup chips to the 33 audited models

**Files:**
- Modify: `education/data.js` (`mentors[].setups` arrays, ~lines 215–245)

- [ ] **Step 1: Align each `setups` array to the classification table**

For each mentor's `setups:[[name,code],…]` array in `data.js`, make the names match the classification table's model names and the codes match the verdicts (`s`/`a`/`r`). Concretely, the one known drift: the **ICT** card currently lists `Venom`, `MMXM`, `SMC Opening-Range Gap` — replace so ICT reads:

```js
  setups:[["NY AM V-shape / OTE","s"],["Silver Bullet","a"],["Judas Swing / Turtle Soup","a"],["MSS + FVG (2022 model)","a"]],
```

Check the other six mentors' `setups` arrays against the table and fix any name/code mismatch the same way (TTrades, Daye, GxT, Dexter, XYJ, Daye Mentorship). Do not change any other field in `data.js`.

- [ ] **Step 2: Verify syntax**

Run: `node --check ~/mnq_trading/education/data.js`
Expected: no output, exit 0.

- [ ] **Step 3: Verify ICT drift fixed**

Run: `grep -c "Venom\|SMC Opening-Range Gap" ~/mnq_trading/education/data.js`
Expected: `0` (or only in non-setups prose if intentionally kept elsewhere — confirm the `setups` array no longer contains them).

- [ ] **Step 4: Commit**

```bash
cd ~/mnq_trading && git add education/data.js && \
git commit -m "fix(education): reconcile mentor-card setup chips to the 33 audited models

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 6: Update the PWA service worker + regenerate the offline mobile bundle

**Files:**
- Modify: `education/sw.js` (cache list + version)
- Modify: `diagnostics/build_bundle.js` (inline `models.js` + the Model Playbook markup)
- Regenerate: `education/mentor-guides.html`

- [ ] **Step 1: Add `models.js` to the SW cache + bump the version**

In `education/sw.js`, add `'models.js?v=11'` (and matching `?v=11` for the other bumped assets) to the cached-assets array, and bump the cache name version (e.g. `v4`→`v5`). Match the existing string style in the file.

- [ ] **Step 2: Verify sw.js syntax**

Run: `node --check ~/mnq_trading/education/sw.js`
Expected: no output, exit 0.

- [ ] **Step 3: Include models.js + the view in the bundle builder**

In `diagnostics/build_bundle.js`, add `models.js` to the list of JS files it inlines and ensure the Model Playbook `<section id="models">` markup + nav button are carried into the single-file output (the builder already inlines `data.js`/`uses.js`/`app.js` and the view sections — extend the same lists/logic; do not restructure it).

- [ ] **Step 4: Regenerate the bundle**

Run: `node ~/mnq_trading/diagnostics/build_bundle.js`
Expected: it prints success and rewrites `education/mentor-guides.html` (size grows from ~151KB).

- [ ] **Step 5: Verify the bundle carries the view + all 33 models**

Run: `grep -c 'id="models"\|window.MODELS' ~/mnq_trading/education/mentor-guides.html`
Expected: `>= 2`.

- [ ] **Step 6: Commit**

```bash
cd ~/mnq_trading && git add education/sw.js diagnostics/build_bundle.js education/mentor-guides.html && \
git commit -m "feat(education): PWA cache + offline bundle carry the Model Playbook

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Y74Xb73fBpwXA9nFpQZ4RE"
```

---

## Task 7: End-to-end verification in a headless browser

**Files:** none (verification only)

- [ ] **Step 1: Serve the education dir**

Run: `cd ~/mnq_trading/education && python3 -m http.server 8791 &`
Expected: server starts on :8791.

- [ ] **Step 2: Drive the page with the gstack browse binary**

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
$B goto "http://127.0.0.1:8791/index.html?v=11"
$B eval "document.querySelectorAll('#nav button').length"                       # expect 9
$B eval "(function(){switchView('models');return document.querySelectorAll('#modelGroups .card.model').length})()"  # expect 33
$B eval "document.querySelectorAll('#modelGroups .mgroup').length"              # expect 7
$B eval "[...document.querySelectorAll('#modelGroups .card.model .chip.s')].length"  # expect 2
$B eval "(function(){mFilter.mentor='Dexter';renderModelGroups();return document.querySelectorAll('#modelGroups .card.model').length})()"  # expect 6
```
Expected: 9, 33, 7, 2, 6 respectively.

- [ ] **Step 3: Verify each guide link resolves**

Run:
```bash
for id in ttrades daye gxt ict dexter xyj dayement; do test -f ~/mnq_trading/education/mentors/$id.html && echo "$id ok" || echo "$id MISSING"; done
```
Expected: all seven `ok`.

- [ ] **Step 4: Stop the server + browser**

Run: `pkill -f "http.server 8791"; pkill -f "browse/dist/browse"`
Expected: processes stop.

- [ ] **Step 5: Final confirmation (no commit — verification only)**

Confirm all checks in Step 2 passed (9 / 33 / 7 / 2 / 6) and all seven guide files exist. If any check fails, fix the responsible task before marking the plan complete.

---

## Self-review notes (author checklist, done)

- **Spec coverage:** §4 data model → Task 1; §5 view → Tasks 2–4; §6 honesty banner → Task 2 Step 2 + `chip()` reuse; §7 integration/mobile → Tasks 2,5,6; §8 verification → Task 7. All covered.
- **Verdict system:** uses `window.EDU.verdicts` codes `s/a/r`, `g` never assigned (matches the corrected spec). Exactly 2 `s`.
- **No placeholders:** every code step shows full code; the only intentional literal is `"not covered in corpus"` (a real sentinel, per the no-fabrication rule) and the "author remaining 31" step, which is bounded by the full classification table + exact source pointers.
- **Type consistency:** `mFilter`, `modelMatches`, `renderModelGroups`, `renderModelFilters`, `modelCard`, `MENTOR_ORDER`, `SESSION_LABELS`, `window.MODELS` names are consistent across Tasks 1/3; DOM ids (`#modelGroups`,`#modelFilters`,`#modelSearch`,`#models`) match between Tasks 2 and 3.
