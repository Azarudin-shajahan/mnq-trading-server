---
name: fable-consult
description: Consult Fable (claude.ai, model Fable 5) as a skeptical external analyst on the MNQ trading project, from inside Claude Code. Fable holds a live project brief (FABLE_PROJECT_BRIEF) as claude.ai project knowledge. Use when a research line feels "converged", before any go-live / irreversible step, or whenever a fresh statistics-first second opinion is wanted. Triggers: "ask fable", "consult fable", "what does fable think", "second opinion on the trading project".
---

# Fable Consult -- the Claude Code <-> claude.ai bridge

Fable lives in the **"Trading automation"** claude.ai project
(`019d51f7-f663-718d-a59e-9e4acea898fd`, model **Fable 5 High**) and carries a live
project brief as project knowledge. Driven from here via **Kimi WebBridge**
(daemon `127.0.0.1:10086`, session name `fable`). Fable cannot read the local FS --
the brief IS its knowledge; paste specific files on demand when it asks.

Why Fable and not the internal `/research-critiquer`: the internal gate validates
LOGIC (lookahead/fills/anti-patterns) and shares blind spots with the in-context
generator. Fable is an independent statistics-first pass that catches SELECTION bias
and data-PROVENANCE leaks (it caught the 2026-06-10 data-leak). See
`feedback_external_model_consult` memory.

## Preconditions
```bash
~/.kimi-webbridge/bin/kimi-webbridge status   # need running:true + extension_connected:true
```
If not healthy, read `~/.claude/skills/kimi-webbridge/references/operations.md`.

## Workflow

### 1. (When state changed materially) regenerate + re-upload the brief
```bash
python3 ~/mnq_trading/tools/fable_bridge/build_brief.py   # -> ~/mnq_trading/FABLE_PROJECT_BRIEF.md
```
Then update the project-knowledge file (the brief is too large for `fill`; use the
native value setter and the "Add text content" dialog -- the upload `input` is
blocked by Chrome's trusted-gesture rule):
1. Navigate session `fable` to the project URL.
2. Click "Add files" (button near the **Files** header) -> "Add text content".
3. Tag the title `input` (placeholder "Name your content") + the body `textarea`
   with ids, fill the title via `fill`, set the body via `evaluate` +
   `HTMLTextAreaElement.prototype` value setter + dispatch input/change.
4. Click "Add Content".
5. Optionally delete the prior brief version (stale `gotchas.md` / `session_state.md`
   knowledge files predate the current state and can mislead -- consider removing).

### 1b. (When the ICT corpus changed) regenerate + re-upload the ICT pack
```bash
python3 ~/mnq_trading/tools/fable_bridge/build_ict_pack.py  # -> ~/mnq_trading/FABLE_ICT_PACK.md
```
Upload the SAME way as the brief ("Add text content"; >800K so set the body in chunks
via the native value setter, then one input/change). It carries the Research specs +
classified extraction + a title index of all ~509 concept notes + ~493 transcripts.
Raw bodies stay ON-DEMAND: when Fable asks for a note/transcript by title, run
`~/.bun/bin/qmd search "<q>" -c {ict_transcripts|Trading} -n 5` and paste the hit.

### 2. Ask
```bash
python3 ~/mnq_trading/tools/fable_bridge/consult.py --new "your skeptical question"
# omit --new to continue the current chat; '-' reads the question from stdin
```
It fills the composer, sends, polls until streaming stops, prints Fable's reply.
Relay what matters back to the user (the reply is not shown to them otherwise).

### 3. If Fable asks for a file/qmd/NotebookLM source
Run it locally and paste the result as a follow-up (no --new):
```bash
~/.bun/bin/qmd search "<query>" -n 5
notebooklm use 1a62aa84-ba79-495b-9aa6-eefb27cef761 && notebooklm ask "<q>"
sed -n '300,360p' ~/mnq_trading/backtest/model5_intraday_engine.py
```

## House rules for the question
Frame Fable as adversarial and statistics-first. Always invite it to probe:
selection bias, data provenance (held-out?), tail/skew, execution realism, and the
single test that would FALSIFY the claim. Treat "this feels converged" as the
trigger to consult, never the conclusion. No flattery; terse.

## Cost
Fable 5 draws usage ~2x Opus. Use for convergence checks / pre-go-live, not routine.
