# Week 5: LLM Summarization & Alerts — Design Spec

**Date:** 2026-04-02  
**Phase:** Phase 5 (Alerts + Summarization)  
**Duration:** Days 29-35  
**Status:** Design approved, ready for implementation

---

## Executive Summary

Week 5 adds **RAG-enhanced alert generation** to the credit risk pipeline. The system retrieves relevant articles via semantic search, generates credit risk summaries using Groq API, and triggers alerts based on both rule-based signals and LLM insights. Alerts are deduplicated within 24-hour windows, cached to stay under rate limits, and exposed via FastAPI endpoints.

**Key Design Decision:** Alerts fire based on **risk narratives, not just keyword matching**. The summarizer produces actionable credit context, enabling smarter decisions about which signals matter.

---

## Architecture Overview

```
News Articles (embeddings in pgvector)
         ↓
   ArticleRetriever (top-10 semantic search by obligor)
         ↓
  ObligorSummarizer (Groq API + PostgreSQL cache)
         ↓
  AlertRulesEngine (evaluate credit risk signals + summary)
         ↓
  AlertGenerator (create alerts, dedup by rule + 24h window)
         ↓
  APScheduler (4h/6h cycles) + FastAPI endpoints
```

**Rate Limit Budget:**
- Groq llama-3.3-70b: 1,000 requests/day
- Estimated usage: ~250 calls/day (50 obligors, split 25 high/25 normal)
- Buffer: 4x under limit ✅

---

## 1. Summarizer Module (`src/rag/summarizer.py`)

### Purpose
Retrieve top articles for an obligor, generate credit risk narratives via Groq, cache results to minimize API calls.

### Database Schema

New table `summaries`:
```sql
CREATE TABLE summaries (
    id SERIAL PRIMARY KEY,
    obligor_id INT NOT NULL REFERENCES obligors(id) ON DELETE CASCADE,
    cache_date DATE NOT NULL,
    article_hash VARCHAR(64) NOT NULL,  -- hash of top-K article IDs
    summary_json JSON NOT NULL,         -- {summary, key_events, risk_level, concerns, positive_factors, confidence}
    model_used VARCHAR(50),             -- "llama-3.3-70b-versatile" | "llama-3.1-8b-instant"
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT uq_summaries_obligor_date_hash UNIQUE(obligor_id, cache_date, article_hash)
);
```

### Key Functions

#### `has_new_articles_since(obligor_id: int, last_summary_ts: datetime) -> bool`

**Purpose:** Check if new articles have been published since the last summary was generated.

**Logic:**
```python
def has_new_articles_since(obligor_id: int, last_summary_ts: datetime) -> bool:
    # Query: COUNT(*) FROM articles
    #        WHERE obligor_id=? AND published_at > last_summary_ts
    # Returns: True if count > 0, else False
```

**Why:** Avoids unnecessary Groq calls. If no new articles and cache exists, reuse cached summary.

#### `call_groq_with_backoff(prompt: str, retries: int = 3) -> str`

**Purpose:** Call Groq API with intelligent retry logic and model fallback.

**Logic:**
1. Try primary model: `llama-3.3-70b-versatile`
2. On 429 (rate limit):
   - Wait `20s × attempt_number`
   - Retry up to `retries` times
3. If primary exhausted after all retries:
   - Switch to fallback: `llama-3.1-8b-instant`
   - Reset retry counter, try again
4. On final failure: raise exception
5. Log every retry + which model was used

**Timeout:** 30 seconds per call

#### `summarize_obligor_risk(obligor_id: int, days: int = 7) -> Dict`

**Purpose:** Generate a credit risk summary for an obligor based on recent articles.

**Algorithm:**
```python
def summarize_obligor_risk(obligor_id: int, days: int = 7) -> Dict:
    # Step 1: Check cache
    cached = query_summaries(obligor_id, today, article_hash=None)
    if cached and is_valid(cached.created_at, ttl=TTL_MINUTES):
        # Step 2a: If cache hit and no new articles → return cached
        if not has_new_articles_since(obligor_id, cached.created_at):
            return parse_cached_summary(cached)
    
    # Step 2b: No cache or expired or new articles → fetch fresh
    # Retrieve top 10 articles via ArticleRetriever
    articles = ArticleRetriever().search_by_obligor(obligor_id, days=days, top_k=10)
    
    if not articles:
        return empty_summary(obligor_id)
    
    # Step 3: Get company name
    obligor = db.query(Obligor).filter_by(id=obligor_id).one()
    
    # Step 4: Format articles for prompt
    formatted_articles = format_articles_for_prompt(articles)
    
    # Step 5: Build and send prompt
    prompt = build_summary_prompt(obligor.name, formatted_articles)
    response = call_groq_with_backoff(prompt)
    
    # Step 6: Parse JSON response
    summary_json = json.loads(response)
    
    # Step 7: Store in cache
    article_ids = [a["article_id"] for a in articles]
    article_hash = hash(tuple(sorted(article_ids)))
    cache_entry = Summaries(
        obligor_id=obligor_id,
        cache_date=date.today(),
        article_hash=article_hash,
        summary_json=summary_json,
        model_used=MODEL_USED  # captured from last Groq call
    )
    db.add(cache_entry)
    db.commit()
    
    # Step 8: Return structured response
    return {
        "company": obligor.name,
        "summary": summary_json["summary"],
        "key_events": summary_json["key_events"],
        "risk_level": summary_json["risk_level"],
        "concerns": summary_json["concerns"],
        "positive_factors": summary_json["positive_factors"],
        "confidence": summary_json.get("confidence", 0.75),
        "model_used": MODEL_USED,
        "cached": False  # mark if this came from cache
    }
```

**Return Structure:**
```python
{
    "company": str,                          # e.g., "Tesla Inc."
    "summary": str,                          # 1-2 sentence narrative
    "key_events": List[str],                 # 3-5 most important events
    "risk_level": "low" | "medium" | "high" | "critical",
    "concerns": List[str],                   # risk factors
    "positive_factors": List[str],           # any mitigating factors
    "confidence": float,                     # 0.0-1.0
    "model_used": str,                       # "llama-3.3-70b-versatile" or fallback
    "cached": bool                           # True if from cache, False if fresh
}
```

### Cache TTL

- **High-risk obligors:** 230 minutes (4-hour cycle - 10-minute buffer)
- **Normal obligors:** 350 minutes (6-hour cycle - 10-minute buffer)

Rationale: Buffer ensures cache expires before next scheduled cycle, forcing fresh summary fetch.

### Prompt Template

```
System Prompt:
"You are a credit risk analyst with expertise in corporate finance and debt markets.
Analyze the provided articles for credit risk signals.
Respond ONLY with valid JSON, no preamble, no markdown backticks, no explanation."

User Prompt:
"Analyze these recent articles about [Company Name] for credit risk.

Provide structured JSON with exactly these fields:
- summary: 1-2 sentence credit risk narrative (string)
- key_events: list of 3-5 most important events (array of strings)
- risk_level: severity assessment: 'low' | 'medium' | 'high' | 'critical' (string)
- concerns: list of 3-5 credit risk factors (e.g., liquidity, covenant, downgrade) (array of strings)
- positive_factors: list of any mitigating positive factors, or empty array (array of strings)
- confidence: your confidence in this assessment, 0.0 to 1.0 (number)

Articles (with source and date):
[Formatted article excerpts, 1 per line]
Article 1: "[Source] [Date] [Excerpt 1]"
Article 2: "[Source] [Date] [Excerpt 2]"
...

Provide only valid JSON."
```

### Error Handling

- **No articles found:** Return empty summary `{summary: "No recent articles", risk_level: "low", ...}`
- **Groq timeout/failure:** Log error, attempt fallback, raise `SummarizerError` if both fail
- **Invalid JSON response:** Log full response, raise `SummarizerError`

---

## 2. Alert Rules Engine (`src/alerts/rules.py`)

### Purpose
Evaluate daily signals and summary to determine if an alert should fire and at what severity.

### Rule Definitions

**Rule 1: Credit Event Detected**
- **Condition:** `event_types` contains any of: `default`, `bankruptcy`, `fraud`
- **Severity:** `CRITICAL`
- **Rationale:** Immediate solvency threat

**Rule 2: Covenant/Liquidity Risk**
- **Condition:** `event_types` contains `covenant_breach` OR `liquidity_crisis`, OR summary.risk_level == `"critical"`
- **Severity:** `HIGH`
- **Rationale:** Technical default or cash flow crisis

**Rule 3: Downgrade/Rating Watch**
- **Condition:** `event_types` contains `downgrade` OR `rating_watch`
- **Severity:** `MEDIUM`
- **Rationale:** Market-signaled credit deterioration

**Rule 4: Negative Sentiment Spike**
- **Condition:** `avg_sentiment` (7-day) < -0.5 AND `credit_relevant_count` >= 3
- **Severity:** `MEDIUM`
- **Rationale:** Sustained negative coverage on credit-relevant topics

**Rule 5: Multiple Event Types**
- **Condition:** Number of distinct event types in last 48 hours >= 2
- **Severity:** `HIGH`
- **Rationale:** Clustering of different risks signals compounding stress

### AlertEngine Class

```python
class AlertEngine:
    """Evaluate rules and determine if alerts should fire."""
    
    def evaluate(
        self,
        obligor_id: int,
        date: datetime,
        summary: Dict = None  # cached or fresh from summarizer
    ) -> List[Dict]:
        """
        Evaluate all rules for an obligor on a given date.
        
        Returns: List of triggered rules
        [{
            "rule_name": str,
            "severity": str,
            "trigger_evidence": str  # human-readable why rule fired
        }]
        """
        # Fetch daily signals
        signals = db.query(ObligorDailySignals).filter_by(
            obligor_id=obligor_id,
            date=date
        ).one_or_none()
        
        if not signals:
            return []
        
        # Fetch summary (or use passed-in parameter)
        if summary is None:
            summary = summarizer.summarize_obligor_risk(obligor_id)
        
        triggered = []
        
        # Evaluate each rule
        if self._rule_credit_event(signals):
            triggered.append({
                "rule_name": "Rule1_CreditEvent",
                "severity": "CRITICAL",
                "trigger_evidence": f"Events detected: {signals.event_types}"
            })
        
        if self._rule_covenant_liquidity(signals, summary):
            triggered.append({
                "rule_name": "Rule2_CovenantLiquidity",
                "severity": "HIGH",
                "trigger_evidence": "Covenant or liquidity risk detected"
            })
        
        if self._rule_downgrade_watch(signals):
            triggered.append({
                "rule_name": "Rule3_DowngradeWatch",
                "severity": "MEDIUM",
                "trigger_evidence": f"Rating event: {signals.event_types}"
            })
        
        if self._rule_sentiment_spike(signals):
            triggered.append({
                "rule_name": "Rule4_SentimentSpike",
                "severity": "MEDIUM",
                "trigger_evidence": f"Sentiment {signals.avg_sentiment:.2f}, {signals.credit_relevant_count} credit articles"
            })
        
        if self._rule_multiple_events(obligor_id, date):
            triggered.append({
                "rule_name": "Rule5_MultipleEvents",
                "severity": "HIGH",
                "trigger_evidence": "Multiple distinct event types in 48h"
            })
        
        return triggered
    
    def _rule_credit_event(self, signals) -> bool:
        return signals.event_types and any(
            e in signals.event_types 
            for e in ["default", "bankruptcy", "fraud"]
        )
    
    def _rule_covenant_liquidity(self, signals, summary) -> bool:
        has_covenant_liquidity = signals.event_types and any(
            e in signals.event_types 
            for e in ["covenant_breach", "liquidity_crisis"]
        )
        has_critical_summary = summary and summary.get("risk_level") == "critical"
        return has_covenant_liquidity or has_critical_summary
    
    # ... other rule implementations ...
```

---

## 3. Alert Generator (`src/alerts/generator.py`)

### Purpose
Orchestrate alert creation with caching, fallback logic, and deduplication.

### Key Functions

#### `generate_alerts(obligor_id: int) -> None`

**Algorithm:**
```python
def generate_alerts(obligor_id: int) -> None:
    """Generate alerts for a single obligor."""
    
    try:
        # Step 1: Get latest daily signals
        signals = db.query(ObligorDailySignals).filter_by(
            obligor_id=obligor_id
        ).order_by(ObligorDailySignals.date.desc()).first()
        
        if not signals:
            logger.info(f"No signals for obligor {obligor_id}, skipping")
            return
        
        # Step 2: Check for new articles
        summary = None
        last_summary = db.query(Summaries).filter_by(
            obligor_id=obligor_id
        ).order_by(Summaries.created_at.desc()).first()
        
        if last_summary and has_new_articles_since(obligor_id, last_summary.created_at):
            # New articles → need fresh summary
            summary = summarizer.summarize_obligor_risk(obligor_id)
        elif last_summary and is_valid_cache(last_summary.created_at, TTL):
            # Cache still valid and no new articles → reuse
            summary = parse_cached_summary(last_summary)
        else:
            # No cache or expired → generate fresh
            summary = summarizer.summarize_obligor_risk(obligor_id)
        
        # Step 3: Run alert rules
        engine = AlertEngine()
        triggered_rules = engine.evaluate(obligor_id, signals.date, summary)
        
        if not triggered_rules:
            logger.info(f"No alerts triggered for obligor {obligor_id}")
            return
        
        # Step 4: Create alerts with deduplication
        for rule in triggered_rules:
            # Check dedup: any alert for this rule in last 24h?
            recent_alert = db.query(Alert).filter_by(
                obligor_id=obligor_id
            ).filter(
                Alert.triggered_at > datetime.now(UTC) - timedelta(hours=24)
            ).filter(
                Alert.extra_data["rule_name"].astext == rule["rule_name"]
            ).first()
            
            if recent_alert:
                logger.info(f"Alert {rule['rule_name']} already triggered in last 24h, skipping")
                continue
            
            # Insert new alert
            alert = Alert(
                obligor_id=obligor_id,
                triggered_at=datetime.now(UTC),
                severity=rule["severity"],
                summary=summary.get("summary", ""),
                event_types=signals.event_types,
                article_ids=fetch_relevant_article_ids(obligor_id),
                extra_data={
                    "rule_name": rule["rule_name"],
                    "trigger_evidence": rule["trigger_evidence"],
                    "risk_level": summary.get("risk_level"),
                    "concerns": summary.get("concerns", [])
                }
            )
            db.add(alert)
            db.commit()
            logger.info(f"Created alert for obligor {obligor_id}: {rule['rule_name']} ({rule['severity']})")
    
    except SummarizerError as e:
        logger.error(f"Summarizer failed for obligor {obligor_id}: {e}")
        # Fallback: create rule-based alert without summary
        triggered = AlertEngine().evaluate(obligor_id, signals.date, summary=None)
        for rule in triggered:
            alert = Alert(
                obligor_id=obligor_id,
                triggered_at=datetime.now(UTC),
                severity=rule["severity"],
                summary="Summary generation failed; alert based on signals only",
                event_types=signals.event_types,
                article_ids=fetch_relevant_article_ids(obligor_id),
                extra_data={
                    "rule_name": rule["rule_name"],
                    "fallback": True,
                    "error": str(e)
                }
            )
            db.add(alert)
            db.commit()
    
    except Exception as e:
        logger.error(f"Unexpected error generating alerts for obligor {obligor_id}: {e}")
        # Log error, continue (don't crash scheduler)
```

#### `check_all_obligors() -> None`

**Algorithm:**
```python
def check_all_obligors() -> None:
    """Generate alerts for all obligors (called by scheduler)."""
    obligor_ids = db.query(Obligor.id).all()
    
    for (obligor_id,) in obligor_ids:
        try:
            generate_alerts(obligor_id)
        except Exception as e:
            logger.error(f"Error processing obligor {obligor_id}: {e}")
            # Continue processing other obligors
    
    logger.info(f"Completed alert generation for {len(obligor_ids)} obligors")
```

### Fallback Behavior

When Groq call fails after all retries:
- Still evaluate rules based on `obligor_daily_signals` (no summary required)
- Create alert with severity from event types only
- Mark alert extra_data with `fallback: True` and error message
- Alert still reaches dashboard, but lacks rich narrative

---

## 4. Scheduler (`src/alerts/scheduler.py`)

### Purpose
Run alert generation on a tiered schedule with rate-limit awareness and per-obligor error isolation.

### Priority Tiers

```python
def get_prioritized_obligors() -> List[Tuple[int, str]]:
    """
    Query signals + alerts to assign obligors to tiers.
    
    HIGH RISK: alert_count >= 2 in last 7 days OR min_sentiment < -0.4
    NORMAL: everything else
    
    Returns: [(obligor_id, "high" | "normal"), ...]
    """
    high_risk = db.query(Obligor.id).join(
        Alert, Obligor.id == Alert.obligor_id
    ).filter(
        Alert.triggered_at > datetime.now(UTC) - timedelta(days=7)
    ).group_by(Obligor.id).having(
        func.count(Alert.id) >= 2
    ).all()
    
    sentiments = db.query(Obligor.id, func.min(
        ObligorDailySignals.avg_sentiment
    )).join(
        ObligorDailySignals
    ).filter(
        ObligorDailySignals.date >= date.today() - timedelta(days=7)
    ).group_by(Obligor.id).filter(
        func.min(ObligorDailySignals.avg_sentiment) < -0.4
    ).all()
    
    high_risk_ids = set([row[0] for row in high_risk] + [row[0] for row in sentiments])
    
    result = []
    for (obligor_id,) in db.query(Obligor.id).all():
        tier = "high" if obligor_id in high_risk_ids else "normal"
        result.append((obligor_id, tier))
    
    return result
```

### Job 1: `high_risk_alert_cycle()`

**Schedule:** Every 4 hours (cron: `0 */4 * * *`)

**Algorithm:**
```python
@scheduler.scheduled_job('cron', hour='*/4', minute='0')
def high_risk_alert_cycle():
    """Process high-risk obligors every 4 hours."""
    try:
        logger.info("Starting high-risk alert cycle")
        
        # Get priority list
        obligors = get_prioritized_obligors()
        high_risk = [(oid, tier) for oid, tier in obligors if tier == "high"]
        
        # Rate limit budget check
        calls_this_cycle = len(high_risk)
        remaining_daily = 1000 - get_used_groq_calls_today()
        if calls_this_cycle > 0.8 * remaining_daily:
            logger.warning(f"Alert cycle will use {calls_this_cycle} calls, {remaining_daily} remaining (>80%)")
        
        # Process with 15s sleep between calls
        for obligor_id, _ in high_risk:
            try:
                generate_alerts(obligor_id)
                time.sleep(15)  # Rate limit throttle
            except Exception as e:
                logger.error(f"Error processing obligor {obligor_id}: {e}")
                continue  # Don't crash entire job
        
        logger.info(f"Completed high-risk cycle for {len(high_risk)} obligors")
    
    except Exception as e:
        logger.critical(f"High-risk alert cycle failed: {e}")
        # Do NOT re-raise; keeps scheduler alive
```

### Job 2: `normal_alert_cycle()`

**Schedule:** Every 6 hours (cron: `0 */6 * * *`)

**Algorithm:** Same as above, but filters to `tier == "normal"` and skips any obligor processed in current `high_risk_alert_cycle()` window (last 4 hours).

### Job 3: `daily_aggregation()` (no change)

Existing signal aggregation job runs daily at 9 AM.

### Error Handling

- **Per-obligor:** Try/except, log error, continue to next obligor
- **Groq timeout:** Handled by `call_groq_with_backoff()` + fallback logic
- **Job-level:** Catch-all try/except logs critical error but does NOT raise (keeps scheduler alive)

---

## 5. FastAPI Alert Endpoints (`src/api/alerts.py`)

### Endpoints

#### `GET /api/alerts`

**Query Parameters:**
- `severity` (optional): filter by severity (low, medium, high, critical)
- `date_from` (optional): ISO 8601 date
- `date_to` (optional): ISO 8601 date
- `obligor_id` (optional): filter by obligor
- `limit` (default 20, max 100)
- `offset` (default 0)

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "obligor_id": 5,
      "obligor_name": "Tesla Inc.",
      "triggered_at": "2026-04-02T10:30:00Z",
      "severity": "HIGH",
      "summary": "Tesla faces covenant pressure and liquidity concerns...",
      "event_types": ["covenant_breach", "downgrade"],
      "article_count": 7,
      "rule_fired": "Rule2_CovenantLiquidity"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/alerts/{alert_id}`

**Response:**
```json
{
  "id": 1,
  "obligor_id": 5,
  "obligor_name": "Tesla Inc.",
  "triggered_at": "2026-04-02T10:30:00Z",
  "severity": "HIGH",
  "summary": "...",
  "event_types": ["covenant_breach", "downgrade"],
  "rule_fired": "Rule2_CovenantLiquidity",
  "trigger_evidence": "Covenant or liquidity risk detected",
  "risk_level": "high",
  "concerns": ["debt maturity", "covenant language"],
  "source_articles": [
    {
      "article_id": 123,
      "title": "Tesla Bond Covenant Tightens",
      "source": "Reuters",
      "published_at": "2026-04-01",
      "snippet": "..."
    }
  ]
}
```

#### `POST /api/alerts/{alert_id}/acknowledge`

**Request:**
```json
{
  "acknowledged": true
}
```

**Response:** 200 OK (marks alert as read, optional feature)

#### `GET /api/obligors/{obligor_id}/summary`

**Query Parameters:**
- `days` (default 7, range 1-30)

**Response:**
```json
{
  "obligor_id": 5,
  "obligor_name": "Tesla Inc.",
  "summary": "Tesla faces increased liquidity pressure...",
  "key_events": [
    "Q4 earnings miss",
    "Covenant language tightened",
    "3 analyst downgrades"
  ],
  "risk_level": "high",
  "concerns": ["liquidity", "covenant", "macro"],
  "positive_factors": [],
  "confidence": 0.78,
  "model_used": "llama-3.3-70b-versatile",
  "cached": true,
  "generated_at": "2026-04-02T09:30:00Z"
}
```

---

## 6. Testing Strategy

### Unit Tests (`tests/unit/test_alerts.py`)

- `test_summarizer_caches_summary()`
- `test_summarizer_skips_api_call_on_valid_cache_and_no_new_articles()`
- `test_summarizer_calls_api_on_cache_miss()`
- `test_groq_fallback_on_rate_limit()`
- `test_alert_rule_1_credit_event()`
- `test_alert_rule_2_covenant_liquidity()`
- `test_alert_rule_deduplication_within_24h()`
- `test_generate_alerts_fallback_on_summarizer_failure()`
- `test_priority_tiers_assign_correctly()`

### Integration Tests (`tests/integration/test_alerts.py`)

- `test_end_to_end_alert_flow()` — create articles → sentiment → summary → alert
- `test_scheduler_respects_rate_limits()` — mock Groq, verify 15s sleep
- `test_api_endpoints_return_correct_format()`
- `test_alert_deduplication_across_cycles()`

### Smoke Tests

- Query summaries table, verify JSON structure
- Trigger high-risk cycle manually, verify alerts created
- Test API endpoints with curl

---

## 7. Implementation Order

1. **Summarizer** (`src/rag/summarizer.py`) + migration for `summaries` table
2. **AlertEngine** (`src/alerts/rules.py`)
3. **AlertGenerator** (`src/alerts/generator.py`) + unit tests
4. **Scheduler** (`src/alerts/scheduler.py`) with two-tier job structure
5. **API** (`src/api/alerts.py`) + FastAPI server integration
6. **Integration tests** + smoke tests on real data
7. **Week 5 wrap** + commit to main

---

## 8. Risk & Mitigations

| Risk | Mitigation |
|------|-----------|
| Groq rate limit exhaustion | Cache TTL + has_new_articles check + fallback model + rate limit budget warning |
| Summary JSON parsing failure | Try/except with detailed logging + fallback to rule-based alert |
| Alert deduplication race condition | Use UNIQUE constraint on (obligor_id, rule_name, 24h window) |
| Scheduler crash on per-obligor error | Try/except per obligor, do NOT raise at job level |
| Cold start (no articles) | Return empty summary gracefully, still evaluate rules |

---

## 9. Success Criteria

- [ ] Summarizer generates credit risk narratives for all obligors
- [ ] Cache reduces API calls by >60%
- [ ] All 5 alert rules firing correctly on test data
- [ ] Deduplication prevents duplicate alerts within 24h
- [ ] Scheduler stays within Groq rate limits (<250 calls/day)
- [ ] API endpoints return well-formed JSON
- [ ] Fallback logic works when Groq fails
- [ ] Tests pass: unit + integration + smoke

---

## 10. Future Enhancements (Out of Scope)

- Upgrade to Claude API for higher-quality summaries (config switch only)
- Historical alert trends dashboard
- Custom alert rule configuration per obligor
- Multi-model ensemble (score summaries from multiple models)
