#!/usr/bin/env python3
"""Build FABLE_PROJECT_BRIEF.md -- the master context document for claude.ai (Fable).

Deterministic, zero-LLM. Concatenates the LIVING canonical sources (memory core +
result files) so the brief never drifts from reality, then adds:
  - a file manifest (engines / diagnostics / data) so Fable knows what exists and
    can ASK for a specific file, which the operator pastes on demand via the bridge,
  - a corpus map (qmd collections, NotebookLM notebook IDs, Obsidian vault),
  - the consult protocol (how to be a skeptical analyst on this project).

Usage:
    python3 tools/fable_bridge/build_brief.py          # writes ./FABLE_PROJECT_BRIEF.md
    python3 tools/fable_bridge/build_brief.py --out /tmp/brief.md

Regenerate before every Fable consult so the brief reflects current state.
"""
import argparse
import datetime as dt
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
REPO = os.path.join(HOME, "mnq_trading")
MEM = os.path.join(HOME, ".claude/projects/-Users-azarudin/memory")

# Canonical living sources, in read order. Each is concatenated verbatim.
MEMORY_CORE = [
    ("session_state.md", "CURRENT STATE (live focus, production books, key numbers)"),
    ("gotchas.md", "ACTIVE GOTCHAS (failed approaches, dead ends, locked lessons)"),
    ("MEMORY.md", "MEMORY INDEX (pointers to every memory file)"),
    ("ict_engine_factory.md", "ICT ENGINE FACTORY (the project goal + ground-truth protocol)"),
    ("model9_oneshot_result.md", "MODEL 9 RESULT (OTE weekly swing engine)"),
    ("model5_scalp_result.md", "MODEL 5 RESULT (OTE intraday scalp diversifier)"),
    ("feedback_external_model_consult.md", "WHY YOU (Fable) ARE BEING CONSULTED"),
]

CORPUS_MAP = """\
## CORPUS MAP -- where the project's knowledge lives

You (Fable, on claude.ai) cannot read the local filesystem. This brief IS your
knowledge base. When you need a specific source not included here, ask for it by
path/ID and the operator (Claude Code, working alongside you) will paste it in.

### Source code -- `~/mnq_trading/`
- `backtest/model9_oneshot_engine.py` -- Model 9 OTE weekly swing engine (shared
  loaders / bias / OTE / stats reused by all engines).
- `backtest/model5_intraday_engine.py` -- Model 5 OTE intraday scalp; holds
  `walk_limit_1m` (the 1m fill resolver) and `--sd {off,confirm,veto}`.
- `backtest/mnq_backtest_engine_v8_18.py` -- the V-shape FVG-reversal combine engine
  (62T PERFECT config); holds `simulate_trade`, `check_nq_leads`, driver flags.
- `diagnostics/` -- one-off audits & ablations (clean_is, oos_books, audit_62t_1m,
  model5_sd_ablation, model5_crossindex_ym_*.critique.md, etc.).
- `diagnostics/research-critiquer.skill.md` -- the internal logic-only gate.

### qmd -- local BM25 + vector search (operator runs `~/.bun/bin/qmd`)
- collection `Trading` -- Obsidian vault (~1181 docs).
- collection `memory`  -- the memory files (~57 docs).
- collection `ict_transcripts` -- 493 ICT YouTube transcripts (the DISCOVERY layer).
- collection `ict_extraction` -- prior-session extraction (treat as UNVALIDATED synthesis).
- Ask: "qmd <query>" and the operator returns the hits.

### NotebookLM -- rule ground-truth (operator runs `notebooklm`)
- Research (Daye/GXT/ICT methodology): `1a62aa84-ba79-495b-9aa6-eefb27cef761`
- TTrades Extended (50 more videos):    `2a6deaec...`
- Brain (project session logs):         `e59500f3-8d39-4e9b-9b34-41161faf0fa1`

### Obsidian vault -- `/Users/azarudin/Documents/MNQ trading/Trading`
- `JUDGE/` strategy docs+config, `Lab Results/`, `Backlog/` (150 lab items),
  `Sessions/` (daily summaries), `Research/` (engine catalog + specs).
"""

CONSULT_PROTOCOL = """\
## YOUR ROLE (Fable) -- skeptical external analyst

You were brought in (2026-06-10) and immediately caught a DATA-PROVENANCE LEAK the
internal `/research-critiquer` could not: the engines defaulted to `MULTI_*_2020_2025.csv`
files that silently extend to 2026-05-26, so every "validated" number was computed
over 2020-2026 and NEVER held out. That is exactly the value you add.

The internal critiquer validates LOGIC (lookahead, fills, point values, anti-patterns).
It structurally CANNOT catch (a) SELECTION bias from searching many configs on one
dataset, or (b) data-window provenance. You and the in-context generator share no
blind spots -- so:

When consulted, be adversarial and statistics-first. Always probe:
1. Selection bias -- how many configs/instruments were tried before this one survived?
   "lookahead-corrected" != "selection-corrected".
2. Provenance -- was the test window actually held out? (grep max trade date.)
3. Tail / skew -- a 96% WR with n~2 losers carries zero tail information.
4. Execution realism -- slippage, commissions, fill assumptions, sim-to-live gap.
5. The single test that would FALSIFY the claimed edge.
Treat "this feels converged" as the TRIGGER to dig, never the conclusion.
"""


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return "(missing: %s)" % path


def sh(cmd):
    try:
        return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                              timeout=20).stdout.strip()
    except Exception as e:  # noqa
        return "(failed: %s)" % e


def manifest():
    lines = []
    eng = sh(["bash", "-lc", "ls backtest/model*.py backtest/mnq_backtest_engine_v8_18.py 2>/dev/null"])
    lines.append("### Engines\n" + (eng or "(none)"))
    diag = sh(["bash", "-lc", "ls diagnostics/*.py diagnostics/*.critique.md 2>/dev/null | head -60"])
    lines.append("\n### Diagnostics (run on request)\n" + (diag or "(none)"))
    data = sh(["bash", "-lc", "ls -1 data/MULTI_*.csv 2>/dev/null"])
    lines.append("\n### Data files (note the 2020_2025 files extend to 2026-05-26 -- the leak)\n" + (data or "(none)"))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "FABLE_PROJECT_BRIEF.md"))
    args = ap.parse_args()

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    gitlog = sh(["git", "log", "--oneline", "-15"])

    parts = []
    parts.append("# MNQ TRADING -- PROJECT BRIEF FOR FABLE\n")
    parts.append("_Generated %s by tools/fable_bridge/build_brief.py. "
                 "Regenerated each consult; reflects live state._\n" % now)
    parts.append("\n> **THE ONE FACT THAT FRAMES EVERYTHING:** No clean out-of-sample\n"
                 "> test exists yet. Every 'validated' number (Book C return/DD 31.7,\n"
                 "> the 62T combine config) was computed over 2020-2026 and never held\n"
                 "> out. The only pristine OOS left is FORWARD / LIVE-DEMO data. Treat\n"
                 "> all backtest headlines as IN-SAMPLE pending live demo.\n")
    parts.append("\n## RECENT COMMITS\n```\n%s\n```\n" % gitlog)
    parts.append("\n## FILE MANIFEST\n" + manifest() + "\n")
    parts.append("\n" + CORPUS_MAP)
    parts.append("\n" + CONSULT_PROTOCOL)
    parts.append("\n---\n# LIVING MEMORY CORE (verbatim, canonical)\n")
    for fname, label in MEMORY_CORE:
        parts.append("\n\n## ===== %s =====\n_%s_\n\n" % (fname, label))
        parts.append(read(os.path.join(MEM, fname)))

    out = "\n".join(parts)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s (%d chars, ~%dk tokens)" % (args.out, len(out), len(out) // 4000))


if __name__ == "__main__":
    sys.exit(main())
