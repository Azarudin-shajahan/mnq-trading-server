# Scope — Daily Data Refresh for the HTF Capture Loop

**Status:** SCOPE for approval · 2026-06-19 · prerequisite for Phase 2 of
`2026-06-19-htf-context-discretion-capture.md`

---

## Goal
Keep a current, lookahead-clean NQ/ES/YM bar feed so `htf_context.py` can compute
real levels and `htf_outcomes.py --update` can score outcomes day to day. Today
the canonical file ends **2026-05-26**; there is a ~24-day gap before the loop can
run on live days.

## Hard reality that shapes the design
**Databento *Historical* has intraday lag** — it will NOT have today's Asia/London/
pre-NY bars during your IST evening (when you tag). So a same-day, fully-automated
"today's pre-NY context" is not reliable from Historical. Two architectures:

| | A. Databento **Live** (real-time) | B. **T+1 nightly** Historical (recommended) |
|---|---|---|
| Same-day machine context | yes, streamed | no - you read your own live chart (you already do) |
| Build complexity | high (streaming client, session mgmt) | low (one cron, reuse `download_full` pattern) |
| Cost | higher (live subscription) | ~cents/day (ohlcv-1m, 3 symbols, 1 day) |
| Outcome scoring | same | next morning, exact |
| Fit to a discretionary trader | redundant (you watch charts) | clean separation of concerns |

**Recommendation: B.** You are the live read (that is the whole point - capturing
*your* discretion). The machine's job is the disciplined record: deterministic
levels + outcome scoring + the eventual test. All of that works perfectly T+1.
`htf_capture` already stamps `tagged_ts` live, so the pre-outcome guarantee holds
even though the context columns finalize the next morning.

## What this means for the daily flow (architecture B)
```
  Evening (IST, < 20:30):  you run htf_capture --bias ... (read YOUR charts).
                           Row locked with tagged_ts. Context cols may be from
                           the last completed day (reference only).
  Next morning (cron):     refresh pulls yesterday's 1m NQ/ES/YM -> resample ->
                           append to the rolling live file. Then:
                           htf_outcomes --update <yesterday> fills the TRUE
                           deterministic context + actual outcome + v8.18 result.
```
Net: your bias is live + pre-outcome; every machine column is finalized exactly,
one day later. No lookahead (context for day D uses only <= D's pre-NY bars).

## Design - `scripts/databento_daily_refresh.py` (NEW)
Reuses the proven `databento_download_full.py` mechanics (GLBX.MDP3, `ohlcv-1m`,
`stype_in=continuous`, symbols `NQ.v.0/ES.v.0/YM.v.0`, `IST_OFFSET=+5:30`, the
`AGG` resample dict).

- **Incremental window:** `start = last timestamp in live file + 1min`,
  `end = today 00:00 UTC` (only complete days). First run backfills 2026-05-27 -> yesterday.
- **Output (NOT the canonical historical file):** `data/MULTI_5min_live_IST.csv`
  - a rolling NQ/ES/YM 5m file. Keeping it separate avoids re-committing the
  "file outgrew its name" provenance leak (the historical 2020_2025 file stays frozen).
  Also write `MULTI_4h_live_IST.csv` (4h resample) for HTF features that want it.
- **Append + dedup:** concat, drop duplicate `timestamp`, sort, write. Idempotent -
  re-running the same day is a no-op.
- **Columns:** nq/es/ym OHLCV only (what `htf_context` reads). The other 5
  instruments in the historical MULTI are irrelevant to the capture loop.
- **Point the loop at it:** `htf_context.DEFAULT_5M` stays the historical file for
  backfill; `htf_capture`/`--update` get a `--data data/MULTI_5min_live_IST.csv`
  flag (or a small loader that concatenates historical-tail + live). Decision below.

## Cron
```
# 06:30 IST daily (well after US close, Databento settled): pull + score yesterday
30 6 * * 1-5  DATABENTO_API_KEY=$(<secure>) python3 ~/mnq_trading/scripts/databento_daily_refresh.py \
                 && python3 ~/mnq_trading/diagnostics/htf_outcomes.py --update $(date -v-1d +\%F)
```
(Weekdays only; `--update` is idempotent and harmless if no forward row exists.)

## Cost & key
- ohlcv-1m, 3 symbols, 1 trading day ~ a few cents; the 24-day backfill ~ well under $1.
  The script prints a `get_cost` estimate first (free) and can run `--cost-only`.
- **Security (blocker):** `DATABENTO_API_KEY` is not in env. Memory flags the
  Databento keys as plaintext in `~/.claude/settings.json` and due for rotation.
  Before wiring a cron: **rotate the key**, store it in the macOS keychain (or a
  root-only env file), and have the cron read it from there - never inline in the crontab.

## Risks
| Risk | Mitigation |
|---|---|
| Databento settlement lag > expected | run cron at 06:30 IST (post-settlement); `--update` retries next day if a column is blank |
| Continuous-contract roll seam | `NQ.v.0` handles rolls; same as historical build, so consistent |
| Live file drifts from historical conventions | reuse the exact `AGG` + `IST_OFFSET`; spot-check first 3 appended days vs a known source |
| Key exposure in cron | keychain/secure-file read, rotate first |

## Build steps (on approval)
1. **Rotate** the Databento key; put it in keychain; confirm `DATABENTO_API_KEY` resolves.
2. `scripts/databento_daily_refresh.py` - incremental pull + resample + append/dedup to the two live files; `--cost-only` and `--since` flags; prints cost before charging.
3. One-shot **backfill run** 2026-05-27 -> yesterday; spot-check 3 days.
4. Add `--data` wiring so `htf_capture`/`htf_outcomes` read `historical-tail + live`.
5. Install the weekday cron; verify one cycle end-to-end (refresh -> --update fills a row).

## Decisions I need
1. **Architecture A (Live) or B (T+1 nightly)?** - *Recommend B.*
2. **Loader:** add a `--data` flag (simple) vs auto-concat historical-tail+live inside `htf_context` (smoother, slightly more code)? - *Recommend the small auto-concat so you never think about it.*
3. **Key handling:** OK to rotate the Databento key now and store in keychain? (required before any cron)
4. Same branch `htf-context-capture`, named-files-only.
