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
# playbook_grade = the cockpit/playbook verdict grade shown for this setup at
# decision time (forward-only, like the human labels). Lets grades be EARNED
# yellow->green from forward outcomes (hardened cockpit plan).
GRADE_FIELDS = ['playbook_grade']
V818_FIELDS  = ['v818_traded', 'v818_dir', 'v818_outcome', 'v818_pts']
OUTCOME_FIELDS = ['actual_dir', 'actual_range_pts']
# tagged_ts = wall-clock IST when the human locked the bias (proves pre-outcome).
ALL_FIELDS = (H.CONTEXT_FIELDS + ['tagged_ts'] + HUMAN_FIELDS + GRADE_FIELDS
              + V818_FIELDS + OUTCOME_FIELDS + ['split'])

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
        for f in HUMAN_FIELDS + GRADE_FIELDS:
            row[f] = ''                      # human label + grade: forward-only, never backfilled
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


def update_outcomes(date):
    """Fill a forward row's outcome columns the day AFTER capture. Requires the
    data feed + v8.18 trade log to be current through `date`. Idempotent: only
    touches a forward row whose outcome is still blank."""
    if not os.path.exists(JOURNAL):
        print("no journal yet"); return
    rows = list(csv.DictReader(open(JOURNAL)))
    df = H.load_5m()
    tradelog = list(csv.DictReader(open(TRADELOG)))
    hit = False
    for r in rows:
        if r['date'] == str(date) and r['split'] == 'forward' and not r['actual_dir']:
            # fill pending machine context now that the day's bars have settled
            if not r['true_open_d']:
                ctx = H.compute_context(df, date)
                if ctx:
                    for k, v in ctx.items():
                        r[k] = '' if v is None else v
            adir, rng = actual_outcome(df, date)
            r['actual_dir'] = adir if adir is not None else ''
            r['actual_range_pts'] = rng if rng is not None else ''
            for k, v in v818_for_date(tradelog, date).items():
                r[k] = '' if v is None else v
            hit = True
    if not hit:
        print(f"no open forward row for {date}"); return
    with open(JOURNAL, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"updated outcomes for {date}")


def update_pending():
    """Retry every forward row whose outcome is still blank (robust to data lag;
    the natural cron call - no date guessing)."""
    if not os.path.exists(JOURNAL):
        print("no journal yet"); return
    rows = list(csv.DictReader(open(JOURNAL)))
    dates = sorted({r['date'] for r in rows
                    if r['split'] == 'forward' and not r['actual_dir']})
    if not dates:
        print("no pending forward rows"); return
    for ds in dates:
        update_outcomes(datetime.date.fromisoformat(ds))


if __name__ == '__main__':
    import sys
    if '--backfill' in sys.argv:
        backfill_journal()
    elif '--update-pending' in sys.argv:
        update_pending()
    elif '--update' in sys.argv:
        update_outcomes(datetime.date.fromisoformat(sys.argv[sys.argv.index('--update') + 1]))
    else:
        print("usage: python3 htf_outcomes.py --backfill | --update YYYY-MM-DD | --update-pending")
