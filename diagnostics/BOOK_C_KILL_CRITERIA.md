# Book C -- Pre-Registered Kill Criteria

_Generated 2026-06-10T23:52:25. FROZEN before the first demo trade. sha256 `9a7506c67d4bad76`._

> Book C is 100% in-sample (engines default to data through 2026-05-26; never held out). This bootstrap baseline INCLUDES the burned 2025-2026 window on purpose (it is the best estimate of a real edge's 12-week behaviour). The DEMO is the only clean OOS.

## Frozen config
- Book C = M9(ote/r2 + turtle/r3, maxrisk=30) + 0.5*M5-NQ + 0.5*M5-YM
- m9_cot=off, R_USD=100, weights={'m9': 1.0, 'm5nq': 0.5, 'm5ym': 0.5}
- In-sample: 2020-01-14 -> 2026-05-14 (331 calendar weeks, 1574 trades {'m9': 333, 'm5nq': 609, 'm5ym': 632})

## Bootstrap
- circular block, n=20000, block=4 weeks, window=12 weeks, seed=20260610
- 12wk PF percentiles: {'1': 0.7037, '5': 0.9004, '25': 1.25, '50': 1.5666, '75': 1.9665, '95': 2.7618}
- 12wk R-sum percentiles: {'1': -6.0013, '5': -1.9998, '25': 4.2329, '50': 8.7336, '75': 13.3139, '95': 19.9986}
- 12wk trade-count percentiles: {'1': 37.0, '5': 43.0, '25': 51.0, '50': 57.0, '75': 63.0, '95': 71.0}

## KILL CRITERIA (no re-tuning, no regime excuse)
1. **Primary** -- KILL if a demo window's realized **PF < 0.9004** OR **R-sum < -1.9998** (re-scored at the demo's exact week-length via `--score`, 5th percentile).
2. **Secondary tripwire** -- KILL the pipeline if trade frequency is outside **[28.5, 114.0]** per 12 weeks (median 57, >2x deviation).

## Demo protocol
- Freeze config (this file). Run 8-12 weeks demo at min size, target >=40-60 trades across M9+M5-NQ+M5-YM. Score with --score. PASS != validated; it only clears the one pristine OOS gate.

## Scoring forward results
```bash
python3 diagnostics/book_c_kill_criteria.py --score demo_trades.csv
# demo_trades.csv columns: date,entry,sl,pnl,leg   (leg in m9/m5nq/m5ym)
```
