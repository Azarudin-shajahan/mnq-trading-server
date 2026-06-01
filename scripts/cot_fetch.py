#!/usr/bin/env python3
"""Fetch CFTC Commitment of Traders (legacy, futures-only) for the index futures
and compute the COT index ICT teaches (Month 10 - Commitment Of Traders).

Source: https://www.cftc.gov/files/dea/history/deacot{YEAR}.zip  (free, no auth,
no Cloudflare). Each zip holds annual.txt = all markets, weekly (Tuesday) rows.
ICT watches COMMERCIALS only (smart money): net = commercial_long - commercial_short,
then the 6-month (26wk) and 12-month (52wk) range position of that net.

Output: ~/mnq_trading/data/cot_index_2020_2025.csv
Columns: date, symbol, market_name, open_interest, comm_long, comm_short,
         comm_net, cot_index_26w, cot_index_52w, zero_line, bias
  - date: weekly report (Tuesday) YYYY-MM-DD
  - comm_net: commercial_long - commercial_short (+ = net long, - = net short)
  - cot_index_Nw: 100*(net - min_N)/(max_N - min_N) over trailing N weeks (0..100)
  - zero_line: 'buy' if comm_net>0 else 'sell' (ICT buy/sell program)
  - bias: bull if cot_index_52w>=80, bear if <=20, else neutral (ICT extreme read)
Model 9 reads this as its weekly-bias gate (align with the 20-week draw-on-liquidity).

Legacy futures-only column indices used: 0 market, 2 date(YYYY-MM-DD),
7 open-interest, 11 commercial-long, 12 commercial-short.
"""
import csv
import io
import urllib.request
import zipfile
from pathlib import Path

YEARS = range(2020, 2026)
URL = "https://www.cftc.gov/files/dea/history/deacot{}.zip"
OUT = Path.home() / "mnq_trading/data/cot_index_2020_2025.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# symbol -> (primary market-name match, exclude substring or None)
# Consolidated series = all contract sizes combined = fullest commercial read.
MARKETS = {
    "ES":  ("S&P 500 CONSOLIDATED", None),
    "NQ":  ("NASDAQ-100 CONSOLIDATED", None),
    "YM":  ("DJIA CONSOLIDATED", None),
    "RTY": ("RUSSELL E-MINI", "1000"),     # Russell 2000 e-mini; exclude RUSSELL 1000 VALUE
}


def download_year(year):
    req = urllib.request.Request(URL.format(year), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        blob = r.read()
    zf = zipfile.ZipFile(io.BytesIO(blob))
    name = [n for n in zf.namelist() if n.endswith(".txt")][0]
    return zf.read(name).decode("utf-8", "ignore")


def match_symbol(market_name):
    up = market_name.upper()
    for sym, (pat, excl) in MARKETS.items():
        if pat in up and (excl is None or excl not in up):
            return sym
    return None


def cot_index(series, i, n):
    """100*(x - min)/(max - min) over the trailing n values ending at i."""
    window = series[max(0, i - n + 1): i + 1]
    lo, hi = min(window), max(window)
    if hi == lo:
        return ""
    return round(100.0 * (series[i] - lo) / (hi - lo), 1)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # symbol -> list of (date, market_name, oi, cl, cs)
    raw = {s: [] for s in MARKETS}
    for year in YEARS:
        try:
            text = download_year(year)
        except Exception as ex:
            print(f"WARN {year}: {ex}")
            continue
        rows = list(csv.reader(io.StringIO(text)))
        cnt = 0
        for r in rows[1:]:
            if len(r) < 13:
                continue
            sym = match_symbol(r[0])
            if not sym:
                continue
            try:
                date = r[2]
                oi = int(r[7]); cl = int(r[11]); cs = int(r[12])
            except ValueError:
                continue
            raw[sym].append((date, r[0].strip(), oi, cl, cs))
            cnt += 1
        print(f"{year}: +{cnt} index rows")

    out_rows = []
    for sym, recs in raw.items():
        recs.sort()  # by date
        nets = [cl - cs for (_, _, _, cl, cs) in recs]
        for i, (date, mkt, oi, cl, cs) in enumerate(recs):
            net = nets[i]
            i26 = cot_index(nets, i, 26)
            i52 = cot_index(nets, i, 52)
            bias = "neutral"
            if i52 != "":
                bias = "bull" if i52 >= 80 else "bear" if i52 <= 20 else "neutral"
            out_rows.append({
                "date": date, "symbol": sym, "market_name": mkt,
                "open_interest": oi, "comm_long": cl, "comm_short": cs,
                "comm_net": net, "cot_index_26w": i26, "cot_index_52w": i52,
                "zero_line": "buy" if net > 0 else "sell", "bias": bias,
            })
    out_rows.sort(key=lambda r: (r["date"], r["symbol"]))
    cols = ["date", "symbol", "market_name", "open_interest", "comm_long",
            "comm_short", "comm_net", "cot_index_26w", "cot_index_52w",
            "zero_line", "bias"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nwrote {len(out_rows)} rows -> {OUT}")
    for sym in MARKETS:
        n = sum(1 for r in out_rows if r["symbol"] == sym)
        last = [r for r in out_rows if r["symbol"] == sym]
        tail = last[-1] if last else None
        if tail:
            print(f"  {sym}: {n} weeks | latest {tail['date']} net={tail['comm_net']:+} "
                  f"COT52={tail['cot_index_52w']} bias={tail['bias']}")


if __name__ == "__main__":
    main()
