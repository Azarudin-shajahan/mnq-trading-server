#!/usr/bin/env python3
"""ORG driver-skeleton FALSIFIER (Fable's design, 2026-06-11).

Tests the Opening Range Gap *repricing driver* in isolation -- stripped of any FVG
entry dressing -- to decide whether a genuine fill-direction edge exists BEFORE any
ORG engine gets built. Per Fable: "the FVG entry can't rescue a driver that doesn't
exist; it would just be another FVG engine wearing a gap costume."

Mechanic (skeleton-B, no FVG):
  - Gap  = NQ RTH 9:30 ET open  -  prior RTH 16:00 ET close.
  - Trade only in-band gaps (|gap| in [gap_min, gap_max] points).
  - Direction (the entire directional CLAIM): gap-up -> SHORT toward fill;
    gap-down -> LONG toward fill. No weekly/OTE bias imported.
  - Entry  = market at the 9:31 ET bar open.
  - Stop   = gap far edge (the 9:30 open) + buffer.
  - Target = full fill (prior RTH close).
  - Time-stop: flat at 16:00 ET.
  - Intrabar resolution at 1-MINUTE, STOP-FIRST when a bar spans both (conservative;
    same anti-lookahead discipline as the engine gotchas).

Controls that isolate "is the DIRECTION the edge":
  - fill      : the hypothesis (toward fill).
  - inverted  : opposite direction, SAME bracket magnitudes (Tdist/Sdist held constant).
  - random    : random direction per day (seeded), same bracket magnitudes; plus a
                NULL distribution over many seeds to place the fill arm in a band.

KILL the driver if fill PF <= 1.0 OR fill <= inverted OR fill is inside the random
5-95 pct NULL band. Only a surviving driver justifies building the FVG entry.

Timezone: data timestamps are naive IST -> localize Asia/Kolkata (no DST) -> convert
America/New_York so the 9:30/16:00 ET anchors are exact across US DST.

ASCII-only source (this Python 3.10 rejects U+2014 in literals).
"""
import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.expanduser("~"), "mnq_trading/data")
MD_OUT = os.path.join(HERE, "ORG_DRIVER_FALSIFIER.md")

RTH_OPEN = 9 * 60 + 30      # 570  (9:30 ET)
RTH_ENTRY = 9 * 60 + 31     # 571  (9:31 ET)
RTH_CLOSE = 16 * 60         # 960  (16:00 ET)


def load(fname, inst, start, end):
    path = os.path.join(DATA, fname)
    cols = ["timestamp", f"{inst}_open", f"{inst}_high", f"{inst}_low", f"{inst}_close"]
    df = pd.read_csv(path, usecols=cols, parse_dates=["timestamp"])
    df = df.rename(columns={f"{inst}_open": "o", f"{inst}_high": "h",
                            f"{inst}_low": "l", f"{inst}_close": "c"})
    ts = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df["et_date"] = ts.dt.normalize().dt.tz_localize(None)
    df["et_min"] = ts.dt.hour * 60 + ts.dt.minute
    df["et"] = ts
    df = df[(df["et_date"] >= pd.Timestamp(start)) & (df["et_date"] <= pd.Timestamp(end))]
    rth = df[(df["et_min"] >= RTH_OPEN) & (df["et_min"] <= RTH_CLOSE)].copy()
    return rth.sort_values("et").reset_index(drop=True)


def day_table(rth):
    """Per ET date: 9:30 open, 9:31 entry open, RTH close, and the intrabar path."""
    days = {}
    for d, g in rth.groupby("et_date"):
        g = g.sort_values("et_min")
        opn = g[g["et_min"] == RTH_OPEN]
        ent = g[g["et_min"] == RTH_ENTRY]
        if opn.empty or ent.empty:
            continue
        path = g[g["et_min"] >= RTH_ENTRY]              # entry bar onward (incl. its range)
        days[d] = {
            "open": float(opn["o"].values[0]),
            "entry": float(ent["o"].values[0]),
            "close": float(g["c"].values[-1]),         # last RTH minute close (half-day safe)
            "ph": path["h"].values.astype(float),
            "pl": path["l"].values.astype(float),
            "pc": path["c"].values.astype(float),
        }
    return days


def resolve(direction, stop, target, ph, pl, pc):
    """1-min intrabar walk, STOP-FIRST. direction +1 long / -1 short. Returns exit price."""
    if direction == -1:                                # short: stop above, target below
        for i in range(len(ph)):
            if ph[i] >= stop:
                return stop
            if pl[i] <= target:
                return target
    else:                                              # long: stop below, target above
        for i in range(len(pl)):
            if pl[i] <= stop:
                return stop
            if ph[i] >= target:
                return target
    return float(pc[-1])                               # time-stop at 16:00 close


def brackets(rec, buffer):
    """fill-direction geometry -> (fill_dir, entry, Tdist, Sdist)."""
    entry, opn, close = rec["entry"], rec["open"], rec["close"]
    if opn > close:                                    # gap-up -> fill DOWN -> short
        fill_dir = -1
        stop = max(opn + buffer, entry + buffer)       # far edge = 9:30 open (validity-guarded)
        target = close
    else:                                              # gap-down -> fill UP -> long
        fill_dir = +1
        stop = min(opn - buffer, entry - buffer)
        target = close
    return fill_dir, entry, abs(entry - target), abs(stop - entry)


def trade(direction, entry, Tdist, Sdist, rec):
    if direction == -1:
        stop, target = entry + Sdist, entry - Tdist
    else:
        stop, target = entry - Sdist, entry + Tdist
    exit_px = resolve(direction, stop, target, rec["ph"], rec["pl"], rec["pc"])
    return (exit_px - entry) * direction, Sdist        # (pnl_pts, risk_pts)


def stats(pnls, risks, years):
    pnls = np.array(pnls, float)
    if len(pnls) == 0:
        return {"n": 0}
    gp = pnls[pnls > 0].sum()
    gl = -pnls[pnls < 0].sum()
    pf = (gp / gl) if gl > 0 else float("inf")
    risk = np.array(risks, float)
    expR = float((pnls / np.where(risk == 0, np.nan, risk)).mean())
    out = {"n": int(len(pnls)), "wr": round(float((pnls > 0).mean()), 3),
           "pf": round(pf, 3) if np.isfinite(pf) else 999.0,
           "expR": round(expR, 3), "total_pts": round(float(pnls.sum()), 1)}
    ya = np.array(years)
    yr = {}
    for y in sorted(set(years)):
        p = pnls[ya == y]
        g2 = -p[p < 0].sum()
        yr[int(y)] = round((p[p > 0].sum() / g2) if g2 > 0 else 999.0, 2)
    out["pf_by_year"] = yr
    return out


def gap_items(days, gap_min, gap_max):
    dates = sorted(days)
    items = []
    for i in range(1, len(dates)):
        rec = dict(days[dates[i]])
        prior_close = days[dates[i - 1]]["close"]
        gap = rec["open"] - prior_close
        if gap_min <= abs(gap) <= gap_max:
            rec["close"] = prior_close                 # target = prior RTH close (full fill)
            rec["gap"] = gap
            items.append((dates[i], rec))
    return items


def run(args):
    rth = load(args.file, args.inst, args.start, args.end)
    days = day_table(rth)
    items = gap_items(days, args.gap_min, args.gap_max)

    fp, fr, ip, ir, sp, sr, yrs = [], [], [], [], [], [], []
    rng = np.random.default_rng(args.seed)
    for d, rec in items:
        fdir, entry, Td, Sd = brackets(rec, args.buffer)
        p, r = trade(fdir, entry, Td, Sd, rec); fp.append(p); fr.append(r)
        p2, r2 = trade(-fdir, entry, Td, Sd, rec); ip.append(p2); ir.append(r2)
        p3, r3 = trade(int(rng.choice([-1, 1])), entry, Td, Sd, rec); sp.append(p3); sr.append(r3)
        yrs.append(d.year)

    fill, inv, rnd = stats(fp, fr, yrs), stats(ip, ir, yrs), stats(sp, sr, yrs)

    null_pf = []
    for s in range(args.rand_iters):
        rg = np.random.default_rng(10000 + s)
        pp = []
        for d, rec in items:
            fdir, entry, Td, Sd = brackets(rec, args.buffer)
            p, _ = trade(int(rg.choice([-1, 1])), entry, Td, Sd, rec)
            pp.append(p)
        pp = np.array(pp, float)
        gl = -pp[pp < 0].sum()
        null_pf.append((pp[pp > 0].sum() / gl) if gl > 0 else 999.0)
    null_pf = np.array(null_pf, float)
    null = {p: round(float(np.percentile(null_pf, p)), 3) for p in (5, 50, 95)}
    fill_pctile = round(float((null_pf < fill["pf"]).mean() * 100), 1)

    kill = (fill["pf"] <= 1.0 or fill["pf"] <= inv["pf"] or null[5] <= fill["pf"] <= null[95])
    res = {"generated": dt.datetime.now().isoformat(timespec="seconds"),
           "window": [args.start, args.end], "inst": args.inst, "n_gap_days": len(items),
           "gap_band_pts": [args.gap_min, args.gap_max], "buffer_pts": args.buffer,
           "fill": fill, "inverted": inv, "random_seed": rnd,
           "random_null_pf": null, "fill_pf_percentile_vs_null": fill_pctile,
           "VERDICT": "KILL (driver not supported)" if kill
                      else "SURVIVES (build FVG-entry variant next)"}
    _report(res)
    return res


def _report(r):
    print("=== ORG driver-skeleton falsifier (%s..%s, %s) ===" %
          (r["window"][0], r["window"][1], r["inst"]))
    print("in-band gap days: %d | band %s pts | buffer %s" %
          (r["n_gap_days"], r["gap_band_pts"], r["buffer_pts"]))
    for nm in ("fill", "inverted", "random_seed"):
        s = r[nm]
        print("  %-12s n=%d WR=%.0f%% PF=%.2f expR=%.3f total=%.0fpt yr=%s"
              % (nm, s["n"], s["wr"] * 100, s["pf"], s["expR"], s["total_pts"], s["pf_by_year"]))
    print("  random NULL PF 5/50/95: %.2f / %.2f / %.2f | fill PF at %.0fth pctile"
          % (r["random_null_pf"][5], r["random_null_pf"][50], r["random_null_pf"][95],
             r["fill_pf_percentile_vs_null"]))
    print("  VERDICT: %s" % r["VERDICT"])
    with open(MD_OUT, "w") as f:
        f.write("# ORG driver-skeleton falsifier\n\n_Generated %s._\n\n```json\n%s\n```\n"
                % (r["generated"], json.dumps(r, indent=2)))
    print("wrote %s" % MD_OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="MULTI_1min_IST_2020_2024.csv")
    ap.add_argument("--inst", default="nq")
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--gap-min", dest="gap_min", type=float, default=10.0)
    ap.add_argument("--gap-max", dest="gap_max", type=float, default=200.0)
    ap.add_argument("--buffer", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=20260611)
    ap.add_argument("--rand-iters", dest="rand_iters", type=int, default=500)
    args = ap.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
