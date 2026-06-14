#!/usr/bin/env python3
"""feed_pull: build a TEXT-ONLY knowledge feed from X handles (no media stored).

Uses gallery-dl --no-download --write-metadata (writes JSON sidecars, zero media
bytes) via the user's Chrome login, parses post text/date/engagement, and upserts
into ~/social_rips/feed.json (dedup by tweet id, newest first). Re-run anytime to
accumulate new posts. The dashboard (build_dashboard.py) renders this feed.

Cost: ZERO model tokens - pure scraping. ASCII-only source.

Usage:
  /usr/local/bin/python3 feed_pull.py RoundtableSpace [handle2 ...] [--limit 1-300]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime

FEED = os.path.expanduser("~/social_rips/feed.json")


def pull_handle(handle, rng, browser):
    handle = handle.lstrip("@").strip()
    url = "https://x.com/%s" % handle
    tmp = tempfile.mkdtemp(prefix="feed_%s_" % handle)
    cmd = ["gallery-dl", "--cookies-from-browser", browser, "--no-download",
           "--write-metadata", "-o", "extractor.twitter.text-tweets=true", "-d", tmp]
    if rng:
        cmd += ["--range", rng]
    cmd += [url]
    print("+ pulling @%s ..." % handle, flush=True)
    subprocess.run(cmd, capture_output=True, text=True)
    posts = {}
    for j in glob.glob(os.path.join(tmp, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(j))
        except Exception:
            continue
        tid = str(d.get("tweet_id") or d.get("id") or "")
        if not tid:
            continue
        author = d.get("author") or {}
        name = author.get("name") if isinstance(author, dict) else None
        name = name or handle
        media = d.get("type") or (d.get("extension") and (
            "video" if d.get("extension") in ("mp4", "m4v", "mov") else "image"))
        rec = {
            "id": tid, "handle": handle, "date": str(d.get("date") or ""),
            "text": (d.get("content") or "").strip(),
            "likes": d.get("favorite_count") or 0,
            "rt": d.get("retweet_count") or 0,
            "replies": d.get("reply_count") or 0,
            "views": d.get("view_count") or 0,
            "url": "https://x.com/%s/status/%s" % (name, tid),
            "media": media or "",
        }
        prev = posts.get(tid)
        # keep the richest (longest text) sidecar per tweet
        if not prev or len(rec["text"]) > len(prev.get("text", "")):
            posts[tid] = rec
    return posts


def load_feed():
    try:
        return json.load(open(FEED))
    except Exception:
        return {"handles": [], "posts": []}


def main():
    ap = argparse.ArgumentParser(description="Build/refresh a text-only X knowledge feed.")
    ap.add_argument("handles", nargs="+", help="X handles (without @)")
    ap.add_argument("--limit", dest="rng", default=None,
                    help="range e.g. 1-300 (default: all up to ~3200)")
    ap.add_argument("--browser", default="chrome")
    args = ap.parse_args()

    feed = load_feed()
    by_id = {p["id"]: p for p in feed.get("posts", [])}
    handles = set(feed.get("handles", []))
    added = 0
    for h in args.handles:
        got = pull_handle(h, args.rng, args.browser)
        for tid, rec in got.items():
            if tid not in by_id:
                added += 1
            by_id[tid] = rec
        handles.add(h.lstrip("@").strip())

    posts = sorted(by_id.values(), key=lambda p: p.get("date", ""), reverse=True)
    out = {
        "updated": datetime.now().isoformat(timespec="seconds"),
        "handles": sorted(handles),
        "count": len(posts),
        "posts": posts,
    }
    os.makedirs(os.path.dirname(FEED), exist_ok=True)
    json.dump(out, open(FEED, "w"), indent=1, ensure_ascii=False)
    print("feed: %d posts total (+%d new) from %s -> %s"
          % (len(posts), added, ", ".join(sorted(handles)), FEED))


if __name__ == "__main__":
    main()
