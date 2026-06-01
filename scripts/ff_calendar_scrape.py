#!/usr/bin/env python3
"""Scrape the full ForexFactory historical economic calendar via Kimi WebBridge.

FF is Cloudflare-protected (direct curl -> 403), so we drive the user's
logged-in Chrome through the WebBridge daemon (127.0.0.1:10086). FF embeds all
calendar data in window.calendarComponentStates -- we read that JS object
directly (reliable; no DOM scraping).

Covers 2020-01 .. 2025-12 (one navigate per week, ~313 weeks). Resumable:
weeks already present in the CSV are skipped. Saves incrementally every week so
a crash loses at most one week. Run with: /usr/local/bin/python3 -u ff_calendar_scrape.py

Output: ~/mnq_trading/data/ff_calendar_2020_2025.csv
Columns: id, dateline_unix, date_ff, time_ff, currency, impact, name,
         actual, forecast, previous, better_worse
  - dateline_unix: epoch seconds (UTC) of the release -- TZ-proof source of truth
  - impact: low | medium | high | holiday | (blank)
  - better_worse: -1 worse / 0 inline / +1 better than forecast (FF actualBetterWorse)
This is the superset the Model 9 news gate reads (filter impact==high & currency==USD).
"""
import csv
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

WB = "http://127.0.0.1:10086/command"
SESSION = "ff-scrape"
OUT = Path.home() / "mnq_trading/data/ff_calendar_2020_2025.csv"
COLS = ["id", "dateline_unix", "date_ff", "time_ff", "currency", "impact",
        "name", "actual", "forecast", "previous", "better_worse"]
START = dt.date(2019, 12, 30)   # Monday covering the first 2020 week
END = dt.date(2025, 12, 29)
MON = ["jan", "feb", "mar", "apr", "may", "jun",
       "jul", "aug", "sep", "oct", "nov", "dec"]

EXTRACT_JS = """(()=>{ const s=window.calendarComponentStates; if(!s) return {ok:false};
  const st=s[1]||s[Object.keys(s)[0]]; const days=(st&&st.days)||[]; const out=[];
  days.forEach(d=>{(d.events||[]).forEach(e=>out.push({
    id:e.id, dateline:e.dateline, date:e.date, time:e.timeLabel, currency:e.currency,
    impact:e.impactName, name:e.name, actual:e.actual, forecast:e.forecast,
    previous:e.previous, bw:e.actualBetterWorse}));});
  return {ok:true, n:out.length, ev:out}; })()"""


def wb(action, args):
    body = json.dumps({"action": action, "args": args, "session": SESSION}).encode()
    req = urllib.request.Request(WB, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def week_anchor(d: dt.date) -> str:
    return f"{MON[d.month - 1]}{d.day}.{d.year}"


def fetch_week(anchor: str, first: bool):
    url = f"https://www.forexfactory.com/calendar?week={anchor}"
    wb("navigate", {"url": url, "newTab": first, "group_title": "FF-scrape"})
    # poll until the JS calendar state is populated
    for _ in range(12):
        time.sleep(1.5)
        res = wb("evaluate", {"code": EXTRACT_JS})
        val = res.get("data", {}).get("value") or {}
        if val.get("ok") and val.get("n", 0) > 0:
            return val["ev"]
    return []


def load_existing():
    rows, weeks = {}, set()
    if OUT.exists():
        with open(OUT, newline="") as f:
            for r in csv.DictReader(f):
                rows[r["id"]] = r
                if r["dateline_unix"]:
                    wk = dt.datetime.utcfromtimestamp(int(r["dateline_unix"])).date()
                    weeks.add(wk - dt.timedelta(days=wk.weekday()))  # that row's Monday
    return rows, weeks


def save(rows):
    out = sorted(rows.values(), key=lambda r: int(r["dateline_unix"] or 0))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows, done_weeks = load_existing()
    print(f"resuming: {len(rows)} events, {len(done_weeks)} weeks already scraped")
    d = START
    first = not OUT.exists()
    n_weeks = 0
    while d <= END:
        if d in done_weeks:
            d += dt.timedelta(days=7)
            continue
        anchor = week_anchor(d)
        try:
            evs = fetch_week(anchor, first)
            first = False
        except Exception as ex:
            print(f"  {anchor}: ERROR {ex} -- retrying once")
            time.sleep(5)
            try:
                evs = fetch_week(anchor, False)
            except Exception as ex2:
                print(f"  {anchor}: FAILED {ex2}")
                d += dt.timedelta(days=7)
                continue
        added = 0
        for e in evs:
            if not e.get("id"):
                continue
            key = str(e["id"])
            if key not in rows:
                added += 1
            rows[key] = {
                "id": key, "dateline_unix": e.get("dateline", ""),
                "date_ff": e.get("date", ""), "time_ff": e.get("time", ""),
                "currency": e.get("currency", ""), "impact": e.get("impact", ""),
                "name": e.get("name", ""), "actual": e.get("actual", ""),
                "forecast": e.get("forecast", ""), "previous": e.get("previous", ""),
                "better_worse": e.get("bw", ""),
            }
        save(rows)
        n_weeks += 1
        hi = sum(1 for r in rows.values() if r["impact"] == "high" and r["currency"] == "USD")
        print(f"  {anchor}: +{added} ({len(evs)} evs) | total {len(rows)} | High-USD {hi}", flush=True)
        d += dt.timedelta(days=7)
        time.sleep(1.0)  # be polite
    print(f"DONE. {n_weeks} weeks this run. total events: {len(rows)} -> {OUT}")


if __name__ == "__main__":
    main()
