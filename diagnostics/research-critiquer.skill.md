---
name: research-critiquer
description: Independent critiquer for the trading-research loop - audits an engine spec + backtest result against grounding, overfitting, and anti-pattern rubrics; emits PASS/REVISE before any artifact is marked validated.
---

# research-critiquer

The **critiquer** half of a generator-critiquer loop for the MNQ/ICT research pipeline.
The **generator** (the build session) produces a research artifact - an engine spec + backtest
result, a skill, or a config. This critiquer independently audits that artifact against a fixed
rubric and emits a **PASS / REVISE** verdict BEFORE the artifact may be marked "validated" or
"production". It mechanizes the locked rule "validate before declaring done" so a miss does not
depend on the user catching it (e.g. the Model 9 COT gap that one transcript-read produced).

## When to invoke
- After building or materially changing any backtest engine, before writing a "VALIDATED" /
  "PRODUCTION" verdict into a spec, memory, or session_state.
- Before pushing an engine spec to Obsidian `Research/` as ground truth.
- Before installing a generated skill/config as production.
- On request ("critique this", "review the engine before I commit").

## Inputs (the generator must supply)
1. **Artifact** - the spec/claims doc (e.g. `Research/ICT_Model<N>_*_Spec.md`) OR the skill/config file.
2. **Result** - the raw backtest output the claims rest on (log, per-year table, trade CSV).
3. **Corpus pointers** - the technique's ground-truth sources: qmd collection (e.g. `ict_transcripts`),
   the relevant NotebookLM notebook id, and any execution corpus (e.g. `gxt_execution_posts.csv`).

## Execution protocol (judge = in-session Claude subagent)
Dispatch a **read-only** subagent (Explore or general-purpose) with: this rubric, the artifact text,
the result text, and the corpus pointers. The subagent must:
- Treat the generator's claims as **unproven** until traced to a source or a result line.
- Use qmd/Obsidian/Read to **independently verify** grounding claims it can check; never accept a
  rule because the spec asserts it.
- Return the verdict in the **Output format** below.
Write the returned verdict to `<artifact>.critique.md` (alongside the artifact, or in `diagnostics/`).
Do NOT let the same context that generated the artifact also pass it - independence is the point.

## Rubric - score every item, cite evidence

### A. Grounding completeness  (the Model 9 COT failure)
- [ ] Every claimed rule traced to a **specific** source (transcript line / video / post), not asserted.
- [ ] **ALL** of the technique's transcripts/videos read - not the first match. Count them; name them.
- [ ] Every named lecture/episode in the technique enumerated - no collapsing a series into a blob
      (the bias cluster: COT, Open Interest, Seasonals, Intermarket, Relative Strength must survive).
- [ ] Named ICT/GxT sources the author cites are present (e.g. CFTC COT) - flag any the author names
      but the build never loaded.

### B. Cross-corpora reconciliation
- [ ] Reconciled against BOTH methodology (NotebookLM/qmd) AND execution data (X posts) where one exists.
- [ ] "Taught vs traded" checked - a technique taught but never executed live is a red flag
      (e.g. Oil triad taught, 0 executions -> "CL is dead").

### C. Anti-pattern falsification  (discretionary reads do not mechanize)
- [ ] No component is a **fixed-candle mechanical proxy for a discretionary/real-time read** without
      an explicit ablation proving it adds edge. Known anti-predictive: news gate, reversal-confirm,
      Judas/liquidity-sweep gate, PSP proxy, driver-v2/driver-news, smt-gate. If present -> BLOCKER
      until ablated.
- [ ] The entry **mechanic** itself was falsification-tested (cf. FVG-CE PF-ceiling 0.96 vs OTE/turtle;
      "V-shape IS the edge / limit orders collapse WR"). A win rate without an entry-ablation is suspect.

### D. Overfitting discipline
- [ ] Every parameter is a toggle with a **measured** contribution (added vs removed), not a free knob.
- [ ] A **robustness sweep** exists on the key threshold and the edge survives a wide band
      (e.g. min_imp 8-50pt), not a single tuned value.
- [ ] Result is **every-year-positive** or the year-by-year is shown and the carry-year named; a PF
      driven by one regime/year is flagged.
- [ ] Drawdown is honest: raw vs filtered both shown; return/DD stated; no DD hidden by a late filter.
- [ ] **Concentration caveats disclosed** - overlapping books same-direction (OTE/turtle 99/100),
      correlated underlyings (cross-index), 2x sizing -> half-budget rule stated.

### E. Regime vs bug
- [ ] Any recent-year fade is **diagnosed** (e.g. %-of-price scaling tested AND rejected), labeled
      regime vs parameterization, not silently curve-fit away.

### F. Reproducibility & honesty
- [ ] The exact command/config to reproduce the headline number is in the artifact.
- [ ] Negative results are recorded (so they are not re-run) - matches the gotchas discipline.
- [ ] No number is cited from the wrong surface (e.g. TV strategy-tester recent-only data as a baseline).

## Output format (verdict)
```
VERDICT: PASS | REVISE
SUMMARY: <one line>
FINDINGS:
  [BLOCKER] <finding> -> <specific fix>          # must fix before "validated"
  [WARN]    <finding> -> <specific fix>          # should fix / disclose
  [NIT]     <finding> -> <optional>
GROUNDING CHECKS RUN: <what the critiquer independently verified, with source>
```
- **REVISE** if any BLOCKER. A BLOCKER = an ungrounded production claim, an un-ablated discretionary
  proxy, a single-point (un-swept) threshold, an undisclosed concentration/DD, or a one-year carry.
- PASS only when A-F are clean and the headline claim is reproducible and honestly caveated.

## Deployment as a hosted Routine (later)
This skill is the routine's instruction body. To run unattended via Claude Code Routines
([[ref-claude-routines]]): `/schedule` an **event-based** routine triggered on a spec commit / PR open
in `mnq_trading`, connect the repo + qmd/Obsidian, paste this rubric as the prompt, and route the
verdict to Telegram/Slack. Generator opens the PR; this critiquer triggers on that PR's creation and
comments before the user merges. Keep execution (Tradovate) OUT of the routine - review/monitoring only.

## Provenance
Rubric distilled from the project's hard-won gotchas (cross-corpora rule, grounding-completeness,
driver/PSP/news anti-predictive results, FVG-CE falsification, robustness-sweep + regime-vs-bug
discipline) and the generator-critiquer pattern from Claude Code Routines ([[ref-claude-routines]]).
