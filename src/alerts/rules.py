"""Alert rules engine for credit risk evaluation."""
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.db.models import Alert, ObligorDailySignals
from src.utils.constants import (
    ALERT_RULE_CREDIT_EVENT,
    ALERT_RULE_COVENANT_LIQUIDITY,
    ALERT_RULE_DOWNGRADE_WATCH,
    ALERT_RULE_SENTIMENT_SPIKE,
    ALERT_RULE_MULTIPLE_EVENTS,
    SENTIMENT_SPIKE_THRESHOLD,
    SENTIMENT_SPIKE_MIN_ARTICLES,
    MULTIPLE_EVENTS_THRESHOLD,
    MULTIPLE_EVENTS_WINDOW_HOURS,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlertRule:
    """Single alert rule with name, severity, and evaluation function."""

    def __init__(self, name: str, severity: str, condition_fn):
        self.name = name
        self.severity = severity
        self.condition_fn = condition_fn

    def evaluate(self, signals, summary, obligor_id, db):
        """Evaluate if rule fires."""
        try:
            return self.condition_fn(signals, summary, obligor_id, db)
        except Exception as e:
            logger.error(f"Error evaluating {self.name}: {e}")
            return False


class AlertEngine:
    """Evaluate all alert rules for an obligor."""

    def __init__(self):
        self.rules = self._init_rules()

    def _init_rules(self) -> List[AlertRule]:
        """Initialize all rules."""
        return [
            AlertRule(ALERT_RULE_CREDIT_EVENT, "CRITICAL", self._rule_credit_event),
            AlertRule(ALERT_RULE_COVENANT_LIQUIDITY, "HIGH", self._rule_covenant_liquidity),
            AlertRule(ALERT_RULE_DOWNGRADE_WATCH, "MEDIUM", self._rule_downgrade_watch),
            AlertRule(ALERT_RULE_SENTIMENT_SPIKE, "MEDIUM", self._rule_sentiment_spike),
            AlertRule(ALERT_RULE_MULTIPLE_EVENTS, "HIGH", self._rule_multiple_events),
        ]

    def evaluate(
        self,
        obligor_id: int,
        date_val: date,
        signals: ObligorDailySignals = None,
        summary: Dict = None,
        db: Session = None,
    ) -> List[Dict]:
        """Evaluate all rules. Return list of triggered rules."""
        triggered = []

        for rule in self.rules:
            if rule.evaluate(signals, summary, obligor_id, db):
                triggered.append(
                    {
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "trigger_evidence": self._get_trigger_evidence(rule.name, signals),
                    }
                )

        return triggered

    def _rule_credit_event(self, signals, summary, obligor_id, db) -> bool:
        """Rule 1: Credit Event Detected (CRITICAL)"""
        if not signals.event_types:
            return False
        return bool({"default", "bankruptcy", "fraud"} & set(signals.event_types))

    def _rule_covenant_liquidity(self, signals, summary, obligor_id, db) -> bool:
        """Rule 2: Covenant/Liquidity Risk (HIGH)"""
        if not signals.event_types:
            has_event = False
        else:
            has_event = bool({"covenant_breach", "liquidity_crisis"} & set(signals.event_types))

        has_critical = summary and summary.get("risk_level") == "critical"
        return has_event or has_critical

    def _rule_downgrade_watch(self, signals, summary, obligor_id, db) -> bool:
        """Rule 3: Downgrade/Rating Watch (MEDIUM)"""
        if not signals.event_types:
            return False
        return bool({"downgrade", "rating_watch"} & set(signals.event_types))

    def _rule_sentiment_spike(self, signals, summary, obligor_id, db) -> bool:
        """Rule 4: Negative Sentiment Spike (MEDIUM)"""
        if signals.avg_sentiment is None:
            return False
        has_low = signals.avg_sentiment < SENTIMENT_SPIKE_THRESHOLD
        has_articles = signals.credit_relevant_count >= SENTIMENT_SPIKE_MIN_ARTICLES
        return has_low and has_articles

    def _rule_multiple_events(self, signals, summary, obligor_id, db) -> bool:
        """Rule 5: Multiple Event Types (HIGH)"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=MULTIPLE_EVENTS_WINDOW_HOURS)
        count = (
            db.query(Alert)
            .filter(
                Alert.obligor_id == obligor_id,
                Alert.triggered_at >= cutoff,
            )
            .count()
        )
        return count >= MULTIPLE_EVENTS_THRESHOLD

    def _get_trigger_evidence(self, rule_name: str, signals: ObligorDailySignals) -> str:
        """Generate human-readable evidence."""
        if rule_name == ALERT_RULE_CREDIT_EVENT:
            events = [e for e in signals.event_types if e in {"default", "bankruptcy", "fraud"}]
            return f"Credit events: {', '.join(events)}"
        elif rule_name == ALERT_RULE_COVENANT_LIQUIDITY:
            return "Covenant or liquidity risk"
        elif rule_name == ALERT_RULE_DOWNGRADE_WATCH:
            events = [e for e in signals.event_types if e in {"downgrade", "rating_watch"}]
            return f"Rating events: {', '.join(events)}"
        elif rule_name == ALERT_RULE_SENTIMENT_SPIKE:
            return f"Sentiment {signals.avg_sentiment:.2f}, {signals.credit_relevant_count} articles"
        elif rule_name == ALERT_RULE_MULTIPLE_EVENTS:
            return "Multiple events in 48h"
        return "Rule triggered"
