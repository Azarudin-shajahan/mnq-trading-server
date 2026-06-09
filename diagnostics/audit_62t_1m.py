"""1m-resolution audit of the v8.18 62T PERFECT config.
Re-runs the exact 62T config with simulate_trade resolved at 1m (proper intra-bar
SL-vs-BE-vs-TP ordering) vs the original 5m sim. If the '0 losses / DD $0' claim
survives 1m it's clean; if losses appear, the zero-DD is an intra-bar ordering artifact.
"""
import sys, io, contextlib, os
import pandas as pd, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnq_trading/backtest'))
import mnq_backtest_engine_v8_18 as E

DATA = os.path.expanduser('~/mnq_trading/data')
df5m = pd.read_csv(f'{DATA}/MULTI_5min_IST_2020_2025.csv', parse_dates=['timestamp'])
df4h = pd.read_csv(f'{DATA}/MULTI_4h_IST_2020_2025.csv', parse_dates=['timestamp'])

m1files = [f'{DATA}/MULTI_1min_IST_2020_2024.csv', f'{DATA}/MULTI_1min_IST_2025.csv']
hdr = pd.read_csv(m1files[0], nrows=1).columns
m1insts = [i for i in ('nq','es','ym','rty') if f'{i}_high' in hdr]
uc = ['timestamp'] + [f'{i}_{s}' for i in m1insts for s in ('high','low')]
d1 = pd.concat([pd.read_csv(f, usecols=lambda c: c in uc, parse_dates=['timestamp']) for f in m1files],
               ignore_index=True)
d1['date'] = d1['timestamp'].dt.date
ONE_M = {d: g for d, g in d1.groupby('date')}
print(f'1m loaded: {len(ONE_M)} days, insts {m1insts}', flush=True)

orig = E.simulate_trade
def sim_1m(df_sim, entry_price, sl, tp, direction, entry_ts, end_ts, instrument='nq'):
    hi = f'{instrument}_high'; lo = f'{instrument}_low'
    onem = ONE_M.get(entry_ts.date() if hasattr(entry_ts,'date') else pd.Timestamp(entry_ts).date())
    if onem is None or hi not in onem.columns:
        return orig(df_sim, entry_price, sl, tp, direction, entry_ts, end_ts, instrument)
    fut = onem[(onem['timestamp'] > entry_ts) & (onem['timestamp'] <= end_ts)]
    risk = abs(entry_price - sl); be = False; sl_live = sl
    bull = direction == 'bull'
    for _, fb in fut.iterrows():
        fh = float(fb[hi]); fl = float(fb[lo])
        if np.isnan(fh) or np.isnan(fl): continue
        if bull:
            if not be and fh >= entry_price + risk: be = True; sl_live = entry_price
            if fl <= sl_live:
                return ('BE' if be else 'LOSS', entry_price if be else sl_live, fb['timestamp'])
            if fh >= tp: return ('WIN', tp, fb['timestamp'])
        else:
            if not be and fl <= entry_price - risk: be = True; sl_live = entry_price
            if fh >= sl_live:
                return ('BE' if be else 'LOSS', entry_price if be else sl_live, fb['timestamp'])
            if fl <= tp: return ('WIN', tp, fb['timestamp'])
    return ('EXPIRED', entry_price, end_ts)

cfg = dict(instruments=('nq','es','ym','gc','rty'), tp_mode='full', no_london=True,
           london_gate='skip-expand', include_premarket=True, nq_confirm=True,
           one_per_session=False, nq_leads=True, driver_model=True, h4_direction_gate=True,
           holiday_filter=True, entry_cutoff_hm=20*60+30, max_gap_pts={'nq': 80})

def summarize(trades, daily_pnl):
    o = lambda k: sum(1 for t in trades if t['outcome'] == k)
    net = sum(daily_pnl.values())
    eq = 0; pk = 0; dd = 0
    for d in sorted(daily_pnl): eq += daily_pnl[d]; pk = max(pk, eq); dd = min(dd, eq - pk)
    L = o('LOSS'); W = o('WIN')
    wr = W / max(1, W + L) * 100
    return f"{len(trades)}T  W{W} L{L} BE{o('BE')} EXP{o('EXPIRED')}  WR{wr:.1f}%  Net${net:.2f}  DD${dd:.2f}"

print('\n62T PERFECT config — original 5m sim vs 1m-resolved:')
for tag, fn in [('ORIGINAL 5m', orig), ('1m-RESOLVED', sim_1m)]:
    E.simulate_trade = fn
    with contextlib.redirect_stdout(io.StringIO()):
        trades, daily_pnl, stats = E.run_backtest(df5m, None, df4h, **cfg)
    print(f'  {tag:13}: {summarize(trades, daily_pnl)}')
