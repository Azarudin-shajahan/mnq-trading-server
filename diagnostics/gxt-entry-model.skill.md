---
name: gxt-entry-model
description: Use when identifying or validating a GxT-style intraday entry (Universal Sequence + SMT triad confirmation) on index/oil/gold futures.
---

# GxT Entry Model

## When to Use
*   Intraday trading on indices, oil, or gold futures using correlated triads to
spot algorithmic synchronization.
*   Framing 4-hour expansion candles to anticipate the high and low of the daily
profile.
*   Aligning lower-timeframe universal models inside higher-timeframe draws on 
liquidity.
*   Timing intraday continuations and reversals following 8:30 AM or 9:30 AM 
macroeconomic drivers.

## Stage 0 — Top-Down Bias (start here, before any entry work)
GxT does NOT start at the entry. He builds bias top-down, Weekly -> Daily ->
intraday. Do this first:
*   **Map the Universal Sequence on Weekly then Daily:** classify the current
market cycle as one of the three models below (Internal->External,
External->Internal, or Order Pairing Ranges) on the HTF before dropping down.
The intraday setup must agree with this HTF narrative.
*   **Read the previous Weekly/Daily candle profile:** if the prior candle was an
expansion candle, anticipate a new phase (retracement or reversal) early in the
new week/day.
*   **Anticipate the open (fluid motion):** form the daily bias by predicting how
the candle opens. A bullish expansion day opens and immediately forms its low
with a small wick ("fluid motion"), leaving an unestablished high as the target.

## Stage 0.5 — Liquidity Mapping (where the trade is going)
Before selecting a level, classify all liquidity so you know what to target vs
what to reverse from:
*   **Relevant swings vs Failure swings:** *Relevant swings* are spaced-out,
significant structural extremes -> these are levels to REVERSE FROM. *Failure
swings* are clusters of close-proximity highs/lows -> these are the
"low-resistance" Draw on Liquidity (DOL) to TARGET.
*   **The trade runs from a relevant swing into a failure-swing DOL.** The
failure-swing cluster is the objective; the relevant swing (often holding a Fair
Value Gap) is where you enter the reversal.
*   Only after the DOL and the reversal level are mapped do you apply gap
selection (below) and the SMT filter.

## The Universal Sequence
The GxT Universal Sequence uses three rigid models to map price moving 
mechanically from Point A to Point B:
1. **Internal to External:** Price hits a Fair Value Gap (Internal Range 
Liquidity) and expands to a swing high or low (External Range Liquidity).
2. **External to Internal:** Price sweeps a swing high or low and reverses back 
into a Fair Value Gap within the current range.
3. **Order Pairing Ranges (Manipulation Range):** Price sweeps a major range low
and expands entirely across the range to target opposing failure swings.

*   **Gap selection by HTF open proximity:** To trade an expansion candle, 
strictly select gaps in close proximity to the opening price of the 
higher-timeframe candle. Deep gaps are avoided because retracing to them creates
a "large wick" on the higher-timeframe candle, violating the requirement that 
expansion candles must have small wicks.
*   **Candle profiles:** A valid expansion candle must open and immediately form
its low/high first with a small wick (a "fluid motion" or shallow retracement), 
leaving behind low resistance liquidity.
*   **4H PO3 if-then logic:** 4H profiles act as an "If-Then" sequence. If the 
2:00 AM (London) candle manipulates and forms the reversal, then 6:00 AM (NY AM)
continues. If 6:00 AM manipulates, 10:00 AM (NY PM) continues.
*   **8:30/9:30 driver pairing:** If the low of the day is put in *prior* to the
driver and price has already retraced into a key level, the driver must act as a
one-sided expansion away from that level. If no reversal is put in prior, the 
driver must hit the key level and create a V-shaped reversal.

## SMT / Asset Synchronisation
*   **Explicit Triads:**
    *   **Indices:** NQ, ES, YM (or RTY). *Rule: NQ and YM act as opposites in 
strength; ES is always the middle asset*.
    *   **Gold (Super Triad):** Gold, XAU/EUR, XAU/GBP.
    *   **Oil:** CL, RB, HO.
    *   **Execution weighting (confirmed in GxT live posts):** Gold (GC) is a
*primary* traded instrument, not a secondary one - it appears as often as NQ in
live executions, alongside YM, ES, and RTY. The Oil triad is taught but rarely
(if ever) executed - treat CL/RB/HO as theory, not a live setup to chase.
*   **Two-stage SMT confirmation:** A valid reversal requires a two-stage 
sequence to filter out fake divergences. Stage 1 is an SMT divergence exactly at
the key level (gap or swing point). Stage 2 is confirmed by either a Swing SMT 
(divergence between the confirmed swing lows) or a Precision Swing Point (PSP).
*   **PSP (Precision Swing Point) Definition:** A PSP is explicitly defined as a
strength-switch close divergence. It occurs when two correlated assets form 
swing points but print opposing candle closures (e.g., the leading asset closes 
bearish while the lagging asset closes bullish), visibly proving a transfer of 
institutional strength.
*   **SMT Fill:** The highest probability sequence. Occurs when a Universal 
Sequence drops into a Fair Value Gap, and an SMT divergence or PSP forms 
*inside* the gap.
*   **SMT Break (Failure to Manipulate):** If the leading asset hits a draw on 
liquidity and consolidates or displaces through it rather than printing a 
V-shaped reversal, the SMT is fake and will break. You must then actively trade 
the lagging asset *into* the fake SMT high/low to catch up.

## Entry / Invalidation Rules
*   **Entry Trigger:** Price must hit an aligned key level, form a Two-Stage 
SMT, and print a V-shaped reversal confirmed by a lower-timeframe Change in 
State of Delivery (CSD).
*   **Live-execution vocabulary (confirmed in GxT X posts):** In practice GxT
labels the structure as candle profiles - C2 (manipulation candle that sweeps and
closes back inside) then C3 (the continuation/expansion candle that is the actual
trade). The CSD trigger is taken as a *lower-timeframe order block (OB) entry*,
typically on a 3-minute or 30-minute chart (e.g. "30min psp -> 3min continuation
ob"). PSP itself can be two-stage ("2 stage PSP"). The 9:30 driver and the 10am
4H continuation (C3) are the most-cited live windows.
*   **Stop Placement:** Stops are placed structurally behind the initial CSD or 
the low of the gap that triggered the reversal.
*   **Moving the Goalpost (Invalidation):** Invalidation is strictly 
progressive. Once price hits a key level, creates a CSD, and expands away, it 
creates a new Fair Value Gap. Your invalidation point immediately moves to this 
new gap. If price disrespects this new gap, the continuation is dead.
*   **4H EQ Invalidation:** To trade an intraday 4H continuation, mark the 
Equilibrium (EQ/midpoint) of the previous 4H expansion candle's range. The wick 
of the new 4H candle must hold within the upper/lower half (EQ) of the previous 
candle to remain valid.

## What This Skill Must NOT Do
*   **DO NOT** trade a reversal candle with a large opposing wick for a 
continuation expansion; large wicks cap the range and do not support fluid 
expansion.
*   **DO NOT** long the leading asset that creates the double sweep in a 
Two-Stage SMT. You must long the lagging asset that creates the failure swing, 
as it is the one momentarily switching to the stronger asset.
*   **DO NOT** trust SMTs that form in close proximity to the draw on liquidity 
on the wrong side of the curve (e.g., a bullish SMT forming in a premium of the 
current range). These are low-probability "fake" SMTs that will likely break.
*   **DO NOT** trade a 10:00 AM reversal unless the 8:30/9:30 AM drivers hit a 
key level late and failed to reverse. 10:00 AM is structurally meant for 
continuation or trading counter-trend back into a capped daily range.

---
*Provenance & verification: generated from the GxT NotebookLM notebook
(`1a62aa84-ba79-495b-9aa6-eefb27cef761`) and fact-checked against it on
2026-05-31 - all Stage 0 / 0.5 / Universal Sequence / SMT / entry / invalidation
claims returned CONFIRMED (7/7 on the top-down + liquidity-mapping stages), each
backed by a direct source quote. Instrument weighting (GC as a primary) and the
C2/C3 + order-block entry vocabulary were cross-checked against GxT's live X
executions (`~/mnq_trading/data/gxt_execution_posts.csv`). Covers all 7 of GxT's
trade-discovery stages, top-down bias through progressive invalidation.*
