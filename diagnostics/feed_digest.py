#!/usr/bin/env python3
"""feed_digest: deterministic (zero-model) classifier + "what's new" digest.

Reads ~/social_rips/feed.json, tags each post by keyword into AI-news categories,
and writes back a `digest` block (counts by category + recent highlights). No LLM,
no API, no token/limit cost. The dashboard renders the digest panel.

Usage:  /usr/local/bin/python3 feed_digest.py [--hours 72] [--top 14]
"""
import argparse
import json
import os
from datetime import datetime, timedelta

FEED = os.path.expanduser("~/social_rips/feed.json")

# priority-ordered (first match wins); AI-news categories
RULES = [
    ("funding", ["raises", "raised", "funding", "valuation", "series ", "seed round",
                 "billion", "$1b", "acquire", "acquisition", "ipo"]),
    ("release", ["launch", "released", "releasing", "now available", "rolls out",
                 "unveil", "drops", "ships", "is here", "out now", "introducing",
                 "announce", "general availability", " ga "]),
    ("model", ["gpt", "claude", "gemini", "llama", "mistral", "sora", "qwen", "deepseek",
               "o1", "o3", "flux", "parameters", "benchmark", "sota", "fine-tune",
               "model", "multimodal"]),
    ("tool", ["open-source", "open source", "open-sourced", "github", "repo", " mcp",
              " sdk", " api", "extension", "library", "framework", "plugin", "app ",
              "tool", "cli"]),
    ("research", ["paper", "research", "arxiv", "study", "technique", "breakthrough",
                  "discover", "method"]),
    ("agent", ["agent", "autonomous", "agentic", "self-improv"]),
]


def classify(text):
    t = (text or "").lower()
    for tag, kws in RULES:
        for kw in kws:
            if kw in t:
                return tag
    return "other"


def parse_date(s):
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=72, help="recency window for highlights")
    ap.add_argument("--top", type=int, default=14, help="max highlights")
    args = ap.parse_args()

    feed = json.load(open(FEED))
    posts = feed.get("posts", [])
    by_tag = {}
    for p in posts:
        p["tag"] = classify(p.get("text", ""))
        by_tag[p["tag"]] = by_tag.get(p["tag"], 0) + 1

    # recent window; fall back to top-by-likes if nothing recent
    newest = parse_date(posts[0]["date"]) if posts else None
    cutoff = (newest or datetime.now()) - timedelta(hours=args.hours)
    recent = [p for p in posts if (parse_date(p["date"]) or datetime.min) >= cutoff]
    pool = recent if recent else posts
    hi = sorted(pool, key=lambda p: (p.get("likes") or 0), reverse=True)[:args.top]
    highlights = [{"tag": p["tag"], "date": p["date"], "likes": p.get("likes", 0),
                   "text": (p.get("text") or "").replace("\n", " ").strip()[:200],
                   "url": p.get("url", "")} for p in hi]

    feed["digest"] = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window_hours": args.hours,
        "recent_count": len(recent),
        "by_tag": dict(sorted(by_tag.items(), key=lambda kv: -kv[1])),
        "highlights": highlights,
    }
    json.dump(feed, open(FEED, "w"), indent=1, ensure_ascii=False)
    print("digest: %d posts tagged %s; %d recent (<=%dh); %d highlights"
          % (len(posts), feed["digest"]["by_tag"], len(recent), args.hours, len(highlights)))


if __name__ == "__main__":
    main()
