#!/usr/bin/env python3
"""
ICT Charter Model 5 - Intraday Volatility Expansion engine.

A/B two entry techniques (ICT calls the entry "plug-and-play"):
  fvg : 15-min FVG-extreme, first-touch near-edge (low-hanging-fruit / IOF) - the Trade Plan entry
  ote : 70.5% OTE retrace of the killzone impulse - reuse Model 9's validated OTE

Core (both entries): HTF weekly-bias direction, Tue-Thu, London/NY killzone, bias-dir 15-min FVG
in the premium/discount half of the prior-day range (toggle), TARGET = prior-day liquidity
(prev-day low for shorts / high for longs), INTRADAY exit (same-day tp/sl, else session-end be).

Reuses model9_oneshot_engine: loaders, build_weekly_bias, detect_4h_fvgs (generic 3-candle FVG),
find_alt_entry (OTE), stats, peryear, killzone constants. SD-confluence filter = TODO (off-by-default).
Spec: Obsidian Research/ICT_Model5_IntradayVolExpansion_Spec.md.
"""
import sys
import argparse
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import numpy as np
import pandas as pd
import model9_oneshot_engine as M9

LONDON_KZ, NY_KZ, SL_BUF = M9.LONDON_KZ, M9.NY_KZ, M9.SL_BUF
PT = {"nq": 20.0, "es": 50.0, "ym": 5.0, "rty": 50.0}


def resample_15m(df5):
    g = (df5.set_index("timestamp")
         .resample("15min")
         .agg(open=("open", "first"), high=("high", "max"),
              low=("low", "min"), close=("close", "last"))
         .dropna().reset_index())
    return g


def prior_day_levels(df5):
    daily = df5.groupby("date").agg(h=("high", "max"), l=("low", "min"))
    return daily["h"].shift(1).to_dict(), daily["l"].shift(1).to_dict()


def in_kz(m, sess):
    if sess in ("london", "both") and LONDON_KZ[0] <= m < LONDON_KZ[1]:
        return True
    if sess in ("ny", "both") and NY_KZ[0] <= m < NY_KZ[1]:
        return True
    return False


def kz_end_of(m):
    """End minute of the killzone the entry bar sits in (for scalp exit-by-KZ-end)."""
    if LONDON_KZ[0] <= m < LONDON_KZ[1]:
        return LONDON_KZ[1]
    if NY_KZ[0] <= m < NY_KZ[1]:
        return NY_KZ[1]
    return 24 * 60


def find_fvg_entry(bias, fvgs, ts, mins, hi, lo, sess, pdmid, half_filter):
    """First-touch near-edge entry into a bias-dir 15m FVG during the killzone.
    bear: short at FVG bot, SL above top. bull: long at FVG top, SL below bot."""
    for k in range(len(mins)):
        if not in_kz(mins[k], sess):
            continue
        for f in fvgs:
            if f["dir"] != bias or f["formed"] >= ts[k]:
                continue
            if half_filter:
                if bias == "bear" and f["ce"] > pdmid:    # bear FVG must sit in lower half
                    continue
                if bias == "bull" and f["ce"] < pdmid:    # bull FVG must sit in upper half
                    continue
            if bias == "bear" and lo[k] <= f["bot"] <= hi[k]:
                return k, f["bot"], f["top"] + SL_BUF
            if bias == "bull" and lo[k] <= f["top"] <= hi[k]:
                return k, f["top"], f["bot"] - SL_BUF
    return None


def walk_intraday(day_df, k, entry, sl, tp, bias):
    """Exit at tp(win)/sl(loss) within the same day from bar k, else session-end close (be).
    pnl is signed in trade direction (short = entry-exit, long = exit-entry)."""
    H = day_df["high"].values[k:]
    L = day_df["low"].values[k:]
    C = day_df["close"].values[k:]
    for i in range(len(H)):
        if bias == "bear":
            if H[i] >= sl:
                return "loss", entry - sl       # sl > entry -> negative
            if L[i] <= tp:
                return "win", entry - tp
        else:
            if L[i] <= sl:
                return "loss", sl - entry       # sl < entry -> negative
            if H[i] >= tp:
                return "win", tp - entry
    last = C[-1]
    return "be", (entry - last) if bias == "bear" else (last - entry)


# --- 1m-resolved limit-entry execution (ENTRY-TIMING FIX 2026-06-05) ----------
# M5 entries (OTE / FVG-extreme) are LIMIT fills - filled when price TOUCHES the
# level intrabar. Resolving them on the 5m entry bar let that bar's PRE-fill range
# trigger exits that were not executable (a lookahead that inflated M5 PF 3.84 ->
# true 1.78). Fix: resolve the entry 5m bar on 1m (find the fill, walk SL-first
# from there); if filled-but-unresolved continue on 5m from k+1. Falls back to a
# conservative k+1 5m walk when 1m data is missing for the day (e.g. 2026).
_M1_FILES = ["MULTI_1min_IST_2020_2024.csv", "MULTI_1min_IST_2025.csv"]
_M1_CACHE = {}


def _load_1m(inst):
    if inst not in _M1_CACHE:
        cols = ["timestamp", f"{inst}_high", f"{inst}_low"]
        try:
            df = pd.concat([pd.read_csv(f"/Users/azarudin/mnq_trading/data/{f}",
                                        usecols=cols, parse_dates=["timestamp"])
                            for f in _M1_FILES], ignore_index=True)
            df["date"] = df["timestamp"].dt.normalize()
            df["mins"] = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute
            df = df.sort_values("mins")
            _M1_CACHE[inst] = {d: (g[f"{inst}_high"].values, g[f"{inst}_low"].values, g["mins"].values)
                               for d, g in df.groupby("date")}
        except Exception:
            _M1_CACHE[inst] = None
    return _M1_CACHE[inst]


def walk_limit_1m(inst, d, exit_df, k, mins_arr, entry, sl, tp, bias):
    """Limit-entry execution: 1m fill-forward on the entry bar, then 5m from k+1."""
    cache = _load_1m(inst)
    day = cache.get(d) if cache else None
    if day is not None:
        H1, L1, M1 = day
        emins = int(mins_arr[k])
        sel = (M1 >= emins) & (M1 < emins + 5)
        Hh, Ll = H1[sel], L1[sel]
        fill = -1
        for i in range(len(Hh)):
            if (bias == "bull" and Ll[i] <= entry) or (bias == "bear" and Hh[i] >= entry):
                fill = i
                break
        if fill >= 0:
            for i in range(fill, len(Hh)):              # SL-first from the true fill
                if bias == "bull":
                    if Ll[i] <= sl:
                        return "loss", sl - entry
                    if Hh[i] >= tp:
                        return "win", tp - entry
                else:
                    if Hh[i] >= sl:
                        return "loss", entry - sl
                    if Ll[i] <= tp:
                        return "win", entry - tp
            # filled but not resolved within the entry bar -> continue on 5m from k+1
    if k + 1 >= len(exit_df):
        return "be", 0.0
    return walk_intraday(exit_df, k + 1, entry, sl, tp, bias)


def week_start(d):
    return (d - pd.Timedelta(days=int(d.dayofweek))).normalize()


def backtest(cfg, inst="nq"):
    df5 = M9._load(M9.M5, inst)
    df15 = resample_15m(df5)
    fvgs = M9.detect_4h_fvgs(df15).to_dict("records")   # generic 3-candle FVG on 15m bars
    _weekly, bias_map = M9.build_weekly_bias("off", inst)
    pdh_map, pdl_map = prior_day_levels(df5)
    by_date = {d: g.reset_index(drop=True) for d, g in df5.groupby("date")}
    days_ok = {"tuethu": {1, 2, 3}, "monwed": {0, 1, 2}, "all": {0, 1, 2, 3, 4}}[cfg["days"]]
    mi = cfg["min_imp"]
    trades = []
    traded_weeks = set()
    for d in sorted(by_date):
        if d.dayofweek not in days_ok:
            continue
        ws = week_start(d)
        bias = bias_map.get(ws, "neutral")
        if bias == "neutral":
            continue
        if cfg["one_per_week"] and ws in traded_weeks:
            continue                                # Model 8: one selective setup per week
        pdh = pdh_map.get(d)
        pdl = pdl_map.get(d)
        if pdh is None or pdl is None or np.isnan(pdh) or np.isnan(pdl):
            continue
        pdmid = (pdh + pdl) / 2.0
        g = by_date[d]
        mins = g["mins"].values
        hi = g["high"].values
        lo = g["low"].values
        cl = g["close"].values
        ts = g["timestamp"].values
        if cfg["entry"] == "fvg":
            day_fvgs = [f for f in fvgs
                        if f["dir"] == bias and f["formed"] < ts[-1]
                        and f["formed"] >= np.datetime64(d) - np.timedelta64(7, "D")]
            res = find_fvg_entry(bias, day_fvgs, ts, mins, hi, lo,
                                 cfg["session"], pdmid, cfg["half_filter"])
        else:  # ote - reuse Model 9's validated OTE finder (killzone impulse 70.5% retrace)
            ocfg = dict(M9.DEFAULTS, entry="ote",
                        kz=("ny" if cfg["session"] == "ny" else "both"),
                        maxrisk=0, min_imp=mi, sl_buf=SL_BUF)
            res = M9.find_alt_entry(ocfg, bias, mins, hi, lo, cl, pdl, pdh, min_imp=mi)
        if not res:
            continue
        k, entry, sl = res
        risk = abs(entry - sl)
        if risk <= 0:
            continue
        if cfg["tp"] == "prevday":
            tp = pdl if bias == "bear" else pdh
            if not ((bias == "bear" and tp < entry) or (bias == "bull" and tp > entry)):
                continue                            # target already swept / wrong side
        elif cfg["tp"] == "fixed":                  # Model 8: fixed point target (25 handles)
            tp = entry - cfg["tp_pts"] if bias == "bear" else entry + cfg["tp_pts"]
        else:                                       # fixed R multiple (r1/r1.5/r2/r3) - modest target
            mult = float(cfg["tp"][1:])
            tp = entry - mult * risk if bias == "bear" else entry + mult * risk
        if cfg["maxrisk"] and risk > cfg["maxrisk"]:
            continue
        exit_df = g
        if cfg["exit"] == "kz":                      # scalp: exit by killzone end, not session close
            kze = kz_end_of(mins[k])
            j = k
            while j + 1 < len(mins) and mins[j + 1] < kze:
                j += 1
            exit_df = g.iloc[:j + 1]
        out, pnl = walk_limit_1m(inst, d, exit_df, k, mins, entry, sl, tp, bias)
        R = (abs(entry - tp)) / risk
        trades.append({"date": d, "dir": bias, "entry": round(entry, 2),
                       "sl": round(sl, 2), "tp": round(tp, 2), "R": round(R, 2),
                       "out": out, "pnl": round(pnl, 2), "dow": int(d.dayofweek),
                       "emins": int(mins[k])})
        traded_weeks.add(ws)
    return pd.DataFrame(trades)


DEFAULTS = dict(entry="fvg", days="tuethu", session="both",
                half_filter=True, maxrisk=0, min_imp=20.0, tp="prevday", exit="session",
                tp_pts=25.0, one_per_week=False)


def show(name, tr):
    s = M9.stats(tr)
    print(f"\n{name}: n={s['n']} wr={s['wr']}% pf={s['pf']} pnl={s['pnl']}pt avgR={s['avgR']}")
    if len(tr):
        eq = tr.pnl.cumsum()
        dd = (eq - eq.cummax()).min()
        print(f"  maxDD={dd:.0f}pt | ${s['pnl']*M9.NQ_PT:,.0f}/1NQ | per-yr pf: "
              + " ".join(f"{y}:{v[3]}" for y, v in M9.peryear(tr).items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", choices=["fvg", "ote"], default=None)
    ap.add_argument("--inst", default="nq")
    ap.add_argument("--days", default="tuethu", choices=["tuethu", "monwed", "all"])
    ap.add_argument("--session", default="both", choices=["both", "ny"])
    ap.add_argument("--no-half-filter", dest="half_filter", action="store_false")
    ap.add_argument("--maxrisk", type=float, default=0)
    ap.add_argument("--min-imp", dest="min_imp", type=float, default=20.0)
    ap.add_argument("--tp", default="prevday", choices=["prevday", "r1", "r1.5", "r2", "r3", "fixed"])
    ap.add_argument("--tp-pts", dest="tp_pts", type=float, default=25.0)
    ap.add_argument("--exit", dest="exit_mode", default="session", choices=["session", "kz"])
    ap.add_argument("--one-per-week", dest="one_per_week", action="store_true")
    args = ap.parse_args()
    base = dict(DEFAULTS, days=args.days, session=args.session, tp=args.tp, exit=args.exit_mode,
                tp_pts=args.tp_pts, one_per_week=args.one_per_week,
                half_filter=args.half_filter, maxrisk=args.maxrisk, min_imp=args.min_imp)
    print(f"MODEL 5 Intraday Vol Expansion | inst={args.inst} days={args.days} "
          f"session={args.session} half_filter={args.half_filter} maxrisk={args.maxrisk}")
    if args.entry:
        show(f"entry={args.entry}", backtest(dict(base, entry=args.entry), args.inst))
    else:  # A/B both entries (default)
        print("=== A/B: FVG-extreme vs OTE entry ===")
        show("FVG-extreme", backtest(dict(base, entry="fvg"), args.inst))
        show("OTE-70.5%   ", backtest(dict(base, entry="ote"), args.inst))


if __name__ == "__main__":
    main()
