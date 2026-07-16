# TTFM Clone — Phase-1 ground-truth parity gate (Task 7 Step 3)

**Date:** 2026-07-16 · **Video:** "Fractal Model [Pro+] TradingView Indicator Breakdown by Toodegrees and TTrades" (`-n31VuAijzo`, uploaded 2026-01-01) · **Frames:** `/tmp/ttfm_frames/` (1 per 20s, 24 frames)

## Verdict: PASS with findings (no detection-rule mismatch; settings/ladder deltas fixed or queued)

## What was compared

1. **Element vocabulary + state semantics** (video f_004/f_005/f_010/f_018 vs our MNQ1! 5m replay at 2025-12-15): both render C2/C3/C4 text labels at closure candles, ★ ideal flag, sweep line under the C1 extreme, CISD level (dashed pending → solid confirmed), candle-EQ line, T-Spot zone on the expansion-side half drawn across the next HTF period, HTF candle panel right of price with open/vertical lines, info table bottom-right (Asset/TF/Pairing/countdown/Bias/Filter). Video overlay narration ("CANDLE 3 — (EXPANSION PHASE) EXPANDS AWAY FROM THE CISD", f_004) matches our C3 semantics.
2. **Same-date replication**: attempted NQ/MNQ 5m. f_005's chart (NQ1! 5m, low ≈25,235, day "15") is NOT 2025-12-15 (MNQ traded ≈26,100 then — verified in replay); most likely 2025-10-15, which is **beyond TV's 5m bar-replay depth** (replay would not advance past the anchor at 2025-10-14 23:59). f_018's 4h chart (pinned Mon 24 Nov '25 via hover) uses a **Custom 4h↔Daily pairing** (f_014 shows Custom Fractal "1 hour - 1 day" style settings); programmatic input override on our study returned `updated_inputs: {}` (tv CLI limitation), so the pinned-date element-for-element table is **deferred to Task 14 round 2** (use the settings dialog UI or a recent-date formation instead).

## Parity findings (real deltas vs the real TTFM panel, from f_006/f_014/f_018)

| # | Finding | Action |
|---|---|---|
| 1 | Real pairing dropdown has **1s-1m, 15s-5m, 1m-15m** rungs; ours started at 3m-30m | **FIXED this commit** — ladder + presets extended (1→15 wired; 1S/15S guarded) |
| 2 | Real `History` default = **1** (f_014); ours was 0 | **FIXED this commit** |
| 3 | Real STDV defaults: Type **Wick**, levels string begins **"-1, -1.5, -2, …"** (f_018; plan said −1, −2, −2.5, −4, −4.5 from the TV script page) | Queued into **Task 8** — default `-1, -1.5, -2, -2.5, -4, -4.5` |
| 4 | Real Formation Liquidity default style: **Dotted, width 1, black** (f_018); plan snippet used solid orange | Queued into **Task 9** |
| 5 | Real Time Filter defaults: **02:00–05:00 / 08:00–11:00 / 13:30–16:15**, Apply below **1 hour**, optional **Custom Timezone UTC±h:m** (f_018); plan example used 0930-1100 NY | Queued into **Task 10** |
| 6 | Real HTF Candles count default = **4**, size Small, Hide? toggle (f_014) | Matches ours (no change) |
| 7 | Real info table: Show Info **Table/Small**, **Border?** unchecked, Bottom-Right (f_018) | Matches ours (no change) |
| 8 | Real C2/C3/C4 labels are small plain gray text; ours are filled label boxes (state colors gray/orange/red per script page `XdwK9qQQ` are semantics, not style) | Style-only; revisit in Task 14 if screen parity wanted |

## No-mismatch confirmations

- C2 = sweep + close back inside C1 range (labels sit on closure candles in all video frames, incl. wick-sweep-only candles NOT labeled).
- T-Spot zone drawn on expansion-side half of C2 range, across the next HTF period (f_004/f_005 zones match our placement rule).
- CISD dashed→solid lifecycle visible in f_010 (dotted level) consistent with ours.
- Failed formations stop projecting (red-state cease rule) — consistent with video (no stale zones on failed structures).

## Artifacts

- Our replay render: `tradingview-mcp-jackson/screenshots/tv_chart_2026-07-15T13-50-08-943Z.png` (MNQ1! 5m @ 2025-12-15 ~06:38 ET)
- Video frames: f_004 (C3 narration), f_005 (NQ 5m formation), f_006 (pairing dropdown), f_010 (1m model), f_014 (general settings), f_018 (projections/liquidity/time-filter/info-table panel + Nov 24 '25 pin)

---

# Round 2 — Phase-2 QA + parity (Task 14, 2026-07-16)

## Verdict: PASS with one open item (replay-based pixel parity remains user-assisted follow-up)

## What was verified

1. **Full build renders on the live chart** (MNQ1! 5m realtime): after Tasks 8-13 landed, the on-chart study hit a "Can't parse pine" RUNTIME error (stale on-chart instance after many update-on-chart cycles — root-caused via the chart model's study status, not visible in `tv state`). Fixed by remove + fresh add. Post-fix the study computes live: info table reads Asset/TF/Pairing 60↔5/countdown/Bias/Filter via `tv data tables`.
2. **Phase-2 element vocabulary vs the real TTFM** (video frames f_005/f_010/f_018): STDV dotted projection levels with small labels (ours: dotted, input color, labels -1/-1.5/... = matches video's left-side level stack); projection defaults now Wick + "-1,-1.5,-2,-2.5,-4,-4.5" (panel-confirmed prefix); formation liquidity dotted black (panel-confirmed); time filters 02-05/08-11/13:30-16:15 apply-below-1H (panel-confirmed); Auto Bias 1/2 options + info-table arrow; SMT dashed divergence lines + label (video's SMT module semantics).
3. **Non-repaint evidence**: (a) 2026-07-15 bar-replay session at 2025-12-15 (5m): formations printed on closed HTF candles during forward stepping and did not move (screenshot tv_chart_2026-07-15T13-50-08-943Z.png); (b) independent reviewer verified the SMT `request.security` idiom is aligned non-repainting ([1]/[2]+lookahead_on, chart-side vs pair-side same periods); (c) all draw calls fire once on HTF closure from confirmed candles (reviewed per task).
4. **Replay QA limitation (open)**: on 2026-07-16 TV's bar-replay pane would not swap to the replay dataset (quote follows replay, candles stay realtime; "Continue/Start new" session dialog implicated; 4 clean attempts). The full ≥5-formation bar-replay sweep incl. one red/orange/ideal is deferred — run manually or next session (recipe: replay 2025-12-15 5m, autoplay 50ms, watch labels persist).

## Runtime-error lesson (banked)
After many `tv pine compile` update-on-chart cycles, the on-chart study instance can silently enter a "Can't parse pine" runtime-error state (zero graphics, no legend error via CLI state). Detection: `tv data tables --filter <name>` returns study_count 0 while the study is listed in `tv state`; confirm via chart-model status eval. Fix: `tv indicator remove --id <id>` then recompile → "Add to chart".
