"""
MNQ GxT ENGINE v8.18 - GxT full alignment: NQ-leads, Driver P2, C2/C3 gate
============================================================================
New flags:
  --nq-leads            For YM/GC/RTY entries: NQ must have moved further in same
                        direction from session open (lagging asset gate).
  --driver-model        9:30 Driver entry on YM/GC/RTY only (NQ/ES excluded).
                        Entry at body midpoint retracement, TP at PDH/PDL.
  --h4-direction-gate   C2/C3 model gate for NY_AM: block entries where 16:00 IST
                        4H bar expands strongly (>=40% body) against daily bias.
  --c2-continuation     On C2 days blocked by h4-direction-gate, flip direction
                        and look for continuation FVG entries instead.

Inherits from v8.17: --us-holiday-filter, --entry-cutoff-ist.
"""

import argparse, sys, os, csv, datetime
from collections import defaultdict, namedtuple

import pandas as pd
import numpy as np

# ── Economic calendar ─────────────────────────────────────────────────────────
_ECO_CAL_PATH = os.path.expanduser("~/mnq_trading/data/economic_calendar.csv")

def load_economic_calendar():
    """Load affect_date -> surprise_direction mapping from economic_calendar.csv."""
    if not os.path.exists(_ECO_CAL_PATH):
        print(f"  WARNING: economic_calendar.csv not found at {_ECO_CAL_PATH}")
        print(f"  Run: /usr/local/bin/python3 ~/mnq_trading/scripts/build_economic_calendar.py")
        return {}
    df = pd.read_csv(_ECO_CAL_PATH, parse_dates=["affect_date"])
    cal = {}
    for _, row in df.iterrows():
        d = row["affect_date"].date()
        direction = row["surprise_direction"]
        if direction in ("bull", "bear"):
            # Last event of the day wins if multiple events on same day
            cal[d] = direction
    return cal

# ── Paths ─────────────────────────────────────────────────────────────────────
DEFAULT_5M  = os.path.expanduser("~/mnq_trading/data/MULTI_5min_IST_2020_2024.csv")
DEFAULT_4H  = os.path.expanduser("~/mnq_trading/data/MULTI_4h_IST_2020_2024.csv")
DEFAULT_1M  = os.path.expanduser("~/mnq_trading/data/MULTI_1min_IST_2020_2024.csv")
DEFAULT_15M = os.path.expanduser("~/mnq_trading/data/MULTI_15min_IST_2020_2025.csv")

POINT_VALUE = 0.50  # intentional backtest scale — live = $2/pt NQ, never change

# Instrument-specific config
INST_CONFIG = {
    'nq':  dict(min_gap=3.0,  tick=0.25, disp_ratio=1.5, disp_body=0.50),
    'es':  dict(min_gap=1.0,  tick=0.25, disp_ratio=1.5, disp_body=0.50),
    'ym':  dict(min_gap=6.0,  tick=1.0,  disp_ratio=1.5, disp_body=0.50),
    'gc':  dict(min_gap=2.0,  tick=0.10, disp_ratio=1.5, disp_body=0.50),
    'rty': dict(min_gap=1.5,  tick=0.10, disp_ratio=1.5, disp_body=0.50),
    'cl':  dict(min_gap=0.10, tick=0.01,   disp_ratio=1.5, disp_body=0.50),
    'rb':  dict(min_gap=0.003,tick=0.0001, disp_ratio=1.5, disp_body=0.50),
    'ho':  dict(min_gap=0.003,tick=0.0001, disp_ratio=1.5, disp_body=0.50),
}

# Failure-swing DOL test: per-instrument "equal-highs/lows" proximity tolerance
# (fixed, tick-derived, NOT swept - overfit guard). Used only by --tp failure-swing.
FS_CLUSTER_TOL = {'nq': 4.0, 'es': 1.0, 'ym': 8.0, 'gc': 1.0,
                  'rty': 1.0, 'cl': 0.10, 'rb': 0.01, 'ho': 0.01}

MIN_GAP_4H    = 3.0
MAX_GAP_AGE   = 15
DISP_RATIO    = 1.5
DISP_BODY     = 0.50
IPDA_LOOKBACK = 20
CLOSE_POS_BULL = 0.65
CLOSE_POS_BEAR = 0.35

FVG = namedtuple('FVG', ['gap_top', 'gap_bot', 'direction', 'formed_ts', 'formed_idx', 'instrument'])


# ── ECONOMIC CALENDAR ─────────────────────────────────────────────────────────
def _build_nfp_dates():
    dates = set()
    for year in range(2020, 2028):
        for month in range(1, 13):
            d = datetime.date(year, month, 1)
            while d.weekday() != 4:
                d += datetime.timedelta(days=1)
            dates.add(d)
    return dates

_FOMC_DATES = {
    datetime.date(2020,1,29), datetime.date(2020,3,3),   datetime.date(2020,3,15),
    datetime.date(2020,4,29), datetime.date(2020,6,10),  datetime.date(2020,7,29),
    datetime.date(2020,9,16), datetime.date(2020,11,5),  datetime.date(2020,12,16),
    datetime.date(2021,1,27), datetime.date(2021,3,17),  datetime.date(2021,4,28),
    datetime.date(2021,6,16), datetime.date(2021,7,28),  datetime.date(2021,9,22),
    datetime.date(2021,11,3), datetime.date(2021,12,15),
    datetime.date(2022,1,26), datetime.date(2022,3,16),  datetime.date(2022,5,4),
    datetime.date(2022,6,15), datetime.date(2022,7,27),  datetime.date(2022,9,21),
    datetime.date(2022,11,2), datetime.date(2022,12,14),
    datetime.date(2023,2,1),  datetime.date(2023,3,22),  datetime.date(2023,5,3),
    datetime.date(2023,6,14), datetime.date(2023,7,26),  datetime.date(2023,9,20),
    datetime.date(2023,11,1), datetime.date(2023,12,13),
    datetime.date(2024,1,31), datetime.date(2024,3,20),  datetime.date(2024,5,1),
    datetime.date(2024,6,12), datetime.date(2024,7,31),  datetime.date(2024,9,18),
    datetime.date(2024,11,7), datetime.date(2024,12,18),
}
_NFP_DATES   = _build_nfp_dates()
_MAJOR_DATES = _NFP_DATES | _FOMC_DATES

def eco_day_type(d):
    if d in _MAJOR_DATES:
        return 'SKIP_NFP_FOMC'
    if (d + datetime.timedelta(days=1)) in _NFP_DATES:
        return 'PREFER_PRE_NFP'
    return 'normal'


# ── US MARKET HOLIDAYS ────────────────────────────────────────────────────────
def _observed(d):
    """Shift to observed date: Sat -> Fri, Sun -> Mon."""
    dow = d.weekday()
    if dow == 5: return d - datetime.timedelta(days=1)
    if dow == 6: return d + datetime.timedelta(days=1)
    return d

def _nth_weekday(year, month, n, weekday):
    """nth occurrence (1-based) of weekday (0=Mon) in given month."""
    d = datetime.date(year, month, 1)
    d += datetime.timedelta(days=(weekday - d.weekday()) % 7 + (n - 1) * 7)
    return d

def _last_weekday(year, month, weekday):
    """Last occurrence of weekday (0=Mon) in given month."""
    import calendar as _cal
    last = datetime.date(year, month, _cal.monthrange(year, month)[1])
    return last - datetime.timedelta(days=(last.weekday() - weekday) % 7)

def _easter(year):
    a = year % 19; b = year // 100; c = year % 100
    d = b // 4;    e = b % 4;    f = (b + 8) // 25
    g = (b - f + 1) // 3;  h = (19*a + b - d - g + 15) % 30
    i = c // 4;    k = c % 4;    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day   = ((h + l - 7*m + 114) % 31) + 1
    return datetime.date(year, month, day)

def _us_market_holidays(year):
    """NYSE market holidays for given year, with weekend-shift observation."""
    h = {
        _observed(datetime.date(year, 1, 1)),        # New Year's Day
        _nth_weekday(year, 1, 3, 0),                 # MLK Day (3rd Mon Jan)
        _nth_weekday(year, 2, 3, 0),                 # Presidents Day (3rd Mon Feb)
        _easter(year) - datetime.timedelta(days=2),  # Good Friday
        _last_weekday(year, 5, 0),                   # Memorial Day (last Mon May)
        _observed(datetime.date(year, 7, 4)),         # Independence Day
        _nth_weekday(year, 9, 1, 0),                 # Labor Day (1st Mon Sep)
        _nth_weekday(year, 11, 4, 3),                # Thanksgiving (4th Thu Nov)
        _observed(datetime.date(year, 12, 25)),       # Christmas Day
    }
    if year >= 2022:
        h.add(_observed(datetime.date(year, 6, 19))) # Juneteenth (from 2022)
    return h

_US_HOLIDAYS = set()
for _yr in range(2020, 2027):
    _US_HOLIDAYS.update(_us_market_holidays(_yr))


# ── SESSION HELPERS ───────────────────────────────────────────────────────────
def is_edt(dt):
    mar1 = datetime.datetime(dt.year, 3, 1)
    edt_start = mar1 + datetime.timedelta(days=(6 - mar1.weekday()) % 7) + datetime.timedelta(weeks=1)
    nov1 = datetime.datetime(dt.year, 11, 1)
    edt_end   = nov1 + datetime.timedelta(days=(6 - nov1.weekday()) % 7)
    d = dt.date() if hasattr(dt, 'date') else dt
    return edt_start.date() <= d < edt_end.date()

def session_times(dt):
    if is_edt(dt):
        return dict(ldn_start=(12,30), ldn_end=(13,30),
                    nyam_start=(18,30), nyam_end=(21,0),
                    pm_start=(23,30), pm_end_next=(0,30),
                    pre_start=(15,0),  pre_end=(18,30),
                    asia_start=(4,0),  asia_end=(10,0), edt=True)
    return dict(ldn_start=(13,30), ldn_end=(14,30),
                nyam_start=(19,30), nyam_end=(22,0),
                pm_start=(0,30),   pm_end_next=(1,30),
                pre_start=(16,0),  pre_end=(19,30),
                asia_start=(4,0),  asia_end=(10,0), edt=False)

def in_window(ts, s, e):
    t = (ts.hour, ts.minute)
    return s <= t < e

def _in_pm_window(ts, st):
    t = (ts.hour, ts.minute)
    if st['edt']:
        return (23,30) <= t <= (23,59) or (0,0) <= t < (0,30)
    return (0,30) <= t < (1,30)

def get_session_label(ts, st):
    if in_window(ts, st['ldn_start'], st['ldn_end']):    return 'london'
    if in_window(ts, st['nyam_start'], st['nyam_end']):  return 'ny_am'
    if in_window(ts, st['pre_start'],  st['pre_end']):   return 'pre_market'
    if _in_pm_window(ts, st):                            return 'ny_pm'
    if in_window(ts, st['asia_start'], st['asia_end']):  return 'asia'
    return None

def is_monday(dt): return dt.weekday() == 0


# ── LONDON CLASSIFIER ────────────────────────────────────────────────────────
def classify_london(london_bars, daily_bias_direction, avg_range_nq=50.0):
    if london_bars is None or len(london_bars) < 3:
        return 'unknown', 0.0, 0.0
    lo = float(london_bars.iloc[0]['nq_open'])
    lc = float(london_bars.iloc[-1]['nq_close'])
    rng = float(london_bars['nq_high'].max()) - float(london_bars['nq_low'].min())
    net = lc - lo
    if rng < avg_range_nq * 0.12:
        return 'consolidation', net, rng
    if daily_bias_direction == 'bull':
        return ('expansion', net, rng) if net > 0 else ('retracement', net, rng)
    else:
        return ('expansion', net, rng) if net < 0 else ('retracement', net, rng)


# ── 4H FVG DETECTION (instrument-aware) ──────────────────────────────────────
def detect_4h_fvgs_for(df_4h, instrument='nq'):
    cfg = INST_CONFIG[instrument]
    hi_col = f'{instrument}_high'
    lo_col = f'{instrument}_low'
    op_col = f'{instrument}_open'
    cl_col = f'{instrument}_close'
    min_gap    = cfg['min_gap']
    disp_ratio = cfg['disp_ratio']
    disp_body  = cfg['disp_body']

    fvgs = []
    df = df_4h.reset_index(drop=True)
    for i in range(2, len(df)):
        b0, b1, b2 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
        prior = df.iloc[max(0, i-7):i-1]
        if len(prior) < 2: continue
        b1_range = float(b1[hi_col]) - float(b1[lo_col])
        if b1_range <= 0: continue
        avg_prior = (prior[hi_col] - prior[lo_col]).mean()
        if avg_prior <= 0 or b1_range < avg_prior * disp_ratio: continue
        body = abs(float(b1[cl_col]) - float(b1[op_col]))
        if body / b1_range < disp_body: continue

        gb_bull = float(b0[hi_col]); gt_bull = float(b2[lo_col])
        if gt_bull - gb_bull >= min_gap and float(b1[cl_col]) > float(b1[op_col]):
            fvgs.append(FVG(gap_top=gt_bull, gap_bot=gb_bull,
                            direction='bull', formed_ts=b2['timestamp'],
                            formed_idx=i, instrument=instrument))
        gt_bear = float(b0[lo_col]); gb_bear = float(b2[hi_col])
        if gt_bear - gb_bear >= min_gap and float(b1[cl_col]) < float(b1[op_col]):
            fvgs.append(FVG(gap_top=gt_bear, gap_bot=gb_bear,
                            direction='bear', formed_ts=b2['timestamp'],
                            formed_idx=i, instrument=instrument))
    return fvgs

def build_fvg_kill_times(fvgs, df_4h):
    df = df_4h.reset_index(drop=True)
    kill_times = {}
    for fvg in fvgs:
        inst = fvg.instrument
        cl_col = f'{inst}_close'
        killed_ts = None
        for _, fb in df[df['timestamp'] > fvg.formed_ts].iterrows():
            if fvg.direction == 'bull' and float(fb[cl_col]) < fvg.gap_bot:
                killed_ts = fb['timestamp']; break
            if fvg.direction == 'bear' and float(fb[cl_col]) > fvg.gap_top:
                killed_ts = fb['timestamp']; break
        kill_times[(inst, fvg.formed_ts)] = killed_ts
    return kill_times

def get_active_fvgs(fvgs, kill_times, as_of_ts, direction, max_age_bars=MAX_GAP_AGE):
    active = []
    for fvg in fvgs:
        if fvg.direction != direction: continue
        if fvg.formed_ts >= as_of_ts:  continue
        key = (fvg.instrument, fvg.formed_ts)
        killed = kill_times.get(key)
        if killed is not None and killed <= as_of_ts: continue
        age_h = (as_of_ts - fvg.formed_ts).total_seconds() / 3600
        if age_h > max_age_bars * 4: continue
        active.append(fvg)
    return active


# ── DAILY BIAS ────────────────────────────────────────────────────────────────
def build_daily_df(df5m):
    g = df5m.groupby(df5m['timestamp'].dt.date)
    return g.agg(nq_open=('nq_open','first'), nq_high=('nq_high','max'),
                 nq_low=('nq_low','min'), nq_close=('nq_close','last')).dropna()

def get_daily_bias(daily_df, today):
    dates = sorted(daily_df.index)
    try: pos = dates.index(today)
    except ValueError: return None
    if pos == 0: return None
    prev = daily_df.loc[dates[pos-1]]
    ph, pl, pc = float(prev['nq_high']), float(prev['nq_low']), float(prev['nq_close'])
    rng = ph - pl
    if rng <= 0: return None
    cp = (pc - pl) / rng
    if cp >= CLOSE_POS_BULL: return dict(direction='bull', prev_date=dates[pos-1], prev_range=rng)
    if cp <= CLOSE_POS_BEAR: return dict(direction='bear', prev_date=dates[pos-1], prev_range=rng)
    return None

def get_ipda_draw(daily_df, prev_date, direction):
    dates = sorted(daily_df.index)
    try: pos = dates.index(prev_date)
    except ValueError: return None
    start = max(0, pos - IPDA_LOOKBACK + 1)
    win = daily_df.loc[dates[start:pos+1]]
    return float(win['nq_high'].max()) if direction == 'bull' else float(win['nq_low'].min())


# ── TTFM C3 FRACTAL CHECK (instrument-aware) ─────────────────────────────────
def check_c3_fractal(sess5m, entry_idx, direction, instrument='nq',
                     lookback=8, min_body_pct=0.25, two_stage=False):
    if entry_idx < 2: return False
    op_col = f'{instrument}_open'
    cl_col = f'{instrument}_close'
    hi_col = f'{instrument}_high'
    lo_col = f'{instrument}_low'
    start   = max(0, entry_idx - lookback)
    pre     = sess5m.iloc[start:entry_idx]
    if len(pre) < 2: return False
    opposing_found = 0
    for i in range(len(pre) - 1, -1, -1):
        bar = pre.iloc[i]
        o, c = float(bar[op_col]), float(bar[cl_col])
        rng  = float(bar[hi_col]) - float(bar[lo_col])
        if rng < 0.5: continue
        if abs(c - o) / rng < min_body_pct: continue
        is_c1 = (direction == 'bull' and c < o) or (direction == 'bear' and c > o)
        if is_c1 and (entry_idx - 1) - (start + i) >= 1:
            opposing_found += 1
            if not two_stage:
                return True
    return opposing_found >= 2 if two_stage else False


# ── STRENGTH SWITCH ───────────────────────────────────────────────────────────
def check_strength_switch(sess5m, entry_bar_idx, direction):
    if entry_bar_idx < 1 or len(sess5m) < 2: return False
    bar, first = sess5m.iloc[entry_bar_idx], sess5m.iloc[0]
    nq0 = float(first['nq_open']); es0 = float(first['es_open'])
    ym0 = float(first['ym_open']) if 'ym_open' in first.index else es0
    if nq0 <= 0 or es0 <= 0: return False
    nq_m = (float(bar['nq_close']) - nq0) / nq0
    es_m = (float(bar['es_close']) - es0) / es0
    ym_m = (float(bar['ym_close']) - ym0) / ym0 if ym0 > 0 else es_m
    if direction == 'bull':
        return es_m > nq_m + 0.0002 or ym_m > nq_m + 0.0002
    return es_m < nq_m - 0.0002 or ym_m < nq_m - 0.0002


# ── PRIOR DAY HIGH/LOW TP (for Driver entries) ───────────────────────────────
def get_pdh_pdl(df5m_c, instrument, date, direction, dates):
    """Return prior trading day's high (bull) or low (bear) for the instrument."""
    prev = [d for d in dates if d < date]
    if not prev:
        return None
    hi_col = f'{instrument}_high'
    lo_col = f'{instrument}_low'
    prev_bars = df5m_c[df5m_c['date'] == prev[-1]]
    if len(prev_bars) == 0 or hi_col not in prev_bars.columns:
        return None
    return float(prev_bars[hi_col].max()) if direction == 'bull' \
           else float(prev_bars[lo_col].min())


def find_failure_swing_dol(df5m_c, instrument, date, direction,
                           gap_top, gap_bot, dates, tol, k=2, lookback_days=3,
                           tf='1h'):
    """GxT Stage-0.5 Draw on Liquidity target: nearest FAILURE-SWING cluster
    (>=2 stacked equal highs/lows within `tol`) beyond the gap, from PRIOR
    trading days' 1H swings (no lookahead). Isolated 'relevant' swings are NOT
    targets. Returns the cluster liquidity level, or None (caller falls back)."""
    prev = [d for d in dates if d < date][-lookback_days:]
    if not prev:
        return None
    hi_col = f'{instrument}_high'; lo_col = f'{instrument}_low'
    w = df5m_c[df5m_c['date'].isin(prev)]
    if len(w) == 0 or hi_col not in w.columns:
        return None
    g = w.set_index('timestamp')
    h1 = g[hi_col].resample(tf).max().dropna().tolist()
    l1 = g[lo_col].resample(tf).min().dropna().tolist()

    def swings(v, kind):
        out = []
        for i in range(k, len(v) - k):
            seg = v[i - k:i + k + 1]
            if kind == 'high' and v[i] == max(seg): out.append(v[i])
            elif kind == 'low' and v[i] == min(seg): out.append(v[i])
        return out

    if direction == 'bull':
        sw = sorted(x for x in swings(h1, 'high') if x > gap_top)   # ascending = nearest first
        if not sw: return None
        cluster = [sw[0]]
        for x in sw[1:]:
            if x - cluster[-1] <= tol:
                cluster.append(x)
            else:
                if len(cluster) >= 2: return max(cluster)
                cluster = [x]
        return max(cluster) if len(cluster) >= 2 else None
    else:
        sw = sorted((x for x in swings(l1, 'low') if x < gap_bot), reverse=True)  # nearest below first
        if not sw: return None
        cluster = [sw[0]]
        for x in sw[1:]:
            if cluster[-1] - x <= tol:
                cluster.append(x)
            else:
                if len(cluster) >= 2: return min(cluster)
                cluster = [x]
        return min(cluster) if len(cluster) >= 2 else None


# ── 4H PROFILING-SEQUENCE GATE (GxT if-then; test, off by default) ───────────
# IST 4H grid opens at 12/16/20 ~ London/NY-AM/NY-PM legs (NY-aligned within ~30min).
_PROF_LEGS = (12, 16, 20)

def classify_4h_candle(bar, inst, opp_wick_min=0.40):
    """Manipulation candle = swept one side and closed back across the midpoint
    (opposing wick >= opp_wick_min of range). Returns manip_up / manip_down / neutral."""
    o = float(bar[f'{inst}_open']); h = float(bar[f'{inst}_high'])
    l = float(bar[f'{inst}_low']);  c = float(bar[f'{inst}_close'])
    rng = h - l
    if rng <= 0:
        return 'neutral'
    up_wick = h - max(o, c); lo_wick = min(o, c) - l; mid = (h + l) / 2
    if lo_wick / rng >= opp_wick_min and c > mid:   # swept lows, reversed up
        return 'manip_up'
    if up_wick / rng >= opp_wick_min and c < mid:   # swept highs, reversed down
        return 'manip_down'
    return 'neutral'

def profiling_sequence_skip(df_4h, date, entry_ts, trade_dir, inst):
    """GxT if-then: SKIP a reversal entry if an EARLIER 4H leg that day already
    manipulated in the trade direction (the reversal was already put in -> this
    leg is continuation territory, a fresh reversal here is late)."""
    bucket = (entry_ts.hour // 4) * 4
    want   = 'manip_up' if trade_dir == 'bull' else 'manip_down'
    day_bars = df_4h[df_4h['timestamp'].dt.date == date]
    for h in _PROF_LEGS:
        if h >= bucket:
            break
        bar = day_bars[day_bars['timestamp'].dt.hour == h]
        if len(bar) and classify_4h_candle(bar.iloc[0], inst) == want:
            return True
    return False


# ── 9:30 DRIVER BAR GATE (v8.18) ─────────────────────────────────────────────
def check_driver_bar(sess5m, direction, instrument='nq',
                     min_body_pct=0.40, min_body_pts=4.0):
    """GxT '9:30 Driver' gate: first bar of NY_AM must be a displacement bar."""
    if len(sess5m) < 1:
        return True
    min_pts = {'nq': 4.0, 'es': 1.5, 'ym': 8.0, 'gc': 2.0, 'rty': 3.0}
    driver  = sess5m.iloc[0]
    op_col  = f'{instrument}_open'
    cl_col  = f'{instrument}_close'
    hi_col  = f'{instrument}_high'
    lo_col  = f'{instrument}_low'
    if op_col not in driver.index:
        return True
    d_open  = float(driver[op_col])
    d_close = float(driver[cl_col])
    d_high  = float(driver[hi_col])
    d_low   = float(driver[lo_col])
    d_range = d_high - d_low
    d_body  = abs(d_close - d_open)
    if d_range < 0.5:
        return False
    if d_body / d_range < min_body_pct:
        return False
    if d_body < min_pts.get(instrument, min_body_pts):
        return False
    bar_dir = 'bull' if d_close > d_open else 'bear'
    return bar_dir == direction


# ── 9:30 DRIVER ENTRY DETECTION (v8.18) ──────────────────────────────────────
_DRIVER_MIN_PTS = {'nq': 5.0, 'es': 2.0, 'ym': 10.0, 'gc': 2.0, 'rty': 3.0}

def find_driver_entry(sess5m, active_fvgs, direction, instrument, min_body_pct=0.40):
    """9:30 Driver Positional Entry. Entry at body midpoint retracement, TP=PDH/PDL."""
    if not active_fvgs or len(sess5m) < 3:
        return None, None, None, None, None

    op_col = f'{instrument}_open';  cl_col = f'{instrument}_close'
    hi_col = f'{instrument}_high';  lo_col = f'{instrument}_low'
    driver = sess5m.iloc[0]
    if op_col not in driver.index:
        return None, None, None, None, None

    d_open  = float(driver[op_col]); d_close = float(driver[cl_col])
    d_high  = float(driver[hi_col]); d_low   = float(driver[lo_col])
    d_range = d_high - d_low;        d_body  = abs(d_close - d_open)

    if d_range < 0.5:
        return None, None, None, None, None
    if d_body / d_range < min_body_pct:
        return None, None, None, None, None
    if d_body < _DRIVER_MIN_PTS.get(instrument, 5.0):
        return None, None, None, None, None
    if (d_close > d_open) != (direction == 'bull'):
        return None, None, None, None, None

    # Phase 2: for YM/GC/RTY entries, NQ must LEAD (stronger bar)
    if instrument != 'nq' and 'nq_open' in driver.index:
        nq_op = float(driver['nq_open']); nq_cl = float(driver['nq_close'])
        nq_hi = float(driver['nq_high']); nq_lo = float(driver['nq_low'])
        nq_range = nq_hi - nq_lo;        nq_body = abs(nq_cl - nq_op)
        nq_dir_bull = nq_cl > nq_op
        if nq_dir_bull != (direction == 'bull'):
            return None, None, None, None, None
        if nq_range < 0.5 or nq_body / nq_range < 0.30 or nq_body < 4.0:
            return None, None, None, None, None
        if d_open > 0 and nq_op > 0:
            if (nq_body / nq_op) <= (d_body / d_open):
                return None, None, None, None, None

    tick     = INST_CONFIG.get(instrument, {}).get('tick', 0.25)
    body_mid = (d_open + d_close) / 2.0
    fvg      = active_fvgs[0]

    for i in range(1, min(len(sess5m), 16)):
        bar = sess5m.iloc[i]
        lo  = float(bar.get(lo_col, d_low))
        hi  = float(bar.get(hi_col, d_high))
        cl  = float(bar.get(cl_col, d_open))
        if direction == 'bull':
            if lo <= body_mid and cl > d_low:
                sl = d_low - tick
                return bar, i, body_mid, sl, fvg
        else:
            if hi >= body_mid and cl < d_high:
                sl = d_high + tick
                return bar, i, body_mid, sl, fvg

    return None, None, None, None, None


# ── LEADING INSTRUMENT GATE (v8.18+) ─────────────────────────────────────────
def check_nq_leads(sess5m, entry_bar_idx, direction, instrument,
                   all_instruments=None, threshold=0.0003):
    """GxT SMT divergence gate — generalised to any leading instrument.

    Passes if:
      (a) inst IS the session's fastest mover (leader), or
      (b) another instrument moved further by >= threshold (inst is lagging).
    Blocks when no meaningful inter-asset divergence exists.

    Replaces NQ-hardcoded version: previously NQ always passed and companions
    required NQ to lead. Now any instrument can be the leader, recovering ~37
    sessions where ES/YM displaced furthest and NQ lagged.
    """
    if entry_bar_idx < 1 or len(sess5m) < 2:
        return True
    bar   = sess5m.iloc[entry_bar_idx]
    first = sess5m.iloc[0]

    inst0 = float(first.get(f'{instrument}_open', 0))
    if inst0 <= 0:
        return True
    inst_m = (float(bar.get(f'{instrument}_close', inst0)) - inst0) / inst0

    all_list = list(all_instruments) if all_instruments else ['nq']

    # GxT triads: each asset class confirms via its own triad, not cross-class.
    #   Indices: NQ | ES | YM  → NQ/ES are primaries
    #   Oil:     CL | RB | HO  → RB/HO confirm CL (and vice versa)
    _primaries = ('nq', 'es')
    _OIL_TRIAD = {'cl': ('rb', 'ho'), 'rb': ('cl', 'ho'), 'ho': ('cl', 'rb')}

    if instrument in _OIL_TRIAD:
        check_list = list(_OIL_TRIAD[instrument])   # use oil companions from df columns
    elif instrument in _primaries:
        check_list = all_list
    else:
        check_list = [i for i in all_list if i in _primaries]

    # Find the fastest mover in entry direction among valid leader instruments
    leader_m     = inst_m   # sentinel: no one beats inst yet
    leader_found = False
    for other in check_list:
        if other == instrument:
            continue
        o0 = float(first.get(f'{other}_open', 0))
        if o0 <= 0:
            continue
        om = (float(bar.get(f'{other}_close', o0)) - o0) / o0
        if direction == 'bull' and om < leader_m:
            leader_m = om; leader_found = True
        elif direction == 'bear' and om > leader_m:
            leader_m = om; leader_found = True

    if not leader_found:
        # inst IS the fastest: NQ/ES can self-lead; oil triad instruments can also self-lead
        return instrument in _primaries or instrument in _OIL_TRIAD

    # Another instrument is the leader; require threshold divergence
    if direction == 'bull':
        return leader_m < inst_m - threshold
    else:
        return leader_m > inst_m + threshold


# ── C2/C3 4H DIRECTION GATE (v8.18) ──────────────────────────────────────────
def check_h4_direction(df_4h, trade_date, direction, min_body_pct=0.40):
    """C2/C3 model gate: block NY_AM entries on strong continuation days.
    The 4H candle at 16:00 IST (6AM EST) that strongly expands AGAINST the daily
    bias signals a C2 continuation day. Only blocks if body >= 40% of range.
    """
    day_bars = df_4h[df_4h['timestamp'].dt.date == trade_date]
    if len(day_bars) == 0:
        return True
    target_hour = 16
    bar_6am = day_bars[day_bars['timestamp'].dt.hour == target_hour]
    if len(bar_6am) == 0:
        return True
    bar = bar_6am.iloc[0]
    nq_open  = float(bar.get('nq_open',  0))
    nq_close = float(bar.get('nq_close', 0))
    nq_high  = float(bar.get('nq_high',  nq_open))
    nq_low   = float(bar.get('nq_low',   nq_open))
    if nq_open <= 0:
        return True
    bar_range = nq_high - nq_low
    bar_body  = abs(nq_close - nq_open)
    if bar_range < 0.5 or bar_body / bar_range < min_body_pct:
        return True
    h4_dir = 'bull' if nq_close > nq_open else 'bear'
    return h4_dir == direction


# ── SMT DIVERGENCE CHECK (Gap 4) — 15m timeframe ────────────────────────────
def check_smt_divergence(df15m, entry_ts, direction, instrument, all_instruments, lookback=4):
    """Proper 15m SMT divergence check.

    Bull: entry instrument's 15m bar makes a new lower low (swept gap_bot),
          while at least one companion holds a higher 15m low (didn't follow down).
    Bear: entry instrument's 15m bar makes a new higher high,
          while at least one companion holds a lower 15m high.

    If df15m is None, falls back to always-True (gate disabled).
    """
    if df15m is None:
        return True
    # GxT triads: SMT divergence must be checked WITHIN the asset class.
    #   Oil: CL | RB | HO  → CL diverges against RB/HO, not indices.
    _OIL_TRIAD = {'cl': ('rb', 'ho'), 'rb': ('cl', 'ho'), 'ho': ('cl', 'rb')}
    if instrument in _OIL_TRIAD:
        companions = list(_OIL_TRIAD[instrument])
    else:
        companions = [i for i in all_instruments if i != instrument]
    if not companions:
        return True

    mask = df15m['timestamp'] <= entry_ts
    if not mask.any():
        return True
    recent = df15m[mask].tail(lookback + 1)
    if len(recent) < 2:
        return True

    curr = recent.iloc[-1]
    prev = recent.iloc[-2]

    inst_lo = f'{instrument}_low'
    inst_hi = f'{instrument}_high'
    if inst_lo not in curr.index:
        return True

    for comp in companions:
        comp_lo = f'{comp}_low'
        comp_hi = f'{comp}_high'
        if comp_lo not in curr.index:
            continue
        if direction == 'bull':
            inst_swept = float(curr[inst_lo]) < float(prev[inst_lo])
            comp_held  = float(curr[comp_lo]) > float(prev[comp_lo])
            if inst_swept and comp_held:
                return True
        else:
            inst_pushed = float(curr[inst_hi]) > float(prev[inst_hi])
            comp_held   = float(curr[comp_hi]) < float(prev[comp_hi])
            if inst_pushed and comp_held:
                return True
    return False


# ── DRIVER V2 (v8.18): GxT 9:30/10:00 driver windows + reversal/continuation + PSP ──
def check_psp(bar, direction, instrument, companions):
    """GxT Precision Swing Point: opposing candle CLOSES across the SMT pair.
    Bull: inst closes bullish (close>open) while >=1 companion closes bearish.
    Bear: inst closes bearish while >=1 companion closes bullish.
    The inst candle must itself close in the trade direction (candle-2 closure).
    """
    io = float(bar.get(f'{instrument}_open', 0)); ic = float(bar.get(f'{instrument}_close', 0))
    if io <= 0:
        return False
    inst_bull = ic > io
    if (direction == 'bull') != inst_bull:
        return False
    for c in companions:
        co = float(bar.get(f'{c}_open', 0)); cc = float(bar.get(f'{c}_close', 0))
        if co <= 0:
            continue
        if (cc > co) != inst_bull:   # opposing close = strength switch
            return True
    return False


_DRIVER_WINDOWS_EDT = [(19, 0), (19, 30)]   # 9:30, 10:00 EST -> IST (EDT)
_DRIVER_WINDOWS_EST = [(20, 0), (20, 30)]   # 9:30, 10:00 EST -> IST (EST)

_DRIVER_NEWS_WINDOWS_EDT = [(18, 0)]   # 8:30 EST -> IST (EDT)
_DRIVER_NEWS_WINDOWS_EST = [(19, 0)]   # 8:30 EST -> IST (EST)

def find_driver_v2_entry(sess5m, active_fvgs, direction, instrument, edt,
                         companions, require_psp=True, min_body_pct=0.40,
                         windows=None):
    """GxT Driver v2: locate the driver bar (default 9:30/10:00, or caller-supplied
    windows), branch reversal vs continuation, confirm with PSP.
    Returns (bar, idx, entry, sl, fvg) or Nones."""
    if not active_fvgs or len(sess5m) < 3:
        return None, None, None, None, None
    op = f'{instrument}_open'; cl = f'{instrument}_close'
    hi = f'{instrument}_high'; lo = f'{instrument}_low'
    if op not in sess5m.columns:
        return None, None, None, None, None
    if windows is None:
        windows = _DRIVER_WINDOWS_EDT if edt else _DRIVER_WINDOWS_EST
    tick    = INST_CONFIG.get(instrument, {}).get('tick', 0.25)
    min_pts = _DRIVER_MIN_PTS.get(instrument, 5.0)
    fvg = active_fvgs[0]
    ts  = sess5m['timestamp']
    for (wh, wm) in windows:
        idxs = [i for i in range(len(sess5m))
                if ts.iloc[i].hour == wh and ts.iloc[i].minute == wm]
        if not idxs:
            continue
        di  = idxs[0]
        drv = sess5m.iloc[di]
        d_open = float(drv[op]); d_close = float(drv[cl])
        d_high = float(drv[hi]); d_low = float(drv[lo])
        d_range = d_high - d_low; d_body = abs(d_close - d_open)
        if d_range < 0.5 or d_body / d_range < min_body_pct or d_body < min_pts:
            continue
        if (d_close > d_open) != (direction == 'bull'):
            continue
        # Branch: was a session HOD/LOD already established BEFORE the driver?
        pre = sess5m.iloc[:di]
        if len(pre) > 0 and direction == 'bull':
            swing_set = float(pre[lo].min()) < d_low
        elif len(pre) > 0:
            swing_set = float(pre[hi].max()) > d_high
        else:
            swing_set = False
        body_mid = (d_open + d_close) / 2.0
        for j in range(di + 1, min(len(sess5m), di + 16)):
            b   = sess5m.iloc[j]
            blo = float(b.get(lo, d_low)); bhi = float(b.get(hi, d_high)); bcl = float(b.get(cl, d_open))
            if direction == 'bull':
                hit = (blo <= body_mid and bcl > d_low) if swing_set else (blo <= d_low and bcl > d_low)
                ep  = body_mid if swing_set else d_low
            else:
                hit = (bhi >= body_mid and bcl < d_high) if swing_set else (bhi >= d_high and bcl < d_high)
                ep  = body_mid if swing_set else d_high
            if not hit:
                continue
            if require_psp and not check_psp(b, direction, instrument, companions):
                continue
            sl = (d_low - tick) if direction == 'bull' else (d_high + tick)
            return b, j, ep, sl, fvg
    return None, None, None, None, None


# ── ASIA SESSION DIRECTION (Gap 1) ────────────────────────────────────────────
def compute_asia_direction(df5m_day_prev, st, threshold_pts=8.0):
    """Compute net direction of the Asia/overnight session.
    Asia = bars between 23:30-12:00 IST (after NY-PM, before London opens).
    Returns 'bull', 'bear', or 'neutral'."""
    lo, hi = (0, 0), (12, 0)
    asia = df5m_day_prev[
        (df5m_day_prev['timestamp'].dt.hour * 60 + df5m_day_prev['timestamp'].dt.minute >= lo[0]*60+lo[1]) &
        (df5m_day_prev['timestamp'].dt.hour * 60 + df5m_day_prev['timestamp'].dt.minute < hi[0]*60+hi[1])
    ]
    if len(asia) < 3: return 'neutral'
    net = float(asia.iloc[-1]['nq_close']) - float(asia.iloc[0]['nq_open'])
    if net > threshold_pts:  return 'bull'
    if net < -threshold_pts: return 'bear'
    return 'neutral'


# ── QUALITY SCORE (v8.16) ────────────────────────────────────────────────────
def compute_quality_score(df_4h, sess_start_ts, direction, london_profile,
                          wick_threshold=0.20):
    score = 0.0
    # Signal 1: Devil's Mark — 4H candle at session open lacks opposing wick
    prior = df_4h[df_4h['timestamp'] <= sess_start_ts]
    if len(prior) > 0:
        bar = prior.iloc[-1]
        hi = float(bar['nq_high']); lo = float(bar['nq_low'])
        op = float(bar['nq_open'])
        rng = hi - lo
        if rng >= 1.0:
            if direction == 'bull':
                if (hi - op) / rng < wick_threshold:
                    score += 1.0
            else:
                if (op - lo) / rng < wick_threshold:
                    score += 1.0
    # Signal 2: London retracement (price pulled back into FVG before NY open)
    if london_profile == 'retracement':
        score += 0.5
    return score


# ── V-SHAPE ENTRY (instrument-aware) ─────────────────────────────────────────
def find_5m_gap_bot_reversal(sess5m, fvg, direction, instrument='nq',
                              max_sweep=None, min_close_pos=0.50,
                              early_window_bars=None):
    lo_col = f'{instrument}_low'
    hi_col = f'{instrument}_high'
    cl_col = f'{instrument}_close'

    for idx, (_, bar) in enumerate(sess5m.iterrows()):
        if early_window_bars is not None and idx >= early_window_bars:
            break
        lo  = float(bar[lo_col])
        hi  = float(bar[hi_col])
        c   = float(bar[cl_col])
        rng = hi - lo
        if rng < 0.5: continue

        if direction == 'bull':
            if lo > fvg.gap_bot:    continue
            if max_sweep is not None and lo < fvg.gap_bot - max_sweep: continue
            if c < fvg.gap_bot:     continue
            if (c - lo) / rng < min_close_pos: continue
            return bar, idx
        else:
            if hi < fvg.gap_top:   continue
            if max_sweep is not None and hi > fvg.gap_top + max_sweep: continue
            if c > fvg.gap_top:    continue
            if (c - lo) / rng > (1.0 - min_close_pos): continue
            return bar, idx

    return None, None


# ── RELATIVE MOVE (for instrument selection) ──────────────────────────────────
def get_session_move(sess5m, entry_bar_idx, instrument):
    if entry_bar_idx < 1 or len(sess5m) < 2: return 0.0
    first = sess5m.iloc[0]
    bar   = sess5m.iloc[entry_bar_idx]
    op0   = float(first[f'{instrument}_open'])
    cl    = float(bar[f'{instrument}_close'])
    return (cl - op0) / op0 if op0 > 0 else 0.0


# ── TRADE SIMULATION (instrument-aware) ──────────────────────────────────────
def simulate_trade(df_sim, entry_price, sl, tp, direction,
                   entry_ts, end_ts, instrument='nq'):
    hi_col = f'{instrument}_high'
    lo_col = f'{instrument}_low'
    future = df_sim[(df_sim['timestamp'] > entry_ts) & (df_sim['timestamp'] <= end_ts)]
    outcome = 'EXPIRED'; exit_price = entry_price; exit_time = end_ts
    be_stop = False; sl_live = sl; risk = abs(entry_price - sl)

    for _, fb in future.iterrows():
        fh = float(fb[hi_col]); fl = float(fb[lo_col])
        if direction == 'bull':
            if not be_stop and fh >= entry_price + risk:
                be_stop = True; sl_live = entry_price
            if fl <= sl_live:
                outcome = 'BE' if be_stop else 'LOSS'
                exit_price = entry_price if be_stop else sl_live
                exit_time = fb['timestamp']; break
            if fh >= tp:
                outcome = 'WIN'; exit_price = tp
                exit_time = fb['timestamp']; break
        else:
            if not be_stop and fl <= entry_price - risk:
                be_stop = True; sl_live = entry_price
            if fh >= sl_live:
                outcome = 'BE' if be_stop else 'LOSS'
                exit_price = entry_price if be_stop else sl_live
                exit_time = fb['timestamp']; break
            if fl <= tp:
                outcome = 'WIN'; exit_price = tp
                exit_time = fb['timestamp']; break

    return outcome, exit_price, exit_time


# ── MAIN BACKTEST ─────────────────────────────────────────────────────────────
def run_backtest(df5m, df_1m, df_4h, df15m=None,
                 instruments=('nq', 'es', 'ym'),
                 tp_mode='full',
                 swing_hold=False,
                 no_london=False,
                 max_sweep=None,
                 min_close_pos=0.50,
                 min_rr=None,
                 nq_leads=False,
                 h4_direction_gate=False,
                 c2_continuation=False,
                 driver_gate=False,
                 driver_model=False,
                 driver_v2=False,
                 driver_v2_psp=True,
                 driver_news=False,
                 ss_gate=False,
                 eco_filter=False,
                 london_gate='any',
                 c3_gate=False,
                 early_window=False,
                 include_premarket=False,
                 one_per_session=True,
                 nq_confirm=False,
                 smt_gate=False,        # Gap 4: SMT divergence at entry bar
                 two_stage_c3=False,    # Gap 3: require 2 opposing candles
                 asia_gate=False,       # Gap 1: skip continuation when Asia+London aligned
                 erl_gate=False,        # Gap 2: per-instrument IPDA draw check
                 news_align=False,      # v8.13: skip trades against NFP/CPI/FOMC surprise
                 eco_calendar=None,     # preloaded {date -> 'bull'/'bear'} dict
                 max_gap_pts=None,      # v8.14: {inst -> max gap_width pts}; None = no cap
                 tp_cap_r=None,         # v8.15: cap TP at entry +/- N*risk; None = use gap_top/bot
                 holiday_filter=False,  # v8.17: skip NYSE market holidays
                 entry_cutoff_hm=None,  # v8.17: skip entries after HH*60+MM (IST); None = no cutoff
                 include_asia=False,    # v8.18: add Asia session (4:00-10:00 IST) as entry window
                 fs_tf='1h',            # failure-swing DOL: swing resample TF (sensitivity)
                 fs_tol_mult=1.0,       # failure-swing DOL: multiply FS_CLUSTER_TOL (sensitivity)
                 profiling_gate=False,  # 4H if-then profiling-sequence selector (test)
                 ):

    active_sessions = ['london', 'ny_am', 'ny_pm']
    if no_london:
        active_sessions = [s for s in active_sessions if s != 'london']
    if include_premarket:
        active_sessions = ['pre_market'] + active_sessions
    if include_asia:
        active_sessions = ['asia'] + active_sessions

    print(f'\n[GxT v8.17 - holiday+cutoff] 5M: {len(df5m):,} | 4H: {len(df_4h):,}')
    print(f'  Range: {df5m["timestamp"].min().date()} → {df5m["timestamp"].max().date()}')
    print(f'  Instruments: {list(instruments)}')
    print(f'  Sessions: {active_sessions}')
    flags = []
    if eco_filter:              flags.append('eco-filter')
    if london_gate != 'any':   flags.append(f'london-gate={london_gate}')
    if c3_gate:                 flags.append('c3-gate')
    if two_stage_c3:            flags.append('two-stage-c3')
    if early_window:            flags.append('early-window')
    if nq_leads:                flags.append('nq-leads')
    if h4_direction_gate:       flags.append('h4-direction')
    if c2_continuation:         flags.append('c2-continuation')
    if driver_gate:             flags.append('driver-gate')
    if driver_model:            flags.append('driver-model')
    if driver_v2:               flags.append('driver-v2' + ('+psp' if driver_v2_psp else ''))
    if driver_news:             flags.append('driver-news(NFP 8:30)' + ('+psp' if driver_v2_psp else ''))
    if ss_gate:                 flags.append('ss-gate')
    if smt_gate:                flags.append('smt-gate')
    if include_asia:            flags.append('asia-session')
    if asia_gate:               flags.append('asia-gate')
    if erl_gate:                flags.append('erl-gate')
    if news_align:              flags.append('news-align')
    if holiday_filter:          flags.append('us-holidays')
    if entry_cutoff_hm is not None:
        flags.append(f'entry-cutoff={entry_cutoff_hm//60:02d}:{entry_cutoff_hm%60:02d}IST')
    if max_gap_pts:
        for inst, cap in max_gap_pts.items():
            flags.append(f'max-gap-{inst}={cap}')
    print(f'  Gates: {flags or ["none"]}')

    # Build FVGs for all requested instruments (shared kill_times dict)
    all_fvgs    = {}   # instrument → list of FVGs
    all_kills   = {}   # (instrument, formed_ts) → killed_ts
    for inst in instruments:
        fvgs_inst = detect_4h_fvgs_for(df_4h, instrument=inst)
        print(f'  [4H FVGs {inst.upper()}] {len(fvgs_inst)} '
              f'({sum(1 for f in fvgs_inst if f.direction=="bull")} bull, '
              f'{sum(1 for f in fvgs_inst if f.direction=="bear")} bear)')
        all_fvgs[inst] = fvgs_inst
        kill = build_fvg_kill_times(fvgs_inst, df_4h)
        all_kills.update(kill)

    trades    = []
    daily_pnl = defaultdict(float)
    stats     = defaultdict(int)

    daily_df = build_daily_df(df5m)
    df5m_c   = df5m.copy()
    df5m_c['date'] = df5m_c['timestamp'].dt.date
    dates    = sorted(df5m_c['date'].unique())
    sim_df   = df_1m if df_1m is not None else df5m

    daily_ranges = daily_df.apply(
        lambda r: float(r['nq_high']) - float(r['nq_low']), axis=1)
    avg_daily_range = daily_ranges.mean()

    for date in dates:
        day_df5m = df5m_c[df5m_c['date'] == date].reset_index(drop=True)
        if len(day_df5m) < 6: continue
        ts0 = day_df5m['timestamp'].iloc[0]
        if is_monday(ts0): continue

        etype = eco_day_type(date)
        if eco_filter and etype == 'SKIP_NFP_FOMC':
            stats['eco_skip'] += 1; continue
        if holiday_filter and date in _US_HOLIDAYS:
            stats['holiday_skip'] += 1; continue

        bias = get_daily_bias(daily_df, date)
        if bias is None:
            stats['ambiguous_bias'] += 1; continue
        direction  = bias['direction']
        ipda_draw  = get_ipda_draw(daily_df, bias['prev_date'], direction)
        stats['days_with_bias'] += 1

        st = session_times(ts0)
        day_df5m = day_df5m.copy()
        day_df5m['session'] = day_df5m['timestamp'].apply(lambda t: get_session_label(t, st))

        london_bars = day_df5m[day_df5m['session'] == 'london']
        london_profile, london_net, _ = classify_london(
            london_bars if len(london_bars) >= 3 else None,
            direction, avg_range_nq=avg_daily_range)

        # Asia direction: bars in previous day's data from 23:30–12:00 IST
        prev_dates = [d for d in dates if d < date]
        asia_dir = 'neutral'
        if asia_gate and prev_dates:
            prev_day_df = df5m_c[df5m_c['date'] == prev_dates[-1]]
            asia_dir = compute_asia_direction(prev_day_df, st)
        # consecutive expansion: Asia and London both expanded in same direction
        london_dir = 'bull' if london_net > 0 else ('bear' if london_net < 0 else 'neutral')
        consec_expansion = (asia_gate and asia_dir != 'neutral'
                            and london_profile == 'expansion'
                            and asia_dir == london_dir)

        for session_label in active_sessions:
            sess5m = day_df5m[day_df5m['session'] == session_label].reset_index(drop=True)
            if len(sess5m) < 3: continue

            if session_label in ('ny_am', 'ny_pm', 'pre_market'):
                if london_gate == 'no-retrace'  and london_profile == 'retracement':
                    stats['london_gate_skip'] += 1; continue
                if london_gate == 'expand-only' and london_profile not in ('expansion','unknown'):
                    stats['london_gate_skip'] += 1; continue
                if london_gate == 'skip-expand' and london_profile == 'expansion':
                    stats['london_gate_skip'] += 1; continue
                # Asia gate: consecutive expansion → skip continuation (same direction as expansion)
                if consec_expansion and direction == london_dir:
                    stats['asia_gate_skip'] += 1; continue

            sess_start_ts = sess5m.iloc[0]['timestamp']
            sess_end_ts   = sess5m.iloc[-1]['timestamp']
            early_bars    = 15 if early_window else None

            # IPDA draw check (use NQ as reference price)
            sess_open_nq = float(sess5m.iloc[0]['nq_open'])
            if ipda_draw is not None:
                if direction == 'bull' and sess_open_nq >= ipda_draw:
                    stats['ipda_draw_reached'] += 1; continue
                if direction == 'bear' and sess_open_nq <= ipda_draw:
                    stats['ipda_draw_reached'] += 1; continue

            # NQ-confirm gate: NQ must have an active FVG before considering ES/YM
            nq_active = get_active_fvgs(all_fvgs.get('nq', []), all_kills,
                                        sess_start_ts, direction)
            if nq_confirm and 'nq' not in instruments and not nq_active:
                stats['nq_confirm_skip'] += 1; continue
            if nq_confirm and not nq_active:
                stats['nq_confirm_skip'] += 1; continue

            # ── Collect valid setup candidates across all instruments ──────
            candidates = []
            for inst in instruments:
                active = get_active_fvgs(
                    all_fvgs[inst], all_kills, sess_start_ts, direction)
                if not active:
                    continue
                stats[f'sessions_with_fvg_{inst}'] += 1

                for fvg in active:
                    entry_bar, entry_bar_idx = find_5m_gap_bot_reversal(
                        sess5m, fvg, direction, instrument=inst,
                        max_sweep=max_sweep,
                        min_close_pos=min_close_pos,
                        early_window_bars=early_bars,
                    )
                    if entry_bar is None:
                        stats[f'no_reversal_{inst}'] += 1; continue

                    if entry_cutoff_hm is not None:
                        et = entry_bar['timestamp']
                        if et.hour * 60 + et.minute > entry_cutoff_hm:
                            stats['entry_cutoff_skip'] += 1; continue

                    if c3_gate and not check_c3_fractal(
                            sess5m, entry_bar_idx, direction, instrument=inst):
                        stats['c3_skip'] += 1; continue

                    if two_stage_c3 and not check_c3_fractal(
                            sess5m, entry_bar_idx, direction, instrument=inst,
                            two_stage=True):
                        stats['two_stage_c3_skip'] += 1; continue

                    if ss_gate and not check_strength_switch(
                            sess5m, entry_bar_idx, direction):
                        stats['ss_skip'] += 1; continue

                    if smt_gate and not check_smt_divergence(
                            df15m, entry_bar['timestamp'], direction, inst, list(instruments)):
                        stats['smt_skip'] += 1; continue

                    # ERL gate: per-instrument IPDA draw check
                    if erl_gate:
                        inst_open = float(sess5m.iloc[0][f'{inst}_open'])
                        inst_fvgs  = all_fvgs.get(inst, [])
                        inst_active = get_active_fvgs(inst_fvgs, all_kills, sess_start_ts, direction)
                        if inst_active:
                            inst_highs = df5m_c[df5m_c['date'] < date][f'{inst}_high'].tail(80)
                            inst_lows  = df5m_c[df5m_c['date'] < date][f'{inst}_low'].tail(80)
                            if direction == 'bull':
                                erl = float(inst_highs.max()) if len(inst_highs) else None
                                if erl and inst_open >= erl:
                                    stats['erl_skip'] += 1; continue
                            else:
                                erl = float(inst_lows.min()) if len(inst_lows) else None
                                if erl and inst_open <= erl:
                                    stats['erl_skip'] += 1; continue

                    if news_align and eco_calendar:
                        news_dir = eco_calendar.get(date)
                        if news_dir and news_dir != direction:
                            stats['news_align_skip'] += 1; continue

                    # h4-direction-gate: C2/C3 model -- only valid for NY_AM
                    if h4_direction_gate and session_label == 'ny_am' \
                            and not check_h4_direction(df_4h, date, direction):
                        stats['h4_dir_skip'] += 1; continue

                    if nq_leads and not check_nq_leads(
                            sess5m, entry_bar_idx, direction, inst, instruments):
                        stats['nq_leads_skip'] += 1; continue

                    # Compute relative move for instrument ranking
                    rel_move = get_session_move(sess5m, entry_bar_idx, inst)
                    candidates.append((inst, fvg, entry_bar, entry_bar_idx,
                                       rel_move, None, None, 'fvg', None, direction))

            # ── 9:30 Driver model (YM/GC/RTY only) ──────────────────────────
            if driver_model and session_label == 'ny_am':
                for inst in [i for i in instruments if i not in ('nq', 'es')]:
                    active = get_active_fvgs(
                        all_fvgs[inst], all_kills, sess_start_ts, direction)
                    if not active: continue
                    drv_bar, drv_idx, drv_ep, drv_sl, drv_fvg = find_driver_entry(
                        sess5m, active, direction, inst)
                    if drv_bar is None: continue
                    if entry_cutoff_hm is not None:
                        et = drv_bar['timestamp']
                        if et.hour * 60 + et.minute > entry_cutoff_hm: continue
                    if nq_leads and not check_nq_leads(sess5m, drv_idx, direction, inst, instruments):
                        continue
                    already = any(c[0] == inst for c in candidates)
                    if not already:
                        drv_tp = get_pdh_pdl(df5m_c, inst, date, direction, dates)
                        candidates.append((inst, drv_fvg, drv_bar, drv_idx,
                                           get_session_move(sess5m, drv_idx, inst),
                                           drv_ep, drv_sl, 'driver', drv_tp, direction))
                        stats['driver_model_add'] = stats.get('driver_model_add', 0) + 1

            # ── Driver v2: GxT 9:30/10:00 windows + reversal/continuation + PSP ──
            if driver_v2 and session_label == 'ny_am':
                _v2_triad = {'cl': ['rb', 'ho'], 'rb': ['cl', 'ho'], 'ho': ['cl', 'rb']}
                for inst in instruments:
                    active = get_active_fvgs(
                        all_fvgs[inst], all_kills, sess_start_ts, direction)
                    if not active: continue
                    comps = _v2_triad.get(inst, ['nq', 'es'])
                    comps = [c for c in comps if c != inst]
                    db, di2, dep, dsl, dfvg = find_driver_v2_entry(
                        sess5m, active, direction, inst, st.get('edt', True),
                        comps, require_psp=driver_v2_psp)
                    if db is None: continue
                    if entry_cutoff_hm is not None:
                        et = db['timestamp']
                        if et.hour * 60 + et.minute > entry_cutoff_hm: continue
                    if not any(c[0] == inst for c in candidates):
                        dtp = get_pdh_pdl(df5m_c, inst, date, direction, dates)
                        candidates.append((inst, dfvg, db, di2,
                                           get_session_move(sess5m, di2, inst),
                                           dep, dsl, 'driver_v2', dtp, direction))
                        stats['driver_v2_add'] = stats.get('driver_v2_add', 0) + 1

            # ── Driver NEWS: 8:30 EST window, NFP days only (GxT news driver) ──
            if driver_news and session_label == 'pre_market' and date in _NFP_DATES:
                _nw = _DRIVER_NEWS_WINDOWS_EDT if st.get('edt', True) else _DRIVER_NEWS_WINDOWS_EST
                _v2_triad = {'cl': ['rb', 'ho'], 'rb': ['cl', 'ho'], 'ho': ['cl', 'rb']}
                for inst in instruments:
                    active = get_active_fvgs(
                        all_fvgs[inst], all_kills, sess_start_ts, direction)
                    if not active: continue
                    comps = [c for c in _v2_triad.get(inst, ['nq', 'es']) if c != inst]
                    db, din, dep, dsl, dfvg = find_driver_v2_entry(
                        sess5m, active, direction, inst, st.get('edt', True),
                        comps, require_psp=driver_v2_psp, windows=_nw)
                    if db is None: continue
                    if entry_cutoff_hm is not None:
                        et = db['timestamp']
                        if et.hour * 60 + et.minute > entry_cutoff_hm: continue
                    if not any(c[0] == inst for c in candidates):
                        dtp = get_pdh_pdl(df5m_c, inst, date, direction, dates)
                        candidates.append((inst, dfvg, db, din,
                                           get_session_move(sess5m, din, inst),
                                           dep, dsl, 'driver_news', dtp, direction))
                        stats['driver_news_add'] = stats.get('driver_news_add', 0) + 1

            # ── C2 Continuation pass ──────────────────────────────────────────
            # C2 day: 4H bar at 16:00 IST expands strongly AGAINST daily bias.
            # GxT trades WITH the 4H direction (continuation), not the reversal.
            # The C2 FVG forms at 20:00 IST (B2 of the displacement bar) — AFTER
            # sess_start_ts (18:30-19:30 IST), so get_active_fvgs rejects it with
            # the normal cutoff. Fix: use sess_end_ts so the C2 FVG is included.
            # Only search bars from 20:00 IST onwards (gap doesn't exist before B2).
            # Skip nq_leads and c3_gate — those are C3 reversal mechanics.
            if c2_continuation and h4_direction_gate and session_label == 'ny_am':
                if not check_h4_direction(df_4h, date, direction):
                    flip_dir = 'bull' if direction == 'bear' else 'bear'
                    c2_sess = sess5m[sess5m['timestamp'].dt.hour >= 20].reset_index(drop=True)
                    if len(c2_sess) >= 2:
                        for inst in instruments:
                            active = get_active_fvgs(all_fvgs[inst], all_kills, sess_end_ts, flip_dir)
                            if not active: continue
                            for fvg in active:
                                eb, eb_idx = find_5m_gap_bot_reversal(
                                    c2_sess, fvg, flip_dir, instrument=inst,
                                    max_sweep=max_sweep, min_close_pos=min_close_pos,
                                    early_window_bars=early_bars)
                                if eb is None: continue
                                if entry_cutoff_hm is not None:
                                    et = eb['timestamp']
                                    if et.hour * 60 + et.minute > entry_cutoff_hm: continue
                                rel = get_session_move(c2_sess, eb_idx, inst)
                                candidates.append((inst, fvg, eb, eb_idx, rel,
                                                   None, None, 'c2', None, flip_dir))
                                stats['c2_add'] = stats.get('c2_add', 0) + 1
                    else:
                        stats['c2_no_window'] = stats.get('c2_no_window', 0) + 1

            if not candidates:
                stats['no_candidates'] += 1; continue

            # ── Select best instrument ────────────────────────────────────
            candidates.sort(key=lambda x: x[4] * (1 if x[9] == 'bull' else -1), reverse=True)

            # Take one trade per session (GxT style), or all candidates
            selected = candidates[:1] if one_per_session else candidates

            for inst, fvg, entry_bar, entry_bar_idx, rel_move, ep_ov, sl_ov, etype, tp_ov, trade_dir in selected:
                tick = INST_CONFIG[inst]['tick']

                entry_price = ep_ov if ep_ov is not None else (
                    fvg.gap_bot + tick if trade_dir == 'bull' else fvg.gap_top - tick)

                lo_col = f'{inst}_low'
                hi_col = f'{inst}_high'
                sl = sl_ov if sl_ov is not None else (
                    float(entry_bar[lo_col]) - tick if trade_dir == 'bull'
                    else float(entry_bar[hi_col]) + tick)
                risk = abs(entry_price - sl)
                if risk < 0.5:
                    stats['sl_invalid'] += 1; continue

                gap_width = fvg.gap_top - fvg.gap_bot
                if max_gap_pts and inst in max_gap_pts and gap_width > max_gap_pts[inst]:
                    stats['max_gap_skip'] += 1; continue
                if tp_mode == 'failure-swing':
                    fs = find_failure_swing_dol(
                        df5m_c, inst, date, trade_dir,
                        fvg.gap_top, fvg.gap_bot, dates,
                        FS_CLUSTER_TOL.get(inst, 1.0) * fs_tol_mult,
                        tf=fs_tf)
                    if fs is not None:
                        tp = fs; stats['fs_dol_target'] += 1
                    else:
                        tp = fvg.gap_top if trade_dir == 'bull' else fvg.gap_bot
                        stats['fs_dol_fallback'] += 1
                elif tp_mode == 'full':
                    tp = fvg.gap_top if trade_dir == 'bull' else fvg.gap_bot
                else:
                    tp = (fvg.gap_top + fvg.gap_bot) / 2
                if tp_ov is not None:
                    tp = tp_ov

                if tp_cap_r is not None:
                    capped = (entry_price + tp_cap_r * risk if trade_dir == 'bull'
                              else entry_price - tp_cap_r * risk)
                    tp = min(tp, capped) if trade_dir == 'bull' else max(tp, capped)

                if trade_dir == 'bull' and tp <= entry_price:
                    stats['tp_invalid'] += 1; continue
                if trade_dir == 'bear' and tp >= entry_price:
                    stats['tp_invalid'] += 1; continue

                rr = abs(tp - entry_price) / risk
                if min_rr is not None and rr < min_rr:
                    stats['low_rr_skip'] += 1; continue

                entry_ts = entry_bar['timestamp']
                if profiling_gate and profiling_sequence_skip(df_4h, date, entry_ts, trade_dir, inst):
                    stats['profiling_gate_skip'] += 1; continue
                sim_end  = (min(entry_ts + datetime.timedelta(hours=72), df5m['timestamp'].max())
                            if swing_hold else sess_end_ts)

                _sim = sim_df if f'{inst}_high' in sim_df.columns else df5m
                outcome, exit_price, exit_time = simulate_trade(
                    _sim, entry_price, sl, tp, trade_dir, entry_ts, sim_end,
                    instrument=inst)

                pts = (exit_price - entry_price) if trade_dir == 'bull' else (entry_price - exit_price)
                pnl = pts * POINT_VALUE
                daily_pnl[date] += pnl
                stats['trades'] += 1
                stats[f'trades_{inst}'] += 1

                q_score = compute_quality_score(
                    df_4h, sess_start_ts, direction, london_profile)

                trades.append({
                    'date':           str(date),
                    'session':        session_label,
                    'instrument':     inst,
                    'direction':      trade_dir,
                    'eco_type':       etype,
                    'london_profile': london_profile,
                    'gap_top':        round(fvg.gap_top, 2),
                    'gap_bot':        round(fvg.gap_bot, 2),
                    'gap_width':      round(gap_width, 2),
                    'entry_ts':       str(entry_ts),
                    'entry':          round(entry_price, 2),
                    'sl':             round(sl, 2),
                    'tp':             round(tp, 2),
                    'risk_pts':       round(risk, 2),
                    'rr':             round(rr, 2),
                    'outcome':        outcome,
                    'exit_ts':        str(exit_time),
                    'exit':           round(exit_price, 2),
                    'pts':            round(pts, 2),
                    'pnl':            round(pnl, 2),
                    'rel_move_bps':   round(rel_move * 10000, 1),
                    'bar_idx_in_sess':entry_bar_idx,
                    'quality_score':  round(q_score, 1),
                })

    return trades, daily_pnl, stats


# ── OUTPUT ────────────────────────────────────────────────────────────────────
def pf_stats(ts, label, indent='    '):
    if not ts: print(f'{indent}{label}: 0 trades'); return
    w  = [t for t in ts if t['outcome'] == 'WIN']
    l  = [t for t in ts if t['outcome'] == 'LOSS']
    gp = sum(t['pnl'] for t in ts if t['pnl'] > 0)
    gl = abs(sum(t['pnl'] for t in ts if t['pnl'] < 0))
    pf = gp / gl if gl > 0 else float('inf')
    wr = len(w) / (len(w) + len(l)) if (len(w) + len(l)) > 0 else 0
    net = sum(t['pnl'] for t in ts)
    print(f'{indent}{label}: {len(ts):3d} trades | PF {pf:6.2f} | WR {wr*100:.1f}% | '
          f'Net ${net:.0f} | W:{len(w)} L:{len(l)}')


def print_results(trades, daily_pnl, stats, instruments):
    if not trades: print('  No trades.'); return
    wins   = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    bes    = [t for t in trades if t['outcome'] == 'BE']
    exp    = [t for t in trades if t['outcome'] == 'EXPIRED']
    gp  = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gl  = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
    pf  = gp / gl if gl > 0 else float('inf')
    net = sum(t['pnl'] for t in trades)
    wr  = len(wins) / (len(wins) + len(losses)) if (len(wins) + len(losses)) > 0 else 0
    pnls  = sorted(daily_pnl.keys())
    peak  = 0; dd = 0; equity = 0
    for d in pnls:
        equity += daily_pnl[d]
        if equity > peak: peak = equity
        dd = min(dd, equity - peak)

    print(f'\n  v8.12: {len(trades)} trades | PF {pf:.2f} | WR {wr*100:.1f}% | '
          f'DD ${abs(dd):.0f} | Net ${net:.0f}')
    print(f'  W:{len(wins)}  L:{len(losses)}  BE:{len(bes)}  EXP:{len(exp)}')

    print('\n  By instrument:')
    for inst in instruments:
        pf_stats([t for t in trades if t['instrument'] == inst], inst.upper())

    print('\n  By year:')
    for yr in range(2020, 2025):
        pf_stats([t for t in trades if t['date'].startswith(str(yr))], str(yr))

    print('\n  By session:')
    for sess in ['pre_market', 'london', 'ny_am', 'ny_pm']:
        pf_stats([t for t in trades if t['session'] == sess], sess)

    print('\n  London profile:')
    for prof in ['expansion', 'retracement', 'consolidation', 'unknown']:
        pf_stats([t for t in trades if t['london_profile'] == prof], f'london={prof}')

    print('\n  ── Comparators ──────────────────────────────────────────')
    print(f'  v8.5 base:                    48t | PF  10.63 | WR 77.8% | DD $20')
    print(f'  v8.6 skip-expand+c3+premarket:48t | PF  76.42 | WR 94.1% | DD $5')
    print(f'  v8.12 this run:              {len(trades):3d}t | PF {pf:6.2f} | WR {wr*100:.1f}% | DD ${abs(dd):.0f}')


def save_csv(trades, path):
    if not trades: return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(trades[0].keys()))
        w.writeheader(); w.writerows(trades)
    print(f'  Trade log → {path}')


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='GxT v8.7 — true multi-instrument execution')
    ap.add_argument('--file-5m',  default=DEFAULT_5M)
    ap.add_argument('--file-4h',  default=DEFAULT_4H)
    ap.add_argument('--file-1m',  default=DEFAULT_1M)
    ap.add_argument('--file-15m', default=DEFAULT_15M,
                    help='15m data for SMT divergence check (default: 2020-2025)')
    ap.add_argument('--instruments', nargs='+', default=['nq','es','ym'],
                    choices=['nq','es','ym','gc','rty','cl'],
                    help='Which instruments to scan (default: nq es ym)')
    ap.add_argument('--tp', choices=['full','half','failure-swing'], default='full')
    ap.add_argument('--fs-tf', default='1h', help='failure-swing DOL swing resample TF (e.g. 5min,30min,1h)')
    ap.add_argument('--fs-tol-mult', type=float, default=1.0, help='multiply FS_CLUSTER_TOL (sensitivity)')
    ap.add_argument('--profiling-gate', action='store_true', help='4H if-then profiling-sequence selector (test)')
    ap.add_argument('--swing', action='store_true')
    ap.add_argument('--no-london', action='store_true')
    ap.add_argument('--max-sweep', type=float, default=None)
    ap.add_argument('--min-close-pos', type=float, default=0.50)
    ap.add_argument('--min-rr', type=float, default=None)
    ap.add_argument('--nq-leads', action='store_true',
                    help='v8.18: for YM/GC/RTY entries, require NQ led the move')
    ap.add_argument('--h4-direction-gate', action='store_true',
                    help='v8.18: C2/C3 gate -- block NY_AM when 16:00 4H bar strongly opposes daily bias')
    ap.add_argument('--c2-continuation', action='store_true',
                    help='v8.18: on C2 days, flip direction and trade continuation FVG entries')
    ap.add_argument('--driver-gate', action='store_true',
                    help='v8.18: NY_AM first bar must be displacement bar (9:30 Driver filter)')
    ap.add_argument('--driver-model', action='store_true',
                    help='v8.18: add 9:30 Driver as parallel entry model (YM/GC/RTY only)')
    ap.add_argument('--driver-v2', action='store_true',
                    help='v8.18: GxT 9:30/10:00 driver windows + reversal/continuation branch + PSP (all instruments)')
    ap.add_argument('--driver-v2-no-psp', action='store_true',
                    help='v8.18: run --driver-v2 without the PSP confirmation gate')
    ap.add_argument('--driver-news', action='store_true',
                    help='v8.18: GxT 8:30 EST news driver, NFP days only (pre_market window)')
    ap.add_argument('--ss-gate', action='store_true')
    ap.add_argument('--eco-filter', action='store_true')
    ap.add_argument('--london-gate',
                    choices=['any','no-retrace','expand-only','skip-expand'], default='any')
    ap.add_argument('--c3-gate', action='store_true')
    ap.add_argument('--early-window', action='store_true')
    ap.add_argument('--include-premarket', action='store_true')
    ap.add_argument('--include-asia', action='store_true',
                    help='Add Asia session (4:00-10:00 IST) as an entry window')
    ap.add_argument('--all-candidates', action='store_true',
                    help='Take ALL valid setups per session (not just best instrument)')
    ap.add_argument('--nq-confirm', action='store_true',
                    help='NQ must have an active FVG before ES/YM are considered')
    ap.add_argument('--smt-gate', action='store_true',
                    help='Gap 4: require SMT divergence at entry bar')
    ap.add_argument('--two-stage-c3', action='store_true',
                    help='Gap 3: require 2 opposing candles before V-shape')
    ap.add_argument('--asia-gate', action='store_true',
                    help='Gap 1: skip continuation when Asia+London both expanded same direction')
    ap.add_argument('--erl-gate', action='store_true',
                    help='Gap 2: skip if instrument open already at/beyond 80-bar ERL')
    ap.add_argument('--news-align', action='store_true',
                    help='v8.13: skip trades against NFP/CPI/FOMC surprise direction')
    ap.add_argument('--max-gap-nq', type=float, default=None,
                    help='v8.14: skip NQ setups where 4H FVG width > N pts')
    ap.add_argument('--max-gap-es', type=float, default=None,
                    help='v8.14: skip ES setups where 4H FVG width > N pts')
    ap.add_argument('--tp-cap-r', type=float, default=None,
                    help='v8.15: cap TP at entry +/- N * SL_pts (GxT 2R-3R partial exit)')
    ap.add_argument('--us-holiday-filter', action='store_true',
                    help='v8.17: skip NYSE market holidays')
    ap.add_argument('--entry-cutoff-ist', type=str, default=None, metavar='HH:MM',
                    help='v8.17: skip entries after this IST time (e.g. 20:30)')
    ap.add_argument('--out', default='mnq_trade_log_v8_18.csv')
    args = ap.parse_args()

    eco_cal = {}
    if args.news_align:
        eco_cal = load_economic_calendar()
        print(f'  Economic calendar: {len(eco_cal)} directional event days loaded')

    print('Loading data...')
    df5m = pd.read_csv(args.file_5m, parse_dates=['timestamp'])
    df4h = pd.read_csv(args.file_4h, parse_dates=['timestamp'])
    try:
        df1m = pd.read_csv(args.file_1m, parse_dates=['timestamp'])
        print(f'  1M: {len(df1m):,} bars')
    except Exception:
        df1m = None

    df15m = None
    if args.smt_gate:
        try:
            df15m = pd.read_csv(args.file_15m, parse_dates=['timestamp'])
            print(f'  15M: {len(df15m):,} bars (SMT divergence)')
        except Exception as e:
            print(f'  WARNING: 15m data not loaded ({e}), SMT gate disabled')

    trades, daily_pnl, stats = run_backtest(
        df5m, df1m, df4h, df15m,
        instruments       = tuple(args.instruments),
        tp_mode           = args.tp,
        fs_tf             = args.fs_tf,
        fs_tol_mult       = args.fs_tol_mult,
        profiling_gate    = args.profiling_gate,
        swing_hold        = args.swing,
        no_london         = args.no_london,
        max_sweep         = args.max_sweep,
        min_close_pos     = args.min_close_pos,
        min_rr            = args.min_rr,
        nq_leads          = args.nq_leads,
        h4_direction_gate = args.h4_direction_gate,
        c2_continuation   = args.c2_continuation,
        driver_gate       = args.driver_gate,
        driver_model      = args.driver_model,
        driver_v2         = args.driver_v2,
        driver_v2_psp     = not args.driver_v2_no_psp,
        driver_news       = args.driver_news,
        ss_gate           = args.ss_gate,
        eco_filter        = args.eco_filter,
        london_gate       = args.london_gate,
        c3_gate           = args.c3_gate,
        early_window      = args.early_window,
        include_premarket = args.include_premarket,
        include_asia      = args.include_asia,
        one_per_session   = not args.all_candidates,
        nq_confirm        = args.nq_confirm,
        smt_gate          = args.smt_gate,
        two_stage_c3      = args.two_stage_c3,
        asia_gate         = args.asia_gate,
        erl_gate          = args.erl_gate,
        news_align        = args.news_align,
        eco_calendar      = eco_cal,
        max_gap_pts       = {k: v for k, v in
                             [('nq', args.max_gap_nq), ('es', args.max_gap_es)]
                             if v is not None} or None,
        tp_cap_r          = args.tp_cap_r,
        holiday_filter    = args.us_holiday_filter,
        entry_cutoff_hm   = (lambda s: int(s.split(':')[0])*60 + int(s.split(':')[1]))(args.entry_cutoff_ist)
                            if args.entry_cutoff_ist else None,
    )

    print_results(trades, daily_pnl, stats, tuple(args.instruments))
    out = os.path.expanduser(f'~/mnq_trading/backtest/{args.out}')
    save_csv(trades, out)
    print(f'\n  Stats: {dict(stats)}')
