"""Proper-ICT Asia FVG test: enter at near-edge / CE (real gap-width risk),
SL beyond the far edge, ENTRY BAR RESOLVED AT 1m. Compares far/near/ce."""
import sys, io, contextlib, os
import pandas as pd, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnq_trading/diagnostics'))
import asia_1h_fvg_test as A

files = [os.path.expanduser('~/mnq_trading/data/MULTI_1min_IST_2020_2024.csv'),
         os.path.expanduser('~/mnq_trading/data/MULTI_1min_IST_2025.csv')]
hdr = pd.read_csv(files[0], nrows=1).columns
insts = [i for i in ('nq','es','ym','rty','gc') if f'{i}_high' in hdr]
usecols = ['timestamp'] + [f'{i}_{s}' for i in insts for s in ('high','low')]
d1 = pd.concat([pd.read_csv(f, usecols=lambda c: c in usecols, parse_dates=['timestamp'])
                for f in files], ignore_index=True)
d1['date'] = d1['timestamp'].dt.date
ONE_M = {d: g for d, g in d1.groupby('date')}
print(f'1m loaded: {len(ONE_M)} days, insts {insts}', flush=True)

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
            if np.isnan(h) or np.isnan(l): continue
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

A.simulate_trade = sim_1m
cfg = dict(use_holiday_filter=True, use_nq_leads=True, use_gap_filter=True, use_companion_gate=True)

def report(mode, trades):
    w = [t for t in trades if t['outcome']=='WIN']; l=[t for t in trades if t['outcome']=='LOSS']
    be=[t for t in trades if t['outcome']=='BE']; ex=[t for t in trades if t['outcome']=='EXPIRED']
    net=sum(t['pnl'] for t in trades); wr=len(w)/max(1,len(w)+len(l))*100
    gw=sum(t['pnl'] for t in w); gl=abs(sum(t['pnl'] for t in l)); pf=gw/gl if gl else float('inf')
    cum=0; pk=0; dd=0
    for t in sorted(trades, key=lambda x:x['date']):
        cum+=t['pnl']; pk=max(pk,cum); dd=min(dd,cum-pk)
    yrs={}
    for t in trades:
        y=pd.Timestamp(t['date']).year; yrs[y]=yrs.get(y,0)+t['pnl']
    yr_str=' '.join(f'{y}:{v:+.0f}' for y,v in sorted(yrs.items()))
    everyyr=all(v>0 for v in yrs.values())
    print(f'  {mode:5} {len(trades):4}T  W{len(w):3} L{len(l):3} BE{len(be):3} EX{len(ex):3}  '
          f'WR{wr:5.1f}%  PF{pf:5.2f}  Net${net:8.2f}  DD${dd:7.2f}  everyYr={everyyr}')
    print(f'        per-yr net: {yr_str}')

print('\nProper-ICT Asia FVG (1m-resolved entry), locked config holiday+nq-leads+gap+companion:')
for mode in ['far','near','ce']:
    with contextlib.redirect_stdout(io.StringIO()):
        tr = A.run(**cfg, entry_mode=mode)
    report(mode, tr)
