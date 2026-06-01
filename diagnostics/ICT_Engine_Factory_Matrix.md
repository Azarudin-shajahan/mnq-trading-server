# ICT Engine Factory — Technique × Instrument Matrix (Phase 2)

> Built 2026-06-01 (Session 36) from qmd `ict_transcripts` (493 docs) + title taxonomy, reconciled against existing `Concepts/ICT/` (509 notes) and the GxT engine family. **This is a build-list, not engine code.** Ground-truth protocol: see [[Engine_Models_Catalog]] + `ict-engine-factory` memory.

## The data wall (shapes the whole build order)
ICT teaches **forex-first** — 56 forex-tagged titles vs 44 NQ. But Databento coverage = **NQ/ES/YM/RTY/GC/CL/RB/HO only**.

| Instrument class | ICT teaching presence | Data? | Notes |
|---|---|---|---|
| Indices (NQ/ES/YM/RTY) | High (NQ 44, ES 9) | ✅ | Primary build target |
| Gold (GC) | Medium (taught, fewer titles) | ✅ | GxT showed GC primacy doesn't fully mechanize under V-shape |
| Oil (CL/RB/HO) | Low (1 title) | ✅ | **CL proven DEAD** (no V-shape/Asia edge) — deprioritise |
| Forex (DXY/EURUSD/GBPUSD/Cable/Fiber/UsdJpy) | **Highest (56)** | ❌ | **DATA-BLOCKED** — richest teaching, no data |
| Bitcoin | Medium (7) | ❌ | DATA-BLOCKED |
| Bonds (ZB/ZN/10yr) | Low (6) | ❌ | DATA-BLOCKED |

**Consequence:** the most-taught techniques are demoed on forex; building them on indices/gold carries translation risk (GxT precedent: CL "oil triad" looked taught but had zero edge). Either source FX/BTC data or accept index-translation as an explicit hypothesis to backtest-falsify.

## Corpus backbone (the systematic teaching = engine candidates)
1. **13 Charter Price Action Models** — each with a "Trade Plan / Algorithmic Theory" lecture (ICT stating the algorithm explicitly). **Highest-value engine candidates.**
2. **Mentorship Core Content Months 1–12** (114 vids) — the technique encyclopedia (building blocks).
3. **OTE Pattern Recognition Series** (16 vids) — OTE deep-dive.
4. **~150 daily/live-execution videos** — the "taught vs actually traded" cross-check + the non-index instrument demos.

## The 13 Charter Models — mechanizability triage
| Model | What it is | Mechanizable? | Overlap w/ existing | Data |
|---|---|---|---|---|
| 1 | Foundational setup (elements of a trade) | partial | building block | ✅ |
| 4 | Position Trading (HTF swings) | likely | none | ✅ idx/gold |
| 5 | Day Trading — Intraday Volatility Expansions | **strong** | adjacent to V-shape | ✅ idx |
| 6 / 7 | Universal Trading Model | **strong** | core | ✅ idx |
| 8 | Targeting 6/month (selective day model) | likely | none | ✅ idx |
| 9 | One Shot One Kill (single high-prob/day) | **strong** | none | ✅ idx |
| 10 | Swing Trading | likely | none | ✅ idx/gold |
| 11 | Day Trading | **strong** | overlaps 62T PERFECT | ✅ idx |
| 12 | Scalping Intraday Model | maybe (noise risk) | none | ✅ idx |
| 13 | 2022 YouTube Model | partial | — | ✅ idx |

## Core technique encyclopedia (Months 1–12) — engine atoms
FVG · Order Block · Breaker · Mitigation Block · Liquidity (BSL/SSL) · OTE (62/70.5/79%) · Killzones (London/NY) · Judas Swing · Turtle Soup · Daily Bias · Power of 3 (AMD) · SMT Divergence · Market Maker Models (MMBM/MMSM) · Silver Bullet · Asian Range · IPDA data ranges.
**Status vs existing engines:** FVG-reversal + V-shape + SMT(oil-triad) + discount-entry + Asian-session-FVG→PDH/PDL are **already mechanized** in the GxT 62T PERFECT + Asia 1H FVG engines (indices+gold). Don't rebuild — *extend/validate*.

## Named later models (2022+ / daily)
Silver Bullet · Unicorn · Venom · Gauntlet · Sons model · NWOG/NDOG · 1st Presented FVG · Storytellers framework (5) · Suspension Block. Mostly index/forex; mechanizability unproven.

## Proposed build order (prioritised, opinionated)
**Tier 1 — build first (explicit algorithm + data + low overlap):**
1. **Charter Model 9 — One Shot One Kill** (indices) — single daily high-prob setup; clean to falsify.
2. **Charter Model 5 — Intraday Volatility Expansion** (indices) — explicit expansion trigger.
3. **Charter Model 6/7 — Universal Model** (indices) — ICT's "universal" claim, directly testable.

**Tier 2 — after Tier 1 proves the pipeline:**
4. Charter Model 10 Swing + Model 4 Position (indices+gold) — HTF, fewer trades, cleaner.
5. Silver Bullet (fixed killzone window — highly mechanical by construction).

**Tier 3 — data-gated / deprioritised:**
6. Any forex/BTC/bond technique → **blocked until data sourced**.
7. Scalping (Model 12), oil (CL dead), discretionary named models → low priority.

**Do NOT rebuild:** FVG-reversal, V-shape, Asia FVG, SMT — already mechanized (GxT family). Phase 3 validates/extends those instead.

## Phase 2 CORRECTION (Session 36) — the Core Content is a curriculum, not a blob
Original draft collapsed Months 1–12 into a one-line "encyclopedia" and **dropped named, first-class techniques** — caught when the user asked why COT (a *named lecture*, Month 10) wasn't surfaced. Enumerating the ~90 Core Content lectures reveals a **bias & confirmation cluster** that feeds Model 9's weakest stage (weekly bias) and was entirely missing:
- **Month 10:** Commitment Of Traders · Open Interest Secrets & Smart-Money Footprint · Relative Strength Analysis (Accumulation) · Importance of Multi-Asset Analysis · Index Futures AM/PM Trend · Commodity Seasonal Tendencies · Premium vs Carrying Charge
- **Month 05:** Seasonal Tendencies (bull/bear/ideal) · Intermarket Analysis · Using 10-Year Notes in HTF Analysis · IPDA Data Ranges · Quarterly Shifts · HTF PD Arrays · Open Float Liquidity
- **Month 03:** Institutional Order Flow · Institutional Sponsorship · Institutional Market Structure (IOF = 3rd leg of the COT blend)
- **Month 07 (Model 9's home month):** One Shot One Kill + Intraweek Reversals + Short-Term Trading set (Weekly Range, Low-Resistance Liquidity, MM Manipulation, Blending IPDA, Using Monthly/Weekly)
- **Month 08:** Central Bank Dealers Range · Intraday Profiles · Projecting Daily Highs/Lows · When To Avoid London
- **Month 04:** full PD-array catalog (FVG, Breaker, Propulsion, Rejection, Vacuum, Mitigation, Reclaimed OB, Liquidity Voids/Pools)
- **Month 11:** Mega-Trades per asset class · **Month 12:** Top-Down Analysis (Long/Intermediate/Short/Intraday) · **Month 09:** Bread & Butter (= Model 8), Day-Trade Routine

**Protocol fix (LOCKED):** Phase 2 enumerates **one row per named lecture**, never a collapsed list. Phase 3 grounds a technique against **ALL** its transcripts (Model 9 had 3; only 1 was read → COT was in an unread sibling). This repeats the Session-33 cross-corpora lesson — see [[gotchas]] and the new feedback memory. The bias cluster above is now first-class input to Model 9's weekly-bias stage, not just the 20-week range + COT.

## Open reconciliation task
509 `Concepts/ICT/` notes = prior unvalidated synthesis. Before Phase 3 per-technique grounding, map each Tier-1 technique to its existing note(s) and treat them as hypotheses to verify against transcripts + NotebookLM, never as ground truth.
