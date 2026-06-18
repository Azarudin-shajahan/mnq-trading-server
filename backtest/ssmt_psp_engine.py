"""SSMT -> PSP -> 1m CISD/PD-array engine (multi-timeframe ICT/GxT model).

Spec: docs/superpowers/specs/2026-06-14-ssmt-psp-multitf-engine-design.md
Plan: docs/superpowers/plans/2026-06-14-ssmt-psp-multitf-engine.md
Backtest point value is $0.50/pt by project convention (never change).

Two spines behind --spine:
  smt-cascade  : 6H SSMT -> 15m PSP -> (90m Stage-2 SSMT) -> 1m CISD/PD-array entry.
  c2c3-closure : daily bias -> swing-TF C2/C3 closure -> 1m CISD/PD-array entry (TTrades).
Both share the 1m CISD entry, PD arrays, CISD-protected stop, target system, gates,
the 1m SL-first fill/walk, and the lookahead invariants.
"""
import numpy as np
import pandas as pd

DATA = "/Users/azarudin/mnq_trading/data"
TRIAD = ("nq", "es", "ym")
TICK = 0.25
SL_BUF = 1.0 * TICK  # buffer beyond the protected swing


# --------------------------------------------------------------------------- #
# Task 1: fractal pivots
# --------------------------------------------------------------------------- #
def swing_highs(high, n=3):
    """Boolean array: True where high[i] is strictly the max of [i-n, i+n]."""
    h = np.asarray(high, float)
    out = np.zeros(len(h), bool)
    for i in range(n, len(h) - n):
        if (h[i] > h[i - n:i]).all() and (h[i] > h[i + 1:i + n + 1]).all():
            out[i] = True
    return out


def swing_lows(low, n=3):
    """Boolean array: True where low[i] is strictly the min of [i-n, i+n]."""
    l = np.asarray(low, float)
    out = np.zeros(len(l), bool)
    for i in range(n, len(l) - n):
        if (l[i] < l[i - n:i]).all() and (l[i] < l[i + 1:i + n + 1]).all():
            out[i] = True
    return out


# --------------------------------------------------------------------------- #
# Task 2 / 4b: loaders + tz-correct CME-anchored resample
# --------------------------------------------------------------------------- #
def load_1m_ohlc(inst, files):
    """Load 1m OHLC for one instrument, tz-convert IST->ET, ET-indexed (tz-naive)."""
    cols = ["timestamp", f"{inst}_open", f"{inst}_high", f"{inst}_low", f"{inst}_close"]
    df = pd.concat([pd.read_csv(f"{DATA}/{f}", usecols=cols, parse_dates=["timestamp"])
                    for f in files], ignore_index=True)
    et = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df.index = et.dt.tz_localize(None)
    df = df.rename(columns={f"{inst}_open": "open", f"{inst}_high": "high",
                            f"{inst}_low": "low", f"{inst}_close": "close"})
    return df[["open", "high", "low", "close"]].sort_index()


def resample_tf(df_et, rule, anchor_et="18:00"):
    """Resample an ET-indexed OHLC frame to `rule` (e.g. '6h','90min') anchored at anchor_et."""
    hh, mm = (int(x) for x in anchor_et.split(":"))
    rule_min = int(pd.tseries.frequencies.to_offset(rule).nanos // 60_000_000_000)
    off = pd.Timedelta(minutes=(hh * 60 + mm) % rule_min)
    return df_et.resample(rule, origin="start_day", offset=off).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def resample_6h(df_et, anchor_et="18:00"):
    """Resample an ET-indexed OHLC frame to 6H buckets anchored at anchor_et."""
    return resample_tf(df_et, "6h", anchor_et)


# --------------------------------------------------------------------------- #
# Task 3: 6H SSMT detector
# --------------------------------------------------------------------------- #
def _prior_pivot(values, pivot_mask, i, n):
    """Most recent pivot CONFIRMED before bar i. A fractal pivot at j needs n right-bars, so it
    is only known at bar j+n; require j + n < i. (Prevents fractal-confirmation lookahead.)"""
    js = [j for j in np.where(pivot_mask[:i])[0] if j + n < i]
    return float(values[js[-1]]) if js else None


def _companion_holds(holds, companions, companion_mode):
    if companion_mode == "either":
        return any(holds)
    if companion_mode == "both":
        return all(holds)
    return holds[companions.index(companion_mode)]


def find_6h_ssmt(frames, inst, companions, companion_mode="either", n=3, upto_idx=None, tf="6h",
                 from_idx=None):
    """Return (bias, protected_level, close_ts) for the FIRST SSMT, else None.

    bull: inst.low[i] < prior inst pivot-low, companion(s) low[i] do NOT break their prior pivot-low.
    NO LOOKAHEAD: prior pivots must be confirmed before bar i; the event timestamp is the bar
    CLOSE (label + tf), since the bar's high/low aren't known until it closes.
    """
    f = frames[inst]
    dur = pd.tseries.frequencies.to_offset(tf)
    hi, lo = f["high"].values, f["low"].values
    plo, phi = swing_lows(lo, n), swing_highs(hi, n)
    comp = {c: frames[c] for c in companions}
    comp_plo = {c: swing_lows(comp[c]["low"].values, n) for c in companions}
    comp_phi = {c: swing_highs(comp[c]["high"].values, n) for c in companions}
    end = len(f) if upto_idx is None else min(upto_idx + 1, len(f))
    start_i = n + 1 if from_idx is None else max(n + 1, from_idx)
    for i in range(start_i, end):
        ref = _prior_pivot(lo, plo, i, n)                    # bull
        if ref is not None and lo[i] < ref:
            holds = [(_prior_pivot(comp[c]["low"].values, comp_plo[c], i, n) is not None
                      and comp[c]["low"].values[i] > _prior_pivot(comp[c]["low"].values, comp_plo[c], i, n))
                     for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                return ("bull", ref, f.index[i] + dur)
        ref = _prior_pivot(hi, phi, i, n)                    # bear
        if ref is not None and hi[i] > ref:
            holds = [(_prior_pivot(comp[c]["high"].values, comp_phi[c], i, n) is not None
                      and comp[c]["high"].values[i] < _prior_pivot(comp[c]["high"].values, comp_phi[c], i, n))
                     for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                return ("bear", ref, f.index[i] + dur)
    return None


def _prior_pivot_series(values, pivot_mask, n):
    """O(n) array: out[i] = value of the most recent pivot CONFIRMED before bar i (j + n < i),
    else NaN. Equivalent to calling _prior_pivot(values, pivot_mask, i, n) for every i, but in a
    single forward scan. (Same confirmed-pivot rule -> no behaviour change, just memoized.)"""
    values = np.asarray(values, float)
    out = np.full(len(values), np.nan)
    pivots = np.where(pivot_mask)[0]
    last, p = np.nan, 0
    for i in range(len(values)):
        while p < len(pivots) and pivots[p] + n < i:
            last = values[pivots[p]]
            p += 1
        out[i] = last
    return out


def all_6h_ssmt(frames, inst, companions, companion_mode, n, tf="6h"):
    """Single-pass version of find_6h_ssmt that returns ALL events as (bias, level, close_ts).
    Identical detector logic to find_6h_ssmt (bull precedence per bar, confirmed prior pivots,
    companion hold rule); pivot masks are computed ONCE instead of per bar (O(n) vs O(n^2))."""
    f = frames[inst]
    dur = pd.tseries.frequencies.to_offset(tf)
    op, hi, lo, cl = f["open"].values, f["high"].values, f["low"].values, f["close"].values
    pp_lo = _prior_pivot_series(lo, swing_lows(lo, n), n)
    pp_hi = _prior_pivot_series(hi, swing_highs(hi, n), n)
    clo = {c: frames[c]["low"].values for c in companions}
    chi = {c: frames[c]["high"].values for c in companions}
    cpp_lo = {c: _prior_pivot_series(clo[c], swing_lows(clo[c], n), n) for c in companions}
    cpp_hi = {c: _prior_pivot_series(chi[c], swing_highs(chi[c], n), n) for c in companions}
    idx = f.index
    events = []
    for i in range(n + 1, len(f)):
        ohlc = (float(op[i]), float(hi[i]), float(lo[i]), float(cl[i]))   # trigger HTF candle (wick filter)
        ref = pp_lo[i]
        if not np.isnan(ref) and lo[i] < ref:
            holds = [(not np.isnan(cpp_lo[c][i]) and clo[c][i] > cpp_lo[c][i]) for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                events.append(("bull", float(ref), idx[i] + dur, ohlc)); continue
        ref = pp_hi[i]
        if not np.isnan(ref) and hi[i] > ref:
            holds = [(not np.isnan(cpp_hi[c][i]) and chi[c][i] < cpp_hi[c][i]) for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                events.append(("bear", float(ref), idx[i] + dur, ohlc))
    return events


# --------------------------------------------------------------------------- #
# Task 4: 15m PSP detector
# --------------------------------------------------------------------------- #
def find_15m_psp(nq15, comp15, bias, after_ts, window_h=24):
    """First 15m opposite-color close in (after_ts, after_ts+window_h] matching bias.
    Returns the bar CLOSE time (label + 15min) so downstream cannot act mid-bar. None if none."""
    end = after_ts + pd.Timedelta(hours=window_h)
    sub = nq15.loc[(nq15.index > after_ts) & (nq15.index <= end)]   # window only -> O(window)
    if not len(sub):
        return None
    comp = comp15.reindex(sub.index)
    nq_up = (sub["close"].values > sub["open"].values)
    cp_up = (comp["close"].values > comp["open"].values)
    valid = comp["open"].notna().values & comp["close"].notna().values
    idxs = sub.index
    for k in range(len(sub)):
        if not valid[k]:
            continue
        if bias == "bull" and (not nq_up[k]) and cp_up[k]:
            return idxs[k] + pd.Timedelta("15min")
        if bias == "bear" and nq_up[k] and (not cp_up[k]):
            return idxs[k] + pd.Timedelta("15min")
    return None


# --------------------------------------------------------------------------- #
# Task 4b: Stage-2 secondary SMT (configurable TF)
# --------------------------------------------------------------------------- #
def _build_smt_precomp(m1, inst, companions, tf, anchor_et, n):
    """Resample the Stage-2 TF + build prior-pivot series ONCE per run (not per event).
    Returns a dict consumed by find_secondary_smt. Same arrays the per-call path would build."""
    insts = (inst, *companions)
    frames = {a: resample_tf(m1[a], tf, anchor_et) for a in insts}
    lo = {a: frames[a]["low"].values for a in insts}
    hi = {a: frames[a]["high"].values for a in insts}
    pp_lo = {a: _prior_pivot_series(lo[a], swing_lows(lo[a], n), n) for a in insts}
    pp_hi = {a: _prior_pivot_series(hi[a], swing_highs(hi[a], n), n) for a in insts}
    return {"frames": frames, "lo": lo, "hi": hi, "pp_lo": pp_lo, "pp_hi": pp_hi}


def find_secondary_smt(m1, inst, companions, bias, after_ts, window_h, tf="90min",
                       anchor_et="18:00", n=3, precomp=None):
    """Stage-2: first same-bias SSMT on `tf`. Acts at the bar CLOSE (label + tf) and uses only
    confirmed prior pivots -> no lookahead. Returns the close ts or None.

    `precomp` (from _build_smt_precomp) memoizes the resample + pivots across events; when None it
    is built internally (same result), so direct callers/tests keep working unchanged."""
    end = after_ts + pd.Timedelta(hours=window_h)
    dur = pd.tseries.frequencies.to_offset(tf)
    if precomp is None:
        precomp = _build_smt_precomp(m1, inst, companions, tf, anchor_et, n)
    f = precomp["frames"][inst]
    idx = f.index
    lo, hi, pp_lo, pp_hi = precomp["lo"], precomp["hi"], precomp["pp_lo"], precomp["pp_hi"]
    for i in range(n + 1, len(f)):
        tclose = idx[i] + dur
        if tclose <= after_ts:
            continue
        if tclose > end:          # idx sorted ascending -> nothing later can be in-window
            break
        if bias == "bull":
            ref = pp_lo[inst][i]
            if np.isnan(ref) or lo[inst][i] >= ref:
                continue
            holds = [(not np.isnan(pp_lo[c][i]) and lo[c][i] > pp_lo[c][i]) for c in companions]
            if any(holds):
                return tclose
        else:
            ref = pp_hi[inst][i]
            if np.isnan(ref) or hi[inst][i] <= ref:
                continue
            holds = [(not np.isnan(pp_hi[c][i]) and hi[c][i] < pp_hi[c][i]) for c in companions]
            if any(holds):
                return tclose
    return None


# --------------------------------------------------------------------------- #
# Task 5a: 1m CISD
# --------------------------------------------------------------------------- #
def find_cisd(o, h, l, c, bias, start, pivot_n=3):
    """Locate the CISD that flips order flow in `bias` direction at/after `start`.
    Returns (confirm_idx, swing_idx, swing_val, cisd_level) or None.
    """
    o, h, l, c = map(np.asarray, (o, h, l, c))
    piv = swing_lows(l, pivot_n) if bias == "bull" else swing_highs(h, pivot_n)
    for swing_idx in [j for j in np.where(piv)[0] if j >= start]:
        # walk back over the leg that made the swing (down-candles for bull / up for bear)
        j = swing_idx
        while j - 1 >= 0 and ((bias == "bull" and c[j - 1] < o[j - 1])
                              or (bias == "bear" and c[j - 1] > o[j - 1])):
            j -= 1
        level = float(o[j])                       # open of first candle of the leg
        # CISD confirm: first close beyond level, but not before the swing pivot itself is
        # confirmed (a fractal low needs pivot_n right-bars) -> start at swing_idx + pivot_n.
        for k in range(swing_idx + pivot_n, len(c)):
            if (bias == "bull" and c[k] > level) or (bias == "bear" and c[k] < level):
                swing_val = float(l[swing_idx]) if bias == "bull" else float(h[swing_idx])
                return (k, int(swing_idx), swing_val, level)
    return None


# --------------------------------------------------------------------------- #
# Task 5b: PD-array detectors
# --------------------------------------------------------------------------- #
def pd_arrays_bull(o, h, l, c, lo_idx, hi_idx, kinds=("fvg", "ifvg", "ob", "breaker")):
    """Bullish PD arrays in window [lo_idx, hi_idx]. Each: {kind, proximal, distal, idx}.
    proximal = price hit FIRST on a downward retrace (higher edge); distal = lower edge.
    """
    o, h, l, c = map(np.asarray, (o, h, l, c))
    out = []
    a, b = lo_idx, hi_idx
    if "fvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if l[i + 1] > h[i - 1]:                       # 3-candle bullish imbalance
                out.append({"kind": "fvg", "proximal": float(l[i + 1]),
                            "distal": float(h[i - 1]), "idx": i})
    if "ifvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if h[i + 1] < l[i - 1]:                       # a bearish FVG ...
                gap_hi, gap_lo = float(l[i - 1]), float(h[i + 1])
                for k in range(i + 2, min(b + 1, len(c))):
                    if c[k] > gap_hi:                     # ... violated to the upside -> inverts
                        out.append({"kind": "ifvg", "proximal": gap_hi,
                                    "distal": gap_lo, "idx": k}); break
    if "ob" in kinds:
        for i in range(b, a, -1):                          # last down-close candle before the up-leg
            if c[i] < o[i]:
                out.append({"kind": "ob", "proximal": float(o[i]),
                            "distal": float(l[i]), "idx": i}); break
    if "breaker" in kinds:
        if lo_idx < len(c) and c[lo_idx] < o[lo_idx]:
            out.append({"kind": "breaker", "proximal": float(o[lo_idx]),
                        "distal": float(l[lo_idx]), "idx": lo_idx})
    return out


def _pd_arrays_bear(o, h, l, c, hi_idx, lo_idx, kinds):
    """Bearish mirror of pd_arrays_bull. proximal = lower edge (hit first on an up retrace)."""
    o, h, l, c = map(np.asarray, (o, h, l, c))
    out = []
    a, b = hi_idx, lo_idx
    if "fvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if h[i + 1] < l[i - 1]:
                out.append({"kind": "fvg", "proximal": float(h[i + 1]),
                            "distal": float(l[i - 1]), "idx": i})
    if "ifvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if l[i + 1] > h[i - 1]:
                gap_lo, gap_hi = float(h[i - 1]), float(l[i + 1])
                for k in range(i + 2, min(b + 1, len(c))):
                    if c[k] < gap_lo:
                        out.append({"kind": "ifvg", "proximal": gap_lo,
                                    "distal": gap_hi, "idx": k}); break
    if "ob" in kinds:
        for i in range(b, a, -1):
            if c[i] > o[i]:
                out.append({"kind": "ob", "proximal": float(o[i]),
                            "distal": float(h[i]), "idx": i}); break
    if "breaker" in kinds:
        if hi_idx < len(c) and c[hi_idx] > o[hi_idx]:
            out.append({"kind": "breaker", "proximal": float(o[hi_idx]),
                        "distal": float(h[hi_idx]), "idx": hi_idx})
    return out


# --------------------------------------------------------------------------- #
# Task 5c: assemble entry (entry/sl/confirm anchor)
# --------------------------------------------------------------------------- #
def assemble_entry(o, h, l, c, bias, start, ssmt_low, ssmt_high, arrays, sl_mode, pivot_n=3):
    """LTF assembly: CISD -> first PD array -> entry + sl + confirm_idx. The TP is NOT chosen here
    from a future swing (that would be lookahead); it is resolved CAUSALLY in walk_setup as the
    impulse peak observed up to the fill. Returns None if incomplete."""
    cis = find_cisd(o, h, l, c, bias, start, pivot_n)
    if cis is None:
        return None
    confirm_idx, swing_idx, swing_val, _ = cis
    if bias == "bull":
        arrs = pd_arrays_bull(o, h, l, c, swing_idx, confirm_idx, arrays)
        if not arrs:
            return None
        protected = swing_val if sl_mode == "local" else ssmt_low
        sl = protected - SL_BUF
        arr = min(arrs, key=lambda x: x["idx"])
        entry = arr["proximal"]
        if not (sl < entry):
            return None
    else:
        arrs = _pd_arrays_bear(o, h, l, c, swing_idx, confirm_idx, arrays)
        if not arrs:
            return None
        protected = swing_val if sl_mode == "local" else ssmt_high
        sl = protected + SL_BUF
        arr = min(arrs, key=lambda x: x["idx"])
        entry = arr["proximal"]
        if not (entry < sl):
            return None
    return {"entry": entry, "sl": sl, "confirm_idx": int(confirm_idx),
            "array_idx": int(arr["idx"]), "kind": arr["kind"], "bias": bias}


# --------------------------------------------------------------------------- #
# Task 5d: nested-FVG key-level gate
# --------------------------------------------------------------------------- #
def htf_fvgs(df_tf, bias, upto_ts):
    """Bias-direction FVG zones on df_tf whose 3rd bar has fully CLOSED by upto_ts (no lookahead).
    Returns [(lo, hi), ...]."""
    h, l, idx = df_tf["high"].values, df_tf["low"].values, df_tf.index
    dur = pd.Series(idx).diff().min() if len(idx) > 1 else pd.Timedelta(0)
    zones = []
    for i in range(1, len(df_tf) - 1):
        if idx[i + 1] + dur > upto_ts:   # 3rd bar must be closed (label + tf) before the cutoff
            break
        if bias == "bull" and l[i + 1] > h[i - 1]:
            zones.append((float(h[i - 1]), float(l[i + 1])))
        if bias == "bear" and h[i + 1] < l[i - 1]:
            zones.append((float(h[i + 1]), float(l[i - 1])))
    return zones


def passes_key_level(entry, bias, fvg_zones, swing_level, mode, tol):
    """GxT key-level gate: nested inside an HTF FVG, near the swept swing, or either."""
    in_fvg = any(lo <= entry <= hi for lo, hi in fvg_zones)
    near_swing = abs(entry - swing_level) <= tol
    if mode == "htf-fvg":
        return in_fvg
    if mode == "swing":
        return near_swing
    return in_fvg or near_swing


# --------------------------------------------------------------------------- #
# Task 5e: fidelity helpers
# --------------------------------------------------------------------------- #
MACRO_WINDOWS = [("09:50", "10:10"), ("10:50", "11:10"), ("13:10", "13:40"), ("15:15", "15:45")]

# TTrades index kill zones (ET): NY AM 08:30-11:00 is where most of the daily range forms.
SESSIONS = {"all": None,
            "ny": [("08:30", "16:00")],
            "ny-am": [("08:30", "11:00")],
            "ny-pm": [("13:30", "16:00")],
            "killzones": [("08:30", "11:00"), ("13:30", "16:00")]}


def in_session(ts_et, mode):
    """True if the ET fill timestamp is inside the selected kill-zone(s); 'all' = no filter."""
    wins = SESSIONS.get(mode)
    if not wins:
        return True
    hm = ts_et.strftime("%H:%M")
    return any(a <= hm <= b for a, b in wins)


def is_displacement(o, h, l, c, idx, frac=0.5):
    """True if candle idx is a strong-bodied displacement (|c-o| >= frac*range)."""
    rng = h[idx] - l[idx]
    return rng > 0 and abs(c[idx] - o[idx]) >= frac * rng


def htf_bias(df_tf, upto_ts, n=3):
    """HTF structural bias at/before upto_ts: HH+HL=bull, LH+LL=bear, else none."""
    sub = df_tf[df_tf.index <= upto_ts]
    h, l = sub["high"].values, sub["low"].values
    ph, pl = np.where(swing_highs(h, n))[0], np.where(swing_lows(l, n))[0]
    if len(ph) < 2 or len(pl) < 2:
        return "none"
    hh, hl = h[ph[-1]] > h[ph[-2]], l[pl[-1]] > l[pl[-2]]
    if hh and hl:
        return "bull"
    if (not hh) and (not hl):
        return "bear"
    return "none"


def in_macro(ts_et, windows=MACRO_WINDOWS):
    """True if the ET timestamp falls inside an algorithmic macro window."""
    hm = ts_et.strftime("%H:%M")
    return any(a <= hm <= b for a, b in windows)


def prior_day_levels(df_et):
    """Per-date prior-day high/low (PDH/PDL). Returns {date: (pdh, pdl)}."""
    g = df_et.groupby(df_et.index.normalize())
    pdh, pdl = g["high"].max().shift(1), g["low"].min().shift(1)
    return {d: (float(pdh[d]), float(pdl[d])) for d in pdh.index if not pd.isna(pdh[d])}


# --------------------------------------------------------------------------- #
# Task B1: Spine-B detectors
# --------------------------------------------------------------------------- #
def candle_closure(o, h, l, c, i, bias):
    """TTrades closure type at candle i vs prior candle i-1, for `bias`. None if no closure."""
    o, h, l, c = map(np.asarray, (o, h, l, c))
    if i < 1:
        return None
    body_hi, body_lo = max(o[i - 1], c[i - 1]), min(o[i - 1], c[i - 1])
    if bias == "bull":
        if l[i] < l[i - 1]:                       # swept prior low
            return "c2" if c[i] > l[i - 1] else "continuation"
        if c[i] > body_hi:                        # no sweep, engulf C2 body up
            return "c3"
    else:
        if h[i] > h[i - 1]:
            return "c2" if c[i] < h[i - 1] else "continuation"
        if c[i] < body_lo:
            return "c3"
    return None


def equilibrium(po, ph, pl, pc):
    """50% of the prior candle's range (TTrades EQ)."""
    return (ph + pl) / 2.0


def in_discount(price, eq):
    return price <= eq


def in_premium(price, eq):
    return price >= eq


def is_relevant(level, prior_level, sep):
    """Swing-significance: a swing is relevant only if it is >= sep from the prior same-side swing
    (range-expansion separation); otherwise it is a failure swing to be ignored."""
    return prior_level is None or abs(level - prior_level) >= sep


def daily_bias_pdclose(fb, upto_ts, tf="1d"):
    """TTrades flagship mechanical daily bias (Step 1) from the last CLOSED bias-TF candle vs the
    prior one's range (causal: only candles fully closed by upto_ts):
      close > prior high -> bull continuation ; close < prior low -> bear continuation
      sweep prior low + close back above -> bull reversal ; sweep prior high + close back below -> bear.
    Returns 'bull'/'bear'/'none'."""
    dur = pd.tseries.frequencies.to_offset(tf)
    closed = fb[fb.index + dur <= upto_ts]
    if len(closed) < 2:
        return "none"
    o, h, l, c = (float(closed.iloc[-1][k]) for k in ("open", "high", "low", "close"))
    ph, pl = float(closed.iloc[-2]["high"]), float(closed.iloc[-2]["low"])
    if c > ph:
        return "bull"
    if c < pl:
        return "bear"
    if l < pl and c > pl:
        return "bull"
    if h > ph and c < ph:
        return "bear"
    return "none"


def spine_b_setups(cfg, m1):
    """TTrades C2/C3-closure spine -> yields (bias, level, trigger_ts) like find_6h_ssmt does, so the
    SAME downstream (1m CISD entry + protected-swing SL + target + walk_setup + gates) applies.
    bias: daily closure; swing TF C2/C3 closure = the trigger; level = swept swing for the SL ref."""
    n = cfg["pivot_n"]
    fb = resample_tf(m1["nq"], cfg["tf_bias"], cfg["anchor_et"])
    fs = resample_tf(m1["nq"], cfg["tf_swing"], cfg["anchor_et"])
    dur_s = pd.tseries.frequencies.to_offset(cfg["tf_swing"])
    fo, fh, fl, fc = (fs["open"].values, fs["high"].values, fs["low"].values, fs["close"].values)
    bias_mode = cfg.get("bias_mode", "struct")
    out = []
    for i in range(2, len(fs)):
        # daily bias as of this swing bar's close (both modes causal/confirmed)
        tclose = fs.index[i] + dur_s
        bias = (daily_bias_pdclose(fb, tclose, cfg["tf_bias"]) if bias_mode == "pd-close"
                else htf_bias(fb, tclose, n))
        if bias == "none":
            continue
        cc = candle_closure(fo, fh, fl, fc, i, bias)
        if cc not in ("c2", "c3"):
            continue
        # protected/level reference = the swept prior swing extreme on the swing TF
        level = float(fl[i - 1]) if bias == "bull" else float(fh[i - 1])
        ohlc = (float(fo[i]), float(fh[i]), float(fl[i]), float(fc[i]))   # C2 candle (wick filter)
        out.append((bias, level, fs.index[i] + dur_s, ohlc))   # trigger = swing bar CLOSE (no lookahead)
    return out


def spine_silver_bullet_setups(cfg, m1, frame_hour=9, win_start="10:00", win_end="11:00"):
    """AM Silver Bullet (TTrades, NQ): the `frame_hour` (09:00 ET) hourly candle defines the range.
    In the win_start-win_end window, the first sweep of one side flips bias to the OTHER side, and the
    target is the opposite side of the 9 a.m. range. Yields
    (bias, level, sweep_ts, trig_ohlc, tp_level) so the shared 1m CISD/PD-array block applies.
    No lookahead: the 9 a.m. candle is fully closed by 10:00, and the sweep ts is a 1m bar in-window."""
    nq = m1["nq"]
    h1 = resample_tf(nq, "1h", "18:00")        # clock-hour ET candles (offset 0 -> tops of the hour)
    hh = h1.index.strftime("%H:%M")
    nine = h1[hh == f"{frame_hour:02d}:00"]
    nine_hl = {t.normalize(): (float(nine.at[t, "high"]), float(nine.at[t, "low"])) for t in nine.index}
    idx = nq.index
    hm = idx.strftime("%H:%M")
    sub = nq[(hm >= win_start) & (hm < win_end)]
    o, h, l, c = sub["open"].values, sub["high"].values, sub["low"].values, sub["close"].values
    dates = sub.index.normalize()
    out, seen = [], set()
    for k in range(len(sub)):
        d = dates[k]
        if d in seen:
            continue
        hl = nine_hl.get(d)
        if hl is None:
            continue
        hi9, lo9 = hl
        if h[k] >= hi9:        # swept the 9am high -> bearish reversal, target the 9am low
            out.append(("bear", hi9, sub.index[k], (float(o[k]), float(h[k]), float(l[k]), float(c[k])), lo9))
            seen.add(d)
        elif l[k] <= lo9:      # swept the 9am low -> bullish reversal, target the 9am high
            out.append(("bull", lo9, sub.index[k], (float(o[k]), float(h[k]), float(l[k]), float(c[k])), hi9))
            seen.add(d)
    return out


def spine_son_setups(cfg, m1, sess_open="09:30"):
    """ICT Son Model: the draw on liquidity = the NEAREST untaken 1H old high/low relative to the
    NY-session open; bias points toward the closer draw; the opposite stop-raid (a 1m CISD, handled
    by the shared block) is the entry; target = the draw level. One setup per day.
    Yields (bias, level, sess_open_ts, trig_ohlc, tp_level). No lookahead: only 1H pivots CONFIRMED
    (label at bar j+n) strictly before the session open are used; trigger_ts = the session open bar."""
    n = cfg["pivot_n"]
    h1 = resample_tf(m1["nq"], "1h", "18:00")
    hv, lv, hidx = h1["high"].values, h1["low"].values, h1.index
    ph = [(hidx[j + n], float(hv[j])) for j in np.where(swing_highs(hv, n))[0] if j + n < len(hidx)]
    pl = [(hidx[j + n], float(lv[j])) for j in np.where(swing_lows(lv, n))[0] if j + n < len(hidx)]
    nq = m1["nq"]
    opens = nq[nq.index.strftime("%H:%M") == sess_open]
    out = []
    for t in opens.index:
        p0 = float(opens.at[t, "open"])
        highs_above = [v for ct, v in ph if ct < t and v > p0]
        lows_below = [v for ct, v in pl if ct < t and v < p0]
        Hd = min(highs_above) if highs_above else None
        Ld = max(lows_below) if lows_below else None
        if Hd is None and Ld is None:
            continue
        if Ld is None or (Hd is not None and (Hd - p0) <= (p0 - Ld)):
            bias, tp_level = "bull", Hd            # draw is the nearer old high above -> fade down-raid up
        else:
            bias, tp_level = "bear", Ld
        out.append((bias, p0, t, (p0, p0, p0, p0), tp_level))
    return out


# --------------------------------------------------------------------------- #
# Task 6: 1m fill + walk
# --------------------------------------------------------------------------- #
def walk_setup(h, l, confirm_idx, entry, sl, bias, tp_fixed=None):
    """Causal 1m resolution. Starts the fill scan at confirm_idx+1 (setup fully known). Tracks the
    impulse peak (running max-high for a bull) BEFORE the fill; at the fill bar TP = that peak (or
    tp_fixed when given). SL-first. Returns (outcome, pnl_points, fill_idx). No lookahead."""
    h, l = np.asarray(h, float), np.asarray(l, float)
    run = h[confirm_idx] if bias == "bull" else l[confirm_idx]   # peak/trough BEFORE the fill
    filled, fill_i, tp = False, -1, None
    for i in range(confirm_idx + 1, len(h)):
        if not filled:
            hit = (l[i] <= entry) if bias == "bull" else (h[i] >= entry)
            if hit:
                filled, fill_i = True, i
                tp = tp_fixed if tp_fixed is not None else run
                if (bias == "bull" and not tp > entry) or (bias == "bear" and not tp < entry):
                    return ("notarget", 0.0, -1)
            else:
                run = max(run, h[i]) if bias == "bull" else min(run, l[i])
                continue
        if bias == "bull":
            if l[i] <= sl:
                return ("loss", sl - entry, fill_i)
            if h[i] >= tp:
                return ("win", tp - entry, fill_i)
        else:
            if h[i] >= sl:
                return ("loss", entry - sl, fill_i)
            if l[i] <= tp:
                return ("win", entry - tp, fill_i)
    return ("be", 0.0, fill_i) if filled else ("nofill", 0.0, -1)


# --------------------------------------------------------------------------- #
# Task 6: data file constants + 15m loader + backtest loop
# --------------------------------------------------------------------------- #
FILES_2020_2024 = {"1m": ["MULTI_1min_IST_2020_2024.csv"],
                   "15m": ["MULTI_15min_IST_2020_2024.csv"]}
FILES_2025 = {"1m": ["MULTI_1min_IST_2025.csv"],
              "15m": ["MULTI_15min_IST_2025.csv"]}


def _load_15m(inst, files):
    cols = ["timestamp", f"{inst}_open", f"{inst}_close"]
    df = pd.concat([pd.read_csv(f"{DATA}/{f}", usecols=cols, parse_dates=["timestamp"])
                    for f in files], ignore_index=True)
    et = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df.index = et.dt.tz_localize(None)
    return df.rename(columns={f"{inst}_open": "open", f"{inst}_close": "close"})[["open", "close"]].sort_index()


def _sig_sep(frame, frac=0.5):
    """Swing-significance separation = frac * mean candle range of the reference frame."""
    return frac * float((frame["high"] - frame["low"]).mean())


def opposing_run_frac(o, h, l, c, bias):
    """TTrades 'opposing run' = the wick opposite the bias, as a fraction of candle range.
    bull -> lower wick min(o,c)-l ; bear -> upper wick h-max(o,c). Small frac = shallow sweep =
    'supports expansion' (Understanding Wick Sizes / Easy Daily Bias). Returns 1.0 for a zero range."""
    rng = h - l
    if rng <= 0:
        return 1.0
    opp = (min(o, c) - l) if bias == "bull" else (h - max(o, c))
    return opp / rng


def _prior_same_side(frame, bias, before_ts, level, n):
    """The same-side confirmed pivot BEFORE the swept `level`'s bar (for swing significance).
    Returns the second-most-recent confirmed pivot value, or None."""
    vals = frame["low"].values if bias == "bull" else frame["high"].values
    mask = swing_lows(vals, n) if bias == "bull" else swing_highs(vals, n)
    idx = frame.index
    cand = [j for j in np.where(mask)[0] if idx[min(j + n, len(idx) - 1)] < before_ts]
    return float(vals[cand[-2]]) if len(cand) >= 2 else None


def run_backtest(cfg, files):
    """Walk spine triggers; one trade per trigger. Returns trades DataFrame.

    Both spines build the SAME setup record then run the shared 1m CISD/PD-array entry block.
    All gates use only info known by the CISD close -> no lookahead.
    """
    if cfg.get("target") == "failure-swing":
        raise NotImplementedError("failure-swing target: implement order-pairing in a follow-up task")
    spine = cfg.get("spine", "smt-cascade")
    m1 = {a: load_1m_ohlc(a, files["1m"]) for a in TRIAD}
    m15 = {a: _load_15m(a, files["15m"]) for a in TRIAD}
    f6 = {a: resample_6h(m1[a], cfg["anchor_et"]) for a in TRIAD}
    kf = {a: resample_tf(m1[a], cfg["key_level_tf"], cfg["anchor_et"]) for a in TRIAD}
    hbf = ({a: resample_tf(m1[a], cfg["htf_bias"], cfg["anchor_et"]) for a in TRIAD}
           if cfg["htf_bias"] != "off" else None)
    pdmap = {a: prior_day_levels(m1[a]) for a in TRIAD} if cfg["target"] == "pdh-pdl" else None
    comp_map = {"either": ["es", "ym"], "es": ["es"], "ym": ["ym"], "both": ["es", "ym"]}
    companions = comp_map[cfg["companion"]]
    n = cfg["pivot_n"]

    # --- Build the spine-agnostic setup list ---
    setups = []
    if spine == "smt-cascade":
        comp = companions[0]
        # precompute the Stage-2 resample + pivots ONCE (was rebuilt per event -> the 68-min cost)
        s2precomp = (_build_smt_precomp(m1, "nq", companions, cfg["stage2_tf"], cfg["anchor_et"], n)
                     if cfg["stage2"] == "secondary-smt" else None)
        for bias, level, ssmt_ts, trig_ohlc in all_6h_ssmt(f6, "nq", companions, cfg["companion"], n, "6h"):
            psp_ts = find_15m_psp(m15["nq"], m15[comp], bias, ssmt_ts, cfg["psp_window_h"])
            if psp_ts is None:
                continue
            entry_start_ts = psp_ts
            if cfg["stage2"] == "secondary-smt":
                stage2_ts = find_secondary_smt(m1, "nq", companions, bias, psp_ts,
                                               cfg["psp_window_h"], cfg["stage2_tf"],
                                               cfg["anchor_et"], n, precomp=s2precomp)
                if stage2_ts is None:
                    continue
                entry_start_ts = stage2_ts
            setups.append({"bias": bias, "level": level, "entry_start_ts": entry_start_ts,
                           "ssmt_ts": ssmt_ts, "psp_ts": psp_ts, "trig_ohlc": trig_ohlc,
                           "sig_frame": f6["nq"], "sig_before": ssmt_ts})
    elif spine == "c2c3-closure":
        fs_nq = resample_tf(m1["nq"], cfg["tf_swing"], cfg["anchor_et"])
        for bias, level, trigger_ts, trig_ohlc in spine_b_setups(cfg, m1):
            setups.append({"bias": bias, "level": level, "entry_start_ts": trigger_ts,
                           "ssmt_ts": trigger_ts, "psp_ts": None, "trig_ohlc": trig_ohlc,
                           "sig_frame": fs_nq, "sig_before": trigger_ts})
    elif spine == "silver-bullet":
        h1_nq = resample_tf(m1["nq"], "1h", "18:00")
        for bias, level, trigger_ts, trig_ohlc, tp_level in spine_silver_bullet_setups(cfg, m1):
            setups.append({"bias": bias, "level": level, "entry_start_ts": trigger_ts,
                           "ssmt_ts": trigger_ts, "psp_ts": None, "trig_ohlc": trig_ohlc,
                           "tp_level": tp_level, "sig_frame": h1_nq, "sig_before": trigger_ts})
    elif spine == "son-model":
        h1_nq = resample_tf(m1["nq"], "1h", "18:00")
        for bias, level, trigger_ts, trig_ohlc, tp_level in spine_son_setups(cfg, m1):
            setups.append({"bias": bias, "level": level, "entry_start_ts": trigger_ts,
                           "ssmt_ts": trigger_ts, "psp_ts": None, "trig_ohlc": trig_ohlc,
                           "tp_level": tp_level, "sig_frame": h1_nq, "sig_before": trigger_ts})
    else:
        raise ValueError(f"unknown spine: {spine}")

    # --- Shared block: 1m CISD/PD-array entry + gates + walk (identical for both spines) ---
    exec_inst = companions[0] if cfg["exec"] == "failure-swing" else "nq"
    ef = (resample_tf(m1[exec_inst], cfg["tf_exec"], cfg["anchor_et"])
          if (spine == "c2c3-closure" and cfg["eq_zone"] == "on") else None)
    dur_exec = pd.tseries.frequencies.to_offset(cfg["tf_exec"]) if ef is not None else None
    trades = []
    for s in setups:
        bias, level, entry_start_ts = s["bias"], s["level"], s["entry_start_ts"]
        # swing-significance filter (both spines, default off)
        if cfg.get("swing_sig", "off") == "on":
            prior_level = _prior_same_side(s["sig_frame"], bias, s["sig_before"], level, n)
            if not is_relevant(level, prior_level, _sig_sep(s["sig_frame"])):
                continue
        # shallow-sweep wick filter (default off): the trigger HTF candle's opposing run must be
        # small -> 'supports expansion' (TTrades wick-size rule). Trig candle is fully closed (no LA).
        if cfg.get("wick_filter", "off") == "on":
            if opposing_run_frac(*s["trig_ohlc"], bias) > cfg["wick_frac"]:
                continue
        win = m1[exec_inst].loc[entry_start_ts: entry_start_ts + pd.Timedelta(hours=cfg["psp_window_h"])]
        if len(win) < 5 * n:
            continue
        o, hh, ll, cc = (win["open"].values, win["high"].values,
                         win["low"].values, win["close"].values)
        e = assemble_entry(o, hh, ll, cc, bias, 0, ssmt_low=level, ssmt_high=level,
                           arrays=tuple(cfg["arrays"]), sl_mode=cfg["sl"], pivot_n=n)
        if e is None:
            continue
        # equilibrium gate (Spine B): entry must be in discount (bull) / premium (bear)
        if ef is not None:
            prev = ef.loc[ef.index + dur_exec <= entry_start_ts]
            if len(prev):
                pc = prev.iloc[-1]
                eq = equilibrium(pc["open"], pc["high"], pc["low"], pc["close"])
                ok = in_discount(e["entry"], eq) if bias == "bull" else in_premium(e["entry"], eq)
                if not ok:
                    continue
        # all gates below use only info known by the CISD close -> no lookahead
        confirm_ts = win.index[e["confirm_idx"]]
        zones = htf_fvgs(kf[exec_inst], bias, confirm_ts)    # HTF FVGs formed before the CISD close
        if not passes_key_level(e["entry"], bias, zones, level, cfg["key_level"], cfg["key_level_tol"]):
            continue
        # displacement gate (array candle is in the past, fully known)
        if cfg["displacement"] == "on":
            di = e["array_idx"]
            if not (is_displacement(o, hh, ll, cc, di, cfg["disp_frac"]) or
                    (di + 1 < len(cc) and is_displacement(o, hh, ll, cc, di + 1, cfg["disp_frac"]))):
                continue
        # HTF bias alignment (TTrades Item 53): block if HTF bias opposes the trigger bias
        if hbf is not None and htf_bias(hbf[exec_inst], s["ssmt_ts"], n) == ("bear" if bias == "bull" else "bull"):
            continue
        # target: PDH/PDL (prior day, known) / fixed 2R (TTrades stated target) / else causal peak
        tp_fixed = None
        if cfg["target"] == "pdh-pdl":
            lev = pdmap[exec_inst].get(confirm_ts.normalize())
            if lev is None:
                continue
            tp_fixed = lev[0] if bias == "bull" else lev[1]
        elif cfg["target"] == "2r":
            risk = abs(e["entry"] - e["sl"])
            tp_fixed = e["entry"] + 2 * risk if bias == "bull" else e["entry"] - 2 * risk
        # Silver Bullet (or any spine carrying an explicit target level) overrides with that level
        if s.get("tp_level") is not None and cfg["target"] not in ("2r",):
            tp_fixed = s["tp_level"]
        out, pnl, fill_idx = walk_setup(hh, ll, e["confirm_idx"], e["entry"], e["sl"], bias, tp_fixed)
        if out in ("nofill", "notarget"):
            continue
        entry_ts = win.index[fill_idx]
        # session/kill-zone gate on the ACTUAL fill time (TTrades kill zones; default 'all' = 24h)
        if not in_session(entry_ts, cfg.get("session", "all")):
            continue
        # macro-time gate on the ACTUAL fill time (ICT macros)
        if cfg["macro"] == "precise" and not in_macro(entry_ts):
            continue
        risk = abs(e["entry"] - e["sl"])
        trades.append({"ssmt_ts": s["ssmt_ts"], "psp_ts": s["psp_ts"], "entry_ts": entry_ts,
                       "inst": exec_inst, "dir": bias, "kind": e["kind"],
                       "entry": round(e["entry"], 2), "sl": round(e["sl"], 2),
                       "out": out, "pnl": round(pnl, 2),
                       "R": round(pnl / risk, 2) if risk else 0.0, "year": s["ssmt_ts"].year})
    return pd.DataFrame(trades)


# --------------------------------------------------------------------------- #
# Task 7 / B2: stats, per-year, CLI
# --------------------------------------------------------------------------- #
import argparse


def stats(tr):
    if not len(tr):
        return {"n": 0, "pf": 0.0, "wr": 0.0, "net": 0.0, "maxdd": 0.0}
    wins = tr.loc[tr.pnl > 0, "pnl"].sum()
    loss = -tr.loc[tr.pnl < 0, "pnl"].sum()
    eq = tr.pnl.cumsum()
    dd = (eq - eq.cummax()).min()
    return {"n": int(len(tr)), "pf": round(wins / loss, 2) if loss else float("inf"),
            "wr": round((tr.pnl > 0).mean() * 100, 1), "net": round(tr.pnl.sum(), 2),
            "maxdd": round(float(dd), 2)}


def peryear(tr):
    if not len(tr):
        return {}
    return {int(y): round(g.pnl.sum(), 2) for y, g in tr.groupby("year")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", choices=["smt-cascade", "c2c3-closure", "silver-bullet", "son-model"], default="smt-cascade")
    ap.add_argument("--exec", choices=["nq", "failure-swing"], default="nq")
    ap.add_argument("--companion", choices=["es", "ym", "either", "both"], default="either")
    ap.add_argument("--stage2", choices=["secondary-smt", "off"], default="secondary-smt")
    ap.add_argument("--stage2-tf", default="90min")
    ap.add_argument("--key-level", choices=["swing", "htf-fvg", "either"], default="either")
    ap.add_argument("--key-level-tf", default="1h")
    ap.add_argument("--key-level-tol", type=float, default=20.0)
    ap.add_argument("--displacement", choices=["on", "off"], default="on")
    ap.add_argument("--disp-frac", type=float, default=0.5)
    ap.add_argument("--htf-bias", choices=["off", "1d", "4h"], default="1d")
    ap.add_argument("--macro", choices=["session", "precise"], default="session")
    ap.add_argument("--session", choices=["all", "ny", "ny-am", "ny-pm", "killzones"], default="all",
                    help="restrict ENTRY fill time to a TTrades kill zone (ET); 'all' = 24h (default)")
    ap.add_argument("--arrays", default="fvg,ifvg,ob,breaker")
    ap.add_argument("--target", choices=["nearest-swing", "pdh-pdl", "2r", "failure-swing"], default="nearest-swing")
    ap.add_argument("--sl", choices=["local", "ssmt"], default="local")
    ap.add_argument("--wick-filter", choices=["off", "on"], default="off",
                    help="require the trigger HTF candle opposing-run (wick) <= --wick-frac (shallow sweep = expansion)")
    ap.add_argument("--wick-frac", type=float, default=0.5)
    ap.add_argument("--anchor-et", default="18:00")
    ap.add_argument("--psp-window-h", type=int, default=24)
    ap.add_argument("--pivot-n", type=int, default=3)
    ap.add_argument("--eq-zone", choices=["on", "off"], default="on")
    ap.add_argument("--swing-sig", choices=["on", "off"], default="off")
    ap.add_argument("--tf-bias", default="1d")
    ap.add_argument("--tf-swing", default="4h")
    ap.add_argument("--tf-exec", default="15min")
    ap.add_argument("--bias-mode", choices=["struct", "pd-close"], default="struct",
                    help="Spine-B daily bias: struct (HH/HL) or pd-close (TTrades close-vs-prior-day-range)")
    ap.add_argument("--holdout", action="store_true", help="run on sealed 2025 data")
    a = ap.parse_args()
    cfg = {"spine": a.spine, "exec": a.exec, "companion": a.companion, "arrays": a.arrays.split(","),
           "stage2": a.stage2, "stage2_tf": a.stage2_tf,
           "key_level": a.key_level, "key_level_tf": a.key_level_tf, "key_level_tol": a.key_level_tol,
           "displacement": a.displacement, "disp_frac": a.disp_frac,
           "htf_bias": a.htf_bias, "macro": a.macro,
           "target": a.target, "sl": a.sl, "anchor_et": a.anchor_et,
           "psp_window_h": a.psp_window_h, "pivot_n": a.pivot_n,
           "eq_zone": a.eq_zone, "swing_sig": a.swing_sig,
           "tf_bias": a.tf_bias, "tf_swing": a.tf_swing, "tf_exec": a.tf_exec,
           "wick_filter": a.wick_filter, "wick_frac": a.wick_frac, "session": a.session,
           "bias_mode": a.bias_mode}
    files = FILES_2025 if a.holdout else FILES_2020_2024
    tr = run_backtest(cfg, files)
    print("CONFIG:", cfg, "| holdout:", a.holdout)
    print("STATS :", stats(tr))
    print("PERYR :", peryear(tr))
    if len(tr):
        print(tr.to_string(index=False))


if __name__ == "__main__":
    main()
