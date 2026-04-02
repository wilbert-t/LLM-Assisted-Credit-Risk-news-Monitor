"""
Unit tests for FastAPI alert endpoints.

Tests cover:
- GET /api/alerts with filters
- GET /api/alerts/{id} single alert
- GET /api/obligors/{id}/summary
"""

from datetime import datetime, timezone, date as datetime_date
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.api import alerts as alerts_module
from src.db.models import Alert, Obligor, ObligorDailySignals


@pytest.fixture
def obligor(db: Session):
    """Create test obligor."""
    obligor = Obligor(id=1, name="Test Corp", ticker="TST", sector="Tech")
    db.add(obligor)
    db.commit()
    return obligor


@pytest.fixture
def alerts(db: Session, obligor: Obligor):
    """Create test alerts."""
    alerts_list = []
    for i in range(3):
        alert = Alert(
            obligor_id=obligor.id,
            triggered_at=datetime.now(timezone.utc),
            severity="HIGH" if i % 2 == 0 else "MEDIUM",
            summary=f"Alert {i}",
            event_types=["bankruptcy"] if i == 0 else [],
            article_ids=[],
            extra_data={"rule_name": f"Rule{i}"},
        )
        db.add(alert)
        alerts_list.append(alert)
    db.commit()
    return alerts_list


def test_list_alerts(db: Session, alerts):
    """Test list_alerts endpoint logic."""
    # Call with explicit None for Query params (not using them in this test)
    result = alerts_module.list_alerts(severity=None, date_from=None, date_to=None, obligor_id=None, limit=10, offset=0, db=db)
    assert result.total > 0
    assert len(result.alerts) > 0


def test_list_alerts_with_severity_filter(db: Session, alerts):
    """Test list_alerts with severity filter."""
    result = alerts_module.list_alerts(severity="HIGH", date_from=None, date_to=None, obligor_id=None, limit=10, offset=0, db=db)
    for alert in result.alerts:
        assert alert.severity == "HIGH"


def test_list_alerts_with_obligor_filter(db: Session, obligor, alerts):
    """Test list_alerts with obligor_id filter."""
    result = alerts_module.list_alerts(severity=None, date_from=None, date_to=None, obligor_id=obligor.id, limit=10, offset=0, db=db)
    for alert in result.alerts:
        assert alert.obligor_id == obligor.id


def test_list_alerts_with_pagination(db: Session, alerts):
    """Test list_alerts with limit and offset."""
    result = alerts_module.list_alerts(severity=None, date_from=None, date_to=None, obligor_id=None, limit=1, offset=0, db=db)
    assert len(result.alerts) <= 1


def test_get_alert(db: Session, alerts):
    """Test get_alert endpoint logic."""
    alert_id = alerts[0].id
    result = alerts_module.get_alert(alert_id, db=db)
    assert result.id == alert_id
    assert result.severity == alerts[0].severity


def test_get_alert_not_found(db: Session):
    """Test get_alert not found."""
    with pytest.raises(HTTPException) as exc_info:
        alerts_module.get_alert(9999, db=db)
    assert exc_info.value.status_code == 404


def test_get_obligor_summary_uses_cache(db: Session, obligor):
    """Test get_obligor_summary returns cached summary."""
    with patch("src.api.alerts.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "company": "Test Corp",
            "summary": "Test summary",
            "risk_level": "medium",
            "key_events": [],
            "concerns": [],
            "positive_factors": [],
            "confidence": 0.8,
            "cached": True,
        }

        result = alerts_module.get_obligor_summary(obligor.id, db=db)
        assert result.company == "Test Corp"


def test_get_obligor_summary_obligor_not_found(db: Session):
    """Test get_obligor_summary obligor not found."""
    with pytest.raises(HTTPException) as exc_info:
        alerts_module.get_obligor_summary(9999, db=db)
    assert exc_info.value.status_code == 404


def test_list_alerts_response_has_total(db: Session, alerts):
    """Test that alert list response includes total."""
    result = alerts_module.list_alerts(severity=None, date_from=None, date_to=None, obligor_id=None, limit=10, offset=0, db=db)
    assert result.total > 0


def test_get_obligor_summary_response_format(db: Session, obligor):
    """Test that summary response has required fields."""
    with patch("src.api.alerts.ObligorSummarizer") as mock_summarizer_class:
        mock_summarizer = MagicMock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_obligor_risk.return_value = {
            "company": "Test Corp",
            "summary": "Test summary",
            "risk_level": "medium",
            "key_events": ["event1"],
            "concerns": ["concern1"],
            "positive_factors": [],
            "confidence": 0.8,
            "cached": False,
        }

        result = alerts_module.get_obligor_summary(obligor.id, db=db)
        assert result.company == "Test Corp"
        assert result.summary == "Test summary"
        assert result.risk_level == "medium"
