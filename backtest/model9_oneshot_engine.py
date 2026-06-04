#!/usr/bin/env python3
"""ICT Charter Model 9 - One Shot One Kill - NQ backtest engine.

Grounded from Research/ICT_Model9_OneShotOneKill_Spec.md (all 3 transcripts).
Separate engine from the v8.x FVG-reversal family.

Model: weekly-range-expansion bias (+ COT confirm/veto) -> on Mon-Wed, in a
killzone, an internal-range FVG entry at consequent encroachment (midpoint) in
the bias direction -> target the opposite (external) liquidity pool (the weekly
draw) -> SL beyond the FVG far side. Optional external->internal (turtle-soup)
polarity. News gate (FF high-impact USD day) optional.

Every component is a TOGGLE so the backtest measures each one's contribution
(same method as the GxT levers). Run a single config or the full sweep.

Run:  /usr/local/bin/python3 backtest/model9_oneshot_engine.py            # sweep
      /usr/local/bin/python3 backtest/model9_oneshot_engine.py --single   # one cfg
Assumptions / simplifications (v1, documented):
  - intraday entries + simulation on 5m NQ; FVGs on 4h NQ.
  - killzones in IST (approx, DST not adjusted): London 12:30-15:00, NY 17:30-20:30.
  - external target = prior-week high/low (the weekly draw); fallback prior-20d extreme.
  - SL = FVG far side +/- buffer. One position per day, first valid killzone entry.
  - point value: backtest uses raw NQ points (P&L reported in points; sizing later).
"""
import argparse
import itertools
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path.home() / "mnq_trading/data"
DAILY = DATA / "MULTI_1d_IST_2020_2025.csv"
H4 = DATA / "MULTI_4h_IST_2020_2025.csv"
M5 = DATA / "MULTI_5min_IST_2020_2025.csv"
COT = DATA / "cot_index_2020_2025.csv"
FFCAL = DATA / "ff_calendar_2020_2025.csv"

# killzones in IST (minutes from midnight)
LONDON_KZ = (12 * 60 + 30, 15 * 60)       # 12:30-15:00
NY_KZ = (17 * 60 + 30, 20 * 60 + 30)      # 17:30-20:30
SL_BUF = 2.0   # NQ points beyond FVG far side


# ── DATA ──────────────────────────────────────────────────────────────────────
def _load(path, inst="nq"):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    cols = {f"{inst}_{k}": k for k in ("open", "high", "low", "close")}
    d = df[["timestamp", *cols]].rename(columns=cols).dropna().sort_values("timestamp")
    d["date"] = d["timestamp"].dt.normalize()
    d["mins"] = d["timestamp"].dt.hour * 60 + d["timestamp"].dt.minute
    d["dow"] = d["timestamp"].dt.dayofweek
    return d.reset_index(drop=True)


def load_daily(inst="nq"):
    df = pd.read_csv(DAILY, parse_dates=["timestamp"])
    cols = {f"{inst}_{k}": k for k in ("open", "high", "low", "close")}
    if all(c in df.columns for c in cols):
        return df[["timestamp", *cols]].rename(columns=cols).dropna().set_index("timestamp").sort_index()
    # fallback: instrument absent from the 1d file (e.g. RTY) -> resample from 4h
    h4 = _load(H4, inst)
    d = h4.groupby("date").agg(open=("open", "first"), high=("high", "max"),
                               low=("low", "min"), close=("close", "last"))
    d.index.name = "timestamp"
    return d.sort_index()


def resample_weekly(daily):
    w = daily.resample("W-SUN").agg(open=("open", "first"), high=("high", "max"),
                                    low=("low", "min"), close=("close", "last")).dropna()
    w.index = w.index - pd.Timedelta(days=6)
    return w


# ── WEEKLY BIAS (no lookahead) ───────────────────────────────────────────────
def weekly_price_bias(weekly):
    o, h, l, c = weekly["open"], weekly["high"], weekly["low"], weekly["close"]
    up = (c > o) & (h > h.shift(1))
    dn = (c < o) & (l < l.shift(1))
    bias = pd.Series("neutral", index=weekly.index)
    bias[up] = "bull"; bias[dn] = "bear"
    bias = bias.shift(1)
    bias.index = weekly.index
    return bias.fillna("neutral")


def load_cot_bias(inst="NQ"):
    c = pd.read_csv(COT, parse_dates=["date"])
    c = c[c["symbol"] == inst].sort_values("date")
    return c[["date", "cot_index_52w", "bias"]].reset_index(drop=True)


def align_cot(week_starts, cot):
    cot = cot.sort_values("date")
    ws = pd.DataFrame({"week_start": pd.to_datetime(week_starts)}).sort_values("week_start")
    m = pd.merge_asof(ws, cot, left_on="week_start", right_on="date",
                      direction="backward", allow_exact_matches=False)
    return m.set_index("week_start")[["bias"]].rename(columns={"bias": "cot_bias"})


def build_weekly_bias(cot_mode="veto", inst="nq"):
    """cot_mode: off | confirm | veto. Returns dict week_start(Monday date) -> bias."""
    weekly = resample_weekly(load_daily(inst))
    pbias = weekly_price_bias(weekly)
    cot = align_cot(weekly.index, load_cot_bias(inst.upper()))["cot_bias"]
    out = {}
    for ws in weekly.index:
        pb = pbias[ws]; cb = cot.get(ws, "neutral")
        if cot_mode == "off":
            b = pb
        elif pb == "neutral":
            b = cb if cot_mode != "off" else pb
        elif cb == "neutral" or cb == pb:
            b = pb
        else:  # contradict
            b = "neutral" if cot_mode == "veto" else pb  # confirm-only ignores veto
        out[ws.normalize()] = b
    return weekly, out


# ── LIQUIDITY MAPS ───────────────────────────────────────────────────────────
def detect_4h_fvgs(df4h):
    """3-candle FVG list: (formed_ts, dir, top, bot, ce). bull gap = h[i-1]<l[i+1]."""
    h = df4h["high"].values; l = df4h["low"].values; ts = df4h["timestamp"].values
    out = []
    for i in range(1, len(df4h) - 1):
        if h[i - 1] < l[i + 1]:                      # bullish FVG
            top, bot = l[i + 1], h[i - 1]
            out.append((ts[i + 1], "bull", top, bot, (top + bot) / 2))
        elif l[i - 1] > h[i + 1]:                    # bearish FVG
            top, bot = l[i - 1], h[i + 1]
            out.append((ts[i + 1], "bear", top, bot, (top + bot) / 2))
    return pd.DataFrame(out, columns=["formed", "dir", "top", "bot", "ce"])


def weekly_draw(weekly, week_start, direction):
    """External target = prior completed week's high (bull) / low (bear)."""
    idx = weekly.index.get_indexer([pd.Timestamp(week_start)])
    i = idx[0]
    if i <= 0:
        return None
    prev = weekly.iloc[i - 1]
    return prev["high"] if direction == "bull" else prev["low"]


# ── BACKTEST ─────────────────────────────────────────────────────────────────
def load_news_days():
    df = pd.read_csv(FFCAL)
    hi = df[(df["impact"] == "high") & (df["currency"] == "USD")].copy()
    days = pd.to_datetime(hi["dateline_unix"], unit="s").dt.normalize()
    return set(days.unique())


def in_kz(mins, cfg):
    if cfg["kz"] == "ny":
        return NY_KZ[0] <= mins <= NY_KZ[1]
    return (LONDON_KZ[0] <= mins <= LONDON_KZ[1]) or (NY_KZ[0] <= mins <= NY_KZ[1])


def walk_to_friday(future_days, entry, sl, tp, direction):
    """Walk 5m bars across the rest of the week (entry day from entry_idx, then later
    days to Friday). One Shot One Kill HOLDS toward the weekly draw. -> win/loss/be."""
    for day5m in future_days:
        hi = day5m["high"].values; lo = day5m["low"].values
        for j in range(len(day5m)):
            if direction == "bull":
                if lo[j] <= sl:
                    return "loss", sl - entry
                if hi[j] >= tp:
                    return "win", tp - entry
            else:
                if hi[j] >= sl:
                    return "loss", entry - sl
                if lo[j] <= tp:
                    return "win", entry - tp
    last = future_days[-1]["close"].values[-1]
    return "be", (last - entry) if direction == "bull" else (entry - last)


def find_alt_entry(cfg, bias, mins, hi, lo, cl, pdl, pdh, min_imp=20.0):
    """Non-FVG entries. Returns (k, entry, sl) or None.
    ote: 70.5% retrace of the killzone impulse leg (displacement then sweet-spot).
    turtle: external->internal — failed sweep of prior-day pool, reclaim, enter.
    NOTE: fixed-point thresholds (min_imp, SL_BUF) validated better than %-of-price
    scaling WITHIN an instrument (see 2024-25 fade investigation). ACROSS instruments
    they are scaled once to each instrument's price level (min_imp, buf via cfg)."""
    n = len(mins)
    buf = cfg.get("sl_buf", SL_BUF)
    if cfg["entry"] == "ote":
        if bias == "bull":
            lo_px = None; hi_px = None; hi_i = -1
            for k in range(n):
                if not in_kz(mins[k], cfg):
                    continue
                if lo_px is None or lo[k] < lo_px:
                    lo_px = lo[k]; hi_px = None; hi_i = -1   # new low resets the leg
                if lo_px is not None and (hi_px is None or hi[k] > hi_px):
                    hi_px = hi[k]; hi_i = k
                if hi_px is not None and hi_px - lo_px >= min_imp and k > hi_i:
                    ote = hi_px - 0.705 * (hi_px - lo_px)
                    if lo[k] <= ote:
                        return k, ote, lo_px - buf
        else:
            hi_px = None; lo_px = None; lo_i = -1
            for k in range(n):
                if not in_kz(mins[k], cfg):
                    continue
                if hi_px is None or hi[k] > hi_px:
                    hi_px = hi[k]; lo_px = None; lo_i = -1
                if hi_px is not None and (lo_px is None or lo[k] < lo_px):
                    lo_px = lo[k]; lo_i = k
                if lo_px is not None and hi_px - lo_px >= min_imp and k > lo_i:
                    ote = lo_px + 0.705 * (hi_px - lo_px)
                    if hi[k] >= ote:
                        return k, ote, hi_px + buf
        return None
    if cfg["entry"] == "turtle":
        if pdl is None or pdh is None:
            return None
        if bias == "bull":
            swept = False; sweep_lo = None
            for k in range(n):
                if not in_kz(mins[k], cfg):
                    continue
                if lo[k] < pdl:
                    swept = True; sweep_lo = lo[k] if sweep_lo is None else min(sweep_lo, lo[k])
                if swept and cl[k] > pdl:                 # reclaim
                    return k, cl[k], sweep_lo - buf
        else:
            swept = False; sweep_hi = None
            for k in range(n):
                if not in_kz(mins[k], cfg):
                    continue
                if hi[k] > pdh:
                    swept = True; sweep_hi = hi[k] if sweep_hi is None else max(sweep_hi, hi[k])
                if swept and cl[k] < pdh:
                    return k, cl[k], sweep_hi + buf
        return None
    return None


def _target(cfg, weekly, ws, bias, entry, sl):
    """TP per tp_mode: weekly draw, or a fixed R multiple of risk."""
    if cfg["tp"] == "weekly":
        return weekly_draw(weekly, ws, bias)
    r = cfg["tp"]  # 'r2'/'r3' -> 2.0/3.0
    mult = float(r[1:])
    risk = abs(entry - sl)
    return entry + mult * risk if bias == "bull" else entry - mult * risk


def backtest(cfg, data):
    weekly, bias_map, df5m, fvgs, news_days = data
    by_date = {d: g.reset_index(drop=True) for d, g in df5m.groupby("date")}
    fvg_arr = fvgs.to_dict("records")
    weeks = {}
    for d in by_date:
        ws = (d - pd.Timedelta(days=int(d.dayofweek))).normalize()
        weeks.setdefault(ws, []).append(d)
    # prior trading day's low/high (for the liquidity-sweep / Judas gate)
    sd = sorted(by_date)
    prevlo = {sd[i]: by_date[sd[i - 1]]["low"].min() for i in range(1, len(sd))}
    prevhi = {sd[i]: by_date[sd[i - 1]]["high"].max() for i in range(1, len(sd))}
    trades = []
    for ws, dates in sorted(weeks.items()):
        bias = bias_map.get(ws, "neutral")
        if bias == "neutral":
            continue
        dates = sorted(dates); took = False
        for d in dates:                                   # ONE shot per week
            if took:
                break
            if cfg["days"] == "monwed" and d.dayofweek > 2:
                continue
            if cfg["news"] and d.normalize() not in news_days:
                continue
            cand = [f for f in fvg_arr if f["dir"] == bias
                    and f["formed"] < np.datetime64(d)
                    and f["formed"] >= np.datetime64(d - pd.Timedelta(days=10))]
            if not cand:
                continue
            day5m = by_date[d]
            mins = day5m["mins"].values; hi = day5m["high"].values
            lo = day5m["low"].values; cl = day5m["close"].values
            cum_lo = np.minimum.accumulate(lo); cum_hi = np.maximum.accumulate(hi)
            pdl = prevlo.get(d); pdh = prevhi.get(d)
            if cfg["entry"] != "fvgce":                    # OTE / turtle entry modes
                res = find_alt_entry(cfg, bias, mins, hi, lo, cl, pdl, pdh,
                                     min_imp=cfg.get("min_imp", 20.0))
                if res:
                    k, entry, sl = res
                    risk = abs(entry - sl)
                    if risk > 0 and not (cfg["maxrisk"] and risk > cfg["maxrisk"]):
                        tp = _target(cfg, weekly, ws, bias, entry, sl)
                        ok = tp is not None and ((bias == "bull" and tp > entry) or
                                                 (bias == "bear" and tp < entry))
                        if ok:
                            # ENTRY-TIMING FIX (2026-06-05): signal is bar k's close (turtle) or a
                            # within-bar-k limit touch (OTE) -> execution is the NEXT bar. Walk from
                            # k+1 to remove the entry-bar lookahead. OTE unaffected (far r2 target is
                            # never reached on bar k: regression PF 1.34 unchanged); turtle 1.72->1.38.
                            # (A tight-target OTE config would need 1m entry-bar resolution like M5.)
                            fut = [day5m.iloc[k + 1:]] + [by_date[x] for x in dates if x > d and x.dayofweek <= 4]
                            out, pnl = walk_to_friday(fut, entry, sl, tp, bias)
                            R = (tp - entry) / risk if bias == "bull" else (entry - tp) / risk
                            trades.append({"week": ws, "date": d, "dir": bias,
                                           "entry": round(entry, 2), "sl": round(sl, 2),
                                           "tp": round(tp, 2), "R": round(R, 2),
                                           "out": out, "pnl": round(pnl, 2),
                                           "emins": int(mins[k])})
                            took = True
                continue
            armed = {}  # fvg id -> touched CE (awaiting close-back)
            for k in range(len(day5m)):
                if took or not in_kz(mins[k], cfg):
                    continue
                for fi, f in enumerate(cand):
                    ce = f["ce"]
                    if bias == "bull":
                        if cfg["sweep"] and not (pdl is not None and cum_lo[k] <= pdl):
                            continue                       # require sellside sweep first
                        touched = lo[k] <= ce
                        if not cfg["confirm"]:             # naive: enter on touch
                            if not (lo[k] <= ce <= hi[k]):
                                continue
                            entry = ce
                        else:                              # confirm: touch then close-back up
                            if touched:
                                armed[fi] = True
                            if not (armed.get(fi) and cl[k] > ce):
                                continue
                            entry = cl[k]
                        sl = f["bot"] - SL_BUF
                        if entry - sl <= 0 or (cfg["maxrisk"] and entry - sl > cfg["maxrisk"]):
                            continue
                        tp = _target(cfg, weekly, ws, bias, entry, sl)
                        if tp is None or tp <= entry:
                            continue
                        fut = [day5m.iloc[k:]] + [by_date[x] for x in dates if x > d and x.dayofweek <= 4]
                        out, pnl = walk_to_friday(fut, entry, sl, tp, "bull")
                        trades.append({"week": ws, "date": d, "dir": "bull", "entry": round(entry, 2),
                                       "sl": round(sl, 2), "tp": round(tp, 2),
                                       "R": round((tp - entry) / (entry - sl), 2), "out": out,
                                       "pnl": round(pnl, 2)}); took = True; break
                    else:
                        if cfg["sweep"] and not (pdh is not None and cum_hi[k] >= pdh):
                            continue                       # require buyside sweep first
                        touched = hi[k] >= ce
                        if not cfg["confirm"]:
                            if not (lo[k] <= ce <= hi[k]):
                                continue
                            entry = ce
                        else:
                            if touched:
                                armed[fi] = True
                            if not (armed.get(fi) and cl[k] < ce):
                                continue
                            entry = cl[k]
                        sl = f["top"] + SL_BUF
                        if sl - entry <= 0 or (cfg["maxrisk"] and sl - entry > cfg["maxrisk"]):
                            continue
                        tp = _target(cfg, weekly, ws, bias, entry, sl)
                        if tp is None or tp >= entry:
                            continue
                        fut = [day5m.iloc[k:]] + [by_date[x] for x in dates if x > d and x.dayofweek <= 4]
                        out, pnl = walk_to_friday(fut, entry, sl, tp, "bear")
                        trades.append({"week": ws, "date": d, "dir": "bear", "entry": round(entry, 2),
                                       "sl": round(sl, 2), "tp": round(tp, 2),
                                       "R": round((entry - tp) / (sl - entry), 2), "out": out,
                                       "pnl": round(pnl, 2)}); took = True; break
    return pd.DataFrame(trades)


def stats(tr):
    if len(tr) == 0:
        return dict(n=0, win=0, wr=0.0, pnl=0.0, avgR=0.0, pf=0.0)
    wins = tr[tr.out == "win"]; losses = tr[tr.out == "loss"]
    gp = tr[tr.pnl > 0].pnl.sum(); gl = -tr[tr.pnl < 0].pnl.sum()
    return dict(n=len(tr), win=int((tr.out == "win").sum()),
                wr=round(100 * (tr.out == "win").mean(), 1),
                pnl=round(tr.pnl.sum(), 1), avgR=round(tr.R.mean(), 2),
                pf=round(gp / gl, 2) if gl > 0 else float("inf"))


def load_all():
    df5m = _load(M5)
    fvgs = detect_4h_fvgs(_load(H4))
    news = load_news_days()
    return df5m, fvgs, news


def make_data(cot_mode, df5m, fvgs, news, inst="nq"):
    weekly, bias_map = build_weekly_bias(cot_mode, inst)
    return (weekly, bias_map, df5m, fvgs, news)


DEFAULTS = dict(cot="off", news=False, kz="both", days="monwed",
                confirm=False, tp="weekly", maxrisk=0, sweep=False, entry="fvgce",
                min_imp=20.0)

NQ_PT = 20.0    # full NQ $/point
MNQ_PT = 2.0    # MNQ micro $/point


def peryear(tr):
    import collections
    out = collections.OrderedDict()
    if len(tr) == 0:
        return out
    t = tr.copy(); t["yr"] = t["date"].dt.year
    for yr, g in t.groupby("yr"):
        gp = g[g.pnl > 0].pnl.sum(); gl = -g[g.pnl < 0].pnl.sum()
        out[int(yr)] = (len(g), round(100 * (g.out == "win").mean()),
                        round(g.pnl.sum(), 1), round(gp / gl, 2) if gl > 0 else 9.99)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--single", action="store_true")
    ap.add_argument("--cot", default="off", choices=["off", "confirm", "veto"])
    ap.add_argument("--news", action="store_true")
    ap.add_argument("--kz", default="both", choices=["both", "ny"])
    ap.add_argument("--days", default="monwed", choices=["monwed", "all"])
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--tp", default="weekly", choices=["weekly", "r2", "r3"])
    ap.add_argument("--maxrisk", type=float, default=0)
    ap.add_argument("--entry", default="fvgce", choices=["fvgce", "ote", "turtle"])
    ap.add_argument("--min-imp", dest="min_imp", type=float, default=20.0)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--combo", action="store_true")
    ap.add_argument("--multi", action="store_true")
    ap.add_argument("--portfolio", action="store_true")
    ap.add_argument("--port-insts", dest="port_insts", default="nq,rty")
    ap.add_argument("--half-budget", dest="half_budget", action="store_true")
    args = ap.parse_args()

    if args.multi:
        # COMBINED engine across indices. Thresholds (min_imp/buf/maxrisk) scaled to
        # each instrument's price level (NQ-validated ratios x median-price ratio).
        news = load_news_days()
        insts = ["nq", "es", "ym", "rty"]
        PT = {"nq": 20.0, "es": 50.0, "ym": 5.0, "rty": 50.0}
        refs = {i: float(load_daily(i)["close"].median()) for i in insts}
        nqmed = refs["nq"]
        print(f"news High-USD days: {len(news)} | median px: "
              + " ".join(f"{i}={refs[i]:.0f}" for i in insts))
        print("\n=== MODEL 9 COMBINED (OTE r2 + Turtle r3) ACROSS INDICES ===")
        print(f"{'inst':4} {'minImp':6} | {'n':>3} {'wr':>4} {'pf':>5} {'pnl(pt)':>8} {'maxDD':>7} {'$(1x)':>9}")
        print("-" * 62)
        for inst in insts:
            scale = refs[inst] / nqmed
            base = dict(DEFAULTS, maxrisk=30 * scale, min_imp=20 * scale, sl_buf=2 * scale)
            df5 = _load(M5, inst); fv = detect_4h_fvgs(_load(H4, inst))
            data = make_data("off", df5, fv, news, inst)
            o = backtest(dict(base, entry="ote", tp="r2"), data)
            t = backtest(dict(base, entry="turtle", tp="r3"), data)
            c = pd.concat([o, t]).sort_values("date").reset_index(drop=True)
            s = stats(c)
            eq = c.pnl.cumsum() if len(c) else pd.Series([0])
            dd = (eq - eq.cummax()).min()
            print(f"{inst:4} {20*scale:6.1f} | {s['n']:>3} {s['wr']:>4} {s['pf']:>5} "
                  f"{s['pnl']:>8.0f} {dd:>7.0f} {s['pnl']*PT[inst]:>9,.0f}")
            py = peryear(c)
            print("     yr pf: " + " ".join(f"{y}:{v[3]}" for y, v in py.items()))
        return

    if args.portfolio:
        # CROSS-INDEX PORTFOLIO - merge each instrument's combo (OTE r2 + Turtle r3)
        # trades into ONE time-ordered book. Two sizings:
        #   equal-RISK     = each trade normalized to a fixed $-risk via realized R-mult
        #                    (pnl/|entry-sl|); scale-free, matches our fixed-$-risk live sizing.
        #   equal-CONTRACT = 1 full lot each via point values; tangible $.
        insts = [s.strip().lower() for s in args.port_insts.split(",") if s.strip()]
        PT = {"nq": 20.0, "es": 50.0, "ym": 5.0, "rty": 50.0}
        R_USD = 100.0  # $ risked per trade in the equal-risk book (linear scaling constant)
        news = load_news_days()
        nqmed = float(load_daily("nq")["close"].median())
        refs = {i: float(load_daily(i)["close"].median()) for i in insts}
        books, standalone = [], {}
        for inst in insts:
            scale = refs[inst] / nqmed
            base = dict(DEFAULTS, maxrisk=30 * scale, min_imp=20 * scale, sl_buf=2 * scale)
            df5 = _load(M5, inst); fv = detect_4h_fvgs(_load(H4, inst))
            data = make_data("off", df5, fv, news, inst)
            o = backtest(dict(base, entry="ote", tp="r2"), data)
            t = backtest(dict(base, entry="turtle", tp="r3"), data)
            c = pd.concat([o, t]).sort_values("date").reset_index(drop=True)
            if not len(c):
                continue
            c["inst"] = inst
            c["risk"] = (c.entry - c.sl).abs()
            c["rmult"] = c.pnl / c.risk            # realized R per trade (scale-free)
            c["usd_rp"] = c.rmult * R_USD          # equal-risk $ ($100 risked/trade)
            c["usd_1x"] = c.pnl * PT[inst]         # equal-contract $ (1 lot)
            books.append(c)
            er = c.usd_rp.cumsum(); e1 = c.usd_1x.cumsum()
            standalone[inst] = dict(rp=c.usd_rp.sum(), ddr=(er - er.cummax()).min(),
                                    u1=c.usd_1x.sum(), dd1=(e1 - e1.cummax()).min())
        book = pd.concat(books).sort_values("date").reset_index(drop=True)
        book["yr"] = book["date"].dt.year
        # concurrency = # of OTE+turtle same-(week,dir) positions WITHIN an instrument.
        # 2 = OTE+turtle overlap (execution diversification, NOT 2x takeable risk) -> half each;
        # 1 = solo week -> full. Caps each instrument's per-week directional risk at 1 unit.
        book["concurrency"] = book.groupby(["inst", "week", "dir"])["pnl"].transform("size")
        book["weight"] = 1.0 / book["concurrency"]
        book["usd_rp_hb"] = book.usd_rp * book.weight   # half-budget (constant 1-unit/wk/inst)

        def pf_col(b, col):
            gp = b[b[col] > 0][col].sum(); gl = -b[b[col] < 0][col].sum()
            return round(gp / gl, 2) if gl > 0 else float("inf")

        def maxdd(col):
            eq = book[col].cumsum(); return (eq - eq.cummax()).min()

        def pf_year(col, y):
            return pf_col(book[book.yr == y], col)

        wr = round(100 * (book.out == "win").mean(), 1)
        years = sorted(book.yr.unique())
        print(f"\n=== MODEL 9 CROSS-INDEX PORTFOLIO: {'+'.join(i.upper() for i in insts)} ===")
        print(f"merged {len(book)} trades (one book) | bias=range-expansion (cot=off) | median px: "
              + " ".join(f"{i}={refs[i]:.0f}" for i in insts))

        trp = book.usd_rp.sum(); ddr = maxdd("usd_rp")
        print(f"\n[EQUAL-RISK] ${R_USD:.0f} risked/trade (scale-free; $ & DD scale linearly):")
        print(f"  n={len(book)} wr={wr}% PF={pf_col(book,'usd_rp')} total=${trp:,.0f} "
              f"maxDD=${ddr:,.0f} return/DD={trp/abs(ddr):.1f}  "
              f"(= {trp/R_USD:.0f}R / {abs(ddr)/R_USD:.1f}R DD)")
        print("  per-yr PF: " + " ".join(
            f"{y}:{pf_year('usd_rp', y)}{'(part)' if y == years[-1] else ''}" for y in years))

        t1 = book.usd_1x.sum(); dd1 = maxdd("usd_1x")
        print(f"\n[EQUAL-CONTRACT] 1 full lot each (NQ $20 / RTY,ES $50 / YM $5 per pt):")
        print(f"  PF={pf_col(book,'usd_1x')} total=${t1:,.0f} maxDD=${dd1:,.0f} "
              f"return/DD={t1/abs(dd1):.1f}")
        print("  per-yr $:  " + " ".join(
            f"{y}:${book[book.yr==y].usd_1x.sum():,.0f}{'(part)' if y == years[-1] else ''}" for y in years))
        print("  (1-lot mixes risk: RTY/ES $50/pt weight > NQ $20/pt; equal-risk above is the production sizing)")

        sdr = sum(s["ddr"] for s in standalone.values())
        sd1 = sum(s["dd1"] for s in standalone.values())
        print(f"\n[DIVERSIFICATION] (does staggering weak years reduce drawdown?)")
        for i, s in standalone.items():
            print(f"  {i:4} standalone: equal-risk ${s['rp']:,.0f} DD ${s['ddr']:,.0f} | "
                  f"1-lot ${s['u1']:,.0f} DD ${s['dd1']:,.0f}")
        print(f"  additive (sum) DD:  equal-risk ${sdr:,.0f} | 1-lot ${sd1:,.0f}")
        print(f"  PORTFOLIO combo DD: equal-risk ${ddr:,.0f} | 1-lot ${dd1:,.0f}")
        if sdr:
            print(f"  -> equal-risk DD cut {100*(1-abs(ddr)/abs(sdr)):.0f}% vs additive "
                  f"(caveat: correlated underlyings)")
        if args.half_budget:
            ov = int((book.concurrency == 2).sum()); solo = int((book.concurrency == 1).sum())
            rdn = trp / abs(ddr)                                   # naive return/DD
            wk_naive = book.groupby("week").usd_rp.sum().min()     # worst realized week (all insts)
            # ALWAYS-HALF (LIVE, no lookahead): every book at 0.5 budget = uniform scale of naive.
            ah_tot, ah_dd, ah_wk = trp * 0.5, ddr * 0.5, wk_naive * 0.5
            # CONCURRENCY-AWARE (full on solo wks): needs intra-week foresight (don't know at OTE
            # entry whether turtle fires later same week) = backtest UPPER BOUND, not deployable.
            thb = book.usd_rp_hb.sum(); ddhb = maxdd("usd_rp_hb")
            wk_hb = book.groupby("week").usd_rp_hb.sum().min()
            print(f"\n[HALF-BUDGET SIZING] cap each instrument's per-week directional risk at 1 unit")
            print(f"  trades on overlap weeks (OTE+turtle same wk/dir): {ov} | solo weeks: {solo}")
            print(f"  NAIVE (hidden 2x on overlap): total=${trp:,.0f} maxDD=${ddr:,.0f} "
                  f"return/DD={rdn:.1f} | worst week ${wk_naive:,.0f} (~4 units: 2 inst x 2 books)")
            print(f"  ALWAYS-HALF (LIVE rule, no lookahead): total=${ah_tot:,.0f} maxDD=${ah_dd:,.0f} "
                  f"return/DD={rdn:.1f} | worst week ${ah_wk:,.0f} (HALVED)  <- DEPLOY THIS")
            print(f"  CONCURRENCY-AWARE (full on solo wks, needs intra-week foresight = backtest upper bound): "
                  f"total=${thb:,.0f} maxDD=${ddhb:,.0f} return/DD={thb/abs(ddhb):.1f} | worst week ${wk_hb:,.0f}")
            print(f"  RULE: size EACH book (OTE, turtle) at HALF the per-trade $-risk budget. The 99/100 overlap "
                  f"is execution diversification, NOT 2x takeable risk -> halving caps worst week at ~2 units, "
                  f"keeps return/DD {rdn:.1f}.")
            wd = book.groupby("date").usd_rp.sum().min() * 0.5    # worst single ENTRY-day (always-half)
            ceil = len(insts) * R_USD                             # each inst's OTE+turtle capped at 1 unit
            print(f"  funded fit (DAILY, not weekly): each inst's OTE+turtle is capped at 1 unit, so max "
                  f"concurrent open risk = {len(insts)} units = ${ceil:,.0f}/$100-unit. worst entry-day "
                  f"${wd:,.0f}; worst week ${ah_wk:,.0f}.")
            print(f"  -> at unit=$300 the DAILY loss ceiling = ${ceil*3:,.0f} (clears a $1,000+ daily limit). "
                  f"NB backtest holds weekly (no daily MTM); the {len(insts)}-unit ceiling bounds any single day.")
        book.to_csv("/tmp/model9_portfolio_trades.csv", index=False)
        print("\n  trades -> /tmp/model9_portfolio_trades.csv")
        return

    print("loading data...", flush=True)
    df5m, fvgs, news = load_all()
    print(f"5m bars: {len(df5m):,} | 4h FVGs: {len(fvgs)} | news High-USD days: {len(news)}", flush=True)

    if args.combo:
        # COMBINED ENGINE — OTE r2 + turtle r3 as two diversified books (one trade
        # per week per book). Their weak years are complementary -> smoother curve.
        data = make_data("off", df5m, fvgs, news)
        o = backtest(dict(DEFAULTS, entry="ote", tp="r2", maxrisk=30), data); o["mode"] = "ote"
        t = backtest(dict(DEFAULTS, entry="turtle", tp="r3", maxrisk=30), data); t["mode"] = "turtle"
        c = pd.concat([o, t]).sort_values("date").reset_index(drop=True)
        print("\n=== MODEL 9 COMBINED ENGINE (OTE r2 + Turtle r3) ===")
        for nm, tr in [("OTE     ", o), ("TURTLE  ", t), ("COMBINED", c)]:
            s = stats(tr)
            print(f"{nm}: n={s['n']:3d} wr={s['wr']:4} pf={s['pf']:5} pnl={s['pnl']:8}pt")
        print("\nper-year (pf | combined pnl):")
        po, pt, pc = peryear(o), peryear(t), peryear(c)
        for yr in sorted(pc):
            a = po.get(yr, (0, 0, 0, 0))[3]; b = pt.get(yr, (0, 0, 0, 0))[3]; d = pc[yr]
            print(f"  {yr}: ote {a:>4}  turtle {b:>4}  ->  COMBINED pf {d[3]:>4}  pnl {d[2]:>+7}")
        eq = c.pnl.cumsum(); dd = (eq - eq.cummax()).min()
        # overlap: weeks where both books traded the same direction (concentration risk)
        ok = set(zip(o["week"], o["dir"])); tk = set(zip(t["week"], t["dir"]))
        overlap = len(ok & tk)
        print(f"\ncombined: total {c.pnl.sum():+.1f}pt | maxDD {dd:.1f}pt | trades {len(c)}")
        print(f"  $ @1NQ ${c.pnl.sum()*NQ_PT:,.0f} (DD ${abs(dd)*NQ_PT:,.0f}) | @1MNQ ${c.pnl.sum()*MNQ_PT:,.0f} (DD ${abs(dd)*MNQ_PT:,.0f})")
        print(f"  same-week+dir overlaps (2x concentration): {overlap} of {len(ok)+len(tk)} book-weeks")
        c.to_csv("/tmp/model9_combo_trades.csv", index=False)
        return

    if args.validate:
        data = make_data("off", df5m, fvgs, news)
        def run(**kw):
            return backtest(dict(DEFAULTS, **kw), data)
        print("\n=== OTE vs TURTLE (maxrisk=30) per-year ===")
        for name, kw in [("OTE r2", dict(entry="ote", tp="r2", maxrisk=30)),
                         ("OTE r3", dict(entry="ote", tp="r3", maxrisk=30)),
                         ("TURTLE r3", dict(entry="turtle", tp="r3", maxrisk=30)),
                         ("TURTLE wk", dict(entry="turtle", tp="weekly", maxrisk=0))]:
            tr = run(**kw); s = stats(tr); py = peryear(tr)
            print(f"\n{name}: {s}")
            print("  yr:  " + "  ".join(f"{y}:pf{v[3]}" for y, v in py.items()))
        print("\n=== min_imp SENSITIVITY (OTE r2 maxrisk30) ===")
        print(f"{'min_imp':>7} | {'n':>4} {'wr':>5} {'pnl':>8} {'pf':>5}")
        for mi in [8, 12, 16, 20, 24, 30, 40, 50]:
            s = stats(run(entry="ote", tp="r2", maxrisk=30, min_imp=mi))
            print(f"{mi:>7} | {s['n']:>4} {s['wr']:>5} {s['pnl']:>8} {s['pf']:>5}")
        print("\n=== $ SIZING (OTE r2 maxrisk30, +650pt baseline) ===")
        s = stats(run(entry="ote", tp="r2", maxrisk=30))
        pnl = s["pnl"]
        print(f"  1 MNQ (${MNQ_PT}/pt):  P&L ${pnl*MNQ_PT:,.0f}  | maxrisk/trade ~30pt = ${30*MNQ_PT:.0f}")
        print(f"  1 NQ  (${NQ_PT}/pt):  P&L ${pnl*NQ_PT:,.0f}  | maxrisk/trade ~30pt = ${30*NQ_PT:.0f}")
        print("  (sizing to a fixed $-risk budget scales these linearly)")
        return

    if args.single:
        cfg = dict(DEFAULTS, cot=args.cot, news=args.news, kz=args.kz, days=args.days,
                   confirm=args.confirm, tp=args.tp, maxrisk=args.maxrisk, entry=args.entry)
        tr = backtest(cfg, make_data(args.cot, df5m, fvgs, news))
        print(cfg, "->", stats(tr))
        tr.to_csv("/tmp/model9_trades.csv", index=False)
        if len(tr):
            print(tr.head(20).to_string())
        return

    # LAST-STONE SWEEP — entry mechanic (fvgce/ote/turtle) x tp x maxrisk x news
    print("\n=== MODEL 9 LAST-STONE SWEEP (cot=off, kz=both, days=monwed) ===")
    hdr = f"{'entry':7} {'tp':7} {'maxR':5} {'news':5} | {'n':>4} {'win':>4} {'wr':>6} {'pnl(pt)':>9} {'avgR':>6} {'pf':>6}"
    print(hdr); print("-" * len(hdr))
    data = make_data("off", df5m, fvgs, news)
    for entry, tp, maxrisk, news_g in itertools.product(
            ["fvgce", "ote", "turtle"], ["weekly", "r2", "r3"], [0, 30], [False, True]):
        cfg = dict(DEFAULTS, entry=entry, tp=tp, maxrisk=maxrisk, news=news_g)
        s = stats(backtest(cfg, data))
        print(f"{entry:7} {tp:7} {str(maxrisk):5} {str(news_g):5} | {s['n']:>4} "
              f"{s['win']:>4} {s['wr']:>6} {s['pnl']:>9} {s['avgR']:>6} {s['pf']:>6}")


if __name__ == "__main__":
    main()
