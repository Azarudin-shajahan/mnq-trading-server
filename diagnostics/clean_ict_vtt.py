#!/usr/bin/env python3
"""Clean ICT WebVTT auto-caption files into dedup'd markdown for qmd indexing.

Reads ~/mnq_trading/diagnostics/ict_transcripts/*.en.vtt (falls back to
.en-orig.vtt when no .en.vtt exists for that video id), strips VTT headers,
timestamps and inline cue tags, collapses the rolling-caption duplication,
and writes clean/<id>__<title>.md with small frontmatter.
"""
import re
from pathlib import Path

SRC = Path.home() / "mnq_trading/diagnostics/ict_transcripts"
OUT = SRC / "clean"
OUT.mkdir(exist_ok=True)

TAG = re.compile(r"<[^>]+>")            # <00:00:00.000>, <c>, </c>
CUE = re.compile(r"-->")               # timestamp cue lines
HDR = re.compile(r"^(WEBVTT|Kind:|Language:)")

def clean_vtt(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out, last = [], None
    for ln in lines:
        if not ln.strip() or HDR.match(ln) or CUE.search(ln) or ln.strip().isdigit():
            continue
        txt = TAG.sub("", ln).strip()
        if not txt or txt == last:
            continue
        # skip rolling-caption fragments that are a prefix of / contained in the prior line
        if last and (txt in last or last in txt):
            if len(txt) > len(last):
                out[-1] = txt; last = txt
            continue
        out.append(txt); last = txt
    return "\n".join(out)

# Prefer .en.vtt; fall back to .en-orig.vtt only for ids lacking an .en.vtt
by_id = {}
for f in SRC.glob("*.vtt"):
    name = f.name
    if name.endswith(".en.vtt"):
        vid = name.split("__", 1)[0]; by_id.setdefault(vid, {})["en"] = f
    elif name.endswith(".en-orig.vtt"):
        vid = name.split("__", 1)[0]; by_id.setdefault(vid, {})["orig"] = f

written = 0
for vid, tracks in by_id.items():
    src = tracks.get("en") or tracks.get("orig")
    if not src:
        continue
    title = src.name.split("__", 1)[1].rsplit(".en", 1)[0]
    body = clean_vtt(src)
    if len(body) < 40:   # skip empties
        continue
    md = (f"---\ntitle: \"{title}\"\nvideo_id: {vid}\n"
          f"url: https://www.youtube.com/watch?v={vid}\nsource: InnerCircleTrader\n---\n\n"
          f"# {title}\n\n{body}\n")
    (OUT / f"{vid}__{re.sub(r'[^A-Za-z0-9 ._-]', '', title)[:80]}.md").write_text(md, encoding="utf-8")
    written += 1

print(f"cleaned transcripts written: {written} -> {OUT}")
print(f"total chars: {sum(p.stat().st_size for p in OUT.glob('*.md')):,}")
