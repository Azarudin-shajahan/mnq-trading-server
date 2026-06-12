#!/usr/bin/env python3
"""xcap -- capture X feeds via the logged-in WebBridge session into SQLite.

Technique: instead of scraping the rendered DOM, capture the X web app's internal
GraphQL `UserTweets` JSON responses (structured, all fields) while auto-scrolling each
profile. Reuses your authenticated browser session (no API cost, no extra account).

Modes:
  --handles a,b,c        live capture: per handle, scroll + grab UserTweets JSON -> DB
  --probe HANDLE         capture once and DUMP the raw network list + first detail to a
                         file, so the exact daemon/X field paths can be confirmed/adapted
  --from-file dump.json  parse a saved JSON capture into the DB (validate the parser
                         offline, no live X needed)
  --selftest             run the parser+classifier on a synthetic tweet object

Caveats (read the README): X serves ~3200 most-recent tweets per profile timeline;
deeper history needs paged search. Scraping is against X ToS -- low rate, your own login.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import xparse
import xstore

DAEMON = "http://127.0.0.1:10086/command"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "posts.db")
TIMELINE_OPS = ("UserTweets", "UserTweetsAndReplies", "SearchTimeline")


def cmd(action, args, session, timeout=60):
    payload = {"action": action, "args": args, "session": session}
    req = urllib.request.Request(DAEMON, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())


def _harvest(detail):
    """Robustly pull tweet records out of whatever shape a network 'detail' returns.

    Walks the structure AND json.loads any embedded JSON-string body, then runs the
    schema-robust xparse.extract over each."""
    recs = {}

    def consider(o):
        for r in xparse.extract(o):
            recs[r["tweet_id"]] = r

    def scan(o):
        if isinstance(o, str):
            s = o.lstrip()
            if len(s) > 200 and s.startswith("{") and ("rest_id" in s or "tweet_results" in s):
                try:
                    consider(json.loads(s))
                except Exception:
                    pass
        elif isinstance(o, dict):
            for v in o.values():
                scan(v)
        elif isinstance(o, list):
            for v in o:
                scan(v)

    consider(detail)   # body may already be a parsed dict
    scan(detail)       # or a JSON string nested somewhere
    return list(recs.values())


def _req_id(entry):
    for k in ("requestId", "request_id", "id", "rid"):
        if isinstance(entry, dict) and entry.get(k):
            return entry[k]
    return None


def _matching_ids(listing):
    ids = []

    def walk(o):
        if isinstance(o, dict):
            url = str(o.get("url") or o.get("request_url") or "")
            if any(op in url for op in TIMELINE_OPS):
                rid = _req_id(o)
                if rid:
                    ids.append(rid)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(listing)
    return list(dict.fromkeys(ids))


def capture(con, handle, scrolls, wait, session, probe=False):
    print("== @%s ==" % handle, flush=True)
    cmd("navigate", {"url": "https://x.com/%s" % handle, "newTab": False}, session)
    time.sleep(4)
    cmd("network", {"cmd": "start", "filter": "Timeline"}, session)
    for i in range(scrolls):
        cmd("evaluate", {"code": "window.scrollBy(0, document.body.scrollHeight); 'ok'"}, session)
        time.sleep(wait)
    listing = cmd("network", {"cmd": "list"}, session)
    ids = _matching_ids(listing)
    print("  captured %d timeline requests" % len(ids))
    if probe:
        first = cmd("network", {"cmd": "detail", "requestId": ids[0]}, session) if ids else None
        p = os.path.join(HERE, "probe_%s.json" % handle)
        open(p, "w").write(json.dumps({"list": listing, "first_detail": first}, indent=2)[:2_000_000])
        print("  wrote probe -> %s (inspect to confirm field paths)" % p)
        return
    recs = {}
    for rid in ids:
        d = cmd("network", {"cmd": "detail", "requestId": rid}, session)
        for r in _harvest(d):
            r["author"] = r.get("author") or handle
            recs[r["tweet_id"]] = xparse.enrich(r)
    cmd("network", {"cmd": "stop"}, session)
    rows = list(recs.values())
    new = xstore.upsert(con, rows)
    if rows:
        xstore.set_watermark(con, handle, max(rows, key=lambda r: r["tweet_id"])["tweet_id"])
    print("  parsed %d tweets, %d new -> DB" % (len(rows), new))


def from_file(con, path):
    obj = json.load(open(path))
    rows = [xparse.enrich(r) for r in xparse.extract(obj)]
    new = xstore.upsert(con, rows)
    print("parsed %d tweets from %s, %d new" % (len(rows), path, new))


def selftest():
    sample = {"data": {"user": {"result": {"timeline_v2": {"timeline": {"instructions": [{
        "type": "TimelineAddEntries", "entries": [{"content": {"itemContent": {"tweet_results": {"result": {
            "__typename": "Tweet", "rest_id": "1900000000000000001",
            "core": {"user_results": {"result": {"legacy": {"screen_name": "TraderX"}}}},
            "legacy": {"full_text": "NQ short from premium, target the sellside liquidity. +2R banked.",
                       "created_at": "Wed Jun 11 13:30:00 +0000 2026", "favorite_count": 42,
                       "retweet_count": 5, "reply_count": 3, "quote_count": 1, "lang": "en",
                       "entities": {"urls": [{"expanded_url": "https://example.com/chart"}]}}}}}}}]}]}}}}}}
    recs = [xparse.enrich(r) for r in xparse.extract(sample)]
    assert len(recs) == 1, "expected 1 tweet"
    r = recs[0]
    assert r["author"] == "TraderX" and r["instrument"] == "nq" and r["direction"] == "bear" \
        and r["outcome"] == "win", r
    print("SELFTEST OK ->", {k: r[k] for k in ("author", "created_at", "instrument", "direction", "outcome", "likes")})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handles", help="comma-separated X handles (no @)")
    ap.add_argument("--probe", metavar="HANDLE")
    ap.add_argument("--from-file", dest="from_file")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--scrolls", type=int, default=25)
    ap.add_argument("--wait", type=float, default=2.5)
    ap.add_argument("--session", default="x")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    con = xstore.connect(a.db)
    if a.from_file:
        return from_file(con, a.from_file)
    if a.probe:
        return capture(con, a.probe, a.scrolls, a.wait, a.session, probe=True)
    if a.handles:
        for h in [x.strip().lstrip("@") for x in a.handles.split(",") if x.strip()]:
            capture(con, h, a.scrolls, a.wait, a.session)
        n, _ = xstore.stats(con)
        print("\nDB now holds %d posts (%s)" % (n, a.db))
        return
    ap.print_help()


if __name__ == "__main__":
    sys.exit(main())
