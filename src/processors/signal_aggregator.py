"""
Daily signal aggregation for obligors.

Reads article_obligors + processed_articles to compute per-obligor, per-date
metrics, then upserts into obligor_daily_signals.

neg_article_count = articles where sentiment_score < -0.1
avg_sentiment     = average sentiment_score (articles with non-null score)
credit_relevant_count = articles where is_credit_relevant = True
risk_score        = average score_article_risk() across all articles for the day
"""

import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Article, ArticleObligor, ObligorDailySignals, ProcessedArticle
from src.models.risk_scorer import score_article_risk
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
        {obligor_id, date, neg_article_count, avg_sentiment,
         credit_relevant_count, risk_score}
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        rows = (
            db.query(
                ProcessedArticle.sentiment_score,
                ProcessedArticle.is_credit_relevant,
                ProcessedArticle.event_types,
            )
            .join(Article, Article.id == ProcessedArticle.article_id)
            .join(ArticleObligor, ArticleObligor.article_id == Article.id)
            .filter(
                ArticleObligor.obligor_id == obligor_id,
                func.date(Article.published_at) == date,
            )
            .all()
        )

        neg_article_count = sum(
            1 for r in rows
            if r.sentiment_score is not None and r.sentiment_score < -0.1
        )
        credit_relevant_count = sum(1 for r in rows if r.is_credit_relevant)

        scores_with_values = [r.sentiment_score for r in rows if r.sentiment_score is not None]
        avg_sentiment = sum(scores_with_values) / len(scores_with_values) if scores_with_values else None

        risk_scores = [
            score_article_risk({
                "sentiment_score":    r.sentiment_score,
                "is_credit_relevant": r.is_credit_relevant,
                "event_types":        r.event_types,
            })
            for r in rows
        ]
        risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None

        row = {
            "obligor_id":            obligor_id,
            "date":                  date,
            "neg_article_count":     neg_article_count,
            "avg_sentiment":         avg_sentiment,
            "credit_relevant_count": credit_relevant_count,
            "risk_score":            risk_score,
        }

        stmt = (
            pg_insert(ObligorDailySignals)
            .values(row)
            .on_conflict_do_update(
                constraint="uq_obligor_daily_signals_obligor_date",
                set_={
                    "neg_article_count":     row["neg_article_count"],
                    "avg_sentiment":         row["avg_sentiment"],
                    "credit_relevant_count": row["credit_relevant_count"],
                    "risk_score":            row["risk_score"],
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
