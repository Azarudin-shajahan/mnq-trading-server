# x_scraper — pull trading X feeds into SQLite for correlation

Capture certain traders' X feeds via your **logged-in WebBridge session** (no API cost,
no extra account), store in SQLite, classify each post (instrument/direction/outcome),
and correlate. Mirrors the `data/gxt_execution_posts.csv` schema so scraped posts slot
into the same analysis.

## Technique
Instead of scraping rendered HTML, capture the X web app's internal **GraphQL
`UserTweets` JSON** while auto-scrolling each profile — structured, all fields, robust to
CSS changes. `xcap.py` drives the Kimi WebBridge daemon (`127.0.0.1:10086`, session `x`).

## Pieces
- `xstore.py` — SQLite store (`posts` table + per-author watermark). Run it to print stats.
- `xparse.py` — schema-robust tweet extractor + `classify()` (instrument/direction/outcome).
- `xcap.py` — the capture driver / CLI.
- `xcorr.py` — author×author daily-direction correlation (+ optional vs price CSV).

## Use
```bash
# 0. WebBridge healthy + logged into X in its window:
~/.kimi-webbridge/bin/kimi-webbridge status

# 1. (one time) probe one handle to confirm the daemon's network field paths:
python3 xcap.py --probe SomeTrader            # writes probe_SomeTrader.json — inspect it
#    if no tweets parse, open the probe JSON and adjust _matching_ids/_harvest in xcap.py.

# 2. capture feeds (re-run anytime; dedups, only new posts ingested):
python3 xcap.py --handles TraderA,TraderB,TraderC --scrolls 30

# 3. correlate:
python3 xcorr.py                              # author x author, all instruments
python3 xcorr.py --instrument nq --price ../../data/nq_daily.csv   # vs next-day NQ return

# offline checks (no live X):
python3 xcap.py --selftest                    # parser+classifier on a synthetic tweet
python3 xcap.py --from-file probe_SomeTrader.json   # parse a saved capture into the DB
python3 xstore.py posts.db                    # DB stats
```

## Caveats / reality
- **History cap:** X serves only ~**3200 most-recent** tweets per profile timeline. For
  deeper history, page X **search** (`from:user since:.. until:..`) — same capture
  technique on the SearchTimeline op (TIMELINE_OPS already includes it). Or just re-run
  on a schedule to **accumulate forward** (usually what correlation needs).
- **ToS / rate:** scraping is against X ToS. Keep `--wait` >= 2.5s, modest `--scrolls`,
  your own login. Don't hammer it.
- **Schema drift:** X changes GraphQL shapes often. The parser is intentionally tolerant
  (finds tweets anywhere with `rest_id`+`legacy.full_text`); `--probe` + `--from-file`
  let you validate/fix without re-capturing.
- **Classification is regex** (cheap). For better instrument/direction/outcome extraction
  at scale, swap `xparse.classify` for a local model (e.g. Gemma 4 E4B) or qmd.
- `posts.db` and `probe_*.json` are gitignored (data, not code).

## Status
SCAFFOLD. Parser + store + correlation are self-tested (`xcap.py --selftest`). The live
network-capture glue (`_matching_ids` / `_harvest`) is structured + probe-able but must be
confirmed against the real daemon `network detail` shape on first `--probe` run.
