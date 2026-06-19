#!/usr/bin/env python3
"""Vol-targeting SHADOW sizer for the forward demo.

Wires vol-targeting into the demo chain WITHOUT changing what is actually traded.
The demo executes at min size (1 lot) for a clean OOS read; this reads the demo
trade CSV that `demo_reconciliation.to_demo_csv` emits (date,entry,sl,pnl,leg) and
computes, per trade:
  - regime (causal, from regime_filter)
  - vol_mult = clip(target_atr / atr_for_date, LO, HI)
  - rec_contracts under FIXED vs VOL-TARGET sizing
  - the shadow $ P&L each scheme WOULD have produced (live pt value)
then builds both shadow equity curves under the prop rules. This lets you MEASURE,
forward, whether vol-targeting improves $ return/DD on the REAL demo trades before
ever sizing up. It is a RECOMMENDATION/measurement layer only.

SCOPE: research/decision layer. Does NOT place or size live orders; AUTOMATION
stays OFF. Actual demo size is unchanged.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict

import regime_filter as RF
from risk_sizer import _atr_targets, VOL_LO, VOL_HI

LIVE_PT_VALUE = 2.00          # live MNQ $/pt (demo). backtest is 0.50 - do not confuse.


def _contracts(risk_pts, risk_dollars, mult, pt_value, max_contracts):
    if risk_pts <= 0:
        return 0
    c = round(risk_dollars * mult / (risk_pts * pt_value))
    return max(1, min(int(c), max_contracts))


def size_demo(trades, args, atr_map, regime_map):
    """Return per-trade shadow rows + fixed/vol-target equity sims."""
    sims = {}
    for mode in ('fixed', 'vol-target'):
        equity = args.start_equity
        peak = equity
        max_dd = 0.0
        breached = None
        by_day = defaultdict(float)
        reg_pnl = defaultdict(float)
        rows = []
        for tr in trades:
            date = tr['date'][:10]
            if by_day[date] <= -args.daily_loss:
                continue
            risk_pts = abs(float(tr['entry']) - float(tr['sl']))
            atr, target = atr_map.get(date, (None, None))
            if mode == 'vol-target' and atr and target and atr > 0:
                mult = max(VOL_LO, min(target / atr, VOL_HI))
            else:
                mult = 1.0
            contracts = _contracts(risk_pts, args.risk_dollars, mult,
                                   args.pt_value, args.max_contracts)
            pnl = float(tr['pnl']) * args.pt_value * contracts
            equity += pnl
            by_day[date] += pnl
            reg = regime_map.get(date, 'unknown')
            reg_pnl[reg] += pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            if peak - equity >= args.trailing_dd and breached is None:
                breached = date
            if mode == 'vol-target':
                rows.append({'date': date, 'leg': tr.get('leg', ''), 'regime': reg,
                             'risk_pts': round(risk_pts, 2), 'vol_mult': round(mult, 2),
                             'rec_contracts': contracts, 'shadow_pnl_usd': round(pnl, 2)})
        total = equity - args.start_equity
        sims[mode] = {'total': round(total, 2), 'max_dd': round(max_dd, 2),
                      'ret_dd': round(total / max_dd, 2) if max_dd > 0 else float('inf'),
                      'breached': breached, 'reg_pnl': dict(reg_pnl), 'rows': rows}
    return sims


def report(trades, args):
    atr_map = _atr_targets()
    regime_map = RF.load_table()
    sims = size_demo(trades, args, atr_map, regime_map)
    print("\n  DEMO VOL-TARGET SHADOW  (recommendation only; actual demo = min size, "
          "AUTOMATION off)")
    print(f"  {len(trades)} demo trades | live pt=${args.pt_value} | "
          f"risk=${args.risk_dollars}/trade | start=${args.start_equity:.0f}")
    print("  " + "-" * 60)
    print(f"  {'mode':12} {'shadow$':>9} {'maxDD$':>8} {'ret/DD':>8} {'breach':>10}")
    for mode in ('fixed', 'vol-target'):
        s = sims[mode]
        rd = 'inf' if s['ret_dd'] == float('inf') else f"{s['ret_dd']:.2f}"
        print(f"  {mode:12} {s['total']:>9.0f} {s['max_dd']:>8.0f} {rd:>8} "
              f"{str(s['breached']):>10}")
    print("\n  per-trade vol-target recommendation:")
    print(f"  {'date':11} {'leg':5} {'regime':10} {'riskPts':>7} {'xmult':>6} "
          f"{'rec_ct':>6} {'shadow$':>8}")
    for r in sims['vol-target']['rows']:
        print(f"  {r['date']:11} {r['leg']:5} {r['regime']:10} {r['risk_pts']:>7.2f} "
              f"{r['vol_mult']:>6.2f} {r['rec_contracts']:>6} {r['shadow_pnl_usd']:>8.0f}")
    print()
    return sims


def load_demo(path):
    return sorted(csv.DictReader(open(path)), key=lambda r: r['date'])


def selftest():
    """Prove the wire end-to-end on demo_reconciliation's synthetic demo CSV."""
    import demo_reconciliation as DR
    DR.selftest()
    demo_csv = "/tmp/demo_recon_selftest_trades.csv"
    trades = load_demo(demo_csv)

    class A:
        start_equity = 50000
        risk_dollars = 150
        daily_loss = 1000
        trailing_dd = 2000
        max_contracts = 40
        pt_value = LIVE_PT_VALUE
    report(trades, A())
    print("SELF-TEST OK: demo CSV -> vol-target shadow sizing + equity curves "
          "(actual demo size unchanged).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', help='demo trades CSV (date,entry,sl,pnl,leg) from demo_reconciliation')
    ap.add_argument('--start-equity', type=float, default=50000)
    ap.add_argument('--risk-dollars', type=float, default=150)
    ap.add_argument('--pt-value', type=float, default=LIVE_PT_VALUE)
    ap.add_argument('--daily-loss', type=float, default=1000)
    ap.add_argument('--trailing-dd', type=float, default=2000)
    ap.add_argument('--max-contracts', type=int, default=40)
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest or not args.demo:
        selftest()
    else:
        report(load_demo(args.demo), args)


if __name__ == '__main__':
    main()
