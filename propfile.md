# Prop Firm Profile — Top 5 Futures Prop Firms

> **Scope:** Futures prop firms (this project trades MNQ via the JUDGE strategy), ranked by size/relevance.
> **Data pulled:** 2026-05-31 from official sites + help centers (topstep.com, apextraderfunding.com, myfundedfutures.com, takeprofittrader.com, tradeify.co).
> **⚠️ Caveats:** Prop-firm pricing runs near-constant promos (often 50–90% off) — treat list prices as ceilings. Rules change frequently; verify the exact current parameter page before committing money. Some per-size figures were cross-referenced across the firm's own help-center articles where the marketing page was JS/anti-bot gated.

---

## At-a-glance comparison ($50K tier where applicable)

| Dimension | TopStep | Apex | MyFundedFutures | Take Profit Trader | Tradeify |
|---|---|---|---|---|---|
| Eval steps | 1 (Combine) | 1 | 1 (most plans) | 1 ("Test") | 1, or **instant** (Lightning) |
| $50K eval price | $49/mo (+$149 act) **or** $95/mo ($0 act) | ~$150–167/mo (heavy promos) | ~$80–165/mo (varies by plan) | ~$150/mo (flash sales) | one-time (Lightning $50K ~sale) |
| $50K profit target | $3,000 | $3,000 | $3,000 (most plans) | $3,000 | varies by plan |
| $50K drawdown | $2,000 **EOD trailing** | **$2,000 EOD** (EOD acct) *or* $2,500 **intraday** (legacy/Tradovate) — **pick the EOD account** | $2,000 **EOD trailing** | $2,000 **intraday trailing** (PRO); **EOD** on PRO+ live | **EOD** |
| Daily loss limit | Optional | **None** | **None** (most) | None | None |
| Consistency (eval) | Best day ≤ 50% of profit | **None** (EOD acct: *Not Applied*) | Best day ≤ 50% of target ($1,500) | None on Test | Growth: none / Select: 40% / Lightning: 20% |
| Consistency (funded) | Payout-path option (40%) | Payout rules (negative-day) | Plan-dependent (40% Starter) | **None** | **None once funded** |
| Min trading days | Winning-day req (no hard min) | **0** | Low (Rapid: 2-day pass) | **5** | Growth: 1 / Select: 3 |
| Profit split | 90% | 100% first $25K, then 90% | 80% (up to 90% Rapid) | 80% (PRO) / 90% (PRO+) | 90% (after $15K) |
| Min payout | — (up to $6K/request) | $500 | $500 (Flex) | no min, no max | varies |
| Payout cadence | 5 winning days ($150+) or 3 days @40% | every 8 trading days (≥5 @ $50+) | weekly/bi-weekly/**daily** (Rapid) | **daily, from day 1** (PRO) | **1-hour** payouts; daily or 5-day path |
| Platforms | TopstepX, NinjaTrader, Tradovate | Rithmic, Tradovate, NinjaTrader | Tradovate, NinjaTrader, Rithmic, TradingView | Tradovate + others | Tradovate, WealthCharts, Rithmic |

---

## ⚠️ Ground-Truth Validation (NotebookLM, official sources — 2026-05-31)

This profile was cross-checked against the firms' official help-center pages ingested into NotebookLM (notebook `cc2fa8a9`), queried **restricted to the official sources** (not this file) — a real validation, not circular. The grounded query found these corrections to my initial synthesis. **Where they conflict with the table above, trust these:**

- **Take Profit Trader — eval consistency:** table said *"None on Test"* → **WRONG.** Official: a **soft 50%** rule (biggest day must stay <50% of target; it doesn't fail you, but you can't pass until smaller days dilute it).
- **Take Profit Trader — eval drawdown TYPE:** official FAQ says the **test/eval is EOD**; intraday applies to standard **PRO**; **EOD** again on **PRO+ live**. (My "intraday-trailing eval" was wrong.)
- **MyFundedFutures — drawdown TYPE is stage-dependent:** **EOD during evaluation, INTRADAY trailing once Sim-Funded** (Rapid: trails the high-water mark by $2,000, locks at $100). My blanket "EOD trailing" was only half right.
- **TopStep — payout cap:** Standard path max **$5,000**/request; Consistency path max **$6,000** (I listed only $6,000). XFA split confirmed **90/10**.
- **TopStep — Daily Loss Limit amounts:** optional DLL = **$1,000 / $2,000 / $3,000** for $50K/$100K/$150K (a "Responsible Trading Discount" at checkout).
- **TopStep — MLL $ amounts ($2,000/$3,000/$4,500):** from web search, **NOT confirmed** by the ingested official pages (the Combine-parameters page lists only contract sizes). Verify on TopStep before relying.
- **Tradeify — split:** keep **100% of first $15,000, then 90%** (I wrote "90% after $15K" — same threshold, but 100% applies below it).
- **Apex — NOW VERIFIED (WebBridge, 2026-06-01):** the Cloudflare wall was bypassed via the logged-in real browser. **Key correction: Apex offers a distinct EOD account family** (EOD Evaluation + EOD Performance), not just the intraday/legacy accounts the earlier synthesis assumed. Verified from apextraderfunding.com help-center:
  - **EOD Evaluation (50K):** target **$3,000**, Max Drawdown **$2,000 EOD** (calc'd once daily at close, then fixed/enforced next session), DLL **$1,000**, Max contracts **6**, 30-day access, **Consistency: Not Applied**, Scaling: Not Applied, **0 min trading days** (can pass in 1 day), 7 days to activate PA.
  - **EOD Performance / funded (50K):** Max Drawdown **$2,000 EOD** (threshold fixed at prior close, unrealized PnL checked against it — does **not** trail intraday), Max contracts **4**, tier-based scaling + DLL, **100% payout split** "upon meeting payout eligibility requirements."
  - **Still to confirm:** the specific payout-eligibility consistency threshold (Apex's historical "30%-largest-day" / safety-net rule) is no longer published on the EOD rules/PA pages — confirm in-dashboard at payout time. This matters because our models are NQ-concentrated (73–77%).

**Verdict:** drawdown-TYPE and consistency are the error-prone fields (they shift by stage/account-tier) — that's where my synthesis missed. The rest of the table held up. The verified facts are encoded in the installed **`propfirm-selector`** skill.

---

## 1. TopStep — `topstep.com`
**Positioning:** the legacy/industry-standard futures prop firm; strongest brand, strictest combine.

- **Account sizes:** $50K, $100K, $150K.
- **Two pricing paths:** **Standard** $49/mo + **$149** activation on pass; **No-Activation** $95/mo + **$0** activation.
- **Profit targets:** $50K → **$3,000** | $100K → **$6,000** | $150K → **$9,000**.
- **Max Loss Limit (trailing, set at END OF DAY):** $50K → **$2,000** | $100K → **$3,000** | $150K → **$4,500**. `MLL = (account high) − (max drawdown)`, recalculated EOD; once you bank enough, it locks at starting balance.
- **Max contracts:** $50K → 5 (50 micros) | $100K → 10 (100) | $150K → 15 (150).
- **Daily Loss Limit:** optional, self-set.
- **Consistency target (Combine):** single best winning day must be ≤ **50%** of total profit; exceed it and your profit target rises.
- **Funded (Express/Live):** payout = keep **90%**, request up to **$6,000**/payout; Standard path needs **5 winning days** of ≥$150 (non-consecutive) + net profit > $0; Consistency path needs **3 days @ 40%** consistency. *Per project memory: TopStep's funded/XFA stage has NO consistency rule — consistency lives in the Combine only.*
- **Rules:** CME futures only; flat by session close; news allowed.

## 2. Apex Trader Funding — `apextraderfunding.com`
**Positioning:** highest volume / most account sizes; aggressive promos. **Offers BOTH an EOD account family and an intraday/legacy family — choose EOD for hold-through strategies.**

### EOD account family (VERIFIED via WebBridge 2026-06-01 — our recommended Apex path)
- **EOD Evaluation (50K):** target **$3,000** · Max Drawdown **$2,000 EOD** (calc'd once daily at close, fixed & enforced next session — no intraday trail) · DLL **$1,000** · Max contracts **6** · 30-day access · **Consistency: Not Applied** · Scaling: Not Applied · **0 min trading days** · 7 days to activate PA after passing.
- **EOD Performance / funded (50K):** Max Drawdown **$2,000 EOD** (threshold fixed at prior close; unrealized PnL checked against it, does **not** trail intraday) · Max contracts **4** · tier-based scaling + DLL · **100% payout split** upon meeting payout-eligibility requirements.
- **Why this matters for us:** EOD drawdown + **no consistency rule on the eval** = structurally ideal for both the V-shape core and (uniquely) the lossy/NQ-concentrated Asia 1H FVG model. ⚠️ Confirm the payout-eligibility consistency threshold in-dashboard (the historical 30%-largest-day rule isn't published on the current rules pages).

### Intraday / legacy family (the older default — avoid for hold-through entries)
- **Account sizes & contracts:** 25K (4) · 50K (10) · 75K (12) · 100K (14) · 150K (17) · 250K (27) · 300K static (35). *(full-size minis)*
- **Profit targets:** 25K **$1,500** · 50K **$3,000** · 75K **$4,250** · 100K **$6,000** · 150K **$9,000** · 250K **$15,000** · 300K **$20,000**.
- **Trailing drawdown:** 25K **$1,500** · 50K **$2,500** · 75K **$2,750** · 100K **$3,000** · 150K **$5,000** · 250K **$6,500** · 300K **$7,500 (static)**. **Intraday trailing** — on **Tradovate it trails forever**; on **Rithmic it locks** at the "safety net" (`balance + drawdown + $100`, e.g. $50K → $52,600).
- **Eval price:** list ~$147–$657/mo by size, but **near-permanent promos** drop it to ~$17–$147/mo. **PA activation:** one-time 25K $150 / 50K $160 / 100K $240 / 150K $280 / 250K $320 / 300K $360 — *or* ~$85/mo.
- **Min trading days:** **0** (pass the moment target is hit; 30-day access window).
- **Daily loss limit / consistency (eval):** **none**.
- **Payout:** **100% of first $25K** then 90%; min **$500**; ≥ **8 trading days** between requests with ≥5 days of $50+ profit; first 5 payouts gated, then 100%. Negative-day/"30%" risk rules apply on the funded (PA) side.
- **Rules:** CME futures; flat overnight; news generally allowed.

## 3. MyFundedFutures (MFFU) — `myfundedfutures.com`
**Positioning:** most plan variety; fast/daily payouts; **the firm we already hold (Builder 50K)**.

- **Plan lineup (2026):** Starter (~$97/mo), Starter Plus, Expert, Pro, **Rapid** (daily payouts, 2-day pass, 90/10, $0 activation), **Flex** (no buffer, performance payouts), **Builder** (custom Max-Loss-Limit at checkout), plus Core/Scale marketing tiers.
- **Typical eval params:** $50K → **$3,000** target, **$2,000 EOD trailing** drawdown, **no daily loss limit**. **Consistency:** best day ≤ **50%** of target (= **$1,500** on $50K).
- **Profit split:** **80%** (Starter), up to **90%** (Rapid).
- **Payouts:** Starter — 5 winning days ($100–300/day min) @40% consistency, weekly; Expert — bi-weekly, no withdrawal restrictions; **Rapid** — daily, buffers $2,100 (50K) / $3,100 (100K) / $4,600 (150K), no consistency, $500 min after buffer; **Flex** — 5 winning days ($150+), no buffer, cap 50% of net up to $2,000 (50K).
- **Reset fees:** 50K $157 / 100K $267 / 150K $347.
- **Builder 50K (our plan, per memory):** $1,000 daily soft-pause, $2,000 max EOD trailing DD (hard breach), contract cap **4 minis OR 40 micros** (combined), full GC banned (MGC only), 80/20 split, $2,100 buffer, $2,000 max/cycle, 5 payouts → live.
- **Platforms:** Tradovate, NinjaTrader, Rithmic, TradingView.

## 4. Take Profit Trader (TPT) — `takeprofittrader.com`
**Positioning:** best-in-class payout policy (daily, day-1, no windows/min days for withdrawal).

- **Account sizes:** $25K, $50K, $75K, $100K, $150K (one-step "Test").
- **Profit targets (standard):** 25K $1,500 · 50K **$3,000** · 75K $4,500 · 100K $6,000 · 150K $9,000.
- **Drawdown:** **intraday trailing** in the eval & PRO; **PRO+ live accounts (since Jun 30) use EOD drawdown**.
- **Min trading days:** **5** to pass.
- **Profit split / payout:** **PRO 80%** with a buffer (withdraw anything above buffer), **PRO+ 90%** no buffer. Withdraw **from day 1, then daily**; **no minimum profitable days, no payout windows, no payout delays, no max withdrawal.**
- **Limits:** max **5** PRO/PRO+ accounts; **no news trading on specific major events**; flat before **5 PM EST** close.
- **Pricing:** monthly subscription with frequent flash sales (e.g. "NOFEE50").

## 5. Tradeify — `tradeify.co`
**Positioning:** newer, fast-growing; EOD drawdown across the board; instant-funding option.

- **Account sizes:** 25K, 50K, 100K, 150K.
- **Plans:** **Growth** (1-day pass, EOD DD, no eval consistency, 40% reset fee) · **Select** (3-day pass, 40% eval consistency) · **Lightning Funded** (instant, no eval, 20% consistency that relaxes per payout; $50K/150K on sale, e.g. 150K **$251** from $359).
- **Eval example (150K):** target **$9,000**, EOD DD **$4,500**.
- **Funded paths:** **Daily** (activation $1,500, payout cap $1,250, EOD DD $2,500, no consistency) · **Flex/5-day** (activation $4,000, no payout cap, EOD DD $3,000, no consistency).
- **Drawdown:** **EOD** throughout. **No consistency once funded.**
- **Profit split:** **90%** after a **$15K** threshold; payouts in **~1 hour**.
- **Platforms:** Tradovate, WealthCharts, Rithmic. **News:** free rein (volatility warnings). Max **5** accounts.

---

## Deeper understanding — fit for *our* MNQ / JUDGE strategy

Our two locked configs drive the firm choice:
- **62T PERFECT** (combine config): WR 100%, **DD $0**, Net $289 raw — designed to satisfy a strict combine.
- **Funded-stage configs** (87T MAX-PNL / 209T Asia): carry real losses + drawdown (live DD up to ~$473) — these need a funded stage that **tolerates losses and has NO consistency rule**.

**Two distinct requirements → possibly two different firms:**

### A. The evaluation/combine — what matters: drawdown TYPE + cost + consistency
- **EOD (end-of-day) trailing >> intraday trailing** for us. Our V-shape entries sometimes sit through adverse excursion before resolving; an **intraday** trailing stop (Apex's *legacy/Tradovate* accounts, TPT PRO) can clip a trade that the EOD model would survive. **TopStep, MFFU (eval), Tradeify, and Apex's EOD account family all use EOD** drawdown → structurally friendlier. (Apex EOD verified 2026-06-01 — it is NOT intraday-only.)
- **Consistency rule** is the real combine hazard, not DD (we're $0-DD). 62T PERFECT's P&L concentration (NQ alone ≈ 77% of profit) risks tripping a **best-day-≤50%** rule. **Apex (no consistency) and Tradeify Growth (no eval consistency)** sidestep this entirely; **TopStep/MFFU 50%** rules require spreading wins (the documented "big early win locks consistency for months" gotcha).
- **Cost:** Apex (promo ~$17–147) and MFFU Starter (~$80–97) are cheapest; TopStep $49/mo Standard is competitive but adds $149 on pass.

### B. The funded stage — what matters: NO consistency + loss tolerance + payout speed
- Our funded configs **lose trades**, so a funded stage with a **consistency rule is disqualifying** for steady withdrawals.
- **Best funded fits:** **TopStep** (no consistency in funded/XFA per memory), **Take Profit Trader** (no consistency, **daily day-1 payouts, no windows**), **Tradeify** (no consistency once funded, 1-hour payouts), and **Apex EOD PA** (EOD drawdown, no account-level consistency shown, **100% split**). ⚠️ Apex's *payout-eligibility* consistency threshold (historical 30%-largest-day rule) is unconfirmed on current pages — verify before relying for the NQ-concentrated models.
- **Payout velocity:** TPT and Tradeify/MFFU-Rapid (daily/1-hour) > Apex (8-day gaps) for cash-flow.

### Ranking for this strategy (combine → funded)
1. **TopStep** — EOD DD + clean funded (no consistency); the combine consistency rule is the only friction, manageable with 62T PERFECT spread. *(Already the active go-live candidate.)*
2. **MyFundedFutures** — EOD DD, cheap, daily payouts (Rapid), and **we already hold a Builder 50K**; consistency 50% on eval is the watch-item.
3. **Take Profit Trader** — unbeatable payout policy + EOD on PRO+; **5-day min + intraday-trailing eval** are the cons.
4. **Tradeify** — all-EOD + instant-funding + 1-hour payouts; newest/least track record → higher counterparty risk.
5. **Apex** — cheapest + most sizes + **no eval consistency + a verified EOD account family (EOD DD, 100% funded split)**. Re-rated UP after WebBridge verification (2026-06-01): the old "intraday-only → last" placement was wrong. Using the **EOD account**, Apex is a legitimate fit for *both* models; the only open risk is the unconfirmed payout-eligibility consistency rule. (Still #5 mainly on track-record/payout-cadence, not structure.)

**Net recommendation:** keep **TopStep** for the combine (decision pending: Standard $49+$149 vs No-Activation $95/mo) and lean on **EOD-drawdown firms** generally — which now explicitly **includes Apex's EOD account family** (TopStep / MFFU-eval / Tradeify / **Apex-EOD**). Avoid intraday-trailing accounts (Apex *legacy/Tradovate*, TPT PRO, MFFU *funded*) for hold-through entries — especially the positional **Asia 1H FVG** model, which is **only safe on an EOD funded account**. Re-confirm live pricing/promos before purchase.

---

## Sources (official, pulled 2026-05-31)
- TopStep: [Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters), [Pricing](https://help.topstep.com/en/articles/9208217-topstep-pricing), [No Activation Fee](https://www.topstep.com/no-activation-fee), [Consistency Target](https://help.topstep.com/en/articles/8284208-what-is-the-consistency-target), [Express Funded Parameters](https://help.topstep.com/en/articles/8284215-express-funded-account-parameters)
- Apex (EOD family verified via WebBridge 2026-06-01): [All Apex Trading Account Rules](https://apextraderfunding.com/help-center/legacy-helpful-items/all-apex-trading-account-rules/), [EOD Evaluation Rules](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-evaluations), [EOD Performance (PA) Rules](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa), [Intraday Evaluations](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-evaluations), [Payout Method Information](https://apextraderfunding.com/help-center/additional-helpful-items/payout-method-information/)
- MyFundedFutures: [Understanding Evaluation Parameters](https://help.myfundedfutures.com/en/articles/8528339-understanding-evaluation-parameters-at-myfunded-futures), [Builder Plan](https://help.myfundedfutures.com/en/articles/14290805-builder-plan-a-comprehensive-guide), [Rapid Plan](https://myfundedfutures.com/plans/rapid), [Flex Plan](https://myfundedfutures.com/plans/flex), [Payout Policy](https://help.myfundedfutures.com/en/articles/13745661-payout-policy-overview-best-and-fastest-prop-firm-payouts)
- Take Profit Trader: [FAQs](https://try.takeprofittrader.com/TPT-FAQs-nf50-0526), [Playbook](https://takeprofittrader.com/playbook), [Terms](https://takeprofittrader.com/terms)
- Tradeify: [tradeify.co](https://tradeify.co/)
