# SSMT → PSP → 1m PD-array Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-timeframe ICT/GxT backtest engine (6H SSMT → 15m PSP → 1m CISD/PD-array entry → first-swing target → CISD-protected stop) with built-in null/tail/holdout rigor gates.

**Architecture:** A single new engine `backtest/ssmt_psp_engine.py` with small, independently-testable pure functions (pivots, 6H resample, SSMT, PSP, CISD/PD-array entry) plus a setup-driven backtest loop that resolves fills on 1m. Two diagnostics scripts (`diagnostics/ssmt_psp_null.py`, `diagnostics/ssmt_psp_tail_holdout.py`) implement the mandatory rigor gates. Tests are plain-`assert` functions on synthetic numpy arrays (project has no pytest), run via `python3`.

**Tech Stack:** Python 3 (`/usr/local/bin/python3`), pandas, numpy. Reuses helper patterns from `backtest/model5_intraday_engine.py` and `backtest/model9_oneshot_engine.py`. Mirrors `diagnostics/org_driver_falsifier.py` for tz handling + the null test.

**Spec:** `docs/superpowers/specs/2026-06-14-ssmt-psp-multitf-engine-design.md`

---

## File Structure

- **Create** `backtest/ssmt_psp_engine.py` — the engine (detectors + backtest loop + CLI).
- **Create** `tests/test_ssmt_psp.py` — plain-`assert` unit tests on synthetic data, with a `__main__` that runs all and prints `ALL PASS` or raises.
- **Create** `diagnostics/ssmt_psp_null.py` — random-direction null (≥500 seeds).
- **Create** `diagnostics/ssmt_psp_tail_holdout.py` — drop-top-3 tail test + 2025 sealed-holdout run.

Test convention: `tests/test_ssmt_psp.py` imports from `backtest.ssmt_psp_engine`. Run the whole
file with `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`. "See it fail" = the run raises
`AttributeError`/`ImportError` for the not-yet-written function. Each task adds its test block to
the same file and re-runs the whole file.

Add once, in Task 1, so imports resolve from repo root:
```python
# top of tests/test_ssmt_psp.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

---

## Lookahead Safety Invariants (enforce in EVERY task + review)

Lookahead has wrecked this project before. These invariants are non-negotiable; the spec/code-quality
reviewers must verify each:

1. **Fractal pivots are confirmed late.** A pivot at bar `j` needs `n` right-bars, so it is only
   known at `j+n`. Never use a pivot as a reference at decision bar `i` unless `j + n < i`
   (`_prior_pivot` enforces this; `find_cisd` starts its CISD scan at `swing_idx + pivot_n`).
2. **HTF events fire at bar CLOSE, not the bar label.** 6H/90m SSMT and 15m PSP return
   `label + timeframe`. Downstream searches start strictly after that close.
3. **The limit goes live only after the setup is fully known.** `walk_setup` starts the fill scan
   at `confirm_idx + 1` (the bar after the CISD close) — never at the PD-array bar, which is in the
   past relative to confirmation.
4. **The target is causal.** TP is the impulse peak observed *before* the fill (running max in
   `walk_setup`), or a prior-day PDH/PDL — never a swing that forms after entry.
5. **Same-bar SL-first.** When a bar straddles SL and TP, count the loss.
6. **Mandatory verification (Task 10):** a 1m re-run is the real gate; additionally assert that
   shifting any HTF event time earlier by one bar would change results (a cheap lookahead tripwire).

---

## Task 1: Scaffold + fractal pivots

**Files:**
- Create: `backtest/ssmt_psp_engine.py`
- Create: `tests/test_ssmt_psp.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_ssmt_psp.py`:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
from backtest.ssmt_psp_engine import swing_highs, swing_lows


def test_pivots():
    # index:    0   1   2   3   4   5   6
    lows  = np.array([5, 4, 3, 4, 5, 6, 7], float)
    highs = np.array([5, 6, 7, 6, 5, 4, 3], float)
    # n=2: a pivot low needs strictly-higher neighbours each side; idx 2 is the low
    assert swing_lows(lows, n=2).tolist() == [False, False, True, False, False, False, False]
    assert swing_highs(highs, n=2).tolist() == [False, False, True, False, False, False, False]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("PASS", name)
    print("ALL PASS")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'swing_highs'`.

- [ ] **Step 3: Write minimal implementation**

Create `backtest/ssmt_psp_engine.py`:
```python
"""SSMT -> PSP -> 1m CISD/PD-array engine (multi-timeframe ICT/GxT model).

Spec: docs/superpowers/specs/2026-06-14-ssmt-psp-multitf-engine-design.md
Backtest point value is $0.50/pt by project convention (never change).
"""
import numpy as np
import pandas as pd

DATA = "/Users/azarudin/mnq_trading/data"
TRIAD = ("nq", "es", "ym")
TICK = 0.25
SL_BUF = 1.0 * TICK  # buffer beyond the protected swing


def swing_highs(high, n=3):
    """Boolean array: True where high[i] is strictly the max of [i-n, i+n]."""
    h = np.asarray(high, float)
    out = np.zeros(len(h), bool)
    for i in range(n, len(h) - n):
        if (h[i] > h[i - n:i]).all() and (h[i] > h[i + 1:i + n + 1]).all():
            out[i] = True
    return out


def swing_lows(low, n=3):
    """Boolean array: True where low[i] is strictly the min of [i-n, i+n]."""
    l = np.asarray(low, float)
    out = np.zeros(len(l), bool)
    for i in range(n, len(l) - n):
        if (l[i] < l[i - n:i]).all() and (l[i] < l[i + 1:i + n + 1]).all():
            out[i] = True
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_pivots` then `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): scaffold engine + fractal pivot detectors"
```

---

## Task 2: True 6H resample (CME-anchored, tz-correct)

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

- [ ] **Step 1: Write the failing test** (append to `tests/test_ssmt_psp.py`, before `__main__`)

```python
def test_resample_6h_anchor():
    from backtest.ssmt_psp_engine import resample_6h
    # 13 hourly ET bars from 18:00 ET; first 6H bucket = 18:00-23:59 (6 bars)
    idx = pd.date_range("2021-03-01 18:00", periods=13, freq="h")  # tz-naive ET
    df = pd.DataFrame({
        "open":  np.arange(13, dtype=float),
        "high":  np.arange(13, dtype=float) + 1,
        "low":   np.arange(13, dtype=float) - 1,
        "close": np.arange(13, dtype=float) + 0.5,
    }, index=idx)
    out = resample_6h(df, anchor_et="18:00")
    # bucket starts must be 18:00, 00:00, 06:00
    assert [t.strftime("%H:%M") for t in out.index[:3]] == ["18:00", "00:00", "06:00"]
    # first bucket aggregates bars 0..5
    assert out.iloc[0]["open"] == 0.0
    assert out.iloc[0]["high"] == 6.0   # max of highs 1..6
    assert out.iloc[0]["low"] == -1.0   # min of lows -1..4
    assert out.iloc[0]["close"] == 5.5  # close of bar 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'resample_6h'`.

- [ ] **Step 3: Write minimal implementation** (append to `backtest/ssmt_psp_engine.py`)

```python
def load_1m_ohlc(inst, files):
    """Load 1m OHLC for one instrument, tz-convert IST->ET, ET-indexed (tz-naive)."""
    cols = ["timestamp", f"{inst}_open", f"{inst}_high", f"{inst}_low", f"{inst}_close"]
    df = pd.concat([pd.read_csv(f"{DATA}/{f}", usecols=cols, parse_dates=["timestamp"])
                    for f in files], ignore_index=True)
    et = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df.index = et.dt.tz_localize(None)
    df = df.rename(columns={f"{inst}_open": "open", f"{inst}_high": "high",
                            f"{inst}_low": "low", f"{inst}_close": "close"})
    return df[["open", "high", "low", "close"]].sort_index()


def resample_6h(df_et, anchor_et="18:00"):
    """Resample an ET-indexed OHLC frame to 6H buckets anchored at anchor_et."""
    h0 = int(anchor_et.split(":")[0])
    out = df_et.resample("6h", origin="start_day", offset=pd.Timedelta(hours=h0 % 6)).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return out
```

Note: `offset=h0 % 6` makes buckets land on 18:00/00:00/06:00/12:00 for anchor 18:00.

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_resample_6h_anchor` ... `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): CME-anchored 6H resample with IST->ET tz convert"
```

---

## Task 3: 6H SSMT detector

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

Definition: at 6H bar `i`, NQ takes out the most recent prior NQ pivot (low for bull / high for
bear) while at least one (`either`) / the chosen / both companions do NOT take their own most
recent prior pivot of the same side. Emit one event per bar `i`, keyed by `df6h.index[i]`.

- [ ] **Step 1: Write the failing test** (append)

```python
def _mk6h(o, h, l, c):
    idx = pd.date_range("2021-03-01 18:00", periods=len(o), freq="6h")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx, dtype=float)

def test_ssmt_bull_either():
    from backtest.ssmt_psp_engine import find_6h_ssmt
    # pivot low for all at idx2 (n=1). At idx4 NQ makes a LOWER low, ES does NOT.
    nq = _mk6h([10,10,10,10,10,10], [11,11,11,11,11,11], [9, 8, 7, 8, 6, 9], [10,10,10,10,10,10])
    es = _mk6h([10,10,10,10,10,10], [11,11,11,11,11,11], [9, 8, 7, 8, 8, 9], [10,10,10,10,10,10])
    ym = es.copy()
    ev = find_6h_ssmt({"nq": nq, "es": es, "ym": ym}, "nq", ["es", "ym"],
                      companion_mode="either", n=1)
    assert ev is not None
    bias, level, ts = ev
    assert bias == "bull"
    assert level == 7.0           # the swept prior pivot low
    assert ts == nq.index[4] + pd.Timedelta("6h")   # event time = bar CLOSE, not label

def test_ssmt_none_when_companion_also_sweeps():
    from backtest.ssmt_psp_engine import find_6h_ssmt
    nq = _mk6h([10]*6, [11]*6, [9, 8, 7, 8, 6, 9], [10]*6)
    es = _mk6h([10]*6, [11]*6, [9, 8, 7, 8, 6, 9], [10]*6)  # ES ALSO sweeps
    ev = find_6h_ssmt({"nq": nq, "es": es, "ym": es.copy()}, "nq", ["es", "ym"],
                      companion_mode="either", n=1)
    assert ev is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'find_6h_ssmt'`.

- [ ] **Step 3: Write minimal implementation** (append)

```python
def _prior_pivot(values, pivot_mask, i, n):
    """Most recent pivot CONFIRMED before bar i. A fractal pivot at j needs n right-bars, so it
    is only known at bar j+n; require j + n < i. (Prevents fractal-confirmation lookahead.)"""
    js = [j for j in np.where(pivot_mask[:i])[0] if j + n < i]
    return float(values[js[-1]]) if js else None


def _companion_holds(holds, companions, companion_mode):
    if companion_mode == "either":
        return any(holds)
    if companion_mode == "both":
        return all(holds)
    return holds[companions.index(companion_mode)]


def find_6h_ssmt(frames, inst, companions, companion_mode="either", n=3, upto_idx=None, tf="6h",
                 from_idx=None):
    """Return (bias, protected_level, close_ts) for the FIRST SSMT, else None.

    bull: inst.low[i] < prior inst pivot-low, companion(s) low[i] do NOT break their prior pivot-low.
    NO LOOKAHEAD: prior pivots must be confirmed before bar i; the event timestamp is the bar
    CLOSE (label + tf), since the bar's high/low aren't known until it closes.
    """
    f = frames[inst]
    dur = pd.tseries.frequencies.to_offset(tf)
    hi, lo = f["high"].values, f["low"].values
    plo, phi = swing_lows(lo, n), swing_highs(hi, n)
    comp = {c: frames[c] for c in companions}
    comp_plo = {c: swing_lows(comp[c]["low"].values, n) for c in companions}
    comp_phi = {c: swing_highs(comp[c]["high"].values, n) for c in companions}
    end = len(f) if upto_idx is None else min(upto_idx + 1, len(f))
    start_i = n + 1 if from_idx is None else max(n + 1, from_idx)
    for i in range(start_i, end):
        ref = _prior_pivot(lo, plo, i, n)                    # bull
        if ref is not None and lo[i] < ref:
            holds = [(_prior_pivot(comp[c]["low"].values, comp_plo[c], i, n) is not None
                      and comp[c]["low"].values[i] > _prior_pivot(comp[c]["low"].values, comp_plo[c], i, n))
                     for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                return ("bull", ref, f.index[i] + dur)
        ref = _prior_pivot(hi, phi, i, n)                    # bear
        if ref is not None and hi[i] > ref:
            holds = [(_prior_pivot(comp[c]["high"].values, comp_phi[c], i, n) is not None
                      and comp[c]["high"].values[i] < _prior_pivot(comp[c]["high"].values, comp_phi[c], i, n))
                     for c in companions]
            if _companion_holds(holds, companions, companion_mode):
                return ("bear", ref, f.index[i] + dur)
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_ssmt_bull_either`, `PASS test_ssmt_none_when_companion_also_sweeps`, `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): 6H SSMT divergence detector (either/both/single companion)"
```

---

## Task 4: 15m PSP detector

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

Definition: first 15m bar with close time > `ssmt_ts` and ≤ `ssmt_ts + window_h` where NQ and the
companion close OPPOSITE colors and the NQ color matches the bias (bull → NQ bearish candle).

- [ ] **Step 1: Write the failing test** (append)

```python
def test_psp():
    from backtest.ssmt_psp_engine import find_15m_psp
    idx = pd.date_range("2021-03-01 09:00", periods=5, freq="15min")
    nq = pd.DataFrame({"open": [10,10,10,10,10], "close": [11,11,9,11,11]}, index=idx).astype(float)
    es = pd.DataFrame({"open": [10,10,10,10,10], "close": [11,11,11,11,11]}, index=idx).astype(float)
    # bar 2: NQ bearish (9<10), ES bullish (11>10) -> bullish PSP
    ts = find_15m_psp(nq, es, bias="bull", after_ts=idx[0], window_h=24)
    assert ts == idx[2] + pd.Timedelta("15min")   # close time, not label
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'find_15m_psp'`.

- [ ] **Step 3: Write minimal implementation** (append)

```python
def find_15m_psp(nq15, comp15, bias, after_ts, window_h=24):
    """First 15m opposite-color close in (after_ts, after_ts+window_h] matching bias.
    Returns the bar CLOSE time (label + 15min) so downstream cannot act mid-bar. None if none."""
    end = after_ts + pd.Timedelta(hours=window_h)
    j = comp15.reindex(nq15.index)  # align companion to NQ bars
    for t in nq15.index:
        if t <= after_ts or t > end:
            continue
        nq_up = nq15.at[t, "close"] > nq15.at[t, "open"]
        cv = j.loc[t]
        if pd.isna(cv["open"]) or pd.isna(cv["close"]):
            continue
        cp_up = cv["close"] > cv["open"]
        if bias == "bull" and (not nq_up) and cp_up:
            return t + pd.Timedelta("15min")
        if bias == "bear" and nq_up and (not cp_up):
            return t + pd.Timedelta("15min")
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_psp`, `ALL PASS`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): 15m PSP opposite-color-close confirmation"
```

---

## Task 4b: Stage-2 secondary SMT (GxT two-stage validation)

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

GxT needs **two** divergence stages (Item 127): Stage-1 = the 15m PSP; Stage-2 = a *secondary*
same-bias SSMT on a configurable TF (default 90m — the layer the content creator described). This
adds a general resampler + a secondary-SMT detector that searches AFTER the PSP.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_resample_tf_90m():
    from backtest.ssmt_psp_engine import resample_tf
    idx = pd.date_range("2021-03-01 18:00", periods=4, freq="h")  # 4 hourly ET bars from 18:00
    df = pd.DataFrame({"open": [1,2,3,4], "high": [1,2,3,4], "low": [1,2,3,4],
                       "close": [1,2,3,4]}, index=idx).astype(float)
    out = resample_tf(df, "90min", anchor_et="18:00")
    # 90m buckets anchored at 18:00 -> 18:00 (bars 0..1) then 19:30 (bars 2..3)
    assert [t.strftime("%H:%M") for t in out.index[:2]] == ["18:00", "19:30"]

def test_secondary_smt_bull():
    from backtest.ssmt_psp_engine import find_secondary_smt
    # build 1m frames where, after after_ts, NQ makes a lower low on the 90m bucket, ES does not
    idx = pd.date_range("2021-03-01 18:00", periods=540, freq="min")  # 9h of 1m
    base = pd.DataFrame({"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.0}, index=idx)
    nq = base.copy(); es = base.copy()
    # 90m bucket #2 (19:30-21:00) low pivot, bucket #4 (22:30-00:00) NQ sweeps it, ES holds
    nq.loc[idx[120:130], "low"] = 7.0   # ~20:00 pivot low for NQ
    nq.loc[idx[300:310], "low"] = 6.0   # later lower low (NQ sweeps)
    es.loc[idx[120:130], "low"] = 7.0
    es.loc[idx[300:310], "low"] = 7.5   # ES does NOT make a lower low
    ts = find_secondary_smt({"nq": nq, "es": es, "ym": es.copy()}, "nq", ["es", "ym"],
                            bias="bull", after_ts=idx[60], window_h=12,
                            tf="90min", anchor_et="18:00", n=1)
    assert ts is not None
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'resample_tf'`.

- [ ] **Step 3: Implement** (append). Also refactor `resample_6h` to delegate (keeps Task 2 test green):

```python
def resample_tf(df_et, rule, anchor_et="18:00"):
    """Resample an ET-indexed OHLC frame to `rule` (e.g. '6h','90min') anchored at anchor_et."""
    hh, mm = (int(x) for x in anchor_et.split(":"))
    rule_min = int(pd.tseries.frequencies.to_offset(rule).nanos // 60_000_000_000)
    off = pd.Timedelta(minutes=(hh * 60 + mm) % rule_min)
    return df_et.resample(rule, origin="start_day", offset=off).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def find_secondary_smt(m1, inst, companions, bias, after_ts, window_h, tf="90min",
                       anchor_et="18:00", n=3):
    """Stage-2: first same-bias SSMT on `tf`. Acts at the bar CLOSE (label + tf) and uses only
    confirmed prior pivots -> no lookahead. Returns the close ts or None."""
    end = after_ts + pd.Timedelta(hours=window_h)
    dur = pd.tseries.frequencies.to_offset(tf)
    frames = {a: resample_tf(m1[a], tf, anchor_et) for a in (inst, *companions)}
    f = frames[inst]
    hi, lo = f["high"].values, f["low"].values
    plo, phi = swing_lows(lo, n), swing_highs(hi, n)
    cplo = {c: swing_lows(frames[c]["low"].values, n) for c in companions}
    cphi = {c: swing_highs(frames[c]["high"].values, n) for c in companions}
    for i in range(n + 1, len(f)):
        tclose = f.index[i] + dur
        if tclose <= after_ts or tclose > end:
            continue
        if bias == "bull":
            ref = _prior_pivot(lo, plo, i, n)
            if ref is None or lo[i] >= ref:
                continue
            holds = [(_prior_pivot(frames[c]["low"].values, cplo[c], i, n) is not None
                      and frames[c]["low"].values[i] > _prior_pivot(frames[c]["low"].values, cplo[c], i, n))
                     for c in companions]
            if any(holds):
                return tclose
        else:
            ref = _prior_pivot(hi, phi, i, n)
            if ref is None or hi[i] <= ref:
                continue
            holds = [(_prior_pivot(frames[c]["high"].values, cphi[c], i, n) is not None
                      and frames[c]["high"].values[i] < _prior_pivot(frames[c]["high"].values, cphi[c], i, n))
                     for c in companions]
            if any(holds):
                return tclose
    return None
```

Then replace the body of `resample_6h` (from Task 2) with a delegating one-liner:
```python
def resample_6h(df_et, anchor_et="18:00"):
    """Resample an ET-indexed OHLC frame to 6H buckets anchored at anchor_et."""
    return resample_tf(df_et, "6h", anchor_et)
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_resample_tf_90m`, `PASS test_secondary_smt_bull`, and `test_resample_6h_anchor` still PASS.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): Stage-2 secondary SMT detector (configurable TF, GxT two-stage)"
```

---

## Task 5: 1m CISD + PD-array entry assembly

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

This task builds the LTF trigger as small pieces, each tested:
`find_cisd` → `pd_arrays_bull`/`_pd_arrays_bear` → `assemble_entry`.

### 5a — CISD

Definition (bull): find the most recent 1m pivot low at/after `start`; the down-leg ending at that
low = the run of down-candles immediately preceding it; `cisd_level = open of the FIRST down-candle
of that leg`. CISD confirms at the first later bar that **closes above** `cisd_level`.
Returns `(confirm_idx, swing_idx, swing_val, cisd_level)`.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_cisd_bull():
    from backtest.ssmt_psp_engine import find_cisd
    o = np.array([11, 10,  9,  8,  9,   11], float)  # first down candle of the leg = idx1 (open 10)
    h = np.array([11, 10,  9,  8,  9.5, 11], float)
    l = np.array([10,  9,  8,  7,  8,   10], float)  # pivot low at idx3 (n=1)
    c = np.array([10,  9,  8,  9,  10.5,11], float)  # idx4 closes 10.5 (>10) -> CISD confirm
    r = find_cisd(o, h, l, c, bias="bull", start=0, pivot_n=1)
    assert r is not None
    confirm_idx, swing_idx, swing_val, level = r
    assert swing_idx == 3 and swing_val == 7.0      # pivot low at idx3
    assert level == 10.0                            # open of first down candle (idx1)
    assert confirm_idx == 4                          # first close above 10
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'find_cisd'`.

- [ ] **Step 3: Implement** (append)

```python
def find_cisd(o, h, l, c, bias, start, pivot_n=3):
    """Locate the CISD that flips order flow in `bias` direction at/after `start`.
    Returns (confirm_idx, swing_idx, swing_val, cisd_level) or None.
    """
    o, h, l, c = map(np.asarray, (o, h, l, c))
    piv = swing_lows(l, pivot_n) if bias == "bull" else swing_highs(h, pivot_n)
    for swing_idx in [j for j in np.where(piv)[0] if j >= start]:
        # walk back over the leg that made the swing (down-candles for bull / up for bear)
        j = swing_idx
        while j - 1 >= 0 and ((bias == "bull" and c[j - 1] < o[j - 1])
                              or (bias == "bear" and c[j - 1] > o[j - 1])):
            j -= 1
        level = float(o[j])                       # open of first candle of the leg
        # CISD confirm: first close beyond level, but not before the swing pivot itself is
        # confirmed (a fractal low needs pivot_n right-bars) -> start at swing_idx + pivot_n.
        for k in range(swing_idx + pivot_n, len(c)):
            if (bias == "bull" and c[k] > level) or (bias == "bear" and c[k] < level):
                swing_val = float(l[swing_idx]) if bias == "bull" else float(h[swing_idx])
                return (k, int(swing_idx), swing_val, level)
    return None
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_cisd_bull`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): 1m CISD order-flow-shift detector"
```

### 5b — PD-array detectors

- [ ] **Step 1: Write the failing test** (append)

```python
def test_pd_arrays():
    from backtest.ssmt_psp_engine import pd_arrays_bull
    # bullish FVG: high[0]=9, low[2]=10 -> gap distal 9, proximal 10
    o = np.array([8,  9,  10.2], float)
    h = np.array([9,  10.5,11 ], float)
    l = np.array([7,  9.5, 10 ], float)
    c = np.array([8.8,10.3,10.9], float)
    arrs = pd_arrays_bull(o, h, l, c, lo_idx=0, hi_idx=2, kinds=("fvg",))
    assert any(a["kind"] == "fvg" and a["proximal"] == 10.0 and a["distal"] == 9.0 for a in arrs)
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'pd_arrays_bull'`.

- [ ] **Step 3: Implement** (append)

```python
def pd_arrays_bull(o, h, l, c, lo_idx, hi_idx, kinds=("fvg", "ifvg", "ob", "breaker")):
    """Bullish PD arrays in window [lo_idx, hi_idx]. Each: {kind, proximal, distal, idx}.
    proximal = price hit FIRST on a downward retrace (higher edge); distal = lower edge.
    """
    o, h, l, c = map(np.asarray, (o, h, l, c))
    out = []
    a, b = lo_idx, hi_idx
    if "fvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if l[i + 1] > h[i - 1]:                       # 3-candle bullish imbalance
                out.append({"kind": "fvg", "proximal": float(l[i + 1]),
                            "distal": float(h[i - 1]), "idx": i})
    if "ifvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if h[i + 1] < l[i - 1]:                       # a bearish FVG ...
                gap_hi, gap_lo = float(l[i - 1]), float(h[i + 1])
                for k in range(i + 2, min(b + 1, len(c))):
                    if c[k] > gap_hi:                     # ... violated to the upside -> inverts
                        out.append({"kind": "ifvg", "proximal": gap_hi,
                                    "distal": gap_lo, "idx": k}); break
    if "ob" in kinds:
        for i in range(b, a, -1):                          # last down-close candle before the up-leg
            if c[i] < o[i]:
                out.append({"kind": "ob", "proximal": float(o[i]),
                            "distal": float(l[i]), "idx": i}); break
    if "breaker" in kinds:
        if lo_idx < len(c) and c[lo_idx] < o[lo_idx]:
            out.append({"kind": "breaker", "proximal": float(o[lo_idx]),
                        "distal": float(l[lo_idx]), "idx": lo_idx})
    return out


def _pd_arrays_bear(o, h, l, c, hi_idx, lo_idx, kinds):
    """Bearish mirror of pd_arrays_bull. proximal = lower edge (hit first on an up retrace)."""
    o, h, l, c = map(np.asarray, (o, h, l, c))
    out = []
    a, b = hi_idx, lo_idx
    if "fvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if h[i + 1] < l[i - 1]:
                out.append({"kind": "fvg", "proximal": float(h[i + 1]),
                            "distal": float(l[i - 1]), "idx": i})
    if "ifvg" in kinds:
        for i in range(max(a, 1), min(b, len(c) - 1)):
            if l[i + 1] > h[i - 1]:
                gap_lo, gap_hi = float(h[i - 1]), float(l[i + 1])
                for k in range(i + 2, min(b + 1, len(c))):
                    if c[k] < gap_lo:
                        out.append({"kind": "ifvg", "proximal": gap_lo,
                                    "distal": gap_hi, "idx": k}); break
    if "ob" in kinds:
        for i in range(b, a, -1):
            if c[i] > o[i]:
                out.append({"kind": "ob", "proximal": float(o[i]),
                            "distal": float(h[i]), "idx": i}); break
    if "breaker" in kinds:
        if hi_idx < len(c) and c[hi_idx] > o[hi_idx]:
            out.append({"kind": "breaker", "proximal": float(o[hi_idx]),
                        "distal": float(h[hi_idx]), "idx": hi_idx})
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_pd_arrays`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): bullish/bearish PD-array detectors (fvg/ifvg/ob/breaker)"
```

### 5c — assemble entry (entry/sl/tp/target)

- [ ] **Step 1: Write the failing test** (append)

```python
def test_assemble_entry_bull():
    from backtest.ssmt_psp_engine import assemble_entry, SL_BUF
    o = np.array([11,10, 9, 8, 9,   10.2,11.5,12  ], float)
    h = np.array([11,10, 9, 8, 10.5,11,  12,  12.5], float)
    l = np.array([10, 9, 8, 7, 8,   9.6, 11,  11.5], float)
    c = np.array([10, 9, 8, 9, 10.3,10.9,11.8,12.2], float)
    e = assemble_entry(o, h, l, c, bias="bull", start=0, ssmt_low=7.0, ssmt_high=None,
                       arrays=("fvg","ifvg","ob","breaker"), sl_mode="local", pivot_n=1)
    assert e is not None
    assert e["sl"] < e["entry"]                 # bull geometry (TP resolved later in walk_setup)
    assert e["sl"] == 7.0 - SL_BUF             # protected swing low (local) minus buffer
    assert "confirm_idx" in e and "array_idx" in e   # carries the post-CISD fill-start anchor
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'assemble_entry'`.

- [ ] **Step 3: Implement** (append)

```python
def assemble_entry(o, h, l, c, bias, start, ssmt_low, ssmt_high, arrays, sl_mode, pivot_n=3):
    """LTF assembly: CISD -> first PD array -> entry + sl + confirm_idx. The TP is NOT chosen here
    from a future swing (that would be lookahead); it is resolved CAUSALLY in walk_setup as the
    impulse peak observed up to the fill. Returns None if incomplete."""
    cis = find_cisd(o, h, l, c, bias, start, pivot_n)
    if cis is None:
        return None
    confirm_idx, swing_idx, swing_val, _ = cis
    if bias == "bull":
        arrs = pd_arrays_bull(o, h, l, c, swing_idx, confirm_idx, arrays)
        if not arrs:
            return None
        protected = swing_val if sl_mode == "local" else ssmt_low
        sl = protected - SL_BUF
        arr = min(arrs, key=lambda x: x["idx"])
        entry = arr["proximal"]
        if not (sl < entry):
            return None
    else:
        arrs = _pd_arrays_bear(o, h, l, c, swing_idx, confirm_idx, arrays)
        if not arrs:
            return None
        protected = swing_val if sl_mode == "local" else ssmt_high
        sl = protected + SL_BUF
        arr = min(arrs, key=lambda x: x["idx"])
        entry = arr["proximal"]
        if not (entry < sl):
            return None
    return {"entry": entry, "sl": sl, "confirm_idx": int(confirm_idx),
            "array_idx": int(arr["idx"]), "kind": arr["kind"], "bias": bias}
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_assemble_entry_bull`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): assemble LTF entry (CISD->PD array->entry/sl/tp/target)"
```

---

## Task 5d: Nested-FVG key-level gate (GxT Item 133)

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

GxT's "key level" is an FVG **or** a swing (Item 127), and its top setup nests the entry **inside
an HTF FVG** (Item 133). This adds a key-level gate the entry must pass.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_htf_fvgs():
    from backtest.ssmt_psp_engine import htf_fvgs
    idx = pd.date_range("2021-03-01 00:00", periods=4, freq="h")
    df = pd.DataFrame({"open":[8,9,10.2,10.5], "high":[9,10.5,11,11],
                       "low":[7,9.5,10,10.3], "close":[8.8,10.3,10.9,10.8]}, index=idx).astype(float)
    # bullish FVG: high[0]=9, low[2]=10 -> zone (9,10), forms at bar2
    zones = htf_fvgs(df, "bull", upto_ts=idx[3])
    assert (9.0, 10.0) in [(round(lo,1), round(hi,1)) for lo, hi in zones]
    assert htf_fvgs(df, "bull", upto_ts=idx[1]) == []   # FVG not formed yet at idx1

def test_passes_key_level():
    from backtest.ssmt_psp_engine import passes_key_level
    zones = [(9.0, 10.0)]
    assert passes_key_level(9.5, "bull", zones, 7.0, "htf-fvg", 20)
    assert not passes_key_level(12.0, "bull", zones, 7.0, "htf-fvg", 1)
    assert passes_key_level(8.0, "bull", zones, 7.0, "swing", 2)        # within 7+/-2
    assert not passes_key_level(8.0, "bull", zones, 7.0, "swing", 0.5)
    assert passes_key_level(9.5, "bull", zones, 7.0, "either", 0.5)     # in fvg
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'htf_fvgs'`.

- [ ] **Step 3: Implement** (append)

```python
def htf_fvgs(df_tf, bias, upto_ts):
    """Bias-direction FVG zones on df_tf whose 3rd bar has fully CLOSED by upto_ts (no lookahead).
    Returns [(lo, hi), ...]."""
    h, l, idx = df_tf["high"].values, df_tf["low"].values, df_tf.index
    dur = pd.Series(idx).diff().min() if len(idx) > 1 else pd.Timedelta(0)
    zones = []
    for i in range(1, len(df_tf) - 1):
        if idx[i + 1] + dur > upto_ts:   # 3rd bar must be closed (label + tf) before the cutoff
            break
        if bias == "bull" and l[i + 1] > h[i - 1]:
            zones.append((float(h[i - 1]), float(l[i + 1])))
        if bias == "bear" and h[i + 1] < l[i - 1]:
            zones.append((float(h[i + 1]), float(l[i - 1])))
    return zones


def passes_key_level(entry, bias, fvg_zones, swing_level, mode, tol):
    """GxT key-level gate: nested inside an HTF FVG, near the swept swing, or either."""
    in_fvg = any(lo <= entry <= hi for lo, hi in fvg_zones)
    near_swing = abs(entry - swing_level) <= tol
    if mode == "htf-fvg":
        return in_fvg
    if mode == "swing":
        return near_swing
    return in_fvg or near_swing
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_htf_fvgs`, `PASS test_passes_key_level`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): nested-FVG key-level gate (GxT Item 133)"
```

---

## Task 5e: Fidelity gates (displacement, HTF bias, macro, PDH/PDL target)

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

A corpus re-audit found four book-required conditions. Each is a small helper + an ablatable gate.

- [ ] **Step 1: Write the failing tests** (append)

```python
def test_is_displacement():
    from backtest.ssmt_psp_engine import is_displacement
    o, h, l, c = (np.array([10.0]), np.array([11.0]), np.array([9.0]), np.array([10.9]))
    assert is_displacement(o, h, l, c, 0, 0.4)      # body 0.9 / range 2.0 = 0.45
    assert not is_displacement(o, h, l, c, 0, 0.6)

def test_htf_bias():
    from backtest.ssmt_psp_engine import htf_bias
    idx = pd.date_range("2021-03-01", periods=12, freq="D")
    h = np.array([5,6,5,7,6,8,7,9,8,10,9,11], float)   # rising pivot highs
    l = np.array([1,2,1,3,2,4,3,5,4,6,5,7], float)     # rising pivot lows
    df = pd.DataFrame({"open": h, "high": h, "low": l, "close": h}, index=idx)
    assert htf_bias(df, idx[-1], n=1) == "bull"

def test_in_macro():
    from backtest.ssmt_psp_engine import in_macro
    assert in_macro(pd.Timestamp("2021-03-01 09:55"))
    assert not in_macro(pd.Timestamp("2021-03-01 12:00"))

def test_prior_day_levels():
    from backtest.ssmt_psp_engine import prior_day_levels
    idx = pd.to_datetime(["2021-03-01 10:00","2021-03-01 14:00",
                          "2021-03-02 10:00","2021-03-02 14:00"])
    df = pd.DataFrame({"open":0, "high":[10,12,20,22], "low":[5,4,15,14], "close":0},
                      index=idx).astype(float)
    assert prior_day_levels(df)[pd.Timestamp("2021-03-02")] == (12.0, 4.0)
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'is_displacement'`.

- [ ] **Step 3: Implement** (append)

```python
MACRO_WINDOWS = [("09:50", "10:10"), ("10:50", "11:10"), ("13:10", "13:40"), ("15:15", "15:45")]


def is_displacement(o, h, l, c, idx, frac=0.5):
    """True if candle idx is a strong-bodied displacement (|c-o| >= frac*range)."""
    rng = h[idx] - l[idx]
    return rng > 0 and abs(c[idx] - o[idx]) >= frac * rng


def htf_bias(df_tf, upto_ts, n=3):
    """HTF structural bias at/before upto_ts: HH+HL=bull, LH+LL=bear, else none."""
    sub = df_tf[df_tf.index <= upto_ts]
    h, l = sub["high"].values, sub["low"].values
    ph, pl = np.where(swing_highs(h, n))[0], np.where(swing_lows(l, n))[0]
    if len(ph) < 2 or len(pl) < 2:
        return "none"
    hh, hl = h[ph[-1]] > h[ph[-2]], l[pl[-1]] > l[pl[-2]]
    if hh and hl:
        return "bull"
    if (not hh) and (not hl):
        return "bear"
    return "none"


def in_macro(ts_et, windows=MACRO_WINDOWS):
    """True if the ET timestamp falls inside an algorithmic macro window."""
    hm = ts_et.strftime("%H:%M")
    return any(a <= hm <= b for a, b in windows)


def prior_day_levels(df_et):
    """Per-date prior-day high/low (PDH/PDL). Returns {date: (pdh, pdl)}."""
    g = df_et.groupby(df_et.index.normalize())
    pdh, pdl = g["high"].max().shift(1), g["low"].min().shift(1)
    return {d: (float(pdh[d]), float(pdl[d])) for d in pdh.index if not pd.isna(pdh[d])}
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_is_displacement`, `PASS test_htf_bias`, `PASS test_in_macro`, `PASS test_prior_day_levels`.

- [ ] **Step 5: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): fidelity helpers (displacement, HTF bias, macro, PDH/PDL)"
```

---

## Task 6: 1m fill + walk + setup-driven backtest loop

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`
- Modify: `tests/test_ssmt_psp.py`

Fill model (no lookahead): the limit goes live only AFTER the setup is fully known — i.e. from
`confirm_idx + 1` (the bar after the CISD close). Scan 1m bars; the impulse peak (running
max-high for a bull) is tracked until price first retraces to `entry`. At that fill bar the TP is
locked to the peak seen *before* the fill (or a fixed PDH/PDL when supplied), then resolve
**SL-first**. Nothing uses a bar that hasn't closed or a swing that forms after the fill. Mirror of
M5 `walk_limit_1m`.

- [ ] **Step 1: Write the failing test** (append)

```python
def test_walk_setup_fixed_tp():
    from backtest.ssmt_psp_engine import walk_setup
    # confirm at 0; retrace fills entry 10 at idx2; rallies to tp 12 at idx3
    h = np.array([10.5,10.4,10.2,12.1], float)
    l = np.array([10.2,10.1, 9.9,11.5], float)
    out, pnl, fi = walk_setup(h, l, 0, entry=10.0, sl=7.0, bias="bull", tp_fixed=12.0)
    assert out == "win" and abs(pnl - 2.0) < 1e-9 and fi == 2

def test_walk_setup_sl_first():
    from backtest.ssmt_psp_engine import walk_setup
    # fill bar straddles sl and tp -> SL must win (conservative)
    h = np.array([10.5, 12.5], float)
    l = np.array([10.2,  6.5], float)
    out, pnl, fi = walk_setup(h, l, 0, 10.0, 7.0, "bull", tp_fixed=12.0)
    assert out == "loss" and abs(pnl - (-3.0)) < 1e-9

def test_walk_setup_causal_tp():
    from backtest.ssmt_psp_engine import walk_setup
    # impulse peak 11.5 forms at idx1 (before fill); retrace fills 10 at idx2; then hits 11.5
    h = np.array([10.3,11.5,10.2,11.6], float)
    l = np.array([10.0,11.0, 9.8,11.0], float)
    out, pnl, fi = walk_setup(h, l, 0, 10.0, 7.0, "bull")   # tp = prior peak 11.5
    assert out == "win" and abs(pnl - 1.5) < 1e-9 and fi == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: FAIL — `ImportError: cannot import name 'walk_setup'`.

- [ ] **Step 3: Implement** (append)

```python
def walk_setup(h, l, confirm_idx, entry, sl, bias, tp_fixed=None):
    """Causal 1m resolution. Starts the fill scan at confirm_idx+1 (setup fully known). Tracks the
    impulse peak (running max-high for a bull) BEFORE the fill; at the fill bar TP = that peak (or
    tp_fixed when given). SL-first. Returns (outcome, pnl_points, fill_idx). No lookahead."""
    h, l = np.asarray(h, float), np.asarray(l, float)
    run = h[confirm_idx] if bias == "bull" else l[confirm_idx]   # peak/trough BEFORE the fill
    filled, fill_i, tp = False, -1, None
    for i in range(confirm_idx + 1, len(h)):
        if not filled:
            hit = (l[i] <= entry) if bias == "bull" else (h[i] >= entry)
            if hit:
                filled, fill_i = True, i
                tp = tp_fixed if tp_fixed is not None else run
                if (bias == "bull" and not tp > entry) or (bias == "bear" and not tp < entry):
                    return ("notarget", 0.0, -1)
            else:
                run = max(run, h[i]) if bias == "bull" else min(run, l[i])
                continue
        if bias == "bull":
            if l[i] <= sl:
                return ("loss", sl - entry, fill_i)
            if h[i] >= tp:
                return ("win", tp - entry, fill_i)
        else:
            if h[i] >= sl:
                return ("loss", entry - sl, fill_i)
            if l[i] <= tp:
                return ("win", entry - tp, fill_i)
    return ("be", 0.0, fill_i) if filled else ("nofill", 0.0, -1)
```

- [ ] **Step 4: Run to verify it passes**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `PASS test_walk_setup_fixed_tp`, `PASS test_walk_setup_sl_first`, `PASS test_walk_setup_causal_tp`.

- [ ] **Step 5: Implement the backtest loop** (append; covered by Task 7 smoke run)

```python
FILES_2020_2024 = {"1m": ["MULTI_1min_IST_2020_2024.csv"],
                   "15m": ["MULTI_15min_IST_2020_2024.csv"]}
FILES_2025 = {"1m": ["MULTI_1min_IST_2025.csv"],
              "15m": ["MULTI_15min_IST_2025.csv"]}


def _load_15m(inst, files):
    cols = ["timestamp", f"{inst}_open", f"{inst}_close"]
    df = pd.concat([pd.read_csv(f"{DATA}/{f}", usecols=cols, parse_dates=["timestamp"])
                    for f in files], ignore_index=True)
    et = df["timestamp"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("America/New_York")
    df.index = et.dt.tz_localize(None)
    return df.rename(columns={f"{inst}_open": "open", f"{inst}_close": "close"})[["open", "close"]].sort_index()


def run_backtest(cfg, files):
    """Walk 6H SSMT events; one trade per SSMT. Returns trades DataFrame."""
    if cfg.get("target") == "failure-swing":
        raise NotImplementedError("failure-swing target: implement order-pairing in a follow-up task")
    m1 = {a: load_1m_ohlc(a, files["1m"]) for a in TRIAD}
    m15 = {a: _load_15m(a, files["15m"]) for a in TRIAD}
    f6 = {a: resample_6h(m1[a], cfg["anchor_et"]) for a in TRIAD}
    kf = {a: resample_tf(m1[a], cfg["key_level_tf"], cfg["anchor_et"]) for a in TRIAD}
    hbf = ({a: resample_tf(m1[a], cfg["htf_bias"], cfg["anchor_et"]) for a in TRIAD}
           if cfg["htf_bias"] != "off" else None)
    pdmap = {a: prior_day_levels(m1[a]) for a in TRIAD} if cfg["target"] == "pdh-pdl" else None
    comp_map = {"either": ["es", "ym"], "es": ["es"], "ym": ["ym"], "both": ["es", "ym"]}
    companions = comp_map[cfg["companion"]]
    n = cfg["pivot_n"]
    trades, f = [], f6["nq"]
    for i in range(n + 1, len(f)):
        ev = find_6h_ssmt(f6, "nq", companions, companion_mode=cfg["companion"], n=n,
                          from_idx=i, upto_idx=i, tf="6h")   # is THIS 6H bar an SSMT?
        if ev is None:
            continue
        bias, level, ssmt_ts = ev   # ssmt_ts = bar CLOSE
        comp = companions[0]
        psp_ts = find_15m_psp(m15["nq"], m15[comp], bias, ssmt_ts, cfg["psp_window_h"])
        if psp_ts is None:
            continue
        entry_start_ts = psp_ts
        if cfg["stage2"] == "secondary-smt":
            stage2_ts = find_secondary_smt(m1, "nq", companions, bias, psp_ts,
                                           cfg["psp_window_h"], cfg["stage2_tf"],
                                           cfg["anchor_et"], n)
            if stage2_ts is None:
                continue
            entry_start_ts = stage2_ts
        exec_inst = comp if cfg["exec"] == "failure-swing" else "nq"
        win = m1[exec_inst].loc[entry_start_ts: entry_start_ts + pd.Timedelta(hours=cfg["psp_window_h"])]
        if len(win) < 5 * n:
            continue
        o, hh, ll, cc = (win["open"].values, win["high"].values,
                         win["low"].values, win["close"].values)
        e = assemble_entry(o, hh, ll, cc, bias, 0, ssmt_low=level, ssmt_high=level,
                           arrays=tuple(cfg["arrays"]), sl_mode=cfg["sl"], pivot_n=n)
        if e is None:
            continue
        # all gates below use only info known by the CISD close -> no lookahead
        confirm_ts = win.index[e["confirm_idx"]]
        zones = htf_fvgs(kf[exec_inst], bias, confirm_ts)    # HTF FVGs formed before the CISD close
        if not passes_key_level(e["entry"], bias, zones, level, cfg["key_level"], cfg["key_level_tol"]):
            continue
        # displacement gate (array candle is in the past, fully known)
        if cfg["displacement"] == "on":
            di = e["array_idx"]
            if not (is_displacement(o, hh, ll, cc, di, cfg["disp_frac"]) or
                    (di + 1 < len(cc) and is_displacement(o, hh, ll, cc, di + 1, cfg["disp_frac"]))):
                continue
        # HTF bias alignment (TTrades Item 53): block if HTF bias opposes the SSMT
        if hbf is not None and htf_bias(hbf[exec_inst], ssmt_ts, n) == ("bear" if bias == "bull" else "bull"):
            continue
        # target: PDH/PDL (prior day, known) as a fixed TP, else causal impulse-peak in walk_setup
        tp_fixed = None
        if cfg["target"] == "pdh-pdl":
            lev = pdmap[exec_inst].get(confirm_ts.normalize())
            if lev is None:
                continue
            tp_fixed = lev[0] if bias == "bull" else lev[1]
        out, pnl, fill_idx = walk_setup(hh, ll, e["confirm_idx"], e["entry"], e["sl"], bias, tp_fixed)
        if out in ("nofill", "notarget"):
            continue
        entry_ts = win.index[fill_idx]
        # macro-time gate on the ACTUAL fill time (ICT macros)
        if cfg["macro"] == "precise" and not in_macro(entry_ts):
            continue
        risk = abs(e["entry"] - e["sl"])
        trades.append({"ssmt_ts": ssmt_ts, "psp_ts": psp_ts, "entry_ts": entry_ts,
                       "inst": exec_inst, "dir": bias, "kind": e["kind"],
                       "entry": round(e["entry"], 2), "sl": round(e["sl"], 2),
                       "out": out, "pnl": round(pnl, 2),
                       "R": round(pnl / risk, 2) if risk else 0.0, "year": ssmt_ts.year})
    return pd.DataFrame(trades)
```

- [ ] **Step 6: Commit**

```bash
git add backtest/ssmt_psp_engine.py tests/test_ssmt_psp.py
git commit -m "feat(ssmt): 1m SL-first fill/walk + setup-driven backtest loop"
```

---

## Task 7: CLI, stats, per-year, ablation + first smoke run

**Files:**
- Modify: `backtest/ssmt_psp_engine.py`

- [ ] **Step 1: Implement stats + CLI** (append)

```python
import argparse


def stats(tr):
    if not len(tr):
        return {"n": 0, "pf": 0.0, "wr": 0.0, "net": 0.0, "maxdd": 0.0}
    wins = tr.loc[tr.pnl > 0, "pnl"].sum()
    loss = -tr.loc[tr.pnl < 0, "pnl"].sum()
    eq = tr.pnl.cumsum()
    dd = (eq - eq.cummax()).min()
    return {"n": int(len(tr)), "pf": round(wins / loss, 2) if loss else float("inf"),
            "wr": round((tr.pnl > 0).mean() * 100, 1), "net": round(tr.pnl.sum(), 2),
            "maxdd": round(float(dd), 2)}


def peryear(tr):
    if not len(tr):
        return {}
    return {int(y): round(g.pnl.sum(), 2) for y, g in tr.groupby("year")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exec", choices=["nq", "failure-swing"], default="nq")
    ap.add_argument("--companion", choices=["es", "ym", "either", "both"], default="either")
    ap.add_argument("--stage2", choices=["secondary-smt", "off"], default="secondary-smt")
    ap.add_argument("--stage2-tf", default="90min")
    ap.add_argument("--key-level", choices=["swing", "htf-fvg", "either"], default="either")
    ap.add_argument("--key-level-tf", default="1h")
    ap.add_argument("--key-level-tol", type=float, default=20.0)
    ap.add_argument("--displacement", choices=["on", "off"], default="on")
    ap.add_argument("--disp-frac", type=float, default=0.5)
    ap.add_argument("--htf-bias", choices=["off", "1d", "4h"], default="1d")
    ap.add_argument("--macro", choices=["session", "precise"], default="session")
    ap.add_argument("--arrays", default="fvg,ifvg,ob,breaker")
    ap.add_argument("--target", choices=["nearest-swing", "pdh-pdl", "failure-swing"], default="nearest-swing")
    ap.add_argument("--sl", choices=["local", "ssmt"], default="local")
    ap.add_argument("--anchor-et", default="18:00")
    ap.add_argument("--psp-window-h", type=int, default=24)
    ap.add_argument("--pivot-n", type=int, default=3)
    ap.add_argument("--holdout", action="store_true", help="run on sealed 2025 data")
    a = ap.parse_args()
    cfg = {"exec": a.exec, "companion": a.companion, "arrays": a.arrays.split(","),
           "stage2": a.stage2, "stage2_tf": a.stage2_tf,
           "key_level": a.key_level, "key_level_tf": a.key_level_tf, "key_level_tol": a.key_level_tol,
           "displacement": a.displacement, "disp_frac": a.disp_frac,
           "htf_bias": a.htf_bias, "macro": a.macro,
           "target": a.target, "sl": a.sl, "anchor_et": a.anchor_et,
           "psp_window_h": a.psp_window_h, "pivot_n": a.pivot_n}
    files = FILES_2025 if a.holdout else FILES_2020_2024
    tr = run_backtest(cfg, files)
    print("CONFIG:", cfg, "| holdout:", a.holdout)
    print("STATS :", stats(tr))
    print("PERYR :", peryear(tr))
    if len(tr):
        print(tr.to_string(index=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the unit tests (regression)**

Run: `/usr/local/bin/python3 -u tests/test_ssmt_psp.py`
Expected: `ALL PASS`.

- [ ] **Step 3: Smoke run on real 2020-2024 data**

Run: `/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --companion either`
Expected: prints CONFIG / STATS / PERYR with no exception. The default is now the **two-stage**
cascade (stricter), so if `n == 0` first try `--stage2 off` to confirm the 1-stage cascade
produces trades, then `--psp-window-h 48 --pivot-n 2`. A zero-trade model is itself a recorded
result (the cascade is too strict), not a bug to paper over.

- [ ] **Step 4: Commit**

```bash
git add backtest/ssmt_psp_engine.py
git commit -m "feat(ssmt): CLI, stats, per-year reporting + first smoke run"
```

---

## Task 8: Random-direction null test (rigor gate)

**Files:**
- Create: `diagnostics/ssmt_psp_null.py`

Mirrors `diagnostics/org_driver_falsifier.py`: re-resolve the SAME setups with the trade direction
randomized; build a 500-seed null PF distribution; report where the real model's PF falls. The
model must sit in the upper tail (≥95th pct) to be a real directional edge.

- [ ] **Step 1: Implement** (create file)

```python
"""Random-direction null for the SSMT->PSP engine (ORG-falsifier pattern).
A directional edge must beat a coin-flip on the SAME setups. Run after a non-zero smoke run.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from backtest.ssmt_psp_engine import run_backtest, stats, FILES_2020_2024

CFG = {"exec": "nq", "companion": "either", "arrays": ["fvg", "ifvg", "ob", "breaker"],
       "stage2": "secondary-smt", "stage2_tf": "90min",
       "key_level": "either", "key_level_tf": "1h", "key_level_tol": 20.0,
       "displacement": "on", "disp_frac": 0.5, "htf_bias": "1d", "macro": "session",
       "target": "nearest-swing", "sl": "local", "anchor_et": "18:00",
       "psp_window_h": 24, "pivot_n": 3}


def main(seeds=500):
    tr = run_backtest(CFG, FILES_2020_2024)
    real = stats(tr)["pf"]
    print("REAL pf:", real, "| n:", len(tr))
    if not len(tr):
        print("no trades -> null undefined"); return
    pnl = tr.pnl.values
    R = np.where(pnl > 0, pnl, -pnl)        # per-trade bracket magnitude
    null = []
    for s in range(seeds):
        rs = np.random.default_rng(s)
        v = (rs.integers(0, 2, len(R)) * 2 - 1) * R
        w, l = v[v > 0].sum(), -v[v < 0].sum()
        null.append(w / l if l else np.inf)
    null = np.array([x for x in null if np.isfinite(x)])
    pct = (null < real).mean() * 100
    print(f"null mean pf {null.mean():.3f} | real pf {real:.3f} | percentile {pct:.1f}")
    print("VERDICT:", "edge (>=95th)" if pct >= 95 else "NOT distinguishable from coin-flip")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `/usr/local/bin/python3 -u diagnostics/ssmt_psp_null.py`
Expected: prints REAL pf, null mean, percentile, VERDICT. Record the percentile (go/no-go gate).

- [ ] **Step 3: Commit**

```bash
git add diagnostics/ssmt_psp_null.py
git commit -m "feat(ssmt): random-direction null rigor gate"
```

---

## Task 9: Tail test + sealed 2025 holdout (rigor gate)

**Files:**
- Create: `diagnostics/ssmt_psp_tail_holdout.py`

- [ ] **Step 1: Implement** (create file)

```python
"""Tail test (drop top-3 winners) + sealed 2025 holdout for the SSMT->PSP engine.
Tail-noise check (SSMT-v2 lesson) + the only clean OOS window (data-provenance reframe).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtest.ssmt_psp_engine import run_backtest, stats, peryear, FILES_2020_2024, FILES_2025

CFG = {"exec": "nq", "companion": "either", "arrays": ["fvg", "ifvg", "ob", "breaker"],
       "stage2": "secondary-smt", "stage2_tf": "90min",
       "key_level": "either", "key_level_tf": "1h", "key_level_tol": 20.0,
       "displacement": "on", "disp_frac": 0.5, "htf_bias": "1d", "macro": "session",
       "target": "nearest-swing", "sl": "local", "anchor_et": "18:00",
       "psp_window_h": 24, "pivot_n": 3}


def tail_test(tr):
    if len(tr) < 4:
        return None
    keep = tr.sort_values("pnl", ascending=False).iloc[3:]   # drop top-3 winners
    return stats(keep)


def main():
    tr = run_backtest(CFG, FILES_2020_2024)
    print("IS 2020-2024:", stats(tr), "| peryear:", peryear(tr))
    tt = tail_test(tr)
    print("DROP-TOP-3 :", tt, "->", "TAIL-NOISE" if (tt and tt["pf"] < 1.0) else "survives")
    ho = run_backtest(CFG, FILES_2025)
    print("HOLDOUT 2025:", stats(ho), "| peryear:", peryear(ho))
    print("NOTE: 2025 is the only clean OOS; even a pass is necessary-not-sufficient (live demo is the real OOS).")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `/usr/local/bin/python3 -u diagnostics/ssmt_psp_tail_holdout.py`
Expected: prints IS stats+peryear, drop-top-3 verdict, 2025 holdout stats. Record all three.

- [ ] **Step 3: Commit**

```bash
git add diagnostics/ssmt_psp_tail_holdout.py
git commit -m "feat(ssmt): drop-top-3 tail test + sealed 2025 holdout gate"
```

---

## Task 10: Ablation sweep + research-critiquer handoff

**Files:** none new — analysis/decision task.

- [ ] **Step 1A: Forward selection** (minimal core → add one gate at a time; record n + stats each line)

```bash
cd ~/mnq_trading
# MIN = loosest cascade that still defines a trade (no extra gates)
MIN="--stage2 off --key-level swing --key-level-tol 999999 --displacement off --htf-bias off --macro session"
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN                                  # core only
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN --stage2 secondary-smt           # +Stage-2 SMT
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN --key-level htf-fvg --key-level-tol 20  # +nested FVG
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN --displacement on                # +displacement
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN --htf-bias 1d                     # +HTF bias
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $MIN --macro precise                   # +macro
```
For each added gate, note Δn (trades dropped) and Δstats. A gate that drops trades without
improving PF/per-year is not earning its place; one that lifts PF and holds per-year is.

- [ ] **Step 1B: All-on, then ablate one gate at a time** (max-fidelity baseline)

```bash
cd ~/mnq_trading
ALL="--stage2 secondary-smt --key-level either --displacement on --htf-bias 1d --macro precise"
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL                                   # full fidelity
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL --stage2 off                      # -Stage-2
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL --key-level swing --key-level-tol 999999  # -nested FVG
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL --displacement off                # -displacement
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL --htf-bias off                    # -HTF bias
/usr/local/bin/python3 -u backtest/ssmt_psp_engine.py $ALL --macro session                   # -macro
```

- [ ] **Step 1C: Independent-axis sweeps** (companion / exec / arrays / sl / stage2-tf / target / key-level-tf)

```bash
cd ~/mnq_trading
for COMP in either es ym both;   do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --companion $COMP; done
for EXC  in nq failure-swing;    do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --exec $EXC; done
for ARR  in fvg ifvg ob breaker; do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --arrays $ARR; done
for SL   in local ssmt;          do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --sl $SL; done
for TF   in 60min 90min 4h;      do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --stage2-tf $TF; done
for KTF  in 1h 90min 4h;         do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --key-level htf-fvg --key-level-tf $KTF; done
for TGT  in nearest-swing pdh-pdl; do /usr/local/bin/python3 -u backtest/ssmt_psp_engine.py --target $TGT; done
```
(`--target failure-swing` is intentionally omitted — it raises `NotImplementedError` until the
order-pairing follow-up.)

The `--stage2 off` vs `secondary-smt` line is the direct test of the content creator's claim that
the 90m secondary SSMT matters: if `off` already clears the success criteria with materially more
trades, the second stage is redundant; if `off` fails the null/tail but `secondary-smt` passes, the
two-stage rule is earning its keep.

- [ ] **Step 2: Apply the success criteria** (spec §7)

A config is "alive" ONLY if it clears ALL of: beats the null (Task 8 ≥95th pct), survives
drop-top-3 (Task 9 PF>1.0), every-year-positive 2020-2024, AND holds on the 2025 holdout. Pick the
single best config that clears all four (or conclude none does).

- [ ] **Step 2b: MANDATORY lookahead guard (hard gate — run before ANY validated verdict)**

```bash
cd ~/mnq_trading
/usr/local/bin/python3 -u diagnostics/lookahead_guard.py   # detector self-test must print ALL GUARD SELF-TESTS PASS
# then guard the real engine (corrupts all bars after the cutoff, asserts past trades unchanged):
/usr/local/bin/python3 -u -c "import backtest.ssmt_psp_engine as e; from diagnostics.lookahead_guard import guard_file_engine; \
cfg=dict(exec='nq',companion='either',arrays=['fvg','ifvg','ob','breaker'],stage2='secondary-smt',stage2_tf='90min', \
key_level='either',key_level_tf='1h',key_level_tol=20.0,displacement='on',disp_frac=0.5,htf_bias='1d',macro='session', \
target='nearest-swing',sl='local',anchor_et='18:00',psp_window_h=24,pivot_n=3); \
guard_file_engine(e, cfg, e.FILES_2020_2024, cutoff='2022-06-01')"
```
Expected: `LOOKAHEAD GUARD PASS: N past trades identical after future corruption.` If it raises
`AssertionError: LOOKAHEAD ...`, there is a leak — fix it before proceeding. No PASS = no validated
verdict. (This is the fence that would have caught every prior lookahead disaster.)

- [ ] **Step 3: Gate through research-critiquer**

Invoke `/research-critiquer` on `backtest/ssmt_psp_engine.py` + the chosen config's results
(independent reproduction). Only after PASS may any "validated" language be used — and even then it
is in-sample pending live-demo OOS.

- [ ] **Step 4: Record the verdict to memory**

If dead: append an honest entry to `~/.claude/projects/-Users-azarudin/memory/gotchas.md` (what was
tested, the null/tail/holdout numbers, why it failed) so it is not re-run. If alive: update
`session_state.md` + create a result memory file. Either way, commit named files only; secret-scan
first.

---

## Task B1: Spine-B detectors — candle closure, equilibrium, swing-significance (TTrades)

**Files:** Modify `backtest/ssmt_psp_engine.py` + `tests/test_ssmt_psp.py`.

- [ ] **Step 1: Failing tests** (append)

```python
def test_candle_closure():
    from backtest.ssmt_psp_engine import candle_closure
    o = np.array([10, 10], float); h = np.array([11, 10.5], float)
    l = np.array([9,  8.0], float);  c = np.array([10, 9.8], float)
    # i=1 bull: swept prior low (8<9) AND closed back inside (9.8>9) -> c2 reversal
    assert candle_closure(o, h, l, c, 1, "bull") == "c2"
    c2 = np.array([10, 8.5], float)  # swept + closed BELOW prior low -> continuation
    assert candle_closure(o, h, l, c2, 1, "bull") == "continuation"

def test_candle_closure_c3():
    from backtest.ssmt_psp_engine import candle_closure
    # no sweep (low[1] 9.2 >= low[0] 9) but close engulfs c2 body up -> c3
    o = np.array([10, 9.3], float); h = np.array([10.2, 10.6], float)
    l = np.array([9,  9.2], float);  c = np.array([9.5, 10.4], float)
    assert candle_closure(o, h, l, c, 1, "bull") == "c3"

def test_equilibrium():
    from backtest.ssmt_psp_engine import equilibrium, in_discount, in_premium
    eq = equilibrium(10, 12, 8, 11)          # (12+8)/2 = 10
    assert eq == 10.0
    assert in_discount(9.0, eq) and not in_discount(11.0, eq)
    assert in_premium(11.0, eq) and not in_premium(9.0, eq)

def test_relevant_swing_sep():
    from backtest.ssmt_psp_engine import is_relevant
    assert is_relevant(level=80.0, prior_level=100.0, sep=10.0)      # |80-100|=20 >= 10
    assert not is_relevant(level=98.0, prior_level=100.0, sep=10.0)  # 2 < 10 -> failure swing
```

- [ ] **Step 2: Run -> fail** (`ImportError: candle_closure`).

- [ ] **Step 3: Implement** (append)

```python
def candle_closure(o, h, l, c, i, bias):
    """TTrades closure type at candle i vs prior candle i-1, for `bias`. None if no closure."""
    o, h, l, c = map(np.asarray, (o, h, l, c))
    if i < 1:
        return None
    body_hi, body_lo = max(o[i - 1], c[i - 1]), min(o[i - 1], c[i - 1])
    if bias == "bull":
        if l[i] < l[i - 1]:                       # swept prior low
            return "c2" if c[i] > l[i - 1] else "continuation"
        if c[i] > body_hi:                        # no sweep, engulf C2 body up
            return "c3"
    else:
        if h[i] > h[i - 1]:
            return "c2" if c[i] < h[i - 1] else "continuation"
        if c[i] < body_lo:
            return "c3"
    return None


def equilibrium(po, ph, pl, pc):
    """50% of the prior candle's range (TTrades EQ)."""
    return (ph + pl) / 2.0


def in_discount(price, eq):
    return price <= eq


def in_premium(price, eq):
    return price >= eq


def is_relevant(level, prior_level, sep):
    """Swing-significance: a swing is relevant only if it is >= sep from the prior same-side swing
    (range-expansion separation); otherwise it is a failure swing to be ignored."""
    return prior_level is None or abs(level - prior_level) >= sep
```

- [ ] **Step 4: Run -> pass** (`PASS test_candle_closure` ... `test_relevant_swing_sep`).

- [ ] **Step 5: Commit** `git commit -m "feat(ssmt): Spine-B detectors (candle closure, equilibrium, swing-significance)"`

---

## Task B2: Spine switch + flags + Spine-B setup loop

**Files:** Modify `backtest/ssmt_psp_engine.py`.

- [ ] **Step 1: Add flags** (Task 7 argparse): `--spine {smt-cascade,c2c3-closure}` (default `smt-cascade`);
  `--eq-zone {on,off}` (default `on`); `--swing-sig {on,off}` (default `off`);
  `--tf-bias` (default `1d`), `--tf-swing` (default `4h`), `--tf-exec` (default `15min`). Add all to `cfg`.

- [ ] **Step 2: Implement the Spine-B setup selector** (append; reuses ALL shared machinery)

```python
def spine_b_setups(cfg, m1):
    """TTrades C2/C3-closure spine -> yields (bias, level, trigger_ts) like find_6h_ssmt does, so the
    SAME downstream (1m CISD entry + protected-swing SL + target + walk_setup + gates) applies.
    bias: daily closure; swing TF C2/C3 closure = the trigger; level = swept swing for the SL ref."""
    n = cfg["pivot_n"]
    fb = resample_tf(m1["nq"], cfg["tf_bias"], cfg["anchor_et"])
    fs = resample_tf(m1["nq"], cfg["tf_swing"], cfg["anchor_et"])
    dur_s = pd.tseries.frequencies.to_offset(cfg["tf_swing"])
    out = []
    for i in range(2, len(fs)):
        # daily bias as of this swing bar's close (htf_bias is causal/confirmed)
        bias = htf_bias(fb, fs.index[i] + dur_s, n)
        if bias == "none":
            continue
        cc = candle_closure(fs["open"].values, fs["high"].values, fs["low"].values,
                            fs["close"].values, i, bias)
        if cc not in ("c2", "c3"):
            continue
        # protected/level reference = the swept prior swing extreme on the swing TF
        level = float(fs["low"].values[i - 1]) if bias == "bull" else float(fs["high"].values[i - 1])
        out.append((bias, level, fs.index[i] + dur_s))   # trigger = swing bar CLOSE (no lookahead)
    return out
```

- [ ] **Step 3: Branch `run_backtest` on `cfg["spine"]`**. Replace the per-bar `find_6h_ssmt` loop body
  so that when `cfg["spine"] == "c2c3-closure"` the trigger list comes from `spine_b_setups(cfg, m1)`
  (iterate its `(bias, level, trigger_ts)` tuples); when `smt-cascade`, keep the existing SSMT→PSP→Stage2
  path producing `entry_start_ts`. BOTH then run the identical block: `win = m1[exec_inst].loc[trigger_ts:
  trigger_ts+window]` → `assemble_entry` (1m CISD/PD-array) → key-level/displacement/HTF-bias gates →
  `walk_setup`. Add, after `assemble_entry`, when `cfg["eq_zone"]=="on"` (Spine B): compute the prior
  exec-TF candle EQ and require `in_discount(e["entry"],eq)` (bull) / `in_premium` (bear) else `continue`.
  When `cfg["swing_sig"]=="on"`: require `is_relevant(level, prior_level, sep)` (sep = a fraction of the
  swing-TF ATR) before accepting the setup. SMT in Spine B is an optional confluence (off by default).

- [ ] **Step 4: Verify** `/usr/local/bin/python3 -u tests/test_ssmt_psp.py` (ALL PASS) then smoke-run both spines:
  `... --spine smt-cascade` and `... --spine c2c3-closure`. Record n + stats for each.

- [ ] **Step 5: Commit** `git commit -m "feat(ssmt): dual-spine switch (smt-cascade | c2c3-closure) + EQ/swing-sig gates"`

---

## Task B3: Head-to-head spine ablation (extends Task 10)

- [ ] Run BOTH spines through the full gate stack — lookahead_guard (Step 2b), random-direction null
  (Task 8), drop-top-3 + 2025 holdout (Task 9), per-year — and the forward/all-on ablations (Task 10).
  Report a single table: spine × {n, PF, per-year, null-pctile, drop-top-3, holdout, guard}. A spine is
  "alive" only if it clears ALL gates. Gate the winner (if any) through `/research-critiquer` Section G.
  Record the verdict (alive or graveyard) to memory either way.

---

## Self-Review

**Spec coverage:**
- 6H SSMT (CME-anchored, tz-correct) → Tasks 2, 3. ✓
- 15m PSP opposite-color (Stage 1) → Task 4. ✓
- Stage-2 secondary SMT on configurable TF (GxT two-stage, default 90m, ablatable) → Task 4b, wired in Task 6, flagged in Task 7, swept in Task 10. ✓
- Nested-FVG key-level gate (GxT Item 133: entry inside an HTF FVG, swing/htf-fvg/either, ablatable) → Task 5d, wired in Task 6, flagged in Task 7, swept in Task 10. ✓
- Fidelity gates (displacement / HTF-bias alignment / macro-time / PDH-PDL target, all ablatable) → Task 5e, wired in Task 6, flagged in Task 7, swept in Task 10. ✓
- Dual ablation (forward-selection AND all-on-then-remove) → Task 10 Steps 1A/1B/1C. ✓
- 1m CISD OFS + FVG/IFVG/OB/breaker entry → Task 5 (a/b/c). ✓
- First-swing target + CISD-protected SL → Task 5c. ✓
- 1m fill resolution, SL-first, no entry-bar lookahead → Task 6. ✓
- Flags exec / companion / arrays / sl / anchor / psp-window / pivot-n → Task 7. ✓
- `--target failure-swing` (GxT order-pairing) → parsed in Task 7, raises `NotImplementedError` in `run_backtest` until a follow-up (explicit, fails loudly — not a silent placeholder). ✓
- Rigor gates: null → Task 8; drop-top-3 + 2025 holdout → Task 9; per-year → Task 7; research-critiquer → Task 10. ✓
- Data provenance (2020-2024 dev, 2025 sealed) → file constants in Task 6. ✓

**Placeholder scan:** No TBD/TODO. The one deferral (`--target failure-swing`) is an explicit
loud-failing `NotImplementedError`.

**Type consistency:** `swing_highs/lows(arr, n)→bool[]`; `resample_6h(df, anchor_et)→df`;
`find_6h_ssmt(...)→(bias,level,ts)|None`; `find_15m_psp(...)→ts|None`;
`find_cisd(...)→(confirm_idx,swing_idx,swing_val,level)|None`;
`pd_arrays_bull/_pd_arrays_bear(...)→[{kind,proximal,distal,idx}]`;
`assemble_entry(...)→{entry,sl,confirm_idx,array_idx,kind,bias}|None`;
`walk_setup(h,l,confirm_idx,entry,sl,bias,tp_fixed)→(outcome,pnl,fill_idx)`; `run_backtest(cfg,files)→DataFrame`;
`stats→dict`; `peryear→dict`. Consistent across tasks. ✓

**Known follow-ups (not v1 blockers):** order-pairing target; True-Open entry zone; partials.
