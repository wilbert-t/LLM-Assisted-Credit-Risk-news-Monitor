"""
Scheduled alert job orchestration using APScheduler.

Responsibilities:
- Assign obligors to HIGH or NORMAL risk tiers
- Schedule high-risk cycle (every 4h)
- Schedule normal cycle (every 6h)
- Respect inter-call sleep and error isolation
"""

import time
from datetime import datetime, timedelta, date as datetime_date
from typing import List, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Alert, Obligor, ObligorDailySignals
from src.alerts.generator import generate_alerts
from src.utils.constants import (
    INTER_CALL_SLEEP_SECONDS,
    HIGH_RISK_CYCLE_HOURS,
    NORMAL_CYCLE_HOURS,
    HIGH_RISK_MIN_ALERTS_7D,
    HIGH_RISK_MAX_SENTIMENT,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_prioritized_obligors(db: Session = None) -> List[Tuple[int, str]]:
    """
    Assign HIGH/NORMAL tiers to all obligors based on risk indicators.

    HIGH tier criteria:
    - 2+ alerts in past 7 days, OR
    - min sentiment < -0.4 in past 7 days

    NORMAL tier: everything else

    Args:
        db: Database session (opens new one if None)

    Returns:
        List of (obligor_id, tier) tuples
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        cutoff = datetime_date.today() - timedelta(days=7)

        # High alert obligors
        high_alert = db.query(Alert.obligor_id).filter(
            Alert.triggered_at >= datetime.combine(cutoff, datetime.min.time()).replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )
        ).group_by(Alert.obligor_id).having(
            func.count(Alert.id) >= HIGH_RISK_MIN_ALERTS_7D
        ).all()
        high_alert_ids = {oid for (oid,) in high_alert}

        # High sentiment risk obligors
        high_sentiment = db.query(
            ObligorDailySignals.obligor_id,
            func.min(ObligorDailySignals.avg_sentiment)
        ).filter(
            ObligorDailySignals.date >= cutoff
        ).group_by(ObligorDailySignals.obligor_id).all()
        high_sentiment_ids = set()
        for oid, min_sentiment in high_sentiment:
            if min_sentiment is not None and min_sentiment < HIGH_RISK_MAX_SENTIMENT:
                high_sentiment_ids.add(oid)

        high_risk_ids = high_alert_ids | high_sentiment_ids

        # Assign tiers
        result = []
        for (oid,) in db.query(Obligor.id).all():
            tier = "high" if oid in high_risk_ids else "normal"
            result.append((oid, tier))

        return result

    finally:
        if close_db:
            db.close()


class ScheduledAlertJob:
    """APScheduler wrapper for periodic alert cycles."""

    def __init__(self, db: Session = None):
        """
        Initialize scheduler.

        Args:
            db: Database session (opens new one if None and needed)
        """
        self.db = db
        self.scheduler = None

    def start(self) -> None:
        """
        Start background scheduler with high-risk and normal cycles.

        - High-risk cycle: every 4 hours
        - Normal cycle: every 6 hours
        """
        self.scheduler = BackgroundScheduler()

        # High-risk cycle: every 4 hours
        self.scheduler.add_job(
            self.high_risk_alert_cycle,
            trigger=CronTrigger(hour=f"*/{HIGH_RISK_CYCLE_HOURS}", minute=0),
            id="high_risk_cycle",
            name="High-risk alert cycle",
        )

        # Normal cycle: every 6 hours
        self.scheduler.add_job(
            self.normal_alert_cycle,
            trigger=CronTrigger(hour=f"*/{NORMAL_CYCLE_HOURS}", minute=0),
            id="normal_cycle",
            name="Normal alert cycle",
        )

        self.scheduler.start()
        logger.info(f"Alert scheduler started (high-risk: {HIGH_RISK_CYCLE_HOURS}h, normal: {NORMAL_CYCLE_HOURS}h)")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Alert scheduler stopped")

    def high_risk_alert_cycle(self) -> None:
        """
        Process high-risk obligors.

        Fetches prioritized obligors, filters to HIGH tier, and calls generate_alerts
        for each with inter-call sleep.
        """
        try:
            logger.info("High-risk alert cycle starting")

            obligors = get_prioritized_obligors(self.db)
            high_risk = [oid for oid, tier in obligors if tier == "high"]

            logger.info(f"Processing {len(high_risk)} high-risk obligors")

            for idx, oid in enumerate(high_risk):
                try:
                    generate_alerts(oid, self.db)
                    # Sleep between calls (except after last one)
                    if idx < len(high_risk) - 1:
                        time.sleep(INTER_CALL_SLEEP_SECONDS)
                except Exception as e:
                    logger.error(f"Error generating alerts for obligor {oid}: {e}", exc_info=True)

            logger.info("High-risk alert cycle complete")

        except Exception as e:
            logger.error(f"High-risk alert cycle failed: {e}", exc_info=True)

    def normal_alert_cycle(self) -> None:
        """
        Process normal-risk obligors.

        Fetches prioritized obligors, filters to NORMAL tier, and calls generate_alerts
        for each with inter-call sleep.
        """
        try:
            logger.info("Normal alert cycle starting")

            obligors = get_prioritized_obligors(self.db)
            normal = [oid for oid, tier in obligors if tier == "normal"]

            logger.info(f"Processing {len(normal)} normal-risk obligors")

            for idx, oid in enumerate(normal):
                try:
                    generate_alerts(oid, self.db)
                    # Sleep between calls (except after last one)
                    if idx < len(normal) - 1:
                        time.sleep(INTER_CALL_SLEEP_SECONDS)
                except Exception as e:
                    logger.error(f"Error generating alerts for obligor {oid}: {e}", exc_info=True)

            logger.info("Normal alert cycle complete")

        except Exception as e:
            logger.error(f"Normal alert cycle failed: {e}", exc_info=True)
