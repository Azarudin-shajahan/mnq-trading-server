# MNQ Trading — Claude Guidelines

## Karpathy Coding Principles

### 1. Think Before Coding
Before implementing anything: state assumptions explicitly, surface ambiguity, push back if a simpler path exists.

### 2. Simplicity First
Minimum code that solves the problem. No speculative abstractions, no unrequested configurability, no error handling for impossible scenarios.

### 3. Surgical Changes
Touch only what the task requires. Don't "improve" adjacent code. Match existing style.

### 4. Goal-Driven Execution
Define verifiable success criteria before starting. For multi-step tasks, state a brief plan with a verify step for each.

---

## MNQ Permanent Constraints (never override without explicit instruction)

| Constraint | Value |
|---|---|
| entry_min | **4.5** (never 5.0 — confirmed across 3 grid datasets) |
| Backtest point value | **$0.50/pt** in Python engine (intentional, never change) |
| Live point value | $2.00/pt |
| Canonical data range | MNQ1! + Jan 1 2020 |
| Validated edge | **Python v8.18 62T** (~$286 net, IN-SAMPLE only — no clean OOS yet; the forward/live demo is the real lever). This is the source of truth, NOT JUDGE. |
| ⚠️ Old "C18 baseline" | **SUPERSEDED 2026-06-25.** C18 No-London "PF 9.81 / $91K / 71.9% WR" was the *in-sample, optimistic* read of the **Lineage-A JUDGE** (single-symbol Pine). Backtested honestly it is a NET LOSER (676t/−$13.6k; 122t/−$5.4k at the live config). Do NOT grade off it. See memory `finding-tv-judge-vs-python-edge`. |

## TV Strategy Tester Warning
MNQ1! 5m on this account only has data from **Jan 25, 2026** — TV tester shows ~25 trades / PF ~1.44. This is NOT the baseline. The Python backtester with 2020+ data is the source of truth.

## MFFU Builder 50K Constraints (verified from help center 2026-05-22)
- Daily loss soft pause: **$1,000** (trading blocked rest of day, account NOT breached)
- Max EOD trailing drawdown: **$2,000** (hard breach — account over)
- Contract limit: **4 Minis OR 40 Micros** (combined, cross-instrument, either/or — NOT per instrument)
- T1 news blackout: ±2 min around release (Builder sim allowed — most other plans ban T1 in sim)
- Inactivity: must trade at least once per 7 calendar days (sim funded)
- Auto-liquidation: 4:10 PM EST daily
- Payout: 80/20 split, $2,100 buffer, $2,000 max/cycle, 5 payouts then → live
- Full Gold (GC) BANNED — only Micro Gold (MGC) available
- 2-consecutive-loss pause rule: after 2 consecutive losing trades in a session, skip the next session's first trade (self-imposed, not platform rule)
- London session: DISABLED (adds expired losses, lowers PF)

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
