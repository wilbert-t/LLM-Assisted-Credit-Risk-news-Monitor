"""Unit tests for alert rules engine."""
from datetime import date
from unittest.mock import MagicMock
import pytest
from src.alerts.rules import AlertEngine, AlertRule
from src.db.models import ObligorDailySignals
from src.utils.constants import (
    ALERT_RULE_CREDIT_EVENT,
    ALERT_RULE_COVENANT_LIQUIDITY,
    ALERT_RULE_DOWNGRADE_WATCH,
    ALERT_RULE_SENTIMENT_SPIKE,
    ALERT_RULE_MULTIPLE_EVENTS,
    SENTIMENT_SPIKE_THRESHOLD,
    SENTIMENT_SPIKE_MIN_ARTICLES,
    MULTIPLE_EVENTS_THRESHOLD,
)


@pytest.fixture
def alert_engine():
    return AlertEngine()


@pytest.fixture
def mock_db():
    return MagicMock()


def test_rule_credit_event_fires_on_default(alert_engine, mock_db):
    """Rule 1: Fires on default event."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["default", "downgrade"]
    signals.avg_sentiment = -0.3
    signals.credit_relevant_count = 2

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_CREDIT_EVENT for r in triggered)
    critical = next(r for r in triggered if r["rule_name"] == ALERT_RULE_CREDIT_EVENT)
    assert critical["severity"] == "CRITICAL"


def test_rule_credit_event_fires_on_bankruptcy(alert_engine, mock_db):
    """Rule 1: Fires on bankruptcy event."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["bankruptcy"]
    signals.avg_sentiment = -0.8
    signals.credit_relevant_count = 5

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_CREDIT_EVENT for r in triggered)


def test_rule_credit_event_fires_on_fraud(alert_engine, mock_db):
    """Rule 1: Fires on fraud event."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["fraud"]
    signals.avg_sentiment = -0.5
    signals.credit_relevant_count = 3

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_CREDIT_EVENT for r in triggered)


def test_rule_covenant_liquidity_fires_on_breach(alert_engine, mock_db):
    """Rule 2: Fires on covenant breach."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["covenant_breach"]
    signals.avg_sentiment = -0.2
    signals.credit_relevant_count = 1

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_COVENANT_LIQUIDITY for r in triggered)
    covenant = next(r for r in triggered if r["rule_name"] == ALERT_RULE_COVENANT_LIQUIDITY)
    assert covenant["severity"] == "HIGH"


def test_rule_covenant_liquidity_fires_on_liquidity_crisis(alert_engine, mock_db):
    """Rule 2: Fires on liquidity crisis."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["liquidity_crisis"]
    signals.avg_sentiment = -0.5
    signals.credit_relevant_count = 2

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_COVENANT_LIQUIDITY for r in triggered)


def test_rule_downgrade_watch_fires_on_downgrade(alert_engine, mock_db):
    """Rule 3: Fires on downgrade event."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["downgrade"]
    signals.avg_sentiment = -0.1
    signals.credit_relevant_count = 1

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_DOWNGRADE_WATCH for r in triggered)
    downgrade = next(r for r in triggered if r["rule_name"] == ALERT_RULE_DOWNGRADE_WATCH)
    assert downgrade["severity"] == "MEDIUM"


def test_rule_downgrade_watch_fires_on_rating_watch(alert_engine, mock_db):
    """Rule 3: Fires on rating watch event."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["rating_watch"]
    signals.avg_sentiment = 0.1
    signals.credit_relevant_count = 1

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_DOWNGRADE_WATCH for r in triggered)


def test_rule_sentiment_spike_fires_on_negative_sentiment(alert_engine, mock_db):
    """Rule 4: Fires on negative sentiment spike with 3+ articles."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["earnings_miss"]
    signals.avg_sentiment = -0.6
    signals.credit_relevant_count = 3

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_SENTIMENT_SPIKE for r in triggered)
    sentiment = next(r for r in triggered if r["rule_name"] == ALERT_RULE_SENTIMENT_SPIKE)
    assert sentiment["severity"] == "MEDIUM"


def test_rule_sentiment_spike_does_not_fire_on_insufficient_articles(alert_engine, mock_db):
    """Rule 4: Does not fire with <3 articles."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["earnings_miss"]
    signals.avg_sentiment = -0.6
    signals.credit_relevant_count = 2

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert not any(r["rule_name"] == ALERT_RULE_SENTIMENT_SPIKE for r in triggered)


def test_rule_sentiment_spike_does_not_fire_on_positive_sentiment(alert_engine, mock_db):
    """Rule 4: Does not fire if sentiment > -0.5."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["earnings_miss"]
    signals.avg_sentiment = -0.4
    signals.credit_relevant_count = 5

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert not any(r["rule_name"] == ALERT_RULE_SENTIMENT_SPIKE for r in triggered)


def test_rule_multiple_events_fires_on_2_types(alert_engine, mock_db):
    """Rule 5: Fires on 2+ distinct events in 48h."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["downgrade", "covenant_breach"]
    signals.avg_sentiment = -0.2
    signals.credit_relevant_count = 1

    # Mock the query chain: db.query(Alert).filter(...).filter(...).count()
    # This mimics: db.query(Alert).filter(Alert.obligor_id==1).filter(Alert.triggered_at>=cutoff).count()
    count_mock = MagicMock(return_value=2)
    filter2_mock = MagicMock()
    filter2_mock.count = count_mock
    filter1_mock = MagicMock()
    filter1_mock.filter = MagicMock(return_value=filter2_mock)
    mock_db.query = MagicMock(return_value=filter1_mock)

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert any(r["rule_name"] == ALERT_RULE_MULTIPLE_EVENTS for r in triggered)
    multi = next(r for r in triggered if r["rule_name"] == ALERT_RULE_MULTIPLE_EVENTS)
    assert multi["severity"] == "HIGH"


def test_no_alerts_fired_on_normal_signals(alert_engine, mock_db):
    """No alerts on low-risk signals."""
    signals = MagicMock(spec=ObligorDailySignals)
    signals.event_types = ["earnings_miss"]
    signals.avg_sentiment = -0.1
    signals.credit_relevant_count = 1

    # Mock the query chain for count=0
    count_mock = MagicMock(return_value=0)
    filter2_mock = MagicMock()
    filter2_mock.count = count_mock
    filter1_mock = MagicMock()
    filter1_mock.filter = MagicMock(return_value=filter2_mock)
    mock_db.query = MagicMock(return_value=filter1_mock)

    triggered = alert_engine.evaluate(1, date.today(), signals, None, mock_db)
    assert len(triggered) == 0
