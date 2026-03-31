"""
Deterministic risk scorer for processed articles and obligors.

Usage:
    from src.models.risk_scorer import score_article_risk, aggregate_obligor_risk

    score = score_article_risk({
        "sentiment_score": -0.8,
        "is_credit_relevant": True,
        "event_types": ["default"],
    })
    # 1.0 (clamped)
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Additive bonuses per event type
_EVENT_BONUSES: Dict[str, float] = {
    "default":           0.30,
    "bankruptcy":        0.20,
    "fraud":             0.15,
    "liquidity_crisis":  0.15,
    "downgrade":         0.20,
    "covenant_breach":   0.15,
    "restructuring":     0.10,
    "rating_watch":      0.10,
    "regulatory_action": 0.10,
    "earnings_miss":     0.05,
    "lawsuit":           0.05,
    "management_change": 0.05,
    "merger_acquisition": 0.05,
    "debt_issuance":     0.05,
    "layoffs":           0.05,
}


def score_article_risk(processed_article: Dict) -> float:
    """
    Score a single processed article for credit risk.

    Args:
        processed_article: Dict with keys:
            sentiment_score   (float | None)  — from FinBERT, -1.0 to 1.0
            is_credit_relevant (bool)          — from keyword classifier
            event_types       (list | None)    — list of event type strings

    Returns:
        float in [0.0, 1.0] where 1.0 = maximum credit risk signal.
    """
    score = 0.0

    if processed_article.get("is_credit_relevant"):
        score += 0.5

    sentiment = processed_article.get("sentiment_score")
    if sentiment is not None and sentiment < 0:
        score += 0.3

    event_types: List[str] = processed_article.get("event_types") or []
    for event in event_types:
        score += _EVENT_BONUSES.get(event, 0.0)

    return round(min(score, 1.0), 6)


def aggregate_obligor_risk(
    obligor_id: int,
    days: int,
    db=None,
) -> float:
    """
    Compute the average risk score for an obligor over the last N days.

    Queries processed_articles via article_obligors, scores each article,
    and returns the mean. Returns 0.0 if no articles found.

    Args:
        obligor_id: The obligor to score.
        days:       Look-back window in days.
        db:         SQLAlchemy session (injected for testing).
    """
    from src.db.connection import SessionLocal
    from src.db.models import Article, ArticleObligor, ProcessedArticle

    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        cutoff = datetime.date.today() - datetime.timedelta(days=days)

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
                Article.published_at >= datetime.datetime.combine(
                    cutoff, datetime.time.min
                ),
            )
            .all()
        )

        if not rows:
            return 0.0

        scores = [
            score_article_risk({
                "sentiment_score":    r.sentiment_score,
                "is_credit_relevant": r.is_credit_relevant,
                "event_types":        r.event_types,
            })
            for r in rows
        ]
        return round(sum(scores) / len(scores), 6)

    finally:
        if own_session:
            db.close()
