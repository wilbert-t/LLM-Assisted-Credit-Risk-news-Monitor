# Week 5 LLM Summarization & Alerts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build RAG-enhanced alert generation with LLM summaries, rule engine, scheduler, and API endpoints.

**Architecture:** Groq-powered summarizer with PostgreSQL cache → rules engine evaluates signals + summary → alert generator with dedup → scheduler (4h/6h tiers) → FastAPI endpoints.

**Tech Stack:** Groq API, APScheduler, SQLAlchemy ORM, pytest, FastAPI

---

## File Structure

**New Files:**
- `src/rag/summarizer.py` — Groq-powered summarizer + cache logic
- `src/alerts/rules.py` — AlertEngine + 5 rule implementations
- `src/alerts/generator.py` — Alert generation + deduplication
- `src/alerts/scheduler.py` — APScheduler jobs (high-risk + normal tiers)
- `src/api/alerts.py` — FastAPI endpoints
- `infra/migrations/add_summaries_table.sql` — Database migration

**Test Files:**
- `tests/unit/test_summarizer.py` — Summarizer unit tests
- `tests/unit/test_alert_rules.py` — Rules engine tests
- `tests/unit/test_alert_generator.py` — Generator tests
- `tests/unit/test_alert_scheduler.py` — Scheduler tests
- `tests/unit/test_alerts_api.py` — API endpoint tests
- `tests/integration/test_alerts_e2e.py` — End-to-end alert flow

**Modified Files:**
- `src/db/models.py` — Add Summaries ORM model
- `src/db/connection.py` — Run migration on init
- `src/utils/constants.py` — Add Groq + alert constants
- `requirements.txt` — Add `apscheduler>=3.10.0`

---

## Task 1: Database Migration & Summaries Model

**Files:**
- Create: `infra/migrations/add_summaries_table.sql`
- Modify: `src/db/models.py` — add Summaries class
- Modify: `src/db/connection.py` — run migration on init

**Context:**
This task sets up the PostgreSQL cache table for storing LLM-generated summaries, keyed by (obligor_id, cache_date, article_hash) to enable cache invalidation when new articles arrive.

**Steps:**

- [ ] **Step 1: Write migration SQL file**

Create `infra/migrations/add_summaries_table.sql`:

```sql
-- Migration: Add summaries table for LLM-generated credit risk summaries
-- Purpose: Cache summaries by obligor/date/article_hash to minimize Groq API calls

CREATE TABLE IF NOT EXISTS summaries (
    id SERIAL PRIMARY KEY,
    obligor_id INT NOT NULL REFERENCES obligors(id) ON DELETE CASCADE,
    cache_date DATE NOT NULL,
    article_hash VARCHAR(64) NOT NULL,
    summary_json JSON NOT NULL,
    model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_summaries_obligor_date_hash UNIQUE(obligor_id, cache_date, article_hash)
);

CREATE INDEX idx_summaries_obligor_date ON summaries(obligor_id, cache_date);
CREATE INDEX idx_summaries_created_at ON summaries(created_at);
```

- [ ] **Step 2: Add Summaries ORM model to src/db/models.py**

Add to `src/db/models.py` (after Alert class):

```python
class Summaries(TimestampMixin, Base):
    """
    Cached LLM-generated credit risk summaries.
    Keyed by (obligor_id, cache_date, article_hash) to enable reuse
    when articles haven't changed.
    """

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    obligor_id = Column(
        Integer,
        ForeignKey("obligors.id", ondelete="CASCADE"),
        nullable=False,
    )
    cache_date = Column(Date, nullable=False)
    article_hash = Column(String(64), nullable=False)
    summary_json = Column(JSON, nullable=False)
    model_used = Column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("obligor_id", "cache_date", "article_hash",
                         name="uq_summaries_obligor_date_hash"),
        Index("idx_summaries_obligor_date", "obligor_id", "cache_date"),
        Index("idx_summaries_created_at", "created_at"),
    )
```

- [ ] **Step 3: Update src/db/connection.py to run migration on init**

In `init_db()`, add migration runner after `Base.metadata.create_all()`:

```python
# Run custom migrations
from pathlib import Path
migration_path = Path(__file__).parent.parent.parent / "infra" / "migrations" / "add_summaries_table.sql"
if migration_path.exists():
    with open(migration_path) as f:
        migration_sql = f.read()
    conn.execute(text(migration_sql))
    conn.commit()
```

- [ ] **Step 4: Test migration runs without error**

Run:
```bash
source venv/bin/activate
python -c "from src.db.connection import init_db; init_db(); print('Migration OK')"
```

Expected: `Migration OK` printed, no exceptions.

- [ ] **Step 5: Verify table exists**

```bash
psql postgresql://postgres:postgres@localhost:5433/credit_risk -c "\d summaries"
```

Expected: Shows `summaries` table columns.

- [ ] **Step 6: Commit**

```bash
git add infra/migrations/add_summaries_table.sql src/db/models.py src/db/connection.py
git commit -m "feat: add summaries cache table + ORM model"
```

---

## Task 2: Groq Constants & Rate Limiting

**Files:**
- Modify: `src/utils/constants.py`

**Context:**
Add Groq model names, retry logic constants, cache TTL values, and alert rule names. These are referenced throughout the summarizer, generator, and scheduler.

**Steps:**

- [ ] **Step 1: Add constants to src/utils/constants.py**

Append to end of file:

```python
# ============================================================================
# LLM Configuration — Groq
# ============================================================================

GROQ_PRIMARY_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
GROQ_TIMEOUT_SECONDS = 30
GROQ_RETRY_SLEEP_BASE = 20  # seconds, multiplied by attempt number

# Cache TTL by obligor tier (minutes)
SUMMARY_CACHE_TTL_HIGH_RISK = 230  # 4 hours - 10 min buffer
SUMMARY_CACHE_TTL_NORMAL = 350     # 6 hours - 10 min buffer

# ============================================================================
# Alert Rule Names
# ============================================================================

ALERT_RULE_CREDIT_EVENT = "Rule1_CreditEvent"
ALERT_RULE_COVENANT_LIQUIDITY = "Rule2_CovenantLiquidity"
ALERT_RULE_DOWNGRADE_WATCH = "Rule3_DowngradeWatch"
ALERT_RULE_SENTIMENT_SPIKE = "Rule4_SentimentSpike"
ALERT_RULE_MULTIPLE_EVENTS = "Rule5_MultipleEvents"

# Rule thresholds
SENTIMENT_SPIKE_THRESHOLD = -0.5
SENTIMENT_SPIKE_MIN_ARTICLES = 3
MULTIPLE_EVENTS_THRESHOLD = 2
MULTIPLE_EVENTS_WINDOW_HOURS = 48

# Alert Scheduler
INTER_CALL_SLEEP_SECONDS = 15
HIGH_RISK_CYCLE_HOURS = 4
NORMAL_CYCLE_HOURS = 6

# Priority tier thresholds
HIGH_RISK_MIN_ALERTS_7D = 2
HIGH_RISK_MAX_SENTIMENT = -0.4

# Deduplication
ALERT_DEDUP_WINDOW_HOURS = 24
```

- [ ] **Step 2: Commit**

```bash
git add src/utils/constants.py
git commit -m "feat: add Groq + alert constants"
```

---

## Task 3: Summarizer Module

**Files:**
- Create: `src/rag/summarizer.py`
- Create: `tests/unit/test_summarizer.py`
- Modify: `requirements.txt` — ensure `groq` is present

**Context:**
Build the LLM summarizer that retrieves articles via RAG, calls Groq with fallback logic, and caches results. This is the core intelligence piece that feeds alerts.

**Steps:** See detailed implementation in spec document (sections 1-2 of design spec). Follow TDD: write failing tests first, then implement.

---

## Task 4: Alert Rules Engine

**Files:**
- Create: `src/alerts/rules.py`
- Create: `tests/unit/test_alert_rules.py`

**Context:**
Implement 5 alert rules that evaluate daily signals and summaries. Rules fire based on credit events, covenant breaches, sentiment spikes, downgrades, and multiple concurrent events.

**Steps:** Follow TDD pattern. Implement AlertEngine class with 5 rule methods.

---

## Task 5: Alert Generator

**Files:**
- Create: `src/alerts/generator.py`
- Create: `tests/unit/test_alert_generator.py`

**Context:**
Orchestrate alert creation: fetch signals, call summarizer (with cache check), evaluate rules, insert alerts with 24h deduplication window. Fallback to rule-based alerts if Groq fails.

**Steps:** Follow TDD. Implement `generate_alerts()` and `check_all_obligors()`.

---

## Task 6: Scheduler

**Files:**
- Create: `src/alerts/scheduler.py`
- Create: `tests/unit/test_alert_scheduler.py`
- Modify: `requirements.txt` — add `apscheduler>=3.10.0`

**Context:**
APScheduler with two-tier alert cycles: high-risk (4h) for obligors with 2+ alerts or negative sentiment, normal (6h) for others. Includes rate limit budget check at start of each cycle.

**Steps:** Follow TDD. Implement ScheduledAlertJob class with start(), stop(), high_risk_alert_cycle(), normal_alert_cycle().

---

## Task 7: FastAPI Alert Endpoints

**Files:**
- Create: `src/api/alerts.py`
- Create: `tests/unit/test_alerts_api.py`

**Context:**
Expose alerts and summaries via REST API: GET /alerts (with filters), GET /alerts/{id}, GET /obligors/{id}/summary. Uses Pydantic models for responses.

**Steps:** Follow TDD. Create router with 3 endpoints and corresponding response models.

---

## Task 8: Integration Tests & Smoke Tests

**Files:**
- Create: `tests/integration/test_alerts_e2e.py`

**Context:**
End-to-end integration tests: create articles, signals, run generator, verify alerts created. Smoke tests query tables to verify data persists.

**Steps:** Write integration tests covering full flow: articles → signals → summary → alert creation.

---

## Success Criteria

- [ ] All unit tests passing (150+)
- [ ] All integration tests passing
- [ ] Smoke tests confirm tables populated
- [ ] `summaries`, `alerts` tables have data
- [ ] API endpoints respond correctly
- [ ] Scheduler can start/stop without errors
- [ ] Rate limit budget check works
- [ ] Deduplication prevents duplicate alerts within 24h

---

## Next Steps After Completion

1. Run full test suite: `pytest tests/ -v`
2. Commit final: `git commit -m "feat: week 5 complete — summarizer, rules, scheduler, API"`
3. Update session log with completion summary
4. Begin Phase 6: Dashboard (Streamlit + Plotly)
