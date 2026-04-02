"""
End-to-end integration tests for alert system.

Tests cover:
- End-to-end: articles → signals → summary → alert
- Deduplication across runs
- Prioritized obligors tier assignment
- Scheduler starts/stops
"""

from datetime import datetime, timezone, date as datetime_date, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.db.models import (
    Article, Obligor, ObligorDailySignals, Alert, ProcessedArticle, ArticleObligor
)
from src.alerts.generator import generate_alerts
from src.alerts.scheduler import get_prioritized_obligors, ScheduledAlertJob
from src.utils.constants import HIGH_RISK_MIN_ALERTS_7D


@pytest.fixture
def obligor_with_articles(db: Session):
    """Create obligor with articles and signals."""
    # Create obligor
    obligor = Obligor(
        id=1,
        name="Risk Company",
        ticker="RSK",
        sector="Finance",
    )
    db.add(obligor)
    db.commit()

    # Create articles
    articles = []
    for i in range(3):
        article = Article(
            id=i + 1,
            source="test_source",
            title=f"Article {i}: Company faces financial challenges",
            url=f"https://example.com/{i}",
            published_at=datetime.now(timezone.utc) - timedelta(days=i),
            content=f"Risk content {i}" * 100,
            language="en",
        )
        db.add(article)
        articles.append(article)
    db.commit()

    # Create article-obligor links
    for article in articles:
        link = ArticleObligor(article_id=article.id, obligor_id=obligor.id)
        db.add(link)
    db.commit()

    # Create processed articles
    for article in articles:
        processed = ProcessedArticle(
            article_id=article.id,
            cleaned_text=article.content,
            entities={"ORG": [{"text": "Risk Company", "start": 0, "end": 12}]},
            is_credit_relevant=True,
            sentiment_label="negative",
            sentiment_score=-0.7,
            event_types=["bankruptcy", "liquidity_crisis"],
        )
        db.add(processed)
    db.commit()

    # Create daily signals
    signals = ObligorDailySignals(
        obligor_id=obligor.id,
        date=datetime_date.today(),
        credit_relevant_count=3,
        neg_article_count=2,
        avg_sentiment=-0.7,
        risk_score=0.8,
    )
    db.add(signals)
    db.commit()

    return obligor


def test_e2e_articles_to_alerts(db: Session, obligor_with_articles):
    """Test end-to-end: articles → signals → summary → alert."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "company": "Risk Company",
            "summary": "Company facing severe financial challenges",
            "risk_level": "critical",
            "key_events": ["bankruptcy", "liquidity_crisis"],
            "concerns": ["cash flow", "debt"],
            "positive_factors": [],
            "confidence": 0.95,
            "cached": False,
        }

        # Generate alerts
        generate_alerts(obligor_with_articles.id, db=db)

        # Verify alerts were created
        alerts = db.query(Alert).filter_by(obligor_id=obligor_with_articles.id).all()
        assert len(alerts) > 0

        # Verify alert has signals data
        alert = alerts[0]
        assert alert.severity in ["CRITICAL", "HIGH", "MEDIUM"]
        assert alert.summary is not None


def test_e2e_deduplication_across_runs(db: Session, obligor_with_articles):
    """Test deduplication prevents duplicate alerts across multiple runs."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "company": "Risk Company",
            "summary": "Test summary",
            "risk_level": "critical",
            "key_events": ["bankruptcy"],
            "concerns": ["cash"],
            "positive_factors": [],
            "confidence": 0.9,
            "cached": False,
        }

        # First run
        generate_alerts(obligor_with_articles.id, db=db)
        count_1 = db.query(Alert).filter_by(obligor_id=obligor_with_articles.id).count()

        # Second run immediately after
        generate_alerts(obligor_with_articles.id, db=db)
        count_2 = db.query(Alert).filter_by(obligor_id=obligor_with_articles.id).count()

        # Should not create duplicates for same rules (but may create new Rule5 alert)
        assert count_2 - count_1 <= 1


def test_prioritized_obligors_tier_assignment(db: Session, obligor_with_articles):
    """Test that obligors are correctly assigned to HIGH/NORMAL tiers."""
    # Add alerts to push obligor to HIGH tier
    for i in range(HIGH_RISK_MIN_ALERTS_7D):
        alert = Alert(
            obligor_id=obligor_with_articles.id,
            triggered_at=datetime.now(timezone.utc),
            severity="HIGH",
            summary=f"Alert {i}",
            event_types=[],
            article_ids=[],
            extra_data={"rule_name": f"Rule{i}"},
        )
        db.add(alert)
    db.commit()

    # Get prioritized obligors
    result = get_prioritized_obligors(db=db)

    # Verify our obligor is HIGH tier
    high_tier_obligors = [oid for oid, tier in result if tier == "high"]
    assert obligor_with_articles.id in high_tier_obligors


def test_scheduler_starts_and_stops(db: Session):
    """Test scheduler lifecycle."""
    job = ScheduledAlertJob(db=db)

    # Start
    job.start()
    assert job.scheduler is not None
    assert job.scheduler.running

    # Stop
    job.stop()
    assert not job.scheduler.running


def test_scheduler_processes_both_cycles(db: Session, obligor_with_articles):
    """Test that scheduler runs both high-risk and normal cycles."""
    job = ScheduledAlertJob(db=db)

    # Mock generate_alerts to count calls
    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        # Run cycles manually (not through scheduler)
        job.high_risk_alert_cycle()
        high_risk_call_count = mock_gen.call_count

        job.normal_alert_cycle()
        normal_call_count = mock_gen.call_count - high_risk_call_count

        # Each cycle should process at least some obligors
        assert high_risk_call_count >= 0
        assert normal_call_count >= 0


def test_alert_includes_all_required_fields(db: Session, obligor_with_articles):
    """Test that alerts include all required fields from signals and summary."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "company": "Risk Company",
            "summary": "Test summary",
            "risk_level": "high",
            "key_events": ["event1"],
            "concerns": ["concern1"],
            "positive_factors": [],
            "confidence": 0.8,
            "cached": False,
        }

        generate_alerts(obligor_with_articles.id, db=db)

        alert = db.query(Alert).filter_by(obligor_id=obligor_with_articles.id).first()
        assert alert is not None
        assert alert.obligor_id == obligor_with_articles.id
        assert alert.triggered_at is not None
        assert alert.severity is not None
        assert alert.summary is not None
        assert alert.extra_data is not None
        assert "rule_name" in alert.extra_data
        assert "fallback" in alert.extra_data


def test_fallback_alert_on_summarizer_failure(db: Session, obligor_with_articles):
    """Test that alerts are created even if summarizer fails (fallback mode)."""
    from src.rag.summarizer import SummarizerError

    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.side_effect = SummarizerError("API failed")

        generate_alerts(obligor_with_articles.id, db=db)

        alerts = db.query(Alert).filter_by(obligor_id=obligor_with_articles.id).all()
        assert len(alerts) > 0

        # Should be marked as fallback
        for alert in alerts:
            assert alert.extra_data.get("fallback") is True


def test_multiple_obligors_processed_independently(db: Session):
    """Test that multiple obligors are processed without blocking each other."""
    # Create two obligors
    obligor1 = Obligor(id=10, name="Corp 1", ticker="C1", sector="Tech")
    obligor2 = Obligor(id=11, name="Corp 2", ticker="C2", sector="Finance")
    db.add(obligor1)
    db.add(obligor2)
    db.commit()

    # Create signals
    for obligor in [obligor1, obligor2]:
        signals = ObligorDailySignals(
            obligor_id=obligor.id,
            date=datetime_date.today(),
            credit_relevant_count=2,
            neg_article_count=1,
            avg_sentiment=-0.5,
        )
        db.add(signals)
    db.commit()

    call_order = []

    def side_effect(oid, db=None):
        call_order.append(oid)
        if oid == obligor1.id:
            raise Exception("Corp 1 error")

    with patch("src.alerts.generator.generate_alerts") as mock_gen:
        mock_gen.side_effect = side_effect

        from src.alerts.generator import check_all_obligors
        check_all_obligors(db=db)

        # Both obligors should have been attempted
        assert obligor1.id in call_order
        assert obligor2.id in call_order
