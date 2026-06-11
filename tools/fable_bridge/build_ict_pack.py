#!/usr/bin/env python3
"""Build FABLE_ICT_PACK.md -- the distilled ICT corpus for claude.ai (Fable).

Tiering (matches the ict-engine-factory ground-truth protocol):
  RESIDENT in the project (this pack):
    - Obsidian Research/ specs verbatim (engine catalog, factory matrix, GxT rulebook,
      validated model specs, propfirm table) -- the project's own structured outputs.
    - ICT_Extraction_CLASSIFIED.md verbatim, LABELED unvalidated synthesis.
    - A TITLE INDEX of every Concepts/ICT note (~509) and every cleaned ICT transcript
      (~493) -- so Fable knows the full inventory and can ask for any item by name.
  ON-DEMAND (NOT dumped -- too big / lower-signal; retrieved when Fable asks):
    - raw transcript bodies + concept-note bodies via qmd (collections `ict_transcripts`,
      `Trading`); NotebookLM rule-checks via `notebooklm ask`.

Usage: python3 tools/fable_bridge/build_ict_pack.py   # -> ~/mnq_trading/FABLE_ICT_PACK.md
Then upload as a project-knowledge text file (see the fable-consult skill).

ASCII-only source (this Python 3.10 rejects U+2014 in literals).
"""
import datetime as dt
import glob
import os

HOME = os.path.expanduser("~")
REPO = os.path.join(HOME, "mnq_trading")
VAULT = "/Users/azarudin/Documents/MNQ trading/Trading"
RESEARCH = os.path.join(VAULT, "Research")
CONCEPTS = os.path.join(VAULT, "Concepts/ICT")
TRANSCRIPTS = os.path.join(REPO, "diagnostics/ict_transcripts/clean")
CLASSIFIED = os.path.join(REPO, "_cleanup_staging/desktop_files/ICT_Extraction_CLASSIFIED.md")
OUT = os.path.join(REPO, "FABLE_ICT_PACK.md")

HEADER = """\
# FABLE ICT CORPUS PACK

_Generated %s by tools/fable_bridge/build_ict_pack.py. Companion to FABLE_PROJECT_BRIEF._

## How to use this pack (provenance matters -- you are the skeptic)
- **Research/ specs below = the project's OWN structured outputs** (engine catalog,
  factory matrix, model specs, GxT rulebook). Closest thing to validated, but still
  in-sample (see the brief's OOS framing fact).
- **ICT_Extraction_CLASSIFIED = UNVALIDATED synthesis** of what ICT teaches, auto-extracted
  from transcripts. Treat as an INDEX/hypothesis source, never as proven edge.
- **The two title indexes** list every concept note (~509) and cleaned transcript (~493).
  Their BODIES are NOT here -- ask the operator for any by exact title and they will
  qmd-retrieve and paste it. That is how you "see everything" without a 13MB dump.
- Ground-truth protocol: qmd = discovery, NotebookLM = rule-check, BACKTEST = edge.
  A faithfully-extracted rule is NOT a profitable rule -- demand the backtest.
"""


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return "(missing: %s)" % path


def titles(folder, pattern="**/*.md"):
    files = sorted(glob.glob(os.path.join(folder, pattern), recursive=True))
    rel = [os.path.relpath(p, folder) for p in files]
    return rel


def main():
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [HEADER % now]

    # 1. Research/ specs verbatim.
    parts.append("\n---\n# RESEARCH SPECS (verbatim -- project structured outputs)\n")
    for p in sorted(glob.glob(os.path.join(RESEARCH, "*.md"))):
        parts.append("\n\n## ===== Research/%s =====\n\n" % os.path.basename(p))
        parts.append(read(p))

    # 2. Classified extraction (labeled unvalidated).
    parts.append("\n\n---\n# ICT_Extraction_CLASSIFIED.md "
                 "(UNVALIDATED auto-extraction -- index/hypotheses only)\n\n")
    parts.append(read(CLASSIFIED))

    # 3. Title indexes (bodies retrievable on demand via qmd).
    cn = titles(CONCEPTS)
    tr = titles(TRANSCRIPTS)
    parts.append("\n\n---\n# INVENTORY (bodies on-demand via qmd; ask by exact title)\n")
    parts.append("\n## Concepts/ICT notes (%d) -- qmd collection `Trading`\n" % len(cn))
    parts.append("\n".join("- %s" % t for t in cn))
    parts.append("\n\n## Cleaned ICT transcripts (%d) -- qmd collection `ict_transcripts`\n"
                 % len(tr))
    parts.append("\n".join("- %s" % t for t in tr))
    parts.append("\n\n## Retrieval commands the operator runs for you\n"
                 "```bash\n"
                 "~/.bun/bin/qmd search \"<query>\" -c ict_transcripts -n 5\n"
                 "~/.bun/bin/qmd search \"<query>\" -c Trading -n 5\n"
                 "notebooklm use 1a62aa84-ba79-495b-9aa6-eefb27cef761 && notebooklm ask \"<q>\"\n"
                 "```\n")

    out = "\n".join(parts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s (%d chars, ~%dk tokens) | concept notes=%d transcripts=%d"
          % (OUT, len(out), len(out) // 4000, len(cn), len(tr)))


if __name__ == "__main__":
    main()
