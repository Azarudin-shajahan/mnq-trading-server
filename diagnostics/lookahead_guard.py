"""Generic LOOKAHEAD detector — the fence we never had.

Iron law: FUTURE DATA MUST NOT CHANGE A PAST DECISION.

A backtest's SIGNAL and BRACKET (entry, sl) are decided at/just-before entry time. If you corrupt
every bar strictly AFTER a cutoff and re-run, every trade whose entry is at/before the cutoff MUST
be byte-identical (same existence, same entry, same sl). If anything changes, the engine peeked at
the future => lookahead. (PnL/outcome legitimately depend on future bars, so we NEVER compare those
— only signal + bracket.)

This single test catches the whole family that has cost this project days + tokens:
  - entry-bar fills (M5 scalp 3.84->1.71; Asia 1H FVG $114k->$0)
  - unconfirmed fractal pivots used early
  - HTF events keyed to bar-open instead of bar-close
  - targets taken from a swing that forms after entry

USAGE (real engine — file-based, the pattern all our engines share):
    from diagnostics.lookahead_guard import guard_file_engine
    import backtest.ssmt_psp_engine as eng
    guard_file_engine(eng, cfg, files, cutoff="2022-06-01")   # raises on leak

The engine's run_backtest(cfg, files) must return a DataFrame with columns
['entry_ts', 'entry', 'sl'] (the causal signal+bracket). Run the engine's normal output through
this BEFORE any "validated"/"production" verdict. It is a mandatory research-critiquer gate.

Run this file directly for its self-test (proves the detector flags a leaky engine and passes a
causal one):  /usr/local/bin/python3 -u diagnostics/lookahead_guard.py
"""
import os
import tempfile
import numpy as np
import pandas as pd


# ---------------------------------------------------------------- core comparison
def _signal_frame(trades):
    """Reduce a trades DataFrame to the causal signal+bracket, keyed by entry_ts."""
    cols = ["entry_ts", "entry", "sl"]
    missing = [c for c in cols if c not in trades.columns]
    if missing:
        raise ValueError(f"trades must expose {cols}; missing {missing}")
    df = trades[cols].copy()
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])
    return df.sort_values("entry_ts").reset_index(drop=True)


def assert_no_lookahead(trades_full, trades_corrupt, cutoff):
    """Compare the <=cutoff slice of two runs (full vs future-corrupted). Raise on any diff."""
    cutoff = pd.to_datetime(cutoff)
    a = _signal_frame(trades_full)
    b = _signal_frame(trades_corrupt)
    a = a[a["entry_ts"] <= cutoff].reset_index(drop=True)
    b = b[b["entry_ts"] <= cutoff].reset_index(drop=True)
    if len(a) != len(b):
        raise AssertionError(
            f"LOOKAHEAD: corrupting bars after {cutoff.date()} changed the NUMBER of past trades "
            f"({len(a)} -> {len(b)}). A past signal depended on future data.")
    for col in ("entry_ts", "entry", "sl"):
        if not (a[col].values == b[col].values).all():
            bad = np.where(a[col].values != b[col].values)[0][:3]
            raise AssertionError(
                f"LOOKAHEAD: '{col}' of a past trade changed when the future was corrupted "
                f"(rows {list(bad)}). The signal/bracket used future data.")
    return len(a)


# ---------------------------------------------------------------- file-based engines
def _corrupt_after(src_path, cutoff, seed=0):
    """Write a copy of an OHLC csv with all rows AFTER cutoff replaced by noise. Returns temp path."""
    df = pd.read_csv(src_path, parse_dates=["timestamp"])
    rng = np.random.default_rng(seed)
    mask = df["timestamp"] > pd.to_datetime(cutoff)
    numcols = [c for c in df.columns if c != "timestamp"]
    # replace future with shuffled + jittered values so any future-peeking changes the result
    for c in numcols:
        vals = df.loc[mask, c].values
        if len(vals):
            df.loc[mask, c] = rng.permutation(vals) * (1 + rng.normal(0, 0.05, len(vals)))
    fd, tmp = tempfile.mkstemp(suffix="_guard.csv", dir=os.path.dirname(src_path))
    os.close(fd)
    df.to_csv(tmp, index=False)
    return tmp


def guard_file_engine(engine, cfg, files, cutoff, data_dir=None):
    """Run engine.run_backtest on full data vs future-corrupted data; assert past trades unchanged.

    `files` is the engine's files dict ({'1m': [names], '15m': [names]}). The engine resolves names
    against its DATA constant; we write corrupted copies into that dir and pass their basenames.
    Raises AssertionError on lookahead; returns the count of verified past trades on success.
    """
    data_dir = data_dir or getattr(engine, "DATA")
    tmp_paths, files_corrupt = [], {}
    try:
        for key, names in files.items():
            new_names = []
            for nm in names:
                tmp = _corrupt_after(os.path.join(data_dir, nm), cutoff)
                tmp_paths.append(tmp)
                new_names.append(os.path.basename(tmp))
            files_corrupt[key] = new_names
        full = engine.run_backtest(cfg, files)
        corrupt = engine.run_backtest(cfg, files_corrupt)
        n = assert_no_lookahead(full, corrupt, cutoff)
        print(f"LOOKAHEAD GUARD PASS: {n} past trades identical after future corruption.")
        return n
    finally:
        for p in tmp_paths:
            try:
                os.remove(p)
            except OSError:
                pass


# ---------------------------------------------------------------- self-test
def _selftest():
    """Prove the detector: a causal toy engine PASSES, a leaky one is CAUGHT."""
    ts = pd.date_range("2022-01-01", periods=20, freq="D")
    price = np.arange(20, dtype=float) + 100

    def causal(data):  # entry = current bar -> causal
        return pd.DataFrame({"entry_ts": data["ts"], "entry": data["p"],
                             "sl": data["p"] - 1})

    def leaky(data):   # entry = NEXT bar -> lookahead
        nxt = np.r_[data["p"][1:], data["p"][-1]]
        return pd.DataFrame({"entry_ts": data["ts"], "entry": nxt, "sl": nxt - 1})

    cutoff = ts[8]
    base = {"ts": ts, "p": price.copy()}
    fut = {"ts": ts, "p": price.copy()}
    fut["p"][9:] = price[9:][::-1] * 1.3   # corrupt EVERY bar after cutoff (ts>cutoff == idx>=9)
    assert_no_lookahead(causal(base), causal(fut), cutoff)            # causal: must pass
    print("self-test: causal engine PASSED guard (correct)")
    try:
        assert_no_lookahead(leaky(base), leaky(fut), cutoff)          # leaky: must be caught
        raise SystemExit("FAIL: guard did NOT catch the leaky engine")
    except AssertionError as e:
        print(f"self-test: leaky engine CAUGHT (correct) -> {str(e)[:70]}...")
    print("ALL GUARD SELF-TESTS PASS")


if __name__ == "__main__":
    _selftest()
