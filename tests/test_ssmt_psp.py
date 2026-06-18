import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
from backtest.ssmt_psp_engine import swing_highs, swing_lows


# --- Task 1: pivots ---
def test_pivots():
    # index:    0   1   2   3   4   5   6
    lows  = np.array([5, 4, 3, 4, 5, 6, 7], float)
    highs = np.array([5, 6, 7, 6, 5, 4, 3], float)
    # n=2: a pivot low needs strictly-higher neighbours each side; idx 2 is the low
    assert swing_lows(lows, n=2).tolist() == [False, False, True, False, False, False, False]
    assert swing_highs(highs, n=2).tolist() == [False, False, True, False, False, False, False]


# --- Task 2: 6H resample ---
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


# --- Task 3: 6H SSMT ---
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


# --- Task 4: 15m PSP ---
def test_psp():
    from backtest.ssmt_psp_engine import find_15m_psp
    idx = pd.date_range("2021-03-01 09:00", periods=5, freq="15min")
    nq = pd.DataFrame({"open": [10,10,10,10,10], "close": [11,11,9,11,11]}, index=idx).astype(float)
    es = pd.DataFrame({"open": [10,10,10,10,10], "close": [11,11,11,11,11]}, index=idx).astype(float)
    # bar 2: NQ bearish (9<10), ES bullish (11>10) -> bullish PSP
    ts = find_15m_psp(nq, es, bias="bull", after_ts=idx[0], window_h=24)
    assert ts == idx[2] + pd.Timedelta("15min")   # close time, not label


# --- Task 4b: resample_tf + secondary SMT ---
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


# --- Task 5a: CISD ---
def test_cisd_bull():
    from backtest.ssmt_psp_engine import find_cisd
    # idx0 is a doji (o==c, not a down candle) so the down-leg begins at idx1 (open 10),
    # per the test's intent + spec "open of the first candle of the leg".
    o = np.array([10, 10,  9,  8,  9,   11], float)  # first down candle of the leg = idx1 (open 10)
    h = np.array([11, 10,  9,  8,  9.5, 11], float)
    l = np.array([10,  9,  8,  7,  8,   10], float)  # pivot low at idx3 (n=1)
    c = np.array([10,  9,  8,  9,  10.5,11], float)  # idx4 closes 10.5 (>10) -> CISD confirm
    r = find_cisd(o, h, l, c, bias="bull", start=0, pivot_n=1)
    assert r is not None
    confirm_idx, swing_idx, swing_val, level = r
    assert swing_idx == 3 and swing_val == 7.0      # pivot low at idx3
    assert level == 10.0                            # open of first down candle (idx1)
    assert confirm_idx == 4                          # first close above 10


# --- Task 5b: PD arrays ---
def test_pd_arrays():
    from backtest.ssmt_psp_engine import pd_arrays_bull
    # bullish FVG: high[0]=9, low[2]=10 -> gap distal 9, proximal 10
    o = np.array([8,  9,  10.2], float)
    h = np.array([9,  10.5,11 ], float)
    l = np.array([7,  9.5, 10 ], float)
    c = np.array([8.8,10.3,10.9], float)
    arrs = pd_arrays_bull(o, h, l, c, lo_idx=0, hi_idx=2, kinds=("fvg",))
    assert any(a["kind"] == "fvg" and a["proximal"] == 10.0 and a["distal"] == 9.0 for a in arrs)


# --- Task 5c: assemble entry ---
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


# --- Task 5d: nested-FVG key-level gate ---
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


# --- Task 5e: fidelity helpers ---
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


# --- Task 6: walk_setup ---
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


# --- Task B1: Spine-B detectors ---
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("PASS", name)
    print("ALL PASS")
