# Plan — HTF-Context Discretion Capture Loop

**Status:** DRAFT for approval · **Author:** session 2026-06-19 · **Branch (proposed):** `htf-context-capture`

---

## 0. Premise (read first — what this is and is NOT)

**What we proved this session:**
- The trader's *trigger* (sweep → SMT(NQ/ES/YM) → V-shape/CSD displacement → protected-swing stop → opposite-liquidity target) = **already implemented in v8.18 62T.** GxT + Daye both describe it. Not a missing edge.
- His *discretion* is not a hidden entry rule. His entire public corpus (1,674 "Market Lens" images) is **HTF directional/context bias**: weekly profile (Seek-&-Destroy / trend), SMT-at-session/weekly-open, premium/discount, Daye True-Open quarters — read on D1/H4.
- That HTF-bias/context layer is the **one thing v8.18 does NOT encode** (it boxes NY by clock, blind to weekly-profile context).
- The data to *learn* his discretion **does not exist and cannot be scraped**: his feed is win-biased (2 losses / 48 posts), mostly unlabeled (4/48 fully usable), and the images are idealized teaching graphics with no executions/outcomes.

**Therefore this project builds a way to GENERATE the missing dataset forward** — by having *you* log an HTF-context bias **as a pre-session prediction**, every trading day, against what v8.18 then does and what price actually did. After ~50–100 honest labeled days we can finally run the falsifiable test: **does a human HTF-context read add directional information beyond v8.18?**

**Explicit non-goals (guardrails):**
- ❌ NOT auto-trading, NOT a signal bot, NOT order placement.
- ❌ NOT hand-coding GxT/Daye "rules" into an engine (that path is DEAD-OOS here — SD-confluence, SSMT cascade, drivers, every high-freq line).
- ❌ NOT learning from his curated feed (survivorship-biased, un-labeled).
- ✅ It IS a disciplined, lookahead-clean, self-generated **decision journal + measurement harness**, doubling as the Book-C live-demo journal the project already calls "the real lever."

---

## 1. Success criteria (falsifiable)

The build succeeds operationally if, after the accumulation window, we can answer **both** with the project's standard rigor gates:

1. **Skip-set test:** On days v8.18 takes NO trade, does your pre-logged HTF bias predict the day's NY direction better than a random-direction null (≥95th pct), and does the lift survive drop-top-3? → if yes, the discretion is a *new* edge source.
2. **Agreement test:** On days v8.18 DOES trade, does your bias agreeing vs disagreeing with the engine's direction correlate with the engine's win/loss/expiry? → if yes, your read is a usable *filter* on the existing edge.

Either positive result = capturable discretion, validated on honest data. A null on both = his weekly income is size + screen-time on the shared trigger, not a transferable bias edge — also a valuable, money-saving answer.

**Hard gates reused (non-negotiable):** `diagnostics/lookahead_guard.py` (bias logged pre-outcome by construction), random-direction null, drop-top-3 tail test, and a sealed split of the forward data itself (first 60% train / last 40% never-touched until the end). No "validated" claim without an independent `/research-critiquer` Section-G pass.

---

## 2. The daily loop (core mechanic)

Runs once per trading day, in your **IST evening BEFORE the NY session resolves** (NY 9:30 ET ≈ 19:00–20:00 IST; capture window closes at `entry-cutoff-ist 20:30`, matching v8.18). The pre-outcome timestamp is what makes each row a real prediction, not hindsight.

```
  [T-1 / morning auto]  Machine computes the deterministic HTF context for today
                        (True-Open quarter, SMT-at-open, premium/discount, PDH/PDL,
                         NWOG/NDOG, weekly-profile-so-far, v8.18 pending signal+dir).
            │
            ▼
  [evening, pre-2030 IST]  You are shown that context (CLI or dashboard card) and you TAG:
                        bias ∈ {long, short, no-trade}, confidence ∈ {1,2,3},
                        driver tags (free + checkbox: weekly-profile / SMT / P-D / quarter / news),
                        optional: would you OVERRIDE v8.18 today? (take/skip/flip)
            │            → row LOCKED with timestamp; tag is now immutable (lookahead-safe).
            ▼
  [next day auto]  Machine appends OUTCOMES: actual NY session direction & range,
                        v8.18's trade for that day (dir, outcome, pts) if any.
                        Row is now a complete labeled example.
```

The only human action is the evening tag (~60–90 seconds/day). Everything else is automated.

---

## 3. Data schema — `htf_journal.csv`

One row per trading day. Append-only; never edit a locked row.

| field | source | when | notes |
|---|---|---|---|
| `date` | auto | T-1 | YYYY-MM-DD |
| `snapshot_ts_ist` | auto | tag time | proves pre-outcome |
| `daily_quarter` | auto (deterministic) | T-1 | Daye Q1–Q4 of the day |
| `weekly_quarter` | auto | T-1 | Mon=Q1…Thu=Q4 / Fri=X |
| `true_open_d` / `true_open_w` | auto | T-1 | midnight / Mon-18:00 prices |
| `prem_disc` | auto | T-1 | price vs equilibrium of prior dealing range (premium/discount/eq) |
| `smt_at_open` | auto | T-1 | NQ/ES/YM divergence flag at session/weekly open (which asset diverged) |
| `pdh` / `pdl` / `nwog` / `ndog` | auto | T-1 | key levels |
| `weekly_profile_so_far` | auto + human | T-1 | machine guess of the 5 profiles; human can correct |
| `v818_pending` / `v818_pending_dir` | auto (engine dry-run) | T-1 | does v8.18 have a setup queued, which way |
| **`human_bias`** | **you** | **evening** | **long / short / no-trade — THE label** |
| **`human_conf`** | you | evening | 1–3 |
| **`human_drivers`** | you | evening | tags + free text |
| **`human_override`** | you | evening | take / skip / flip v8.18 |
| `actual_dir` | auto | next day | NY session net direction |
| `actual_range_pts` | auto | next day | day expansion |
| `v818_traded` / `v818_dir` / `v818_outcome` / `v818_pts` | auto | next day | from `mnq_trade_log_v8_18.csv` |
| `split` | auto | end | train / sealed (assigned by date, locked) |

---

## 4. Components & file layout (reuse > rebuild)

```
~/mnq_trading/
  diagnostics/
    htf_context.py          NEW  — deterministic HTF feature computer (no lookahead; uses only data <= snapshot)
    htf_capture.py          NEW  — the daily CLI/loop: show context, take tag, lock row
    htf_outcomes.py         NEW  — next-day outcome appender (reads v8.18 log + price)
    htf_validate.py         NEW  — the eventual test harness (null + drop-top-3 + sealed split)
    lookahead_guard.py      REUSE — assert no human row depends on future bars
    dashboard_server.py     EXTEND (optional) — add a daily capture card at :8787
  data/
    htf_journal.csv         NEW  — the growing labeled dataset
  backtest/
    mnq_backtest_engine_v8_18.py  REUSE — dry-run for `v818_pending`; log for outcomes
  docs/superpowers/plans/
    2026-06-19-htf-context-discretion-capture.md   (this file)
```

- **`htf_context.py`** is the only non-trivial piece: it must compute True Opens, quarters, SMT-at-open, premium/discount, levels **using only bars at/under the snapshot timestamp** — verified by `lookahead_guard`. Reuses v8.18's data loaders and the existing SMT/level helpers; does not re-derive them.
- **`htf_capture.py`** default = terminal prompt (fast, no infra). Optional dashboard card later.
- Engine is **never modified** in Phase 1 — we only dry-run it for the pending signal and read its trade log. (A possible Phase 4 outcome is an additive `--htf-bias-gate` flag, plan-gated separately.)

---

## 5. Phases & milestones

| Phase | What | Output | Exit criteria |
|---|---|---|---|
| **0 — Backfill & wiring** (1 sitting) | Build `htf_context.py` + `htf_outcomes.py`; backfill the journal for v8.18's 62 historical trade days with the *deterministic* fields only (no human label — those can't be faked). Run `lookahead_guard` on `htf_context`. | populated deterministic columns + guard PASS | guard PASS; context values sanity-checked vs 2-3 known days |
| **1 — Daily loop live** (1 sitting) | Build `htf_capture.py`; you log your first real pre-session bias. | working 60-sec evening loop | 3 consecutive days logged cleanly |
| **2 — Accumulate** (~3–5 months) | One tag/evening. No analysis, no peeking at running win-rate (would bias your tagging). | growing `htf_journal.csv` | >=50 labeled days (target 100); >=15 on days v8.18 skipped |
| **3 — Test** (1 sitting) | Run `htf_validate.py`: skip-set test + agreement test, each through null + drop-top-3, train split only. Then ONE look at the sealed split. | PASS/NULL verdict + `/research-critiquer` Section-G | independent critique run |
| **4 — Decide** | If PASS: scope an additive, default-off `--htf-bias-gate` on v8.18 (new plan). If NULL: documented closure — discretion isn't a transferable bias edge; income lever stays size+demo. | decision recorded to memory | — |

---

## 6. Rigor / anti-self-deception safeguards

These are the difference between this and a journal that lies to you:

1. **Pre-outcome lock.** The bias row is timestamped and immutable before the session resolves. No editing after seeing price. Enforced in `htf_capture.py` (writes are append-only; a locked date refuses re-tag).
2. **No running scoreboard during Phase 2.** `htf_capture.py` will NOT show your hit-rate — knowing it would unconsciously tune your tagging toward the sample. Score is computed only in Phase 3.
3. **Sealed forward split.** Last 40% of collected days are quarantined until the very end; config/threshold choices use train only.
4. **Null + tail gates.** Any "edge" must beat a random-direction null (>=95th pct) and survive drop-top-3 — the exact tests that killed the SSMT/strength-switch lines.
5. **Lookahead guard on the feature computer**, not just trust.
6. **Independent critique** before any "validated" verdict (project rule: a self-asserted PASS is not a gate).
7. **Honest-N stop.** If after 6 months N<40 or skip-days<10, we declare it under-powered and stop — we do not over-interpret a thin sample.

---

## 7. Synergy — this is also the live-demo journal

The project's stated "real lever" is the Book-C live demo with `demo_reconciliation.py` / `book_c_kill_criteria.py`. The same `htf_journal.csv` + capture loop is the natural home for logging actual demo fills (add `demo_fill`, `demo_pts` columns). **One journaling instrument serves both goals** — capturing discretion AND making the demo trustworthy — instead of two parallel tools. Building this advances go-live regardless of how the discretion test resolves.

---

## 8. Risks & honest mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **You don't log daily** (the real killer) | High | 60-sec loop; evening IST timing fits your schedule; optional reminder. If adherence <70% over month 1, we redesign or stop. |
| Self-labeling drift / hindsight creep | Med | pre-outcome lock + hidden scoreboard |
| N never reaches power | Med | honest-N stop rule; report under-powered rather than over-claim |
| Your read just mirrors v8.18 (no new info) | Med | that's literally what the agreement test measures — a valid, useful answer |
| Survivorship in your own logging (only logging "good" days) | Med | rule: log EVERY trading day incl. no-trade; no-trade is a label |
| HTF features have subtle lookahead | Low | `lookahead_guard` mandatory on `htf_context.py` |

---

## 9. Decisions I need from you before building Phase 0

1. **Interface:** terminal CLI (fastest to build, I recommend) vs a dashboard card at :8787 (nicer, more work). *Default: CLI now, dashboard later if you stick with it.*
2. **Instruments for the bias tag:** NQ only (matches the live edge), or NQ + ES + YM context? *Default: tag NQ direction; show ES/YM only as SMT context.*
3. **Daily-demo coupling:** wire the Book-C demo fill columns in now (one tool) or keep capture-only first? *Default: capture-only Phase 1; add demo columns at Phase 1.5.*
4. **Commit policy:** new branch `htf-context-capture`, named-files-only commits (per your repo rule). Confirm OK.

---

## 10. What I build immediately on approval

Phase 0, in one pass:
1. `diagnostics/htf_context.py` — deterministic HTF feature computer + `lookahead_guard` self-test.
2. `diagnostics/htf_outcomes.py` — outcome appender from the v8.18 log.
3. Backfill `data/htf_journal.csv` deterministic columns for the 62 historical days; show you 2-3 rows to sanity-check the context values.
4. Then pause for your go-ahead to build Phase 1 (`htf_capture.py`) and you take day 1.
