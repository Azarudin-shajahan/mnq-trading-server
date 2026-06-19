"""Position-sizing + prop-rule equity simulator for the v8.18 trade log.

Two sizing modes compared head-to-head over the same trade sequence:
  fixed       - constant cash risk per trade (size adapts only to the stop)
  vol-target  - Carver-style: scale size inversely to volatility so risk is
                constant in vol-adjusted terms (size up in low vol, down in high)

Also joins regime_filter labels onto every trade and prints a regime breakdown
(outcome + avg points by low_vol/normal/expansion) - the test of the hypothesis
that the V-shape mean-reversion scalp does well in low-vol/range and poorly in
expansion (where the runner archetype lives).

Sizing math (per trade):
  fixed       contracts = risk_dollars                  / (risk_pts * point_value)
  vol-target  contracts = risk_dollars * vol_mult       / (risk_pts * point_value)
  vol_mult    = clip( target_atr / atr_for_date , LO, HI )   (target = expanding median atr)
  pnl_sized   = pts * point_value * contracts            (pts = per-1-contract P&L in points)

Prop rules (defaults = MFFU 50K): daily-loss soft pause, trailing max drawdown
breach, contract cap. IN-SAMPLE study on the trade log; not a forward result.

ASCII-only docstrings (Python 3.10 on this box rejects non-ASCII source).
"""
import os
import csv
import argparse
import datetime
import statistics
from collections import defaultdict
import pandas as pd
import regime_filter as RF

TRADELOG = os.path.expanduser('~/mnq_trading/backtest/v818_62t_trades.csv')
POINT_VALUE = 0.50          # backtest pt value (live = 2.00; never change backtest)
VOL_LO, VOL_HI = 0.5, 2.0   # vol-target multiplier clamp


def _atr_targets(regime_csv=RF.REGIME_CSV):
    """date_str -> (atr, target_atr). target = expanding median of atr (causal)."""
    t = pd.read_csv(regime_csv)
    t = t.dropna(subset=['daily_atr']).sort_values('date').reset_index(drop=True)
    t['target'] = t['daily_atr'].expanding(min_periods=RF.MIN_HIST).median().shift(1)
    out = {}
    for _, r in t.iterrows():
        out[str(r['date'])] = (float(r['daily_atr']),
                               None if pd.isna(r['target']) else float(r['target']))
    return out


def _contracts(risk_pts, risk_dollars, mult, max_contracts):
    if risk_pts <= 0:
        return 0
    c = round(risk_dollars * mult / (risk_pts * POINT_VALUE))
    return max(1, min(int(c), max_contracts))


def simulate(trades, mode, args, atr_map, regime_map):
    """Sequential equity sim. Returns a result dict."""
    equity = args.start_equity
    peak = equity
    max_dd = 0.0
    breached = None
    by_day = defaultdict(float)
    taken = 0
    regime_pnl = defaultdict(float)
    for tr in trades:
        date = tr['date'][:10]
        # daily soft pause: stop taking trades once the day is down past the limit
        if by_day[date] <= -args.daily_loss:
            continue
        atr, target = atr_map.get(date, (None, None))
        if mode == 'vol-target' and atr and target and atr > 0:
            mult = max(VOL_LO, min(target / atr, VOL_HI))
        else:
            mult = 1.0
        contracts = _contracts(float(tr['risk_pts']), args.risk_dollars, mult,
                               args.max_contracts)
        pnl = float(tr['pts']) * POINT_VALUE * contracts
        equity += pnl
        by_day[date] += pnl
        taken += 1
        regime_pnl[regime_map.get(date, 'unknown')] += pnl
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        if peak - equity >= args.trailing_dd and breached is None:
            breached = date
    total = equity - args.start_equity
    return {
        'mode': mode, 'taken': taken, 'total_pnl': round(total, 2),
        'final_equity': round(equity, 2), 'max_dd': round(max_dd, 2),
        'ret_dd': round(total / max_dd, 2) if max_dd > 0 else float('inf'),
        'breached': breached, 'regime_pnl': dict(regime_pnl),
    }


def regime_breakdown(trades, regime_map):
    """Outcome counts + avg points per regime (the hypothesis test)."""
    agg = defaultdict(lambda: {'n': 0, 'WIN': 0, 'BE': 0, 'EXPIRED': 0, 'pts': []})
    for tr in trades:
        reg = regime_map.get(tr['date'][:10], 'unknown')
        a = agg[reg]
        a['n'] += 1
        a[tr['outcome']] = a.get(tr['outcome'], 0) + 1
        a['pts'].append(float(tr['pts']))
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trades', default=TRADELOG)
    ap.add_argument('--start-equity', type=float, default=50000)
    ap.add_argument('--risk-dollars', type=float, default=150)
    ap.add_argument('--daily-loss', type=float, default=1000)
    ap.add_argument('--trailing-dd', type=float, default=2000)
    ap.add_argument('--max-contracts', type=int, default=40)
    args = ap.parse_args()

    trades = sorted(csv.DictReader(open(args.trades)), key=lambda r: r['date'])
    atr_map = _atr_targets()
    regime_map = RF.load_table()

    print(f"\n  RISK SIZER  ({len(trades)} trades, pt=${POINT_VALUE}, "
          f"risk=${args.risk_dollars}/trade, start=${args.start_equity:.0f})")
    print(f"  prop rules: daily-loss ${args.daily_loss:.0f} | trailing-DD "
          f"${args.trailing_dd:.0f} | max {args.max_contracts} contracts")
    print("  " + "-" * 64)
    print(f"  {'mode':12} {'pnl':>9} {'maxDD':>8} {'ret/DD':>8} {'breach':>10} {'#tk':>4}")
    for mode in ('fixed', 'vol-target'):
        r = simulate(trades, mode, args, atr_map, regime_map)
        rd = 'inf' if r['ret_dd'] == float('inf') else f"{r['ret_dd']:.2f}"
        print(f"  {mode:12} {r['total_pnl']:>9.0f} {r['max_dd']:>8.0f} {rd:>8} "
              f"{str(r['breached']):>10} {r['taken']:>4}")

    print("\n  REGIME BREAKDOWN (does the scalp underperform in expansion?)")
    print(f"  {'regime':10} {'n':>3} {'WIN':>4} {'BE':>4} {'EXP':>4} "
          f"{'avgPts':>7} {'sumPts':>7}")
    agg = regime_breakdown(trades, regime_map)
    order = ['low_vol', 'normal', 'expansion', 'unknown']
    for reg in order:
        if reg not in agg:
            continue
        a = agg[reg]
        avg = statistics.mean(a['pts']) if a['pts'] else 0
        print(f"  {reg:10} {a['n']:>3} {a['WIN']:>4} {a['BE']:>4} "
              f"{a['EXPIRED']:>4} {avg:>7.2f} {sum(a['pts']):>7.1f}")
    print()


if __name__ == '__main__':
    main()
