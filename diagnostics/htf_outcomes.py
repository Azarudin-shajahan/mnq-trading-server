"""Outcome appender + Phase-0 backfill for the discretion-capture journal.

- append_outcomes(date): the next-day automation - records what actually
  happened (NY session net direction, day range) and what v8.18 did that date
  (from its trade log). Causal: only uses bars/log for `date` itself.
- backfill_journal(): seeds data/htf_journal.csv with the deterministic HTF
  context + outcomes for every historical v8.18 trade date. Human label columns
  are left BLANK on purpose - they can only be generated forward, pre-outcome.
"""
import os, csv, datetime
import pandas as pd
import htf_context as H

TRADELOG = os.path.expanduser('~/mnq_trading/backtest/mnq_trade_log_v8_18.csv')
JOURNAL  = os.path.expanduser('~/mnq_trading/data/htf_journal.csv')

HUMAN_FIELDS = ['human_bias', 'human_conf', 'human_drivers', 'human_override']
V818_FIELDS  = ['v818_traded', 'v818_dir', 'v818_outcome', 'v818_pts']
OUTCOME_FIELDS = ['actual_dir', 'actual_range_pts']
# tagged_ts = wall-clock IST when the human locked the bias (proves pre-outcome).
ALL_FIELDS = H.CONTEXT_FIELDS + ['tagged_ts'] + HUMAN_FIELDS + V818_FIELDS + OUTCOME_FIELDS + ['split']

_OUTCOME_RANK = {'WIN': 3, 'BE': 2, 'EXPIRED': 1}


def ny_am_window(d):
    st = H._ENG.session_times(datetime.datetime(d.year, d.month, d.day))
    return st['nyam_start'], st['nyam_end']


def actual_outcome(df5m, date):
    """NY-AM net direction + full-day NQ range for `date`."""
    day = df5m[df5m['date'] == date]
    if len(day) == 0:
        return None, None
    (sh, sm), (eh, em) = ny_am_window(date)
    ny = day[((day['timestamp'].dt.hour > sh) |
              ((day['timestamp'].dt.hour == sh) & (day['timestamp'].dt.minute >= sm))) &
             ((day['timestamp'].dt.hour < eh) |
              ((day['timestamp'].dt.hour == eh) & (day['timestamp'].dt.minute < em)))]
    if len(ny) == 0:
        adir = None
    else:
        net = float(ny.iloc[-1]['nq_close']) - float(ny.iloc[0]['nq_open'])
        adir = 'bull' if net > 0 else 'bear' if net < 0 else 'flat'
    rng = round(float(day['nq_high'].max()) - float(day['nq_low'].min()), 2)
    return adir, rng


def v818_for_date(tradelog, date):
    """Aggregate v8.18's trade(s) on `date`. Prefer the NQ leg for direction."""
    rows = [r for r in tradelog if r['date'][:10] == str(date)]
    if not rows:
        return {'v818_traded': 0, 'v818_dir': None, 'v818_outcome': None, 'v818_pts': None}
    nq = [r for r in rows if r['instrument'] == 'nq']
    dir_row = nq[0] if nq else rows[0]
    best = max(rows, key=lambda r: _OUTCOME_RANK.get(r['outcome'], 0))
    pts = round(sum(float(r['pts']) for r in rows), 2)
    return {'v818_traded': 1, 'v818_dir': dir_row['direction'],
            'v818_outcome': best['outcome'], 'v818_pts': pts}


def backfill_journal():
    df = H.load_5m()
    tradelog = list(csv.DictReader(open(TRADELOG)))
    dates = sorted({r['date'][:10] for r in tradelog})
    rows = []
    for ds in dates:
        d = datetime.date.fromisoformat(ds)
        ctx = H.compute_context(df, d)
        if ctx is None:
            continue
        adir, rng = actual_outcome(df, d)
        row = dict(ctx)
        row['tagged_ts'] = ''                # backfill has no human tag time
        for f in HUMAN_FIELDS:
            row[f] = ''                      # human label: forward-only, never backfilled
        row.update(v818_for_date(tradelog, d))
        row['actual_dir'] = adir
        row['actual_range_pts'] = rng
        row['split'] = 'backfill'            # historical seed, not part of the forward test
        rows.append(row)
    with open(JOURNAL, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"backfill: wrote {len(rows)} rows -> {JOURNAL}")
    return rows


if __name__ == '__main__':
    import sys
    if '--backfill' in sys.argv:
        backfill_journal()
    else:
        print("usage: python3 htf_outcomes.py --backfill")
