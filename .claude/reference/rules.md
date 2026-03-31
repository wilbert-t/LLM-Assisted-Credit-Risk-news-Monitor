# Alert Rules, Rate Limits & Keywords

Load this file when working on: alert logic, credit-relevance classifier, event tagging, API scheduling.
Source of truth for these values is `src/utils/constants.py` — this file is a human-readable mirror.

---

## Severity Levels

Ordered low → critical:

| Level    | Meaning                                    |
|----------|--------------------------------------------|
| low      | Routine negative event, monitoring only    |
| medium   | Elevated concern, review recommended       |
| high     | Significant credit risk, action likely     |
| critical | Immediate default/bankruptcy risk          |

---

## Event Types → Default Severity

| Event Type         | Severity | Notes                               |
|--------------------|----------|-------------------------------------|
| default            | critical | Missed payment, payment default     |
| bankruptcy         | critical | Chapter 11/7, insolvency            |
| fraud              | critical | Accounting fraud, embezzlement      |
| liquidity_crisis   | high     | Cash crunch, funding pressure       |
| covenant_breach    | high     | Technical default, waiver request   |
| downgrade          | high     | Rating cut, negative outlook        |
| rating_watch       | medium   | Review for downgrade                |
| restructuring      | medium   | Debt swap, haircut, bond exchange   |
| regulatory_action  | medium   | SEC/DOJ investigation, fines        |
| lawsuit            | medium   | Class action, litigation            |
| earnings_miss      | low      | Profit warning, guidance cut        |
| merger_acquisition | low      | Takeover, buyout, LBO               |
| management_change  | low      | CEO resignation, board shake-up     |
| debt_issuance      | low      | New bond, term loan, credit facility|
| layoffs            | low      | Workforce reduction, redundancies   |

---

## Alert Triggering Logic

An alert is created when ALL of the following are true:
1. `processed_articles.is_credit_relevant = TRUE`
2. `processed_articles.event_types` contains ≥ 1 event type
3. No duplicate alert for the same (obligor, event_type) within dedup window (default 24h)

Severity of the alert = highest severity among matched event types.

---

## Credit Relevance Criteria

An article is marked `is_credit_relevant = TRUE` when:
- `cleaned_text` contains ≥ 1 keyword from the KEYWORDS dict (case-insensitive)
- AND `len(cleaned_text) >= 30` (MIN_TEXT_LENGTH in `src/processors/cleaner.py`)

Bonus signal (higher weight in future scoring):
- `source` matches HIGH_SIGNAL_SOURCES: Bloomberg, Reuters, Financial Times, Wall Street Journal, Moody's, S&P Global, Fitch Ratings, The Economist, CNBC, MarketWatch

---

## Keywords by Event Type

### default
failed to pay, missed payment, payment default, debt default, sovereign default, cross-default

### bankruptcy
bankruptcy, chapter 11, chapter 7, insolvency, insolvent, receivership, administration, liquidation, wound up

### downgrade
downgrade, downgraded, rating cut, credit rating lowered, outlook negative, placed on negative watch

### restructuring
debt restructuring, restructure, debt swap, haircut, bond exchange, liability management, distressed exchange

### rating_watch
credit watch, rating watch, review for downgrade, negative outlook, ratings under review

### covenant_breach
covenant breach, covenant violation, breached covenant, waiver request, technical default

### liquidity_crisis
liquidity crisis, cash crunch, funding pressure, cash flow problem, burning through cash, liquidity concern, short of cash

### fraud
fraud, accounting fraud, financial fraud, misrepresentation, embezzlement, falsified, fictitious, ponzi

### regulatory_action
regulatory action, fined, penalty, enforcement action, cease and desist, regulatory probe, under investigation, SEC charges, DOJ investigation

### merger_acquisition
merger, acquisition, takeover, buyout, acquired by, merging with, deal agreed, LBO, leveraged buyout

### management_change
CEO resigned, CFO departure, management change, stepping down, board shake-up, executive departure, leadership change

### earnings_miss
missed earnings, earnings miss, below expectations, profit warning, revenue shortfall, guidance cut, lowered forecast

### debt_issuance
bond issuance, new debt, credit facility, raised debt, term loan, high-yield bond, junk bond issued

### layoffs
layoffs, job cuts, redundancies, workforce reduction, downsizing, headcount reduction, retrenchment

### lawsuit
lawsuit, sued, legal action, class action, litigation, filed suit, court ruling, damages awarded

---

## API Rate Limits

### NewsAPI (free/developer tier)
- **Requests/day:** 1,000
- **Recommended delay:** 1 second between requests (`scripts/collect_news_all.py`)
- **Results per query:** max 100 (page size 20, max page 5)
- **Content truncation:** `content` field cut at ~200 chars with `[+N chars]` marker
- **Fallback:** use `description` field when `content` is truncated-only

### GDELT (planned — Phase 4)
- No API key required
- No official rate limit — be polite: 1–2 req/sec max
- Full article text available via linked URLs
