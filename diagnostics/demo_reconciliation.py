#!/usr/bin/env python3
"""Live-vs-backtest RECONCILIATION logger (Fable's #1 scaffold, 2026-06-11).

The frozen kill-criteria are only interpretable if a demo miss can be attributed to
EDGE DECAY vs EXECUTION. This logs, per signal/trade: did live fire when the Python
engine would (parity)? fill price vs theoretical (slippage)? latency? It also emits the
`date,entry,sl,pnl,leg` CSV that `book_c_kill_criteria.py --score` consumes -- so the
chain live fills -> reconciliation -> kill-criteria scoring is closed.

TWO LANDMINES this forces you to resolve before day 1 (asserted on every row):
  - SYMBOL: the live contract (e.g. MNQM6) vs the backtest symbol (MNQ1! continuous).
    A signal computed on MNQ1! but executed on MNQM6 can differ at roll -- record both.
  - POINT VALUE: backtest uses $0.50/pt; LIVE MNQ is $2.00/pt. R-units are scale-free,
    but any $ reconciliation must use the live multiplier. `pt_value` is required.

This is a SCAFFOLD: it runs a synthetic self-test now; wire the live Tradovate/feed to
`reconcile()` + `append_row()` when the demo starts. No live feed is required to use it.

ASCII-only source (Python 3.10 rejects U+2014 in literals).
"""
import argparse
import csv
import os
import sys

TICK = 0.25
LEGS = {"m9", "m5nq", "m5ym"}
COLUMNS = [
    "date", "time", "instrument", "symbol", "leg",
    "engine_signal", "live_signal", "parity",
    "engine_entry", "live_entry", "entry_slip_ticks",
    "engine_sl", "engine_exit", "live_exit", "exit_slip_ticks",
    "engine_pnl_pts", "live_pnl_pts", "engine_R", "live_R", "R_diff",
    "latency_ms", "pt_value", "notes",
]


def init_log(path):
    if os.path.exists(path):
        print("log exists: %s" % path)
        return
    with open(path, "w", newline="") as f:
        csv.writer(f).writerow(COLUMNS)
    print("created %s" % path)


def _ticks(a, b):
    return round((a - b) / TICK, 2)


def reconcile(engine, live):
    """engine/live dicts -> a reconciliation row.

    engine keys: date,time,instrument,leg,signal(0/1),entry,sl,exit  (theoretical)
    live   keys: symbol,signal(0/1),entry,exit,latency_ms,pt_value   (actuals; may be 0-signal)
    Slippage sign: POSITIVE ticks = adverse (worse for the trade). Direction inferred
    from sl side (sl below entry => long; above => short).
    """
    leg = engine["leg"]
    assert leg in LEGS, "leg must be one of %s" % LEGS
    pt_value = float(live.get("pt_value", 0))
    assert pt_value > 0, "pt_value (live $/pt) is REQUIRED -- resolve the $0.50 vs $2.00 landmine"
    assert live.get("symbol"), "symbol REQUIRED -- resolve MNQ1! vs MNQM6 landmine"

    e_sig, l_sig = int(engine.get("signal", 0)), int(live.get("signal", 0))
    parity = {(1, 1): "match", (1, 0): "miss_engine_only",
              (0, 1): "miss_live_only", (0, 0): "no_signal"}[(e_sig, l_sig)]

    row = {c: "" for c in COLUMNS}
    row.update({"date": engine["date"], "time": engine.get("time", ""),
                "instrument": engine["instrument"], "symbol": live["symbol"], "leg": leg,
                "engine_signal": e_sig, "live_signal": l_sig, "parity": parity,
                "latency_ms": live.get("latency_ms", ""), "pt_value": pt_value,
                "notes": live.get("notes", "")})

    if e_sig and l_sig:
        ee, es, ex = float(engine["entry"]), float(engine["sl"]), float(engine["exit"])
        le, lx = float(live["entry"]), float(live["exit"])
        long = es < ee                                    # stop below entry => long
        dirn = 1 if long else -1
        entry_adv = _ticks(le, ee) * dirn                 # paid higher(long)/lower(short) = adverse +
        exit_adv = _ticks(ex, lx) * dirn                  # exited lower(long)/higher(short) = adverse +
        risk = abs(ee - es)
        eR = ((ex - ee) * dirn) / risk if risk else float("nan")
        lR = ((lx - le) * dirn) / risk if risk else float("nan")
        row.update({"engine_entry": ee, "live_entry": le, "entry_slip_ticks": round(entry_adv, 2),
                    "engine_sl": es, "engine_exit": ex, "live_exit": lx,
                    "exit_slip_ticks": round(exit_adv, 2),
                    "engine_pnl_pts": round((ex - ee) * dirn, 2),
                    "live_pnl_pts": round((lx - le) * dirn, 2),
                    "engine_R": round(eR, 3), "live_R": round(lR, 3),
                    "R_diff": round(lR - eR, 3)})
    return row


def append_row(path, row):
    if not os.path.exists(path):
        init_log(path)
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=COLUMNS).writerow(row)


def to_demo_csv(log_path, out_path):
    """Emit date,entry,sl,pnl,leg (live fills) for book_c_kill_criteria.py --score."""
    import pandas as pd
    df = pd.read_csv(log_path)
    live = df[(df["parity"] == "match") & (df["live_signal"] == 1)].copy()
    out = pd.DataFrame({"date": live["date"], "entry": live["live_entry"],
                        "sl": live["engine_sl"], "pnl": live["live_pnl_pts"],
                        "leg": live["leg"]})
    out.to_csv(out_path, index=False)
    print("wrote %s (%d live matched trades) -> feed to book_c_kill_criteria.py --score"
          % (out_path, len(out)))


def selftest():
    path = "/tmp/demo_recon_selftest.csv"
    if os.path.exists(path):
        os.remove(path)
    init_log(path)
    cases = [
        # clean match, 1-tick adverse on entry, exit near engine target
        (dict(date="2026-07-06", time="09:35", instrument="nq", leg="m5nq", signal=1,
              entry=20000.0, sl=19985.0, exit=20030.0),
         dict(symbol="MNQU6", signal=1, entry=20000.25, exit=20029.5, latency_ms=180, pt_value=2.0)),
        # engine fired, live MISSED (latency/halt) -> parity miss_engine_only
        (dict(date="2026-07-07", time="09:32", instrument="ym", leg="m5ym", signal=1,
              entry=40000.0, sl=39960.0, exit=40080.0),
         dict(symbol="MYMU6", signal=0, entry=0, exit=0, latency_ms="", pt_value=2.0,
              notes="no fill - feed gap")),
        # m9 swing, adverse on both sides
        (dict(date="2026-07-08", time="20:00", instrument="nq", leg="m9", signal=1,
              entry=20100.0, sl=20060.0, exit=20180.0),
         dict(symbol="MNQU6", signal=1, entry=20101.0, exit=20177.0, latency_ms=250, pt_value=2.0)),
    ]
    for eng, live in cases:
        append_row(path, reconcile(eng, live))
    import pandas as pd
    print("\n--- reconciliation log ---")
    show = ["date", "leg", "parity", "entry_slip_ticks", "exit_slip_ticks",
            "engine_R", "live_R", "R_diff", "latency_ms"]
    print(pd.read_csv(path)[show].to_string(index=False))
    to_demo_csv(path, "/tmp/demo_recon_selftest_trades.csv")
    print("\nSELF-TEST OK: parity + slippage(ticks) + R-diff computed; demo CSV emitted "
          "and is ready for `book_c_kill_criteria.py --score`.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", metavar="LOG", help="create an empty reconciliation log")
    ap.add_argument("--to-demo", nargs=2, metavar=("LOG", "OUT"), help="emit --score CSV")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.init:
        init_log(args.init)
    elif args.to_demo:
        to_demo_csv(*args.to_demo)
    else:
        selftest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
