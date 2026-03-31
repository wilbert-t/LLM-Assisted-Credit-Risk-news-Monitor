"""
Unit tests for src/processors/signal_aggregator.py.
Uses real PostgreSQL test DB via the `db` fixture (transactional rollback).
"""

import datetime

import pytest

from src.db.models import ArticleObligor, ObligorDailySignals
from src.processors.signal_aggregator import aggregate_all_daily, aggregate_daily_signals
from tests.factories import article_model, obligor_model, processed_article_model

TODAY = datetime.date(2026, 3, 28)
YESTERDAY = datetime.date(2026, 3, 27)

_url_counter = 0


def _setup_link(db, obligor, date, sentiment_score=None, is_credit_relevant=False, **kwargs):
    """Create article + processed_article + article_obligor link for given date."""
    global _url_counter
    _url_counter += 1
    from datetime import timezone
    pub_dt = datetime.datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    article = article_model(
        url=f"https://example.com/sig-{obligor.id}-{date}-{_url_counter}",
        published_at=pub_dt,
    )
    db.add(article)
    db.flush()

    pa = processed_article_model(
        article_id=article.id,
        sentiment_score=sentiment_score,
        is_credit_relevant=is_credit_relevant,
        **kwargs,
    )
    db.add(pa)
    db.flush()

    link = ArticleObligor(article_id=article.id, obligor_id=obligor.id)
    db.add(link)
    db.flush()

    return article


# ---------------------------------------------------------------------------
# TestAggregateDailySignals
# ---------------------------------------------------------------------------

class TestAggregateDailySignals:

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

    def test_avg_sentiment_is_none_when_no_scores(self, db):
        o = obligor_model(name="GS Corp", ticker="GS2")
        db.add(o)
        db.flush()

        _setup_link(db, o, TODAY, sentiment_score=None)

        result = aggregate_daily_signals(o.id, TODAY, db=db)

        assert result["avg_sentiment"] is None

    def test_avg_sentiment_computed_when_scores_exist(self, db):
        o = obligor_model(name="JPM Corp", ticker="JPM2")
        db.add(o)
        db.flush()

        _setup_link(db, o, TODAY, sentiment_score=0.8)
        _setup_link(db, o, TODAY, sentiment_score=0.4)

        result = aggregate_daily_signals(o.id, TODAY, db=db)

        assert result["avg_sentiment"] == pytest.approx(0.6, abs=1e-6)

    def test_credit_relevant_count(self, db):
        o = obligor_model(name="BAC Corp", ticker="BAC2")
        db.add(o)
        db.flush()

        _setup_link(db, o, TODAY, is_credit_relevant=True)
        _setup_link(db, o, TODAY, is_credit_relevant=False)

        result = aggregate_daily_signals(o.id, TODAY, db=db)

        assert result["credit_relevant_count"] == 1

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

    def test_returns_zero_count_when_no_articles(self, db):
        o = obligor_model(name="Empty Corp", ticker="EMP2")
        db.add(o)
        db.flush()

        result = aggregate_daily_signals(o.id, TODAY, db=db)

        assert result["neg_article_count"] == 0
        assert result["avg_sentiment"] is None
        assert result["credit_relevant_count"] == 0

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
        _setup_link(db, o, TODAY, sentiment_score=-0.5, is_credit_relevant=True, event_types=[])
        # Article 2: credit_relevant=False, sentiment=0.5, no events → 0.0
        _setup_link(db, o, TODAY, sentiment_score=0.5, is_credit_relevant=False, event_types=[])

        result = aggregate_daily_signals(o.id, TODAY, db=db)

        # avg of [0.8, 0.0] = 0.4
        assert result["risk_score"] == pytest.approx(0.4, abs=1e-6)


# ---------------------------------------------------------------------------
# TestAggregateAllDaily
# ---------------------------------------------------------------------------

class TestAggregateAllDaily:

    def test_processes_all_obligor_date_pairs(self, db):
        o1 = obligor_model(name="All Corp A", ticker="ACA2")
        o2 = obligor_model(name="All Corp B", ticker="ACB2")
        db.add_all([o1, o2])
        db.flush()

        _setup_link(db, o1, TODAY)
        _setup_link(db, o1, YESTERDAY)
        _setup_link(db, o2, TODAY)
        _setup_link(db, o2, YESTERDAY)

        count = aggregate_all_daily(db=db)

        assert count == 4

    def test_returns_zero_when_no_links(self, db):
        count = aggregate_all_daily(db=db)
        assert count == 0
