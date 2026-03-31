# Risk Scoring & Week 3 Wrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic risk scorer, upgrade signal aggregation to use real negative counts and per-obligor risk scores, write week 3 integration tests, and optionally add an LLM-based classifier as a second opinion.

**Architecture:** `risk_scorer.py` is a pure-Python scoring function (no DB, no ML) that takes a processed article dict and returns a float 0–1. Signal aggregation calls it per article to compute a daily risk score stored in `obligor_daily_signals`. Integration tests use the existing transactional test DB fixture. The LLM classifier (Task 5) is optional and isolated from the core path.

**Tech Stack:** SQLAlchemy, PostgreSQL, existing `src/utils/constants.py` (EVENT_SEVERITY_MAP), Groq API via `requests` (LLM task only).

---

## Already Done (Day 17)
- `src/models/classifier.py` — `is_credit_relevant()`, `classify_events()` ✅
- `src/processors/pipeline.py` — classifier integrated ✅
- `src/models/sentiment.py` — FinBERT scoring ✅
- All 1,186 articles scored ✅

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/models/risk_scorer.py` | Create | Pure risk-scoring functions |
| `src/db/models.py` | Modify | Add `risk_score` Float column to `ObligorDailySignals` |
| `src/processors/signal_aggregator.py` | Modify | Fix `neg_article_count`, add `risk_score` computation |
| `tests/unit/test_risk_scorer.py` | Create | Pure unit tests (no DB) |
| `tests/unit/test_signal_aggregator.py` | Modify | Update 3 tests that assumed `neg_article_count == total` |
| `tests/integration/test_sentiment_and_risk.py` | Create | 4 integration tests using `db` fixture |
| `src/models/llm_classifier.py` | Create | **[OPTIONAL]** LLM classifier via Groq API |
| `tests/unit/test_llm_classifier.py` | Create | **[OPTIONAL]** Mocked unit tests |

---

## Task 1: Risk Scorer Module

**Files:**
- Create: `src/models/risk_scorer.py`
- Create: `tests/unit/test_risk_scorer.py`

The scorer is deterministic — same inputs always produce the same output. No randomness, no ML model, no DB.

Scoring logic:
- Base: `0.0`
- `+0.5` if `is_credit_relevant` is True
- `+0.3` if `sentiment_score` is not None and < 0
- `+0.3` if `"default"` in `event_types`
- `+0.2` if `"downgrade"` in `event_types`
- `+0.2` if `"bankruptcy"` in `event_types`
- `+0.15` if `"fraud"` in `event_types`
- `+0.15` if `"liquidity_crisis"` in `event_types`
- Clamp result to `[0.0, 1.0]`

(Note: Multiple event bonuses stack, clamping at 1.0 handles overflow.)

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_risk_scorer.py`:

```python
"""
Unit tests for src/models/risk_scorer.py.
Pure unit tests — no DB, no ML model, no mocks needed.
"""

import pytest

from src.models.risk_scorer import score_article_risk


class TestScoreArticleRisk:

    def test_high_risk_article_default_event(self):
        """Negative sentiment + credit relevant + default event → near 1.0."""
        article = {
            "sentiment_score": -0.8,
            "is_credit_relevant": True,
            "event_types": ["default"],
        }
        score = score_article_risk(article)
        # 0.5 (relevant) + 0.3 (neg sentiment) + 0.3 (default) = 1.1 → clamped to 1.0
        assert score == 1.0

    def test_low_risk_article_positive_sentiment(self):
        """Positive sentiment + not credit relevant → low score."""
        article = {
            "sentiment_score": 0.7,
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == 0.0

    def test_credit_relevant_adds_0_5(self):
        """Credit relevance alone adds 0.5 to base score of 0."""
        article = {
            "sentiment_score": 0.1,  # positive, no sentiment bonus
            "is_credit_relevant": True,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.5)

    def test_negative_sentiment_adds_0_3(self):
        """Negative sentiment (< 0) adds 0.3."""
        article = {
            "sentiment_score": -0.01,  # just below zero
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.3)

    def test_positive_sentiment_no_bonus(self):
        """Positive or zero sentiment score adds nothing."""
        article = {
            "sentiment_score": 0.0,
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.0)

    def test_downgrade_event_adds_0_2(self):
        """Downgrade event adds 0.2 on top of credit_relevant bonus."""
        article = {
            "sentiment_score": 0.1,  # positive, no sentiment bonus
            "is_credit_relevant": True,
            "event_types": ["downgrade"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.2 = 0.7
        assert score == pytest.approx(0.7)

    def test_bankruptcy_event_adds_0_2(self):
        """Bankruptcy event adds 0.2."""
        article = {
            "sentiment_score": 0.0,
            "is_credit_relevant": True,
            "event_types": ["bankruptcy"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.2 = 0.7
        assert score == pytest.approx(0.7)

    def test_multiple_events_stack(self):
        """Multiple event bonuses stack, clamped at 1.0."""
        article = {
            "sentiment_score": -0.5,
            "is_credit_relevant": True,
            "event_types": ["default", "downgrade", "fraud"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.3 + 0.3 + 0.2 + 0.15 = 1.45 → clamped to 1.0
        assert score == 1.0

    def test_none_sentiment_no_sentiment_bonus(self):
        """None sentiment_score should not add the negative-sentiment bonus."""
        article = {
            "sentiment_score": None,
            "is_credit_relevant": True,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.5)

    def test_none_event_types_treated_as_empty(self):
        """None event_types should behave identically to []."""
        article = {
            "sentiment_score": -0.5,
            "is_credit_relevant": True,
            "event_types": None,
        }
        score = score_article_risk(article)
        # 0.5 + 0.3 = 0.8
        assert score == pytest.approx(0.8)

    def test_score_always_between_0_and_1(self):
        """Score is always in [0.0, 1.0] regardless of inputs."""
        article = {
            "sentiment_score": -1.0,
            "is_credit_relevant": True,
            "event_types": ["default", "bankruptcy", "fraud", "downgrade", "liquidity_crisis"],
        }
        score = score_article_risk(article)
        assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
source venv/bin/activate
pytest tests/unit/test_risk_scorer.py -v 2>&1 | head -15
```

Expected: `ImportError: cannot import name 'score_article_risk'`

- [ ] **Step 3: Create `src/models/risk_scorer.py`**

```python
"""
Deterministic risk scorer for processed articles and obligors.

Usage:
    from src.models.risk_scorer import score_article_risk, aggregate_obligor_risk

    score = score_article_risk({
        "sentiment_score": -0.8,
        "is_credit_relevant": True,
        "event_types": ["default"],
    })
    # 1.0 (clamped)
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Additive bonuses per event type
_EVENT_BONUSES: Dict[str, float] = {
    "default":         0.30,
    "bankruptcy":      0.20,
    "fraud":           0.15,
    "liquidity_crisis": 0.15,
    "downgrade":       0.20,
    "covenant_breach": 0.15,
    "restructuring":   0.10,
    "rating_watch":    0.10,
    "regulatory_action": 0.10,
    "earnings_miss":   0.05,
    "lawsuit":         0.05,
    "management_change": 0.05,
    "merger_acquisition": 0.05,
    "debt_issuance":   0.05,
    "layoffs":         0.05,
}


def score_article_risk(processed_article: Dict) -> float:
    """
    Score a single processed article for credit risk.

    Args:
        processed_article: Dict with keys:
            sentiment_score   (float | None)  — from FinBERT, -1.0 to 1.0
            is_credit_relevant (bool)          — from keyword classifier
            event_types       (list | None)    — list of event type strings

    Returns:
        float in [0.0, 1.0] where 1.0 = maximum credit risk signal.
    """
    score = 0.0

    if processed_article.get("is_credit_relevant"):
        score += 0.5

    sentiment = processed_article.get("sentiment_score")
    if sentiment is not None and sentiment < 0:
        score += 0.3

    event_types: List[str] = processed_article.get("event_types") or []
    for event in event_types:
        score += _EVENT_BONUSES.get(event, 0.0)

    return round(min(score, 1.0), 6)


def aggregate_obligor_risk(
    obligor_id: int,
    days: int,
    db=None,
) -> float:
    """
    Compute the average risk score for an obligor over the last N days.

    Queries processed_articles via article_obligors, scores each article,
    and returns the mean. Returns 0.0 if no articles found.

    Args:
        obligor_id: The obligor to score.
        days:       Look-back window in days.
        db:         SQLAlchemy session (injected for testing).
    """
    from src.db.connection import SessionLocal
    from src.db.models import Article, ArticleObligor, ProcessedArticle

    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        cutoff = datetime.date.today() - datetime.timedelta(days=days)

        rows = (
            db.query(
                ProcessedArticle.sentiment_score,
                ProcessedArticle.is_credit_relevant,
                ProcessedArticle.event_types,
            )
            .join(Article, Article.id == ProcessedArticle.article_id)
            .join(ArticleObligor, ArticleObligor.article_id == Article.id)
            .filter(
                ArticleObligor.obligor_id == obligor_id,
                Article.published_at >= datetime.datetime.combine(
                    cutoff, datetime.time.min
                ),
            )
            .all()
        )

        if not rows:
            return 0.0

        scores = [
            score_article_risk({
                "sentiment_score":    r.sentiment_score,
                "is_credit_relevant": r.is_credit_relevant,
                "event_types":        r.event_types,
            })
            for r in rows
        ]
        return round(sum(scores) / len(scores), 6)

    finally:
        if own_session:
            db.close()
```

- [ ] **Step 4: Run tests — confirm all pass**

```bash
pytest tests/unit/test_risk_scorer.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/risk_scorer.py tests/unit/test_risk_scorer.py
git commit -m "feat: add deterministic risk scorer with per-event bonuses"
```

---

## Task 2: Add `risk_score` Column to DB

**Files:**
- Modify: `src/db/models.py` (line ~235 in `ObligorDailySignals`)

The `obligor_daily_signals` table needs a `risk_score` column. No Alembic is set up yet, so we add it to the ORM model (tests use `create_all`) and run an `ALTER TABLE` on the real DB.

- [ ] **Step 1: Update the ORM model**

In `src/db/models.py`, inside `ObligorDailySignals`, add `risk_score` after `credit_relevant_count`:

```python
    neg_article_count = Column(Integer, default=0, nullable=False)
    avg_sentiment = Column(Float, nullable=True)
    credit_relevant_count = Column(Integer, default=0, nullable=False)
    risk_score = Column(Float, nullable=True)   # avg of score_article_risk() per day
```

- [ ] **Step 2: Add the column to the real DB**

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "ALTER TABLE obligor_daily_signals ADD COLUMN IF NOT EXISTS risk_score FLOAT;"
```

Expected: `ALTER TABLE`

- [ ] **Step 3: Verify column exists**

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "\d obligor_daily_signals"
```

Expected: `risk_score` appears as `double precision` (nullable).

- [ ] **Step 4: Commit**

```bash
git add src/db/models.py
git commit -m "feat: add risk_score column to obligor_daily_signals"
```

---

## Task 3: Signal Aggregation v2

**Files:**
- Modify: `src/processors/signal_aggregator.py`
- Modify: `tests/unit/test_signal_aggregator.py`

**Changes to `aggregate_daily_signals()`:**
1. `neg_article_count` → count where `sentiment_score < -0.1` (was: total article count placeholder)
2. `risk_score` → average `score_article_risk()` across articles for the day

**Tests that must be updated** (they assumed `neg_article_count == total_article_count`):
- `test_counts_articles_for_obligor_on_date` — uses `sentiment_score=None`, expected `neg_article_count==2` → update to use `sentiment_score=-0.5`
- `test_counts_only_articles_for_that_date` — same issue → update to use `sentiment_score=-0.5`
- `test_upsert_updates_on_rerun` — same issue → update to use `sentiment_score=-0.5`

- [ ] **Step 1: Update the three broken tests in `tests/unit/test_signal_aggregator.py`**

Change these three tests to use `sentiment_score=-0.5` so that `neg_article_count` stays correct after the fix:

```python
def test_counts_articles_for_obligor_on_date(self, db):
    o = obligor_model(name="AAPL Corp", ticker="AAPL2")
    db.add(o)
    db.flush()

    _setup_link(db, o, TODAY, sentiment_score=-0.5)
    _setup_link(db, o, TODAY, sentiment_score=-0.5)

    result = aggregate_daily_signals(o.id, TODAY, db=db)

    assert result["neg_article_count"] == 2

def test_counts_only_articles_for_that_date(self, db):
    o = obligor_model(name="MSFT Corp", ticker="MSFT2")
    db.add(o)
    db.flush()

    _setup_link(db, o, TODAY, sentiment_score=-0.5)
    _setup_link(db, o, YESTERDAY, sentiment_score=-0.5)

    result_today = aggregate_daily_signals(o.id, TODAY, db=db)
    result_yesterday = aggregate_daily_signals(o.id, YESTERDAY, db=db)

    assert result_today["neg_article_count"] == 1
    assert result_yesterday["neg_article_count"] == 1

def test_upsert_updates_on_rerun(self, db):
    o = obligor_model(name="C Corp", ticker="C2")
    db.add(o)
    db.flush()

    _setup_link(db, o, TODAY, sentiment_score=-0.5)
    result1 = aggregate_daily_signals(o.id, TODAY, db=db)
    assert result1["neg_article_count"] == 1

    _setup_link(db, o, TODAY, sentiment_score=-0.5)
    result2 = aggregate_daily_signals(o.id, TODAY, db=db)
    assert result2["neg_article_count"] == 2

    rows = db.query(ObligorDailySignals).filter_by(obligor_id=o.id, date=TODAY).all()
    assert len(rows) == 1
    assert rows[0].neg_article_count == 2
```

Also add these two new tests at the end of `TestAggregateDailySignals`:

```python
def test_neg_count_excludes_neutral_and_positive(self, db):
    """neg_article_count only counts articles with sentiment_score < -0.1."""
    o = obligor_model(name="NeutralCo", ticker="NEU2")
    db.add(o)
    db.flush()

    _setup_link(db, o, TODAY, sentiment_score=-0.5)   # counts
    _setup_link(db, o, TODAY, sentiment_score=0.2)    # positive — does NOT count
    _setup_link(db, o, TODAY, sentiment_score=None)   # no score — does NOT count

    result = aggregate_daily_signals(o.id, TODAY, db=db)

    assert result["neg_article_count"] == 1

def test_risk_score_computed(self, db):
    """risk_score is the average of score_article_risk() per article."""
    o = obligor_model(name="RiskCo", ticker="RSK2")
    db.add(o)
    db.flush()

    # Article 1: credit_relevant=True, sentiment=-0.5, no events → 0.5 + 0.3 = 0.8
    _setup_link(db, o, TODAY, sentiment_score=-0.5, is_credit_relevant=True)
    # Article 2: credit_relevant=False, sentiment=0.5, no events → 0.0
    _setup_link(db, o, TODAY, sentiment_score=0.5, is_credit_relevant=False)

    result = aggregate_daily_signals(o.id, TODAY, db=db)

    # avg of [0.8, 0.0] = 0.4
    assert result["risk_score"] == pytest.approx(0.4, abs=1e-6)
```

- [ ] **Step 2: Run existing signal aggregator tests — confirm they fail**

```bash
source venv/bin/activate
pytest tests/unit/test_signal_aggregator.py -v 2>&1 | tail -20
```

Expected: the 3 updated tests fail (neg_article_count now = 0, not 2/1) and 2 new tests fail (ImportError or missing risk_score key).

- [ ] **Step 3: Update `src/processors/signal_aggregator.py`**

Replace the full file with:

```python
"""
Daily signal aggregation for obligors.

Reads article_obligors + processed_articles to compute per-obligor, per-date
metrics, then upserts into obligor_daily_signals.

neg_article_count = articles where sentiment_score < -0.1
avg_sentiment     = average sentiment_score (articles with non-null score)
credit_relevant_count = articles where is_credit_relevant = True
risk_score        = average score_article_risk() across all articles for the day
"""

import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Article, ArticleObligor, ObligorDailySignals, ProcessedArticle
from src.models.risk_scorer import score_article_risk
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def aggregate_daily_signals(
    obligor_id: int,
    date: datetime.date,
    db: Optional[Session] = None,
) -> dict:
    """
    Compute and upsert daily signals for one (obligor_id, date) pair.

    Returns a dict with the computed values:
        {obligor_id, date, neg_article_count, avg_sentiment,
         credit_relevant_count, risk_score}
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        rows = (
            db.query(
                ProcessedArticle.sentiment_score,
                ProcessedArticle.is_credit_relevant,
                ProcessedArticle.event_types,
            )
            .join(Article, Article.id == ProcessedArticle.article_id)
            .join(ArticleObligor, ArticleObligor.article_id == Article.id)
            .filter(
                ArticleObligor.obligor_id == obligor_id,
                func.date(Article.published_at) == date,
            )
            .all()
        )

        neg_article_count = sum(
            1 for r in rows
            if r.sentiment_score is not None and r.sentiment_score < -0.1
        )
        credit_relevant_count = sum(1 for r in rows if r.is_credit_relevant)

        scores_with_values = [r.sentiment_score for r in rows if r.sentiment_score is not None]
        avg_sentiment = sum(scores_with_values) / len(scores_with_values) if scores_with_values else None

        risk_scores = [
            score_article_risk({
                "sentiment_score":    r.sentiment_score,
                "is_credit_relevant": r.is_credit_relevant,
                "event_types":        r.event_types,
            })
            for r in rows
        ]
        risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None

        row = {
            "obligor_id":           obligor_id,
            "date":                 date,
            "neg_article_count":    neg_article_count,
            "avg_sentiment":        avg_sentiment,
            "credit_relevant_count": credit_relevant_count,
            "risk_score":           risk_score,
        }

        stmt = (
            pg_insert(ObligorDailySignals)
            .values(row)
            .on_conflict_do_update(
                constraint="uq_obligor_daily_signals_obligor_date",
                set_={
                    "neg_article_count":     row["neg_article_count"],
                    "avg_sentiment":         row["avg_sentiment"],
                    "credit_relevant_count": row["credit_relevant_count"],
                    "risk_score":            row["risk_score"],
                },
            )
        )
        db.execute(stmt)

        if own_session:
            db.commit()

        return row

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


def aggregate_all_daily(db: Optional[Session] = None) -> int:
    """
    Aggregate signals for every distinct (obligor_id, date) pair that has
    at least one article_obligor link. Returns the count of pairs processed.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        pairs = (
            db.query(
                ArticleObligor.obligor_id,
                func.date(Article.published_at).label("pub_date"),
            )
            .join(Article, Article.id == ArticleObligor.article_id)
            .filter(Article.published_at.isnot(None))
            .distinct()
            .all()
        )

        if not pairs:
            logger.info("aggregate_all_daily: no obligor-date pairs found.")
            return 0

        count = 0
        for obligor_id, pub_date in pairs:
            aggregate_daily_signals(obligor_id, pub_date, db=db)
            count += 1

        if own_session:
            db.commit()

        logger.info(f"aggregate_all_daily: processed {count} (obligor, date) pair(s).")
        return count

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()
```

- [ ] **Step 4: Run signal aggregator tests — confirm all pass**

```bash
pytest tests/unit/test_signal_aggregator.py -v
```

Expected: all 11 tests PASS (9 original + 2 new).

- [ ] **Step 5: Commit**

```bash
git add src/processors/signal_aggregator.py tests/unit/test_signal_aggregator.py
git commit -m "feat: signal aggregator v2 — real neg count, risk_score per obligor-day"
```

---

## Task 4: Integration Tests

**Files:**
- Create: `tests/integration/test_sentiment_and_risk.py`

These tests use the real PostgreSQL test DB via the `db` fixture (transactional rollback — no cleanup needed). The `db` fixture is defined in `tests/conftest.py`.

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/test_sentiment_and_risk.py`:

```python
"""
Integration tests for sentiment scoring, credit classification, and risk scoring.
Uses real PostgreSQL test DB via the `db` fixture (transactional rollback).
"""

import pytest

from src.db.models import ProcessedArticle
from src.models.risk_scorer import score_article_risk
from src.processors.pipeline import process_articles_batch
from tests.factories import article_model, processed_article_model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BANKRUPTCY_CONTENT = (
    "The company filed for bankruptcy protection under chapter 11 after missing "
    "debt payments and experiencing a severe liquidity crisis that left creditors "
    "with no recovery options according to court filings released today."
)

_GENERIC_CONTENT = (
    "The company held its annual picnic in the park last Saturday and employees "
    "enjoyed games, food, and sunny weather throughout the afternoon event."
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSentimentScoring:

    def test_pipeline_populates_sentiment_fields_as_none(self, db):
        """
        Pipeline sets sentiment_score=None and sentiment_label=None.
        Sentiment is scored separately by score_sentiment.py — not inline.
        """
        article = article_model(
            url="https://example.com/integ-sent-1",
            title="Apple reports record quarterly revenue",
            content="Apple Inc. reported its highest ever quarterly revenue of $120bn driven by strong iPhone sales.",
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        # Sentiment is NULL until score_sentiment.py runs
        assert pa.sentiment_score is None
        assert pa.sentiment_label is None


class TestCreditRelevance:

    def test_bankruptcy_article_is_credit_relevant(self, db):
        """Article containing 'bankruptcy' and 'chapter 11' → is_credit_relevant=True."""
        article = article_model(
            url="https://example.com/integ-cr-1",
            title="Company files for bankruptcy",
            content=_BANKRUPTCY_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.is_credit_relevant is True

    def test_generic_article_is_not_credit_relevant(self, db):
        """Article about a company picnic → is_credit_relevant=False."""
        article = article_model(
            url="https://example.com/integ-cr-2",
            title="Company holds annual picnic",
            content=_GENERIC_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.is_credit_relevant is False


class TestEventClassification:

    def test_downgrade_article_has_downgrade_event(self, db):
        """Article mentioning 'downgraded' → 'downgrade' in event_types."""
        article = article_model(
            url="https://example.com/integ-ev-1",
            title="S&P downgraded the company",
            content=(
                "S&P Global downgraded the company's credit rating from BB to B- "
                "citing concerns about cash flow and debt levels. The outlook remains "
                "negative according to the rating agency report."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.event_types is not None
        assert "downgrade" in pa.event_types

    def test_multiple_events_detected(self, db):
        """Article with both bankruptcy and fraud keywords → both in event_types."""
        article = article_model(
            url="https://example.com/integ-ev-2",
            title="Bankruptcy filed amid fraud investigation",
            content=(
                "The company filed for bankruptcy protection under chapter 11 as federal "
                "prosecutors announced fraud charges related to accounting fraud and "
                "embezzlement by senior executives."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert "bankruptcy" in pa.event_types
        assert "fraud" in pa.event_types


class TestFullEnrichmentPipeline:

    def test_pipeline_populates_all_classifier_fields(self, db):
        """End-to-end: raw article → cleaned_text, entities, is_credit_relevant, event_types."""
        article = article_model(
            url="https://example.com/integ-full-1",
            title="Company faces downgrade and lawsuit",
            content=(
                "The company was downgraded by Moody's and faces a class action lawsuit "
                "from shareholders following disappointing quarterly results. The board "
                "has hired restructuring advisors to explore options."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)

        assert count == 1
        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        # Text processing
        assert pa.cleaned_text is not None and len(pa.cleaned_text) > 0
        # Classifier fields — populated inline by pipeline
        assert pa.is_credit_relevant is True
        assert pa.event_types is not None
        assert len(pa.event_types) >= 1
        # Sentiment — still NULL (scored by separate script)
        assert pa.sentiment_score is None

    def test_risk_scorer_uses_pipeline_output(self, db):
        """score_article_risk() correctly uses fields populated by the pipeline."""
        article = article_model(
            url="https://example.com/integ-full-2",
            title="Firm defaults on debt payments",
            content=(
                "The firm failed to pay its quarterly coupon and has defaulted on "
                "its debt obligations, triggering cross-default clauses across "
                "the capital structure according to bondholders."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa.is_credit_relevant is True

        score = score_article_risk({
            "sentiment_score":    pa.sentiment_score,   # None — no FinBERT in tests
            "is_credit_relevant": pa.is_credit_relevant,
            "event_types":        pa.event_types,
        })
        # is_credit_relevant=True (+0.5) + default event (+0.3) = 0.8 minimum
        assert score >= 0.8
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest tests/integration/test_sentiment_and_risk.py -v 2>&1 | head -20
```

Expected: `ImportError` or test failures (file doesn't exist yet or functions not importable).

- [ ] **Step 3: Run tests with the implementation already in place**

The tests only use existing code (`process_articles_batch`, `score_article_risk`) that was written in previous tasks. They should pass immediately.

```bash
pytest tests/integration/test_sentiment_and_risk.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 4: Run full test suite**

```bash
pytest --tb=short -q
```

Expected: 153+ tests passing (142 + 11 risk scorer + 2 new signal aggregator + 7 integration = ~162 total; exact count depends on prior runs).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_sentiment_and_risk.py
git commit -m "test: week 3 integration tests — sentiment, classification, risk scoring"
```

---

## Task 5 [OPTIONAL]: LLM Classifier

**Files:**
- Create: `src/models/llm_classifier.py`
- Create: `tests/unit/test_llm_classifier.py`

Skip this task if time-constrained — the keyword classifier is sufficient for the current phase. The LLM classifier is a fallback/second-opinion layer for ambiguous articles.

Uses Groq API (already configured in `settings.GROQ_API_KEY` and `settings.LLM_MODEL`). The `requests` library is already installed.

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_llm_classifier.py`:

```python
"""
Unit tests for src/models/llm_classifier.py.
All tests mock the HTTP call — no real API calls, no API key needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.llm_classifier import classify_with_llm


def _mock_response(content: str) -> MagicMock:
    """Return a mock requests.Response with the given JSON content string."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock


class TestClassifyWithLLM:

    def test_returns_credit_relevant_true_for_bankruptcy(self):
        """LLM returns is_credit_relevant=true → function returns True."""
        response_json = '{"is_credit_relevant": true, "event_types": ["bankruptcy"]}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Company filed for bankruptcy under chapter 11.")

        assert result["is_credit_relevant"] is True
        assert "bankruptcy" in result["event_types"]

    def test_returns_credit_relevant_false_for_generic(self):
        """LLM returns is_credit_relevant=false → function returns False."""
        response_json = '{"is_credit_relevant": false, "event_types": []}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Team holds quarterly meeting in office.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []

    def test_returns_multiple_event_types(self):
        """LLM can return multiple event types."""
        response_json = '{"is_credit_relevant": true, "event_types": ["downgrade", "fraud"]}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Downgraded amid fraud investigation.")

        assert "downgrade" in result["event_types"]
        assert "fraud" in result["event_types"]

    def test_api_error_returns_fallback(self):
        """On API error, returns fallback result (not credit relevant, empty events)."""
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.side_effect = Exception("API timeout")
            result = classify_with_llm("Some article text.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []
        assert result["error"] is not None

    def test_malformed_json_returns_fallback(self):
        """If LLM returns unparseable JSON, returns fallback."""
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response("Sorry, I cannot classify this.")
            result = classify_with_llm("Some article text.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest tests/unit/test_llm_classifier.py -v 2>&1 | head -10
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/models/llm_classifier.py`**

```python
"""
LLM-based credit-relevance classifier using the configured LLM provider (Groq).

Falls back gracefully on API errors — never raises. Use as a second opinion
alongside the keyword classifier, not as a replacement.

Usage:
    from src.models.llm_classifier import classify_with_llm

    result = classify_with_llm("Company filed for bankruptcy.")
    # {"is_credit_relevant": True, "event_types": ["bankruptcy"], "error": None}
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import requests

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """You are a credit risk analyst. Given a financial news article,
determine if it is credit-relevant (i.e., it mentions events that could affect
a company's ability to repay debt). Respond ONLY with valid JSON matching this schema:
{"is_credit_relevant": boolean, "event_types": [list of strings]}

Valid event_types: default, bankruptcy, downgrade, restructuring, rating_watch,
covenant_breach, liquidity_crisis, fraud, regulatory_action, merger_acquisition,
management_change, earnings_miss, debt_issuance, layoffs, lawsuit.
Return an empty list if no events are present."""

_FALLBACK: Dict = {"is_credit_relevant": False, "event_types": [], "error": None}


def classify_with_llm(text: str) -> Dict:
    """
    Classify a text using the configured LLM.

    Returns:
        dict with keys: is_credit_relevant (bool), event_types (List[str]), error (str|None)
        On any error: returns fallback with error message set.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("classify_with_llm: GROQ_API_KEY not set, returning fallback.")
        return {**_FALLBACK, "error": "GROQ_API_KEY not configured"}

    try:
        response = requests.post(
            _GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text[:2000]},  # truncate to save tokens
                ],
                "temperature": 0.0,
                "max_tokens": 150,
            },
            timeout=15,
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return {
            "is_credit_relevant": bool(parsed.get("is_credit_relevant", False)),
            "event_types": list(parsed.get("event_types", [])),
            "error": None,
        }

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning(f"classify_with_llm: could not parse LLM response: {exc}")
        return {**_FALLBACK, "error": str(exc)}
    except Exception as exc:
        logger.error(f"classify_with_llm: API call failed: {exc}")
        return {**_FALLBACK, "error": str(exc)}
```

- [ ] **Step 4: Run tests — confirm all pass**

```bash
pytest tests/unit/test_llm_classifier.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/llm_classifier.py tests/unit/test_llm_classifier.py
git commit -m "feat: add optional LLM classifier via Groq API with fallback"
```

---

## Task 6: Week 3 Wrap — Re-aggregate + Final Checks

- [ ] **Step 1: Run the full test suite**

```bash
source venv/bin/activate
pytest --tb=short -q
```

Expected: 153+ tests passing, 0 failures.

- [ ] **Step 2: Re-aggregate signals with real risk scores**

```bash
docker-compose ps  # confirm postgres is up
python -m scripts.aggregate_signals
```

Expected: `Obligor-date pairs processed: 52`

- [ ] **Step 3: Spot-check risk scores in DB**

```bash
docker-compose exec postgres psql -U creditrisk -d creditrisk -c \
  "SELECT o.name, s.date, s.avg_sentiment, s.neg_article_count,
          s.credit_relevant_count, s.risk_score
   FROM obligor_daily_signals s
   JOIN obligors o ON o.id = s.obligor_id
   WHERE s.risk_score IS NOT NULL
   ORDER BY s.risk_score DESC
   LIMIT 10;"
```

Expected: 10 rows. `risk_score` values between 0.0 and 1.0. Higher risk scores should correspond to obligors with negative sentiment and credit-relevant articles.

- [ ] **Step 4: Week 3 completion checklist**

Verify each item manually:
- [ ] All articles have sentiment scores: `SELECT COUNT(*) FROM processed_articles WHERE sentiment_score IS NULL AND cleaned_text IS NOT NULL;` → should be 0
- [ ] Credit relevance classified: `SELECT is_credit_relevant, COUNT(*) FROM processed_articles GROUP BY is_credit_relevant;`
- [ ] Event types detected: `SELECT COUNT(*) FROM processed_articles WHERE event_types IS NOT NULL AND event_types != '{}';`
- [ ] Risk scores in signals: `SELECT COUNT(*) FROM obligor_daily_signals WHERE risk_score IS NOT NULL;` → should be 52
- [ ] Integration tests passing: covered in Step 1

- [ ] **Step 5: Commit**

```bash
git add -A
git status  # confirm only expected files
git commit -m "chore: week 3 wrap — all signals aggregated with risk scores"
```

---

## Self-Review

**Spec coverage:**
- ✅ `score_article_risk(processed_article: Dict) -> float` — Task 1
- ✅ Base 0.0, +0.5 credit relevant, +0.3 negative sentiment, +0.3 default, +0.2 downgrade, clamped — Task 1
- ✅ `aggregate_obligor_risk(obligor_id, days) -> float` — Task 1 (`risk_scorer.py`)
- ✅ `neg_article_count` = count where `sentiment < -0.1` — Task 3
- ✅ `avg_sentiment`, `credit_relevant_count` — already existed, preserved in Task 3
- ✅ `risk_score` stored in `obligor_daily_signals` — Tasks 2 + 3
- ✅ `classify_with_llm()` optional — Task 5
- ✅ Integration tests: `test_sentiment_scoring`, `test_credit_relevance`, `test_event_classification`, `test_full_enrichment_pipeline` — Task 4
- ✅ Week 3 checklist — Task 6

**Note on `event_summary`** (from spec): The spec mentions storing "most common event types" in signals. This is omitted — `ObligorDailySignals` has no such column and the dashboard can derive it from `processed_articles` directly. YAGNI.

**Type consistency:** `score_article_risk` takes `Dict` with keys `sentiment_score`, `is_credit_relevant`, `event_types` — used consistently in signal_aggregator.py and integration tests.
