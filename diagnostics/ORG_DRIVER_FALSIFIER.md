# ORG driver-skeleton falsifier

_Generated 2026-06-11T09:41:23._

```json
{
  "generated": "2026-06-11T09:41:23",
  "window": [
    "2022-01-01",
    "2024-12-31"
  ],
  "inst": "nq",
  "n_gap_days": 603,
  "gap_band_pts": [
    10.0,
    200.0
  ],
  "buffer_pts": 5.0,
  "fill": {
    "n": 603,
    "wr": 0.182,
    "pf": 1.002,
    "expR": -0.022,
    "total_pts": 13.0,
    "pf_by_year": {
      "2022": 1.08,
      "2023": 0.93,
      "2024": 1.0
    }
  },
  "inverted": {
    "n": 603,
    "wr": 0.211,
    "pf": 1.259,
    "expR": 0.294,
    "total_pts": 1287.8,
    "pf_by_year": {
      "2022": 1.11,
      "2023": 1.1,
      "2024": 1.59
    }
  },
  "random_seed": {
    "n": 603,
    "wr": 0.192,
    "pf": 1.048,
    "expR": 0.055,
    "total_pts": 250.8,
    "pf_by_year": {
      "2022": 0.9,
      "2023": 1.09,
      "2024": 1.15
    }
  },
  "random_null_pf": {
    "5": 0.934,
    "50": 1.125,
    "95": 1.333
  },
  "fill_pf_percentile_vs_null": 15.6,
  "VERDICT": "KILL (driver not supported)"
}
```
