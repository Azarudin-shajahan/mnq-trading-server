"""1m-resolution confirmation of the Asia 1H FVG entry-bar lookahead.
Resolves the entry 5m window (fill + BE + 1-tick SL + TP) at 1-minute granularity,
then continues at 5m identically to the original simulate_trade. Any delta vs the
original is purely the entry-bar realism the original skipped (timestamp > entry_ts).
"""
import sys, io, contextlib, os
import pandas as pd, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnq_trading/diagnostics'))
import asia_1h_fvg_test as A

# preload 1m, only needed cols
files = [os.path.expanduser('~/mnq_trading/data/MULTI_1min_IST_2020_2024.csv'),
         os.path.expanduser('~/mnq_trading/data/MULTI_1min_IST_2025.csv')]
hdr = pd.read_csv(files[0], nrows=1).columns
insts = [i for i in ('nq','es','ym','rty','gc') if f'{i}_high' in hdr]
usecols = ['timestamp'] + [f'{i}_{s}' for i in insts for s in ('high','low')]
print(f'1m instruments available: {insts}', flush=True)
d1 = pd.concat([pd.read_csv(f, usecols=lambda c: c in usecols, parse_dates=['timestamp'])
                for f in files], ignore_index=True)
d1['date'] = d1['timestamp'].dt.date
ONE_M = {d: g for d, g in d1.groupby('date')}
print(f'1m days loaded: {len(ONE_M)}  ({min(ONE_M)} -> {max(ONE_M)})', flush=True)

orig = A.simulate_trade

def sim_1m(df_sim, entry, sl, tp, direction, entry_ts, end_ts, instrument='nq'):
    hi = f'{instrument}_high'; lo = f'{instrument}_low'
    risk = abs(entry - sl); be = False; sl_live = sl
    w1 = entry_ts + pd.Timedelta(minutes=5)
    onem = ONE_M.get(entry_ts.date() if hasattr(entry_ts, 'date') else pd.Timestamp(entry_ts).date())
    bull = direction == 'bull'
    if onem is not None and hi in onem.columns:
        win = onem[(onem['timestamp'] >= entry_ts) & (onem['timestamp'] < w1)]
        filled = False
        for _, b in win.iterrows():
            h = float(b[hi]); l = float(b[lo])
            if np.isnan(h) or np.isnan(l):
                continue
            if not filled:
                if bull and l <= entry: filled = True
                elif (not bull) and h >= entry: filled = True
                else: continue
            if bull:
                if not be and h >= entry + risk: be = True; sl_live = entry
                if l <= sl_live: return ('BE' if be else 'LOSS', entry if be else sl_live, b['timestamp'])
                if h >= tp: return ('WIN', tp, b['timestamp'])
            else:
                if not be and l <= entry - risk: be = True; sl_live = entry
                if h >= sl_live: return ('BE' if be else 'LOSS', entry if be else sl_live, b['timestamp'])
                if l <= tp: return ('WIN', tp, b['timestamp'])
    else:
        eb = df_sim[df_sim['timestamp'] == entry_ts]
        if len(eb):
            l = float(eb.iloc[0][lo]); h = float(eb.iloc[0][hi])
            if bull and l <= sl: return ('LOSS', sl, entry_ts)
            if (not bull) and h >= sl: return ('LOSS', sl, entry_ts)
    fut = df_sim[(df_sim['timestamp'] >= w1) & (df_sim['timestamp'] <= end_ts)]
    for _, fb in fut.iterrows():
        h = float(fb[hi]); l = float(fb[lo])
        if bull:
            if not be and h >= entry + risk: be = True; sl_live = entry
            if l <= sl_live: return ('BE' if be else 'LOSS', entry if be else sl_live, fb['timestamp'])
            if h >= tp: return ('WIN', tp, fb['timestamp'])
        else:
            if not be and l <= entry - risk: be = True; sl_live = entry
            if h >= sl_live: return ('BE' if be else 'LOSS', entry if be else sl_live, fb['timestamp'])
            if l <= tp: return ('WIN', tp, fb['timestamp'])
    return ('EXPIRED', entry, end_ts)

def netwr(trades):
    w = [t for t in trades if t['outcome'] == 'WIN']; l = [t for t in trades if t['outcome'] == 'LOSS']
    return len(trades), len(w), len(l), len(w)/max(1, len(w)+len(l))*100, sum(t['pnl'] for t in trades)

cfg = dict(use_holiday_filter=True, use_nq_leads=True, use_gap_filter=True, use_companion_gate=True)
with contextlib.redirect_stdout(io.StringIO()):
    A.simulate_trade = orig;   base = A.run(**cfg)
    A.simulate_trade = sim_1m; oneM = A.run(**cfg)

nb = netwr(base); no = netwr(oneM)
print('\nLOCKED Asia config (holiday+nq-leads+gap+companion):')
print(f'  ORIGINAL (entry bar SKIPPED) : {nb[0]}T  W:{nb[1]} L:{nb[2]}  WR {nb[3]:.1f}%  Net ${nb[4]:.2f}')
print(f'  1m-RESOLVED entry bar        : {no[0]}T  W:{no[1]} L:{no[2]}  WR {no[3]:.1f}%  Net ${no[4]:.2f}')
print(f'  --> Net change: ${no[4]-nb[4]:.2f}  ({(no[4]-nb[4])/abs(nb[4])*100:+.0f}%)')
