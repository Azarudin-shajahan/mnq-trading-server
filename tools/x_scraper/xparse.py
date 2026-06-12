#!/usr/bin/env python3
"""Parse X GraphQL JSON -> tweet records, and classify trading text.

extract(obj): walk ANY X GraphQL payload (UserTweets / search / a captured network
response) and yield one record per tweet. Deliberately schema-ROBUST: it finds tweet
objects anywhere in the tree (a dict with rest_id + legacy.full_text) rather than
hard-coding the instructions->entries path, which X changes often.

classify(text): regex extraction of instrument / direction / outcome -- mirrors the
columns in data/gxt_execution_posts.csv so scraped posts slot into the same analysis.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import datetime as dt
import re

# ---- tweet extraction ----------------------------------------------------------

def _iso(twitter_ts):
    # X legacy created_at: "Wed Jun 11 01:15:00 +0000 2026"
    try:
        return dt.datetime.strptime(twitter_ts, "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return twitter_ts or ""


def _screen_name(node):
    # author screen_name lives under core.user_results.result.{legacy|core}.screen_name (varies)
    try:
        u = node["core"]["user_results"]["result"]
        return (u.get("legacy") or {}).get("screen_name") or (u.get("core") or {}).get("screen_name")
    except Exception:
        return None


def _one(node):
    """node is a tweet 'result' dict (has rest_id + legacy). Return a record or None."""
    lg = node.get("legacy") or {}
    tid = node.get("rest_id") or lg.get("id_str")
    text = lg.get("full_text")
    if not tid or text is None:
        return None
    urls = [u.get("expanded_url") for u in (lg.get("entities", {}).get("urls") or []) if u.get("expanded_url")]
    is_rt = 1 if ("retweeted_status_result" in lg or text.startswith("RT @")) else 0
    return {
        "tweet_id": str(tid),
        "author": _screen_name(node),
        "created_at": _iso(lg.get("created_at")),
        "text": text,
        "likes": lg.get("favorite_count"), "retweets": lg.get("retweet_count"),
        "replies": lg.get("reply_count"), "quotes": lg.get("quote_count"),
        "is_retweet": is_rt, "is_reply": 1 if lg.get("in_reply_to_status_id_str") else 0,
        "urls": " ".join(urls), "lang": lg.get("lang"),
    }


def extract(obj):
    """Walk any JSON; return de-duped list of tweet records."""
    found = {}

    def walk(o):
        if isinstance(o, dict):
            if ("rest_id" in o and isinstance(o.get("legacy"), dict)) or o.get("__typename") == "Tweet":
                node = o.get("tweet") if isinstance(o.get("tweet"), dict) else o
                rec = _one(node)
                if rec:
                    found[rec["tweet_id"]] = rec
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return list(found.values())


# ---- trading-signal classification (mirrors gxt_execution_posts.csv) -----------

_INSTR = {
    "nq": ["nq", "nasdaq"], "es": ["es ", "s&p", "spx", "spy", "e-mini s&p"],
    "ym": ["ym", "dow", "us30"], "rty": ["rty", "russell", "rut"],
    "gc": ["gc", "gold", "xau", "mgc"], "cl": ["cl", "crude", "oil", "wti"],
    "btc": ["btc", "bitcoin"], "eur": ["eurusd", "fiber", "6e"],
    "gbp": ["gbpusd", "cable", "6b"], "dxy": ["dxy", "dollar index"],
}
_LONG = re.compile(r"\b(long|buy|buys|bought|bull|bullish|calls?)\b", re.I)
_SHORT = re.compile(r"\b(short|sell|sells|sold|bear|bearish|puts?)\b", re.I)
_OUT = [("win", r"\b(win|won|target|tp hit|banked|runner|\+\d+\s*r|green|profit)\b"),
        ("loss", r"\b(loss|stopped|stop hit|red|-\d+\s*r|chopped)\b"),
        ("be", r"\b(break ?even|be |scratch|flat)\b")]


def classify(text):
    t = (text or "").lower()
    instrument = next((k for k, kws in _INSTR.items() if any(w in t for w in kws)), None)
    has_l, has_s = bool(_LONG.search(t)), bool(_SHORT.search(t))
    direction = "bull" if has_l and not has_s else "bear" if has_s and not has_l else None
    outcome = next((o for o, pat in _OUT if re.search(pat, t)), None)
    return instrument, direction, outcome


def enrich(rec):
    rec["instrument"], rec["direction"], rec["outcome"] = classify(rec.get("text"))
    return rec
