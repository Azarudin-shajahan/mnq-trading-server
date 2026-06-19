"""Daily evening capture loop for the discretion-capture journal.

Shows today's deterministic HTF context, then takes a LOCKED, pre-outcome bias
tag and appends ONE immutable row to data/htf_journal.csv. Outcomes (what price
and v8.18 did) are filled the next day by htf_outcomes.

Run it in your IST evening BEFORE the NY session resolves (< 20:30 IST). The
tagged_ts wall-clock and the refuse-to-relog rule are what keep the row honest.

Usage:
  python3 htf_capture.py                       # interactive, today
  python3 htf_capture.py --date 2026-05-26      # interactive, a given date
  python3 htf_capture.py --bias long --conf 2 \\
      --drivers "discount+bull-smt" --override take      # non-interactive
  add --dry-run to preview the row without writing.
"""
import os, csv, sys, argparse, datetime
import htf_context as H
from htf_outcomes import JOURNAL, ALL_FIELDS

BIAS = ('long', 'short', 'no-trade')
OVERRIDE = ('take', 'skip', 'flip')


def already_logged(date_str):
    if not os.path.exists(JOURNAL):
        return False
    with open(JOURNAL) as f:
        return any(r['date'] == date_str and r.get('split') == 'forward'
                   for r in csv.DictReader(f))


def show_context(ctx):
    print("\n" + "=" * 56)
    print(f"  HTF CONTEXT  {ctx['date']}  (weekly {ctx['weekly_quarter']})")
    print("=" * 56)
    print(f"  daily True Open (NQ) : {ctx['true_open_d']}")
    print(f"  PDH / PDL            : {ctx['pdh']} / {ctx['pdl']}")
    print(f"  premium / discount   : {ctx['prem_disc']}")
    print(f"  overnight gap (NDOG) : {ctx['ndog_pts']}    weekend (NWOG): {ctx['nwog_pts']}")
    print(f"  SMT into NY          : {ctx['smt_into_ny']}")
    print(f"  weekly profile guess : {ctx['weekly_profile_so_far']}")
    print(f"  pre-NY snapshot      : {ctx['snapshot_ist']} IST")
    print("-" * 56)
    print("  (this is machine context only; bring your own chart read)\n")


def _ask(label, allowed):
    while True:
        v = input(f"  {label} {list(allowed)}: ").strip().lower()
        if v in allowed:
            return v
        print(f"    -> must be one of {list(allowed)}")


def collect(args):
    if args.bias:
        bias, conf = args.bias, str(args.conf or 2)
        drivers, override = (args.drivers or ''), (args.override or 'take')
    else:
        bias = _ask("bias", BIAS)
        conf = _ask("confidence", ('1', '2', '3'))
        drivers = input("  drivers (free text, e.g. 'discount+bull-smt+Q3'): ").strip()
        override = _ask("vs v8.18 today", OVERRIDE)
    if bias not in BIAS or override not in OVERRIDE:
        sys.exit(f"invalid bias/override: {bias} / {override}")
    return bias, conf, drivers, override


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    ap.add_argument('--bias', choices=BIAS)
    ap.add_argument('--conf', type=int, choices=(1, 2, 3))
    ap.add_argument('--drivers', default=None)
    ap.add_argument('--override', choices=OVERRIDE)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--data', default=H.DEFAULT_5M)
    args = ap.parse_args()

    date = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    date_str = str(date)

    if already_logged(date_str):
        sys.exit(f"REFUSED: {date_str} already has a locked forward row (immutable).")

    df = H.load_5m(args.data)
    ctx = H.compute_context(df, date)
    if ctx is None:
        # architecture B: today's bars are not settled yet. Log the bias now with
        # blank (pending) machine context; htf_outcomes --update fills it tomorrow.
        ctx = {f: '' for f in H.CONTEXT_FIELDS}
        ctx['date'] = date_str
        ctx['weekly_quarter'] = H.weekly_quarter(date)
        sh, sm = H.ny_open_ist(date)
        ctx['snapshot_ist'] = f'{sh:02d}:{sm:02d}'
        ref_date = max(df['date'])
        print(f"\n  [{date_str}] bars not settled yet - context PENDING (fills "
              f"tomorrow). Reference = last completed day {ref_date}:")
        show_context(H.compute_context(df, ref_date))
    else:
        show_context(ctx)
    bias, conf, drivers, override = collect(args)

    row = dict(ctx)
    row['tagged_ts'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row['human_bias'] = bias
    row['human_conf'] = conf
    row['human_drivers'] = drivers
    row['human_override'] = override
    for f in ('v818_traded', 'v818_dir', 'v818_outcome', 'v818_pts',
              'actual_dir', 'actual_range_pts'):
        row[f] = ''                          # filled next day by htf_outcomes
    row['split'] = 'forward'

    if args.dry_run:
        print("  [DRY-RUN] would append:")
        print("   " + {k: row[k] for k in ('date', 'tagged_ts', 'human_bias',
              'human_conf', 'human_drivers', 'human_override', 'split')}.__repr__())
        return

    new_file = not os.path.exists(JOURNAL)
    with open(JOURNAL, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)
    print(f"  LOCKED {date_str}: bias={bias} conf={conf} -> {JOURNAL}")
    print("  (outcome will be appended next day by htf_outcomes)\n")


if __name__ == '__main__':
    main()
