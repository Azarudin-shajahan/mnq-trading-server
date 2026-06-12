#!/usr/bin/env python3
"""xcorr -- correlation pass over the scraped X posts.

Builds, per author, a daily DIRECTION signal (net bull/bear: +1 per bull post, -1 per
bear post, summed per UTC day) for a chosen instrument (or all), then:
  - author x author correlation matrix (do these traders call the same way same day?),
  - optional vs a daily price series (--price date,close CSV) -> do calls lead returns?

This is the "correlation check" the scrape was for. Extend freely (lead-lag, sentiment,
vs your own engine signals by joining a trade log on date).

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import os

import pandas as pd

import xstore

HERE = os.path.dirname(os.path.abspath(__file__))


def daily_direction(con, instrument=None):
    q = "SELECT author, substr(created_at,1,10) d, direction FROM posts WHERE direction IS NOT NULL"
    p = []
    if instrument:
        q += " AND instrument=?"; p = [instrument]
    df = pd.read_sql_query(q, con, params=p)
    if df.empty:
        return pd.DataFrame()
    df["sig"] = df["direction"].map({"bull": 1, "bear": -1}).fillna(0)
    piv = df.pivot_table(index="d", columns="author", values="sig", aggfunc="sum").sort_index()
    return piv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(HERE, "posts.db"))
    ap.add_argument("--instrument", help="filter to one instrument (nq/es/gc/...)")
    ap.add_argument("--price", help="daily price CSV with columns date,close (for lead-lag)")
    ap.add_argument("--min-days", type=int, default=10, help="min overlapping days to report a pair")
    a = ap.parse_args()
    con = xstore.connect(a.db)

    n, by = xstore.stats(con)
    print("posts: %d | authors: %d%s" % (n, len(by), (" | instrument=%s" % a.instrument) if a.instrument else ""))
    piv = daily_direction(con, a.instrument)
    if piv.empty or piv.shape[1] < 1:
        print("no classified directional posts yet -- scrape some feeds first (xcap.py --handles ...)")
        return

    print("\n=== author x author daily-direction correlation ===")
    corr = piv.corr(min_periods=a.min_days)
    print(corr.round(2).to_string())

    if a.price:
        px = pd.read_csv(a.price)
        px.columns = [c.lower() for c in px.columns]
        px["date"] = pd.to_datetime(px["date"]).dt.strftime("%Y-%m-%d")
        px = px.set_index("date").sort_index()
        ret = px["close"].astype(float).pct_change()
        print("\n=== author signal vs NEXT-day price return (does the call lead?) ===")
        nxt = ret.shift(-1)
        for au in piv.columns:
            s = piv[au].reindex(ret.index)
            both = pd.concat([s, nxt], axis=1).dropna()
            if len(both) >= a.min_days:
                print("  %-20s corr(signal, next-day return) = %.3f  (n=%d days)"
                      % (au, both.iloc[:, 0].corr(both.iloc[:, 1]), len(both)))


if __name__ == "__main__":
    main()
