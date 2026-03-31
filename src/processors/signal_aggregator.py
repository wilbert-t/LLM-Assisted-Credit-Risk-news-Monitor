"""
Daily signal aggregation for obligors.

Reads article_obligors + processed_articles to compute per-obligor, per-date
metrics, then upserts into obligor_daily_signals.

Note: neg_article_count stores total article count as a placeholder until
FinBERT sentiment scoring is done in Phase 3 (when it will become negative count).
avg_sentiment is NULL until sentiment_score is populated by FinBERT.
"""

import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Article, ArticleObligor, ObligorDailySignals, ProcessedArticle
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
        {obligor_id, date, neg_article_count, avg_sentiment, credit_relevant_count}
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        # Query: ProcessedArticle JOIN Article JOIN ArticleObligor
        # filtered by obligor_id and date(published_at) == date
        rows = (
            db.query(
                ProcessedArticle.sentiment_score,
                ProcessedArticle.is_credit_relevant,
            )
            .join(Article, Article.id == ProcessedArticle.article_id)
            .join(ArticleObligor, ArticleObligor.article_id == Article.id)
            .filter(
                ArticleObligor.obligor_id == obligor_id,
                func.date(Article.published_at) == date,
            )
            .all()
        )

        total_count = len(rows)
        credit_relevant_count = sum(1 for r in rows if r.is_credit_relevant)

        scores = [r.sentiment_score for r in rows if r.sentiment_score is not None]
        avg_sentiment = sum(scores) / len(scores) if scores else None

        row = {
            "obligor_id": obligor_id,
            "date": date,
            "neg_article_count": total_count,
            "avg_sentiment": avg_sentiment,
            "credit_relevant_count": credit_relevant_count,
        }

        stmt = (
            pg_insert(ObligorDailySignals)
            .values(row)
            .on_conflict_do_update(
                constraint="uq_obligor_daily_signals_obligor_date",
                set_={
                    "neg_article_count": row["neg_article_count"],
                    "avg_sentiment": row["avg_sentiment"],
                    "credit_relevant_count": row["credit_relevant_count"],
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
        # Distinct (obligor_id, date) pairs from article_obligors JOIN articles
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
