"""
Asia 1H FVG Positional Backtest
Strategy: 1H FVGs detected from 5m resampled data.
Entry: first 5m bar that touches the FVG during Asia session (04:00-10:00 IST).
Direction: LONG at bull FVG gap_bot, SHORT at bear FVG gap_top.
TP: Prior Day High (bull) / Prior Day Low (bear).
SL: 1 tick below gap_bot (bull) / 1 tick above gap_top (bear).
Exits run until 21:00 IST same day.

Usage:
  python3 asia_1h_fvg_test.py              # unfiltered + filtered runs
  python3 asia_1h_fvg_test.py --filtered   # filtered only
"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.expanduser('~/mnq_trading/backtest'))

import pandas as pd
import numpy as np
from collections import defaultdict
from mnq_backtest_engine_v8_18 import (
    INST_CONFIG, FVG, simulate_trade, get_pdh_pdl,
    _US_HOLIDAYS, check_nq_leads
)

DATA_5M = os.path.expanduser('~/mnq_trading/data/MULTI_5min_IST_2020_2025.csv')

INSTRUMENTS   = ('nq', 'es', 'ym', 'gc', 'rty', 'cl')
ASIA_START_H  = 4    # 04:00 IST
ASIA_END_H    = 10   # 10:00 IST
SESSION_END_H = 21   # trades expire at 21:00 IST
MAX_FVG_AGE_H = 48   # max age for a 1H FVG to remain active
COMMISSION_RATE = 0.5  # PnL factor (e.g., to account for commissions/slippage)

# Per-instrument gap width bounds for use_gap_filter — calibrated to each instrument's price scale
GAP_BOUNDS = {
    'nq':  (6.0,  80.0),   # NQ pts: tiny noise < 6, wide failures > 80
    'es':  (6.0,  80.0),
    'ym':  (6.0,  80.0),
    'gc':  (0.5,  10.0),   # GC $/oz: typical FVG 0.5–10
    'rty': (0.5,  10.0),
    'cl':  (0.10,  2.0),   # CL $/bbl: typical FVG 10 cents to $2
}


def resample_to_1h(df5m, instrument):
    hi = f'{instrument}_high'; lo = f'{instrument}_low'
    op = f'{instrument}_open'; cl = f'{instrument}_close'
    if hi not in df5m.columns:
        return None
    sub = df5m[['timestamp', op, hi, lo, cl]].copy().set_index('timestamp')
    r = sub.resample('1h').agg({op: 'first', hi: 'max', lo: 'min', cl: 'last'}).dropna()
    return r.reset_index()


def detect_1h_fvgs(df1h, instrument):
    cfg    = INST_CONFIG[instrument]
    hi_col = f'{instrument}_high';  lo_col = f'{instrument}_low'
    op_col = f'{instrument}_open';  cl_col = f'{instrument}_close'
    min_gap = cfg['min_gap']; disp_ratio = cfg['disp_ratio']; disp_body = cfg['disp_body']

    fvgs = []; df = df1h.reset_index(drop=True)
    for i in range(2, len(df)):
        b0, b1, b2 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
        if pd.isna(b0.get(hi_col, float('nan'))): continue
        prior = df.iloc[max(0, i-7):i-1]
        if len(prior) < 2: continue
        b1_range = float(b1[hi_col]) - float(b1[lo_col])
        if b1_range <= 0: continue
        avg_prior = (prior[hi_col].astype(float) - prior[lo_col].astype(float)).mean()
        if avg_prior <= 0 or b1_range < avg_prior * disp_ratio: continue
        body = abs(float(b1[cl_col]) - float(b1[op_col]))
        if body / b1_range < disp_body: continue

        gb_bull = float(b0[hi_col]); gt_bull = float(b2[lo_col])
        if gt_bull - gb_bull >= min_gap and float(b1[cl_col]) > float(b1[op_col]):
            fvgs.append(FVG(gap_top=gt_bull, gap_bot=gb_bull, direction='bull',
                            formed_ts=b2['timestamp'], formed_idx=i, instrument=instrument))
        gt_bear = float(b0[lo_col]); gb_bear = float(b2[hi_col])
        if gt_bear - gb_bear >= min_gap and float(b1[cl_col]) < float(b1[op_col]):
            fvgs.append(FVG(gap_top=gt_bear, gap_bot=gb_bear, direction='bear',
                            formed_ts=b2['timestamp'], formed_idx=i, instrument=instrument))
    return fvgs


def build_1h_kill_times(fvgs, df1h, instrument):
    """Precompute kill timestamps for all FVGs using vectorized numpy ops."""
    cl_col = f'{instrument}_close'
    kill_times = {}
    ts_arr = df1h['timestamp'].values          # numpy datetime64 array
    cl_arr = df1h[cl_col].values.astype(float) # numpy float array

    for fvg in fvgs:
        formed = np.datetime64(fvg.formed_ts)
        mask   = ts_arr > formed
        if not mask.any():
            kill_times[(instrument, fvg.formed_ts)] = None
            continue
        future_ts = ts_arr[mask]
        future_cl = cl_arr[mask]
        if fvg.direction == 'bull':
            hit = future_cl < fvg.gap_bot
        else:
            hit = future_cl > fvg.gap_top
        idx = np.argmax(hit)   # index of first True; 0 if none
        kill_times[(instrument, fvg.formed_ts)] = (
            pd.Timestamp(future_ts[idx]) if hit[idx] else None)
    return kill_times


def get_active_1h_fvgs(fvgs, kill_times, as_of_ts, instrument):
    """Fast active FVG lookup using precomputed kill_times. O(FVGs)."""
    active = []
    for fvg in fvgs:
        if fvg.formed_ts >= as_of_ts: continue
        age_h = (as_of_ts - fvg.formed_ts).total_seconds() / 3600
        if age_h > MAX_FVG_AGE_H: continue
        killed = kill_times.get((instrument, fvg.formed_ts))
        if killed is not None and killed <= as_of_ts: continue
        active.append(fvg)
    return active


def run(use_holiday_filter=False, use_nq_leads=False, use_nq_confirm=False,
        use_gap_filter=False, use_companion_gate=False, entry_mode='far'):
    # entry_mode: 'far' = original gap_bot/gap_top (degenerate ~1-tick risk, lookahead-only),
    #             'near' = gap_top(bull)/gap_bot(bear) first-touch, risk = full gap width,
    #             'ce'  = consequent encroachment (gap midpoint), risk = half gap width.
    # SL always sits beyond the FAR edge (gap_bot-tick bull / gap_top+tick bear).
    print(f"\nLoading 5m data...")
    df5m = pd.read_csv(DATA_5M, parse_dates=['timestamp'])
    df5m['date'] = df5m['timestamp'].dt.date
    dates = sorted(df5m['date'].unique())

    print("Detecting 1H FVGs and precomputing kill times...")
    all_1h_fvgs   = {}
    all_kill_times = {}
    for inst in INSTRUMENTS:
        if f'{inst}_high' not in df5m.columns: continue
        df1h = resample_to_1h(df5m, inst)
        if df1h is None or len(df1h) < 3: continue
        fvgs  = detect_1h_fvgs(df1h, inst)
        kills = build_1h_kill_times(fvgs, df1h, inst)
        all_1h_fvgs[inst]    = fvgs
        all_kill_times[inst] = kills
        print(f"  {inst.upper()}: {len(fvgs)} FVGs "
              f"({sum(1 for f in fvgs if f.direction=='bull')}b/"
              f"{sum(1 for f in fvgs if f.direction=='bear')}be), "
              f"{sum(1 for v in kills.values() if v)} killed")

    # Precompute PDH/PDL for all (inst, date) pairs — avoids O(n) scan per call
    print("Precomputing PDH/PDL cache...")
    pdh_cache = {}; pdl_cache = {}
    for inst in INSTRUMENTS:
        hi_col = f'{inst}_high'; lo_col = f'{inst}_low'
        if hi_col not in df5m.columns: continue
        daily_hi = df5m.groupby('date')[hi_col].max()
        daily_lo = df5m.groupby('date')[lo_col].min()
        prev_hi  = daily_hi.shift(1)   # previous day's high
        prev_lo  = daily_lo.shift(1)
        for d in dates:
            pdh_cache[(inst, d)] = float(prev_hi.get(d, float('nan')))
            pdl_cache[(inst, d)] = float(prev_lo.get(d, float('nan')))
        print(f"  {inst.upper()} PDH/PDL cached")

    # Pre-split df5m by date for fast day lookup
    print("Pre-splitting 5m data by date...")
    df5m_by_date = {d: g.reset_index(drop=True) for d, g in df5m.groupby('date')}

    trades = []; stats = defaultdict(int)
    print(f"Running backtest over {len(dates)} dates...")

    for date in dates:
        if use_holiday_filter and date in _US_HOLIDAYS:
            stats['holiday_skip'] += 1; continue

        day_df5m = df5m_by_date.get(date)
        if day_df5m is None or len(day_df5m) < 6: continue

        asia_bars = day_df5m[
            (day_df5m['timestamp'].dt.hour >= ASIA_START_H) &
            (day_df5m['timestamp'].dt.hour < ASIA_END_H)
        ].reset_index(drop=True)
        if len(asia_bars) == 0: continue

        asia_start_ts = asia_bars['timestamp'].iloc[0]
        sess_end_ts   = dt.datetime.combine(date, dt.time(SESSION_END_H, 0))

        todays_losses = set()
        for inst in INSTRUMENTS:
            if inst not in all_1h_fvgs: continue
            hi_col = f'{inst}_high'; lo_col = f'{inst}_low'
            if hi_col not in day_df5m.columns: continue
            if use_companion_gate and todays_losses:
                stats['companion_gate_skip'] += 1; continue

            tick = INST_CONFIG[inst]['tick']
            pdh  = pdh_cache.get((inst, date))
            pdl  = pdl_cache.get((inst, date))
            if pdh is None or pdh != pdh: pdh = None  # nan check
            if pdl is None or pdl != pdl: pdl = None
            active = get_active_1h_fvgs(
                all_1h_fvgs[inst], all_kill_times[inst], asia_start_ts, inst)
            if not active: continue

            entered_bull = entered_bear = False

            for fvg in sorted(active, key=lambda f: f.formed_ts, reverse=True):

                if use_gap_filter:
                    gap_w = fvg.gap_top - fvg.gap_bot
                    gmin, gmax = GAP_BOUNDS.get(inst, (6.0, 80.0))
                    if gap_w < gmin or gap_w > gmax:
                        stats['gap_filter_skip'] += 1; continue

                if use_nq_confirm and inst != 'nq':
                    nq_active = get_active_1h_fvgs(
                        all_1h_fvgs.get('nq', []), all_kill_times.get('nq', {}),
                        asia_start_ts, 'nq')
                    if not any(f.direction == fvg.direction for f in nq_active):
                        stats['nq_confirm_skip'] += 1; continue

                if fvg.direction == 'bull' and not entered_bull:
                    entry = (fvg.gap_bot if entry_mode == 'far'
                             else fvg.gap_top if entry_mode == 'near'
                             else (fvg.gap_top + fvg.gap_bot) / 2)
                    if pdh is None or pdh <= entry: continue
                    sl_lvl = fvg.gap_bot - tick; tp_lvl = pdh
                    for bidx in range(len(asia_bars)):
                        bar = asia_bars.iloc[bidx]
                        if float(bar.get(lo_col, 9999)) <= entry <= float(bar.get(hi_col, 0)):
                            if use_nq_leads and not check_nq_leads(
                                    asia_bars, bidx, 'bull', inst,
                                    all_instruments=list(all_1h_fvgs.keys())):
                                stats['nq_leads_skip'] += 1; break
                            outcome, exit_px, _ = simulate_trade(
                                day_df5m, entry, sl_lvl, tp_lvl, 'bull',
                                bar['timestamp'], sess_end_ts, instrument=inst)
                            trades.append(dict(date=date, inst=inst, direction='bull',
                                               entry=entry, outcome=outcome,
                                               gap_bot=fvg.gap_bot, gap_top=fvg.gap_top,
                                               pnl=round((exit_px - entry) * COMMISSION_RATE, 2)))
                            if outcome == 'LOSS': todays_losses.add(inst)
                            entered_bull = True; break

                elif fvg.direction == 'bear' and not entered_bear:
                    entry = (fvg.gap_top if entry_mode == 'far'
                             else fvg.gap_bot if entry_mode == 'near'
                             else (fvg.gap_top + fvg.gap_bot) / 2)
                    if pdl is None or pdl >= entry: continue
                    sl_lvl = fvg.gap_top + tick; tp_lvl = pdl
                    for bidx in range(len(asia_bars)):
                        bar = asia_bars.iloc[bidx]
                        if float(bar.get(lo_col, 0)) <= entry <= float(bar.get(hi_col, 0)):
                            if use_nq_leads and not check_nq_leads(
                                    asia_bars, bidx, 'bear', inst,
                                    all_instruments=list(all_1h_fvgs.keys())):
                                stats['nq_leads_skip'] += 1; break
                            outcome, exit_px, _ = simulate_trade(
                                day_df5m, entry, sl_lvl, tp_lvl, 'bear',
                                bar['timestamp'], sess_end_ts, instrument=inst)
                            trades.append(dict(date=date, inst=inst, direction='bear',
                                               entry=entry, outcome=outcome,
                                               gap_bot=fvg.gap_bot, gap_top=fvg.gap_top,
                                               pnl=round((entry - exit_px) * COMMISSION_RATE, 2)))
                            if outcome == 'LOSS': todays_losses.add(inst)
                            entered_bear = True; break

    # ── Summary ───────────────────────────────────────────────────────────────
    wins   = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    bes    = [t for t in trades if t['outcome'] == 'BE']
    exps   = [t for t in trades if t['outcome'] == 'EXPIRED']
    net    = sum(t['pnl'] for t in trades)
    wr     = len(wins) / max(1, len(wins) + len(losses)) * 100
    pf_den = abs(sum(t['pnl'] for t in losses))
    pf     = sum(t['pnl'] for t in wins) / pf_den if pf_den > 0 else float('inf')
    cum = 0; peak = 0; max_dd = 0
    for t in sorted(trades, key=lambda x: x['date']):
        cum += t['pnl']; peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)

    gates = []
    if use_holiday_filter:  gates.append("holiday")
    if use_nq_leads:        gates.append("nq-leads")
    if use_nq_confirm:      gates.append("nq-confirm")
    if use_gap_filter:      gates.append("gap[6-80]")
    if use_companion_gate:  gates.append("companion-gate")
    label = "FILTERED: " + "+".join(gates) if gates else "UNFILTERED"

    print(f"\n{'='*60}")
    print(f"Asia 1H FVG Positional  [{label}]")
    print(f"{'='*60}")
    print(f"Trades: {len(trades)}  W:{len(wins)} L:{len(losses)} BE:{len(bes)} EXP:{len(exps)}")
    print(f"WR    : {wr:.1f}%  ({len(wins)+len(losses)} contested)")
    print(f"PF    : {pf:.2f}")
    print(f"Net   : ${net:.2f}")
    print(f"Max DD: ${max_dd:.2f}")
    print(f"Losses: {len(losses)}")
    print("\nPer instrument:")
    for i in sorted(set(t['inst'] for t in trades)):
        it = [t for t in trades if t['inst'] == i]
        iw = [t for t in it if t['outcome'] == 'WIN']
        il = [t for t in it if t['outcome'] == 'LOSS']
        inet = sum(t['pnl'] for t in it)
        iwr  = len(iw) / max(1, len(iw) + len(il)) * 100
        print(f"  {i.upper():4s}: {len(it):3d}T  WR {iwr:.0f}%  Net ${inet:.2f}")
    if stats:
        print(f"\nGate stats: {dict(stats)}")
    return trades


if __name__ == '__main__':
    filtered_only = '--filtered' in sys.argv
    if not filtered_only:
        run(use_holiday_filter=False, use_nq_leads=False)
    run(use_holiday_filter=True, use_nq_leads=True)
    run(use_holiday_filter=True, use_nq_leads=True,
        use_gap_filter=True)
    run(use_holiday_filter=True, use_nq_leads=True,
        use_gap_filter=True, use_companion_gate=True)
