"""
Unit tests for alert generator.

Tests cover:
- Alert creation on rule fire
- Deduplication within 24h
- Fallback when summarizer fails
- Early return when no signals
- check_all_obligors processes all obligors
- Error isolation (one fails, others continue)
"""

from datetime import datetime, timedelta, timezone, date as datetime_date
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import cast, String
from sqlalchemy.orm import Session

from src.alerts.generator import generate_alerts, check_all_obligors
from src.db.models import Alert, Obligor, ObligorDailySignals
from src.rag.summarizer import SummarizerError, ObligorSummarizer


@pytest.fixture
def obligor(db: Session):
    """Create a test obligor."""
    obligor = Obligor(
        id=1,
        name="Test Corp",
        ticker="TST",
        sector="Technology",
    )
    db.add(obligor)
    db.commit()
    return obligor


@pytest.fixture
def obligor2(db: Session):
    """Create a second test obligor."""
    obligor = Obligor(
        id=2,
        name="Risk Corp",
        ticker="RISK",
        sector="Finance",
    )
    db.add(obligor)
    db.commit()
    return obligor


@pytest.fixture
def obligor_signals(db: Session, obligor):
    """Create daily signals for obligor (stored in DB)."""
    signals = ObligorDailySignals(
        obligor_id=obligor.id,
        date=datetime_date(2026, 4, 2),
        credit_relevant_count=5,
        neg_article_count=2,
        avg_sentiment=-0.6,
    )
    db.add(signals)
    db.commit()
    return signals


def test_generate_alerts_on_rule_fire(db: Session, obligor, obligor_signals):
    """Test that alert is created when rule fires."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "summary": "Test summary",
            "risk_level": "critical",
        }

        with patch("src.alerts.generator._enrich_signals_with_event_types") as mock_enrich:
            def enrich_fn(signals, oid, db):
                signals.event_types = ["bankruptcy"]

            mock_enrich.side_effect = enrich_fn

            generate_alerts(obligor.id, db=db)

            alerts = db.query(Alert).filter_by(obligor_id=obligor.id).all()
            assert len(alerts) > 0
            assert alerts[0].severity in ["CRITICAL", "HIGH", "MEDIUM"]


def test_generate_alerts_dedup_within_24h(db: Session, obligor, obligor_signals):
    """Test that dedup prevents alerts from rapid re-firing."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "summary": "Test summary",
            "risk_level": "critical",
        }

        with patch("src.alerts.generator._enrich_signals_with_event_types") as mock_enrich:
            def enrich_fn(signals, oid, db_):
                signals.event_types = ["bankruptcy"]

            mock_enrich.side_effect = enrich_fn

            # First call - should create alerts
            generate_alerts(obligor.id, db=db)
            count_1 = db.query(Alert).filter_by(obligor_id=obligor.id).count()
            assert count_1 > 0

            # Second call within 24h - should create fewer or same alerts due to dedup
            generate_alerts(obligor.id, db=db)
            count_2 = db.query(Alert).filter_by(obligor_id=obligor.id).count()
            # At most 1 new alert (Rule5_MultipleEvents) should be created
            assert count_2 - count_1 <= 1


def test_generate_alerts_fallback_on_summarizer_error(db: Session, obligor, obligor_signals):
    """Test fallback alert creation when summarizer fails."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.side_effect = SummarizerError("API failed")

        with patch("src.alerts.generator._enrich_signals_with_event_types") as mock_enrich:
            def enrich_fn(signals, oid, db):
                signals.event_types = ["bankruptcy"]

            mock_enrich.side_effect = enrich_fn

            generate_alerts(obligor.id, db=db)

            alerts = db.query(Alert).filter_by(obligor_id=obligor.id).all()
            assert len(alerts) > 0
            # Should be marked as fallback
            if alerts:
                assert alerts[0].extra_data.get("fallback") is True


def test_generate_alerts_no_signals_early_return(db: Session, obligor):
    """Test early return when no signals exist."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer

        generate_alerts(obligor.id, db=db)

        # No summarizer call should be made
        mock_summarizer.summarize_obligor_risk.assert_not_called()

        alerts = db.query(Alert).filter_by(obligor_id=obligor.id).all()
        assert len(alerts) == 0


def test_check_all_obligors_processes_all(db: Session, obligor, obligor2, obligor_signals):
    """Test that check_all_obligors processes all obligors."""
    with patch("src.alerts.generator.generate_alerts") as mock_gen:
        check_all_obligors(db=db)

        # Should be called for each obligor
        assert mock_gen.call_count >= 2


def test_check_all_obligors_error_isolation(db: Session, obligor, obligor2, obligor_signals):
    """Test that error on one obligor doesn't stop processing others."""
    # Add signals for obligor2
    signals2 = ObligorDailySignals(
        obligor_id=obligor2.id,
        date=datetime_date(2026, 4, 2),
        credit_relevant_count=3,
        neg_article_count=1,
        avg_sentiment=-0.3,
    )
    db.add(signals2)
    db.commit()

    call_count = 0

    def side_effect(oid, db=None):
        nonlocal call_count
        call_count += 1
        if oid == obligor.id:
            raise Exception("Test error")

    with patch("src.alerts.generator.generate_alerts") as mock_gen:
        mock_gen.side_effect = side_effect

        # Should not raise
        check_all_obligors(db=db)

        # Should have attempted both
        assert call_count >= 2


def test_generate_alerts_with_open_db(obligor_signals):
    """Test that generate_alerts opens DB when not provided."""
    with patch("src.alerts.generator.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = obligor_signals

        with patch("src.alerts.generator.ObligorSummarizer"):
            generate_alerts(1)

            # Should have opened and closed DB
            mock_db.close.assert_called_once()


def test_generate_alerts_does_not_close_provided_db(db: Session, obligor, obligor_signals):
    """Test that generate_alerts doesn't close DB if one is provided."""
    with patch("src.alerts.generator.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "summary": "Test summary",
            "risk_level": "critical",
        }

        with patch("src.alerts.generator._enrich_signals_with_event_types") as mock_enrich:
            def enrich_fn(signals, oid, db_):
                signals.event_types = ["bankruptcy"]

            mock_enrich.side_effect = enrich_fn

            generate_alerts(obligor.id, db=db)

            # DB should still be usable
            query = db.query(Obligor).filter_by(id=obligor.id).first()
            assert query is not None
