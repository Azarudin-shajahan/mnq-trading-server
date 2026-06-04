#!/usr/bin/env python3
"""Project dashboard generator (deterministic, zero-LLM).

Pulls from three sources and renders a single project view:
  1. project_state.yaml   - small hand-edited "now / next" file (same dir)
  2. git log of ~/mnq_trading  - "what happened"
  3. memory *_result.md frontmatter - validated-engine ledger

Outputs:
  - project_dashboard.html  (local; also the future Railway /research page)
  - Project_Dashboard.md    (Obsidian vault root; syncs to phone)

Regenerate any time with:  python3 build_dashboard.py
ASCII-only source on purpose (this Python 3.10 rejects U+2014 in literals).
"""
import datetime
import glob
import html
import os
import re
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "project_state.yaml")
MNQ_REPO = os.path.expanduser("~/mnq_trading")
MEM_DIR = os.path.expanduser("~/.claude/projects/-Users-azarudin/memory")
OUT_HTML = os.path.join(HERE, "project_dashboard.html")
VAULT = "/Users/azarudin/Documents/MNQ trading/Trading"
OUT_MD = os.path.join(VAULT, "Project_Dashboard.md")


def load_state():
    with open(STATE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def git_log(n=15):
    try:
        res = subprocess.run(
            ["git", "-C", MNQ_REPO, "log",
             "--pretty=format:%h|%ad|%s", "--date=short", "-%d" % n],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return []
    rows = []
    for line in res.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append(parts)
    return rows


def result_engines():
    items = []
    for path in sorted(glob.glob(os.path.join(MEM_DIR, "*_result.md"))):
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        name, desc = os.path.basename(path), ""
        m = re.match(r"^---\n(.*?)\n---", txt, re.S)
        if m:
            fm = m.group(1)
            nm = re.search(r"^name:\s*(.+)$", fm, re.M)
            dm = re.search(r"^description:\s*(.+)$", fm, re.M)
            if nm:
                name = nm.group(1).strip().strip('"')
            if dm:
                desc = dm.group(1).strip().strip('"')
        items.append((name, desc))
    return items


# ---------- HTML rendering ----------

CSS = """
body{background:#0d1117;color:#c9d1d9;font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;
  max-width:1000px;margin:0 auto;padding:24px}
h1{font-size:22px;margin:0 0 2px}h2{font-size:15px;color:#58a6ff;border-bottom:1px solid #21262d;
  padding-bottom:4px;margin:26px 0 10px}
.sub{color:#8b949e;margin:0 0 6px}
table{border-collapse:collapse;width:100%;margin:6px 0}
td,th{border:1px solid #21262d;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#161b22;color:#8b949e;font-weight:600}
code{background:#161b22;padding:1px 5px;border-radius:4px;color:#79c0ff}
ul{margin:6px 0;padding-left:20px}li{margin:2px 0}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:700}
.PRODUCTION,.VALIDATED{background:#1a3d1f;color:#56d364}
.SHELVED,.LOCKED{background:#3d2a1a;color:#e3b341}
.REFINE,.FUNDEDSTAGE{background:#1a2f3d;color:#58a6ff}
.foot{color:#6e7681;font-size:12px;margin-top:30px;border-top:1px solid #21262d;padding-top:10px}
"""


def tag(text):
    cls = re.sub(r"[^A-Z]", "", str(text).upper())
    return '<span class="tag %s">%s</span>' % (cls, html.escape(str(text)))


def h_rows(rows, cols):
    out = ["<table><tr>" + "".join("<th>%s</th>" % c for c in cols) + "</tr>"]
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</table>")
    return "".join(out)


def render_html(st, commits, results):
    e = html.escape
    parts = ["<!doctype html><meta charset=utf-8><title>%s</title><style>%s</style>"
             % (e(st.get("project", "Project")), CSS)]
    parts.append("<h1>%s</h1>" % e(st.get("project", "Project")))
    parts.append('<p class="sub">Updated %s &middot; generated %s</p>'
                 % (e(str(st.get("updated", "?"))),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    parts.append("<p>%s</p>" % e(st.get("focus", "")))

    pb = st.get("production_book", [])
    if pb:
        parts.append("<h2>Production book</h2>")
        rows = [[e(x.get("name", "")), e(x.get("role", "")),
                 tag(x.get("status", "")), e(x.get("metric", ""))] for x in pb]
        parts.append(h_rows(rows, ["Engine", "Role", "Status", "Metric"]))

    eng = st.get("engines", [])
    if eng:
        parts.append("<h2>Engine ledger</h2>")
        rows = [[e(x.get("id", "")), e(x.get("type", "")),
                 tag(x.get("verdict", "")), e(x.get("note", ""))] for x in eng]
        parts.append(h_rows(rows, ["Engine", "Type", "Verdict", "Note"]))

    na = st.get("next_action", [])
    if na:
        parts.append("<h2>Next action</h2><ul>"
                     + "".join("<li>%s</li>" % e(x) for x in na) + "</ul>")

    kn = st.get("key_numbers", [])
    if kn:
        parts.append("<h2>Key numbers (do not re-derive)</h2><ul>"
                     + "".join("<li>%s</li>" % e(x) for x in kn) + "</ul>")

    oi = st.get("open_items", [])
    if oi:
        parts.append("<h2>Open items</h2><ul>"
                     + "".join("<li>%s</li>" % e(x) for x in oi) + "</ul>")

    if results:
        parts.append("<h2>Validated-engine ledger (from memory)</h2>")
        rows = [["<code>%s</code>" % e(n), e(d)] for n, d in results]
        parts.append(h_rows(rows, ["Result note", "Summary"]))

    if commits:
        parts.append("<h2>Recent commits (mnq_trading)</h2>")
        rows = [["<code>%s</code>" % e(h), e(d), e(s)] for h, d, s in commits]
        parts.append(h_rows(rows, ["Hash", "Date", "Subject"]))

    parts.append('<p class="foot">Static, deterministic. Regenerate: '
                 '<code>python3 ~/mnq_trading/diagnostics/build_dashboard.py</code></p>')
    return "".join(parts)


# ---------- Markdown rendering (Obsidian / mobile) ----------

def render_md(st, commits, results):
    L = []
    L.append("# %s" % st.get("project", "Project"))
    L.append("> Updated %s &middot; generated %s &middot; auto-generated, do not hand-edit"
             % (st.get("updated", "?"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    L.append("")
    L.append(st.get("focus", ""))

    pb = st.get("production_book", [])
    if pb:
        L += ["", "## Production book", "", "| Engine | Role | Status | Metric |",
              "|---|---|---|---|"]
        for x in pb:
            L.append("| %s | %s | **%s** | %s |" % (x.get("name", ""), x.get("role", ""),
                                                    x.get("status", ""), x.get("metric", "")))

    eng = st.get("engines", [])
    if eng:
        L += ["", "## Engine ledger", "", "| Engine | Type | Verdict | Note |",
              "|---|---|---|---|"]
        for x in eng:
            L.append("| %s | %s | **%s** | %s |" % (x.get("id", ""), x.get("type", ""),
                                                    x.get("verdict", ""), x.get("note", "")))

    for title, key in [("Next action", "next_action"),
                       ("Key numbers (do not re-derive)", "key_numbers"),
                       ("Open items", "open_items")]:
        vals = st.get(key, [])
        if vals:
            L += ["", "## %s" % title, ""]
            L += ["- %s" % v for v in vals]

    if results:
        L += ["", "## Validated-engine ledger (from memory)", ""]
        for n, d in results:
            L.append("- **%s** - %s" % (n, d))

    if commits:
        L += ["", "## Recent commits (mnq_trading)", "", "| Hash | Date | Subject |",
              "|---|---|---|"]
        for h, d, s in commits:
            L.append("| `%s` | %s | %s |" % (h, d, s.replace("|", "\\|")))

    L += ["", "---", "_Regenerate: `python3 ~/mnq_trading/diagnostics/build_dashboard.py`_"]
    return "\n".join(L) + "\n"


def main():
    st = load_state()
    commits = git_log(15)
    results = result_engines()
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(render_html(st, commits, results))
    wrote = [OUT_HTML]
    try:
        if os.path.isdir(VAULT):
            with open(OUT_MD, "w", encoding="utf-8") as f:
                f.write(render_md(st, commits, results))
            wrote.append(OUT_MD)
    except Exception as exc:
        print("WARN: vault write skipped: %s" % exc)
    print("dashboard: %d commits, %d validated-engine notes" % (len(commits), len(results)))
    for w in wrote:
        print("  wrote " + w)


if __name__ == "__main__":
    main()
