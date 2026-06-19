"""HTF deterministic context computer for the discretion-capture journal.

For a given trading DATE, compute the high-timeframe context a discretionary
trader reads BEFORE the NY session (Daye weekly-quarter, true open, premium/
discount, PDH/PDL, overnight/weekend gap, SMT-into-NY, weekly-profile-so-far).

Hard rule: every feature uses ONLY bars at or before the pre-NY snapshot
(NY-AM open) on the target date, plus prior days. No lookahead. A self-test
(run this file directly) corrupts all bars from the snapshot forward and
asserts the context is byte-identical.
"""
import os, datetime, importlib.util
import pandas as pd

ENGINE_PATH = os.path.expanduser('~/mnq_trading/backtest/mnq_backtest_engine_v8_18.py')
DEFAULT_5M  = os.path.expanduser('~/mnq_trading/data/MULTI_5min_IST_2020_2025.csv')
LIVE_5M     = os.path.expanduser('~/mnq_trading/data/MULTI_5min_live_IST.csv')
TRIAD = ('nq', 'es', 'ym')


def _load_engine():
    spec = importlib.util.spec_from_file_location('v818eng', ENGINE_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_ENG = _load_engine()
is_edt = _ENG.is_edt


def load_5m(path=DEFAULT_5M, include_live=True):
    """Load 5m bars. If the daily-refreshed live file exists, concatenate it on
    top (dedup on timestamp, live wins) so the loop transparently sees fresh days
    without ever mutating the frozen historical file."""
    df = pd.read_csv(path, parse_dates=['timestamp'])
    if include_live and os.path.exists(LIVE_5M):
        live = pd.read_csv(LIVE_5M, parse_dates=['timestamp'])
        df = (pd.concat([df, live], ignore_index=True)
                .drop_duplicates(subset='timestamp', keep='last')
                .sort_values('timestamp').reset_index(drop=True))
    df['date'] = df['timestamp'].dt.date
    return df


def et_midnight_ist(d):
    """IST (hour, minute) of 00:00 ET (the Daye daily True Open) for date d."""
    return (9, 30) if is_edt(datetime.datetime(d.year, d.month, d.day)) else (10, 30)


def ny_open_ist(d):
    """IST (hour, minute) of the NY-AM session open = the pre-trade snapshot."""
    st = _ENG.session_times(datetime.datetime(d.year, d.month, d.day))
    return st['nyam_start']


def weekly_quarter(d):
    return {0: 'Q1', 1: 'Q2', 2: 'Q3', 3: 'Q4', 4: 'X-Fri'}.get(d.weekday(), 'weekend')


def _before(bars, hm):
    h, m = hm
    return bars[(bars['timestamp'].dt.hour < h) |
                ((bars['timestamp'].dt.hour == h) & (bars['timestamp'].dt.minute < m))]


def _bar_open_at(bars, hm, col):
    h, m = hm
    row = bars[(bars['timestamp'].dt.hour == h) & (bars['timestamp'].dt.minute == m)]
    return float(row.iloc[0][col]) if len(row) else None


def _swept_levels(pre_bars, prev_bars, inst):
    """Did inst sweep prior-day low / high during the pre-NY window?"""
    if len(prev_bars) == 0 or len(pre_bars) == 0:
        return False, False
    pdl = float(prev_bars[f'{inst}_low'].min())
    pdh = float(prev_bars[f'{inst}_high'].max())
    swept_low = float(pre_bars[f'{inst}_low'].min()) < pdl
    swept_high = float(pre_bars[f'{inst}_high'].max()) > pdh
    return swept_low, swept_high


def _smt_into_ny(pre_bars, prev_bars):
    """Directional SMT going into NY: NQ swept a prior-day level but a companion
    (ES/YM) did NOT follow. 'bull-smt' = NQ swept PDL alone; 'bear-smt' = NQ
    swept PDH alone; else 'none'. Pre-NY window only (no lookahead)."""
    nq_low, nq_high = _swept_levels(pre_bars, prev_bars, 'nq')
    comp = {i: _swept_levels(pre_bars, prev_bars, i) for i in ('es', 'ym')}
    if nq_low and any(not comp[i][0] for i in comp):
        return 'bull-smt'
    if nq_high and any(not comp[i][1] for i in comp):
        return 'bear-smt'
    return 'none'


def _weekly_profile_so_far(df5m, date, dates):
    """Coarse machine-guess of the weekly profile from this week's completed
    days (Monday .. prior day), on NQ. Honest label: it is a guess the human
    can override."""
    monday = date - datetime.timedelta(days=date.weekday())
    wk = [d for d in dates if monday <= d < date]
    if not wk:
        return 'week-open'
    w = df5m[df5m['date'].isin(wk)]
    hi = float(w['nq_high'].max()); lo = float(w['nq_low'].min())
    first_open = float(df5m[df5m['date'] == wk[0]].iloc[0]['nq_open'])
    last_close = float(df5m[df5m['date'] == wk[-1]].iloc[-1]['nq_close'])
    rng = hi - lo
    net = last_close - first_open
    swept_both = (lo < first_open) and (hi > first_open)
    if rng < 120:
        return 'consolidation'
    if swept_both and abs(net) < rng * 0.25:
        return 'seek-destroy'
    return 'expansion-up' if net > 0 else 'expansion-down'


def compute_context(df5m, date):
    """Deterministic HTF context dict for `date` (pre-NY snapshot). None if the
    date is absent from the data."""
    dates = sorted(df5m['date'].unique())
    if date not in dates:
        return None
    snap = ny_open_ist(date)
    day = df5m[df5m['date'] == date]
    pre = _before(day, snap)
    prev = [d for d in dates if d < date]
    prev_bars = df5m[df5m['date'] == prev[-1]] if prev else day.iloc[0:0]

    out = {
        'date': str(date),
        'snapshot_ist': f'{snap[0]:02d}:{snap[1]:02d}',
        'weekly_quarter': weekly_quarter(date),
        'true_open_d': _bar_open_at(day, et_midnight_ist(date), 'nq_open'),
    }
    if len(prev_bars):
        pdh = float(prev_bars['nq_high'].max()); pdl = float(prev_bars['nq_low'].min())
        eq = (pdh + pdl) / 2.0
        to = out['true_open_d']
        prev_close = float(prev_bars.iloc[-1]['nq_close'])
        today_open = float(day.iloc[0]['nq_open'])
        out['pdh'] = round(pdh, 2)
        out['pdl'] = round(pdl, 2)
        out['prem_disc'] = None if to is None else (
            'premium' if to > eq else 'discount' if to < eq else 'eq')
        out['ndog_pts'] = round(today_open - prev_close, 2)
    else:
        out['pdh'] = out['pdl'] = out['prem_disc'] = out['ndog_pts'] = None
    out['nwog_pts'] = out['ndog_pts'] if (date.weekday() == 0 and len(prev_bars)) else None
    out['smt_into_ny'] = _smt_into_ny(pre, prev_bars)
    out['weekly_profile_so_far'] = _weekly_profile_so_far(df5m, date, dates)
    return out


CONTEXT_FIELDS = ['date', 'snapshot_ist', 'weekly_quarter', 'true_open_d',
                  'pdh', 'pdl', 'prem_disc', 'ndog_pts', 'nwog_pts',
                  'smt_into_ny', 'weekly_profile_so_far']


def _lookahead_selftest():
    """Corrupt every bar from the snapshot forward and assert context is
    unchanged for a sample of dates. Proves the computer is causal."""
    df = load_5m(include_live=False)
    dates = sorted(df['date'].unique())
    sample = dates[len(dates)//3: len(dates)//3 + 8]
    ok = 0
    for d in sample:
        clean = compute_context(df, d)
        snap = ny_open_ist(d)
        corrupt = df.copy()
        h, m = snap
        same_day_future = (corrupt['date'] == d) & (
            (corrupt['timestamp'].dt.hour > h) |
            ((corrupt['timestamp'].dt.hour == h) & (corrupt['timestamp'].dt.minute >= m)))
        future = (corrupt['date'] > d) | same_day_future
        for c in corrupt.columns:
            if c.endswith(('_open', '_high', '_low', '_close')):
                corrupt.loc[future, c] = -999999.0
        dirty = compute_context(corrupt, d)
        assert clean == dirty, f"LOOKAHEAD LEAK on {d}:\n {clean}\n {dirty}"
        ok += 1
    print(f"htf_context lookahead self-test: PASS ({ok} dates, future-corrupted, context identical)")


if __name__ == '__main__':
    _lookahead_selftest()
