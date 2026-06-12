#!/usr/bin/env python3
"""SQLite store for scraped X posts -- incremental, dedup, correlation-ready.

One row per tweet (PK = tweet_id), plus a per-author watermark so re-runs only
ingest new posts. Designed for the correlation pass in xcorr.py.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import os
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts(
  tweet_id   TEXT PRIMARY KEY,
  author     TEXT,
  created_at TEXT,        -- ISO8601 UTC
  text       TEXT,
  likes      INTEGER, retweets INTEGER, replies INTEGER, quotes INTEGER,
  is_retweet INTEGER, is_reply INTEGER,
  urls       TEXT,        -- space-joined expanded urls
  lang       TEXT,
  instrument TEXT, direction TEXT, outcome TEXT,   -- parsed by xparse.classify
  raw_json   TEXT,
  fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_author_time ON posts(author, created_at);
CREATE INDEX IF NOT EXISTS idx_instr ON posts(instrument);
CREATE TABLE IF NOT EXISTS watermark(
  author TEXT PRIMARY KEY, last_seen_id TEXT, updated_at TEXT
);
"""

COLS = ["tweet_id", "author", "created_at", "text", "likes", "retweets", "replies",
        "quotes", "is_retweet", "is_reply", "urls", "lang", "instrument",
        "direction", "outcome", "raw_json", "fetched_at"]


def connect(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def upsert(con, rows):
    """INSERT OR IGNORE rows (list of dicts). Returns count of NEW rows."""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    before = con.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    q = "INSERT OR IGNORE INTO posts(%s) VALUES (%s)" % (",".join(COLS), ",".join("?" * len(COLS)))
    for r in rows:
        r.setdefault("fetched_at", now)
        con.execute(q, [r.get(c) for c in COLS])
    con.commit()
    return con.execute("SELECT COUNT(*) FROM posts").fetchone()[0] - before


def set_watermark(con, author, last_id):
    con.execute("INSERT OR REPLACE INTO watermark(author,last_seen_id,updated_at) VALUES (?,?,?)",
                (author, last_id, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    con.commit()


def get_watermark(con, author):
    r = con.execute("SELECT last_seen_id FROM watermark WHERE author=?", (author,)).fetchone()
    return r[0] if r else None


def stats(con):
    n = con.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    by = con.execute("SELECT author, COUNT(*), MIN(created_at), MAX(created_at) "
                     "FROM posts GROUP BY author ORDER BY 2 DESC").fetchall()
    return n, by


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "posts.db")
    con = connect(path)
    n, by = stats(con)
    print("DB %s: %d posts" % (path, n))
    for a, c, lo, hi in by:
        print("  %-20s %5d  %s .. %s" % (a, c, lo, hi))
