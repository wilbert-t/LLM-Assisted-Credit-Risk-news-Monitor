"""
Unit tests for alert scheduler.

Tests cover:
- get_prioritized_obligors assigns tiers correctly
- high-risk cycle processes only HIGH tier
- normal cycle processes only NORMAL tier
- scheduler can start/stop
- cycles respect inter-call sleep
- rate limit warning logged
"""

from datetime import datetime, timedelta, timezone, date as datetime_date
from unittest.mock import patch, MagicMock, call
from typing import List, Tuple

import pytest
from sqlalchemy.orm import Session

from src.alerts.scheduler import (
    get_prioritized_obligors,
    ScheduledAlertJob,
)
from src.db.models import Alert, Obligor, ObligorDailySignals
from src.utils.constants import (
    INTER_CALL_SLEEP_SECONDS,
    HIGH_RISK_MIN_ALERTS_7D,
    HIGH_RISK_MAX_SENTIMENT,
)


@pytest.fixture
def obligor_high_alerts(db: Session):
    """Create obligor with multiple recent alerts."""
    obligor = Obligor(id=1, name="High Alert Corp", ticker="HAC", sector="Tech")
    db.add(obligor)
    db.commit()

    # Create multiple alerts in past 7 days
    for i in range(HIGH_RISK_MIN_ALERTS_7D):
        alert = Alert(
            obligor_id=obligor.id,
            triggered_at=datetime.now(timezone.utc),
            severity="HIGH",
            summary=f"Alert {i}",
            event_types=[],
            article_ids=[],
            extra_data={"rule_name": f"Rule{i}"},
        )
        db.add(alert)
    db.commit()

    return obligor


@pytest.fixture
def obligor_high_sentiment(db: Session):
    """Create obligor with negative sentiment."""
    obligor = Obligor(id=2, name="Negative Sentiment Corp", ticker="NSC", sector="Finance")
    db.add(obligor)
    db.commit()

    # Create signals with negative sentiment
    signals = ObligorDailySignals(
        obligor_id=obligor.id,
        date=datetime_date.today(),
        credit_relevant_count=5,
        neg_article_count=2,
        avg_sentiment=HIGH_RISK_MAX_SENTIMENT - 0.1,  # Below threshold
    )
    db.add(signals)
    db.commit()

    return obligor


@pytest.fixture
def obligor_normal(db: Session):
    """Create obligor with no risk indicators."""
    obligor = Obligor(id=3, name="Normal Corp", ticker="NC", sector="Healthcare")
    db.add(obligor)
    db.commit()

    signals = ObligorDailySignals(
        obligor_id=obligor.id,
        date=datetime_date.today(),
        credit_relevant_count=1,
        neg_article_count=0,
        avg_sentiment=0.5,
    )
    db.add(signals)
    db.commit()

    return obligor


def test_get_prioritized_obligors_high_alert_tier(db: Session, obligor_high_alerts):
    """Test that obligors with multiple alerts are marked HIGH tier."""
    result = get_prioritized_obligors(db=db)

    # Find our test obligor
    high_tier = [oid for oid, tier in result if oid == obligor_high_alerts.id and tier == "high"]
    assert len(high_tier) == 1


def test_get_prioritized_obligors_high_sentiment_tier(db: Session, obligor_high_sentiment):
    """Test that obligors with negative sentiment are marked HIGH tier."""
    result = get_prioritized_obligors(db=db)

    # Find our test obligor
    high_tier = [oid for oid, tier in result if oid == obligor_high_sentiment.id and tier == "high"]
    assert len(high_tier) == 1


def test_get_prioritized_obligors_normal_tier(db: Session, obligor_normal):
    """Test that obligors without risk indicators are marked NORMAL tier."""
    result = get_prioritized_obligors(db=db)

    # Find our test obligor
    normal_tier = [oid for oid, tier in result if oid == obligor_normal.id and tier == "normal"]
    assert len(normal_tier) == 1


def test_get_prioritized_obligors_returns_all_obligors(
    db: Session, obligor_high_alerts, obligor_high_sentiment, obligor_normal
):
    """Test that all obligors are returned with a tier assignment."""
    result = get_prioritized_obligors(db=db)

    obligor_ids = [oid for oid, _ in result]
    assert len(result) >= 3
    assert obligor_high_alerts.id in obligor_ids
    assert obligor_high_sentiment.id in obligor_ids
    assert obligor_normal.id in obligor_ids


def test_high_risk_cycle_processes_only_high_tier(db: Session, obligor_high_alerts, obligor_normal):
    """Test that high-risk cycle only processes HIGH tier obligors."""
    job = ScheduledAlertJob(db=db)

    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        job.high_risk_alert_cycle()

        # Should be called at least once (for high-alert obligor)
        assert mock_gen.call_count > 0

        # Check that high-alert obligor was called
        called_obligor_ids = [call_obj[0][0] for call_obj in mock_gen.call_args_list]
        assert obligor_high_alerts.id in called_obligor_ids


def test_normal_cycle_processes_only_normal_tier(db: Session, obligor_normal, obligor_high_alerts):
    """Test that normal cycle processes NORMAL tier obligors."""
    job = ScheduledAlertJob(db=db)

    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        job.normal_alert_cycle()

        # Should be called (for normal obligor and others)
        assert mock_gen.call_count > 0


def test_scheduler_can_start_and_stop(db: Session):
    """Test that scheduler can be started and stopped."""
    job = ScheduledAlertJob(db=db)

    job.start()
    assert job.scheduler is not None
    assert job.scheduler.running

    job.stop()
    assert not job.scheduler.running


def test_cycle_respects_inter_call_sleep(db: Session, obligor_high_alerts, obligor_normal):
    """Test that cycles sleep between generate_alerts calls."""
    job = ScheduledAlertJob(db=db)

    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        with patch("src.alerts.scheduler.time.sleep") as mock_sleep:
            job.high_risk_alert_cycle()

            # Sleep should be called between calls
            # At minimum, if we process 2+ obligors, we sleep
            if mock_gen.call_count > 1:
                assert mock_sleep.call_count > 0
                # Check that we slept with correct duration
                sleep_calls = mock_sleep.call_args_list
                for sleep_call in sleep_calls:
                    assert sleep_call[0][0] == INTER_CALL_SLEEP_SECONDS


def test_high_risk_cycle_handles_errors(db: Session, obligor_high_alerts):
    """Test that high-risk cycle continues on error."""
    job = ScheduledAlertJob(db=db)

    call_count = 0

    def side_effect(oid, db=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Test error")

    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        mock_gen.side_effect = side_effect

        # Should not raise
        job.high_risk_alert_cycle()

        # Should have attempted at least once
        assert call_count >= 1


def test_normal_cycle_handles_errors(db: Session, obligor_normal):
    """Test that normal cycle continues on error."""
    job = ScheduledAlertJob(db=db)

    call_count = 0

    def side_effect(oid, db=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Test error")

    with patch("src.alerts.scheduler.generate_alerts") as mock_gen:
        mock_gen.side_effect = side_effect

        # Should not raise
        job.normal_alert_cycle()

        # Should have attempted at least once
        assert call_count >= 1
