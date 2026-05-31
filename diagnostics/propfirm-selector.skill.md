---
name: propfirm-selector
description: Use when comparing futures prop firms to recommend the best fit for a specific trading strategy or trader preference based on verified parameters.
---

# Futures Prop Firm Selector

## When to Use
Use this framework to evaluate and select a futures proprietary trading firm 
based on verified account parameters, trading rules, and payout policies. It is 
designed to match specific trading strategies (like high-win-rate, lossy, or 
V-shape entries) with the structural rules of various prop firms.

## Decision Framework
These are the dimensions that actually decide a firm's fit for a strategy, in 
priority order:

*   **(a) Drawdown TYPE (End-of-day vs. Intraday trailing vs. Static):** This 
defines how losses are measured against account highs. End-of-Day (EOD) trailing
is friendlier because it ignores adverse intraday excursions, whereas intraday 
trailing can prematurely clip a trade based on unrealized profit peaks.
*   **(b) Consistency rule (Eval AND Funded):** Limits the profit you can make 
in a single day (e.g., best day cannot exceed 50% of the target). This 
penalizes strategies with highly concentrated winning days and forces traders to
spread out their profits.
*   **(c) Min trading days:** Dictates the absolute fastest time a trader can 
pass an evaluation and reach funded status, ranging from instant (0 days) to 5+ 
days.
*   **(d) Cost & promos:** Prop firms run near-constant flash sales and 
promotions, making the base "list price" an inaccurate metric for actual capital
outlay.
*   **(e) Payout speed/split/buffer:** Determines cash flow. Key factors include
payout frequency (e.g., daily vs. weekly), the profit split (usually 80-90% to 
the trader), and whether a specific profit "buffer" must be maintained in the 
account before withdrawals are permitted.

## Ground-Truth Firm Facts

### TopStep
*   **$50K Target:** $3,000.
*   **Drawdown Amount & Type:** $2,000 Maximum Loss Limit, End of Day (EOD) 
trailing.
*   **Daily Loss Limit:** Optional limit of $1,000 for the $50K account. 
*   **Eval Consistency %:** Best day must remain at or below 50% of your total 
profit target.
*   **Min Days:** No hard minimum stated for eval, but passing is tied to a 
winning-day requirement. Standard funded path requires 5 winning days of 
$150+.
*   **Split:** 90% to the trader.
*   **Payout:** Maximum of 50% of your balance per request, capped at $5,000 
(Standard path) or $6,000 (Consistency path).

### Apex Trader Funding
*Verified via WebBridge (logged-in browser) 2026-06-01 — the Cloudflare wall was bypassed. **Apex offers TWO families: an EOD account family AND an intraday/legacy family.** For hold-through strategies, choose the EOD account.*
*   **$50K Target:** $3,000 (both families).
*   **Drawdown Amount & Type:** **EOD family = $2,000 EOD** (threshold calc'd once daily at close, then fixed — does NOT trail intraday). Legacy/Tradovate family = ~$2,500 **intraday trailing**. **Pick the EOD account.**
*   **Daily Loss Limit:** $1,000 (EOD Eval, 50K); tier-based DLL on the funded PA.
*   **Eval Consistency %:** **EOD Evaluation = Not Applied** (no consistency rule). This is what makes Apex EOD uniquely viable for lossy / profit-concentrated strategies.
*   **Min Days:** **0** — may pass in a single day; 30-day access; 7 days to activate the PA after passing.
*   **Max Contracts (50K):** 6 (EOD Eval) / 4 (EOD PA funded).
*   **Split:** **100%** payout split on the funded EOD PA (upon meeting payout-eligibility requirements).
*   **Payout — OPEN ITEM:** the specific payout-eligibility consistency threshold (Apex's historical "30%-largest-day" / safety-net rule) is no longer published on the EOD rules/PA pages — **confirm in-dashboard at payout time** before relying on it for an NQ-concentrated account.

### MyFundedFutures (MFFU)
*   **$50K Target:** $3,000 (Rapid Plan).
*   **Drawdown Amount & Type:** $2,000. Type is **EOD** during the 
Evaluation stage and **Intraday trailing** during the Sim Funded stage 
(locks at $100).
*   **Daily Loss Limit:** None (Rapid Plan).
*   **Eval Consistency %:** 50% during the Evaluation stage only. No 
consistency rule once in Sim Funded.
*   **Min Days:** 2 Days (Evaluation).
*   **Split:** 90% to the trader.
*   **Payout:** Daily frequency (every 24 hours), $500 minimum request, requires
building a $2,100 buffer before withdrawing.

### Take Profit Trader
*   **$50K Target:** $3,000.
*   **Drawdown Amount & Type:** End of Day (EOD) in the evaluation test, 
Intraday in the PRO account, and EOD in the PRO+ live-market account.
*   **Daily Loss Limit:** None in the test.
*   **Eval Consistency %:** 50% in the test. This is a soft rule; it does not 
fail you, but you must keep trading until your biggest day is under 50%. No
consistency rule in PRO.
*   **Min Days:** 5 days.
*   **Split:** 80% in PRO, 90% in PRO+.
*   **Payout:** Withdraw from day-one and daily, with no payout windows, delayed
rules, or maximum withdrawal limits.

### Tradeify
*   **$50K Target:** Not explicitly stated in the source text (varies by plan).
*   **Drawdown Amount & Type:** Amount not explicitly stated for 50K (it is 
$1,000 for 25K). Type is End of Day (EOD) trailing.
*   **Daily Loss Limit:** None during the evaluation or Flex funded path. 
The Daily funded path has a $500 limit.
*   **Eval Consistency %:** 40% on Select, None on Growth, 20% on Lightning 
Funded. There is no consistency rule once funded.
*   **Min Days:** 1 day (Growth), 3 days (Select), or Instant Funding 
(Lightning).
*   **Split:** Keep 100% of the first $15,000, then 90%.
*   **Payout:** 60-minute automated payouts; payout frequency paths are Daily or
5-days.

## Pitfalls (What NOT to assume)
*   **Drawdown type can shift between stages:** A firm might use a forgiving EOD
drawdown in the evaluation to attract traders, but switch to a strict intraday 
trailing drawdown in the funded stage. For example, MyFundedFutures Rapid uses 
EOD for eval but intraday trailing for the funded stage. Take Profit 
Trader uses EOD for the test, switches to Intraday for PRO, and reverts to EOD 
for PRO+.
*   **'No consistency' can be misleading:** Take Profit Trader claims a soft 50%
consistency rule in evaluations—violating it won't fail your account, but you 
are barred from passing until you generate enough smaller profits to dilute your
biggest day below 50%.
*   **List prices ignore promos:** Prop firm pricing list prices are essentially
marketing anchors. Actual costs are dictated by near-constant discounts and 
flash sales (e.g., Tradeify's 40% off code, TPT sales, etc.).
