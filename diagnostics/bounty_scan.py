#!/usr/bin/env python3
"""bounty_scan: find open software bounties and score them for "can I win this".

Pulls open bounty-labelled GitHub issues via the public Search API (no key needed),
scores each by stack-match / payout / spec-clarity / freshness / low-competition
(deterministic, ZERO model cost), and writes ~/social_rips/bounties.json. The
dashboard renders a ranked Bounties panel. A local-model scorer can replace
score_bounty() later for smarter judgement.

Usage:  /usr/local/bin/python3 bounty_scan.py [--per-query 50]
Edit ~/social_rips/stack.txt to set the languages/keywords you can deliver.
"""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OUT = os.path.expanduser("~/social_rips/bounties.json")
STACK_FILE = os.path.expanduser("~/social_rips/stack.txt")
DEFAULT_STACK = ["python", "javascript", "typescript", "react", "node", "bash",
                 "html", "css", "sql", "api", "cli", "scraper", "automation"]
QUERIES = [
    'is:issue is:open label:"\U0001f48e Bounty"',   # Algora
    'is:issue is:open label:"\U0001f4b0 Bounty"',
    'is:issue is:open label:"\U0001f4b5 Bounty"',
]
# practice / AI-eval / CTF repos that pollute the bounty labels (not real payouts)
DENY = ("bug-bounty", "agent-playground", "oss-hunter", "securebananalabs", "ctf",
        "sandbox", "playground", "practice", "example", "livefire", "benchmark",
        "eval-", "-eval", "training", "demo-", "test-bounty")
USD = re.compile(r"\$\s?([0-9][0-9,]{1,6})|\b([0-9]{2,6})\s?(?:usd|USD)\b")


def denied(repo, title):
    s = (repo + " " + title).lower()
    return any(d in s for d in DENY)


def comment_amount(comments_url):
    try:
        req = urllib.request.Request(comments_url + "?per_page=40", headers={
            "Accept": "application/vnd.github+json", "User-Agent": "mnq-bounty-scanner"})
        with urllib.request.urlopen(req, timeout=20) as r:
            cs = json.loads(r.read())
        return max([amount(c.get("body", "")) for c in cs] + [0])
    except Exception:
        return 0


def repo_stars(repo):
    try:
        req = urllib.request.Request("https://api.github.com/repos/" + repo, headers={
            "Accept": "application/vnd.github+json", "User-Agent": "mnq-bounty-scanner"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("stargazers_count", 0)
    except Exception:
        return 0


def load_stack():
    try:
        s = [w.strip().lower() for w in open(STACK_FILE) if w.strip() and not w.startswith("#")]
        return s or DEFAULT_STACK
    except Exception:
        return DEFAULT_STACK


def gh_search(q, per_page):
    url = ("https://api.github.com/search/issues?q=%s&sort=created&order=desc&per_page=%d"
           % (urllib.parse.quote(q), per_page))
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "mnq-bounty-scanner"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("items", [])


def amount(text):
    best = 0
    for m in USD.finditer(text or ""):
        v = (m.group(1) or m.group(2) or "").replace(",", "")
        try:
            best = max(best, int(v))
        except Exception:
            pass
    return best


def days_old(iso):
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except Exception:
        return 999


def score_bounty(b, stack, final=False):
    blob = (b["title"] + " " + " ".join(b["labels"]) + " " + b.get("body", "")).lower()
    matches = [w for w in stack if w in blob]
    s = 0.0
    if b["usd"]:
        s += min(b["usd"], 1000) / 1000 * 35       # payout (cap $1000 -> 35)
    s += min(len(matches), 3) / 3 * 25             # stack match
    bl = len(b.get("body", ""))
    s += 12 if bl > 300 else 7 if bl > 100 else 2  # spec clarity
    d = b["created_days"]
    s += 8 if d <= 14 else 5 if d <= 30 else 1     # freshness
    c = b["comments"]                              # competition (contested = bad)
    s += -15 if c > 25 else -8 if c > 10 else 5 if c == 0 else 2 if c <= 2 else 0
    st = b.get("stars", 0)                         # repo legitimacy
    s += 18 if st > 2000 else 12 if st > 500 else 7 if st > 100 else 3 if st > 20 else 0
    if not matches:
        s *= 0.5                                   # outside your stack
    if final and not b["usd"]:
        s *= 0.6                                   # unverified payout
    b["lang"] = matches[0] if matches else "?"
    return round(max(s, 0), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=50)
    args = ap.parse_args()
    stack = load_stack()

    seen = {}
    for q in QUERIES:
        try:
            items = gh_search(q, args.per_query)
        except Exception as ex:
            print("  query failed (%s): %s" % (q[:30], str(ex)[:80]))
            time.sleep(3)
            continue
        for it in items:
            url = it.get("html_url", "")
            if not url or url in seen:
                continue
            repo = "/".join(url.split("/")[3:5]) if url.count("/") >= 4 else ""
            if denied(repo, it.get("title", "")):
                continue
            body = (it.get("body") or "")[:600]
            labels = [l.get("name", "") for l in it.get("labels", [])]
            b = {
                "title": it.get("title", ""), "repo": repo, "url": url,
                "body": body, "labels": labels,
                "comments_url": it.get("comments_url", ""),
                "comments": it.get("comments", 0),
                "created": (it.get("created_at") or "")[:10],
                "created_days": days_old(it.get("created_at") or ""),
                "usd": amount(it.get("title", "") + " " + " ".join(labels) + " " + body),
            }
            b["score"] = score_bounty(b, stack)
            seen[url] = b
        time.sleep(2)  # be gentle with the public API

    # enrich most promising survivors with real $ (Algora bot comment) + repo stars
    top = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:18]
    for b in top:
        if not b["usd"] and b.get("comments_url"):
            b["usd"] = comment_amount(b["comments_url"])
            time.sleep(1)
        b["stars"] = repo_stars(b["repo"])
        b["score"] = score_bounty(b, stack, final=True)
        time.sleep(1)
    for b in seen.values():
        b.pop("body", None)
        b.pop("comments_url", None)
        b.setdefault("stars", 0)
    bounties = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    out = {"updated": datetime.now().isoformat(timespec="seconds"),
           "count": len(bounties), "stack": stack, "bounties": bounties}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    paid = [b for b in bounties if b["usd"]]
    print("bounties: %d found (%d with a $ amount); top score %.1f -> %s"
          % (len(bounties), len(paid), bounties[0]["score"] if bounties else 0, OUT))


if __name__ == "__main__":
    main()
