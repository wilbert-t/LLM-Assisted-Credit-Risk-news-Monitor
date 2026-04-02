"""
Alert generator - orchestrate alert creation from signals and summaries.

Responsibilities:
- Fetch daily signals for an obligor
- Generate (or attempt) summary via LLM
- Evaluate alert rules
- Create alerts with 24-hour deduplication
- Gracefully fallback if summarizer fails
"""

from datetime import datetime, timedelta, timezone, date as datetime_date
from typing import Optional

from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import (
    Alert, Obligor, ObligorDailySignals, Article, ProcessedArticle, ArticleObligor
)
from src.rag.summarizer import ObligorSummarizer, SummarizerError
from src.alerts.rules import AlertEngine
from src.utils.constants import ALERT_DEDUP_WINDOW_HOURS
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _enrich_signals_with_event_types(signals: ObligorDailySignals, obligor_id: int, db: Session) -> None:
    """
    Attach event_types list to signals object by querying recent articles.

    Queries articles published on the same date as signals, joined through obligor,
    and extracts event_types from ProcessedArticle records.

    Args:
        signals: ObligorDailySignals object to enrich
        obligor_id: Obligor ID
        db: Database session
    """
    try:
        event_types_list = (
            db.query(ProcessedArticle.event_types)
            .join(Article, Article.id == ProcessedArticle.article_id)
            .join(ArticleObligor, ArticleObligor.article_id == Article.id)
            .filter(
                ArticleObligor.obligor_id == obligor_id,
                func.date(Article.published_at) == signals.date,
            )
            .all()
        )

        # Flatten and deduplicate event types
        all_events = set()
        for (events,) in event_types_list:
            if events:
                all_events.update(events)

        signals.event_types = list(all_events)
    except Exception as e:
        logger.warning(f"Failed to enrich signals with event_types: {e}")
        signals.event_types = []


def generate_alerts(obligor_id: int, db: Session = None) -> None:
    """
    Orchestrate alert creation for a single obligor.

    Steps:
    1. Get most recent signals for obligor
    2. Early return if no signals
    3. Attempt to generate summary (with fallback)
    4. Evaluate alert rules
    5. Create alerts with 24h dedup window

    Args:
        obligor_id: Obligor ID
        db: Database session (opens new one if None)
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        # Get most recent signals
        signals = (
            db.query(ObligorDailySignals)
            .filter_by(obligor_id=obligor_id)
            .order_by(ObligorDailySignals.date.desc())
            .first()
        )

        if not signals:
            logger.info(f"No signals found for obligor {obligor_id}")
            return

        # Enrich signals with event types from recent articles
        _enrich_signals_with_event_types(signals, obligor_id, db)

        # Attempt to get summary
        summary = None
        try:
            summarizer = ObligorSummarizer(db=db)
            summary = summarizer.summarize_obligor_risk(obligor_id, days=7)
        except SummarizerError as e:
            logger.warning(f"Summarizer failed for obligor {obligor_id}: {e}")

        # Evaluate alert rules
        engine = AlertEngine()
        triggered = engine.evaluate(obligor_id, signals.date, signals, summary, db)

        if not triggered:
            logger.debug(f"No alerts triggered for obligor {obligor_id}")
            return

        # Create alerts with deduplication
        now_utc = datetime.now(timezone.utc)
        dedup_cutoff = now_utc - timedelta(hours=ALERT_DEDUP_WINDOW_HOURS)

        for rule in triggered:
            rule_name = rule["rule_name"]

            # Check if recent alert exists for this rule
            # Query recent alerts and check rule_name in Python since JSON filter is complex
            recent_alerts = (
                db.query(Alert)
                .filter(
                    Alert.obligor_id == obligor_id,
                    Alert.triggered_at > dedup_cutoff,
                )
                .all()
            )

            recent = None
            for alert in recent_alerts:
                if alert.extra_data and alert.extra_data.get("rule_name") == rule_name:
                    recent = alert
                    break

            if recent:
                logger.info(f"Alert {rule_name} already exists within {ALERT_DEDUP_WINDOW_HOURS}h, skipping")
                continue

            # Create alert
            alert = Alert(
                obligor_id=obligor_id,
                triggered_at=now_utc,
                severity=rule["severity"],
                summary=summary.get("summary", "") if summary else "Summary generation failed",
                event_types=signals.event_types if signals.event_types else [],
                article_ids=[],
                extra_data={
                    "rule_name": rule_name,
                    "trigger_evidence": rule["trigger_evidence"],
                    "risk_level": summary.get("risk_level") if summary else None,
                    "fallback": summary is None,
                },
            )

            db.add(alert)
            db.commit()
            logger.info(f"Created alert '{rule_name}' for obligor {obligor_id} with severity {rule['severity']}")

    except Exception as e:
        logger.error(f"Error generating alerts for obligor {obligor_id}: {e}", exc_info=True)

    finally:
        if close_db:
            db.close()


def check_all_obligors(db: Session = None) -> None:
    """
    Generate alerts for all obligors.

    Iterates through all obligors, isolating errors so one failure doesn't stop processing.

    Args:
        db: Database session (opens new one if None)
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        obligor_ids = db.query(Obligor.id).all()
        logger.info(f"Processing alerts for {len(obligor_ids)} obligors")

        for (oid,) in obligor_ids:
            try:
                generate_alerts(oid, db)
            except Exception as e:
                logger.error(f"Error processing obligor {oid}: {e}", exc_info=True)

        logger.info("Alert generation complete")

    finally:
        if close_db:
            db.close()
