"""Causal volatility-regime classifier for the discretion/sizing layer.

For each trading DATE, label the prevailing volatility regime using ONLY
completed prior days (no lookahead): low_vol / normal / expansion. Grounded in
the systematic-trading result that mean-reversion edges (v8.18's V-shape scalp)
work in low-vol/range regimes while trend/expansion regimes favour runners.

Regime = trailing daily-range ATR of NQ vs its own expanding history:
  atr_d   = mean(daily range over the prior N completed days)        (excludes today)
  q33/q66 = expanding 33rd/66th percentiles of atr using prior days  (excludes today)
  regime  = low_vol if atr<=q33, expansion if atr>=q66, else normal

A self-test (run this file directly) corrupts every bar from `date` forward and
asserts the label is byte-identical, proving the classifier is causal.

ASCII-only docstrings (Python 3.10 on this box rejects non-ASCII source).
"""
import os
import datetime
import argparse
import pandas as pd
import htf_context as H

REGIME_CSV = os.path.expanduser('~/mnq_trading/data/regime_table.csv')
N_ATR = 14          # trailing daily-range window
MIN_HIST = 40       # min prior atr values before percentiles are trusted


def _daily_frame(df5m):
    """Per-date NQ daily range + causal trailing ATR + expanding tercile labels."""
    daily = (df5m.groupby('date')
             .agg(hi=('nq_high', 'max'), lo=('nq_low', 'min'),
                  close=('nq_close', 'last'))
             .sort_index())
    daily['range'] = daily['hi'] - daily['lo']
    # trailing ATR: prior N completed days only (shift(1) excludes today)
    daily['atr'] = daily['range'].rolling(N_ATR).mean().shift(1)
    # expanding tercile thresholds from atr values strictly before today
    daily['q33'] = daily['atr'].expanding(min_periods=MIN_HIST).quantile(0.33).shift(1)
    daily['q66'] = daily['atr'].expanding(min_periods=MIN_HIST).quantile(0.66).shift(1)

    def label(r):
        if pd.isna(r['atr']) or pd.isna(r['q33']) or pd.isna(r['q66']):
            return 'unknown'
        if r['atr'] <= r['q33']:
            return 'low_vol'
        if r['atr'] >= r['q66']:
            return 'expansion'
        return 'normal'

    daily['regime'] = daily.apply(label, axis=1)
    return daily


def classify(df5m, date):
    """Regime dict for a single date (causal). None if date absent."""
    d = _daily_frame(df5m)
    if date not in d.index:
        return None
    r = d.loc[date]
    return {
        'date': str(date),
        'daily_atr': None if pd.isna(r['atr']) else round(float(r['atr']), 2),
        'regime': r['regime'],
    }


def build_table(df5m=None, out=REGIME_CSV):
    if df5m is None:
        df5m = H.load_5m()
    d = _daily_frame(df5m).reset_index()
    d['daily_atr'] = d['atr'].round(2)
    cols = ['date', 'range', 'daily_atr', 'regime']
    d[cols].to_csv(out, index=False)
    counts = d['regime'].value_counts().to_dict()
    print(f"regime table -> {out}  ({len(d)} dates)")
    print(f"  regime counts: {counts}")
    return d


def load_table(path=REGIME_CSV):
    """date_str -> regime. Build the table first if missing."""
    if not os.path.exists(path):
        build_table(out=path)
    t = pd.read_csv(path)
    return dict(zip(t['date'].astype(str), t['regime']))


def _lookahead_selftest():
    df = H.load_5m(include_live=False)
    dates = sorted(df['date'].unique())
    sample = dates[len(dates) // 2: len(dates) // 2 + 8]
    ok = 0
    for d in sample:
        clean = classify(df, d)
        corrupt = df.copy()
        future = corrupt['date'] >= d           # regime[d] must use only days < d
        for c in corrupt.columns:
            if c.endswith(('_open', '_high', '_low', '_close')):
                corrupt.loc[future, c] = -999999.0
        dirty = classify(corrupt, d)
        assert clean == dirty, f"LOOKAHEAD LEAK on {d}:\n {clean}\n {dirty}"
        ok += 1
    print(f"regime_filter lookahead self-test: PASS "
          f"({ok} dates, today+future corrupted, label identical)")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        _lookahead_selftest()
    else:
        build_table()
