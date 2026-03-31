"""
Score processed articles with FinBERT sentiment.

Finds processed_articles rows where sentiment_score IS NULL and populates
sentiment_score and sentiment_label for each one.

Usage:
    python -m scripts.score_sentiment
    python -m scripts.score_sentiment --batch-size 50
    python -m scripts.score_sentiment --limit 100
"""

import argparse

from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import ProcessedArticle
from src.models.sentiment import FinBERTSentiment
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def score_sentiment(batch_size: int = 50, limit: int = 0) -> int:
    """
    Score all processed_articles rows with sentiment_score IS NULL.

    Args:
        batch_size: Number of articles to score before committing to DB.
        limit:      Max articles to score total (0 = no limit).

    Returns:
        Number of articles scored.
    """
    db = SessionLocal()
    scorer = FinBERTSentiment()
    total_scored = 0

    try:
        query = (
            db.query(ProcessedArticle)
            .filter(ProcessedArticle.sentiment_score.is_(None))
            .filter(ProcessedArticle.cleaned_text.isnot(None))
        )
        if limit > 0:
            query = query.limit(limit)

        rows = query.all()
        logger.info(f"score_sentiment: {len(rows)} article(s) to score.")

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            texts = [r.cleaned_text for r in batch]
            results = scorer.predict_batch(texts)

            for row, res in zip(batch, results):
                row.sentiment_score = res["score"]
                row.sentiment_label = res["label"]

            db.commit()
            total_scored += len(batch)
            logger.info(
                f"score_sentiment: scored {total_scored}/{len(rows)} articles "
                f"(last batch avg_score={sum(r['score'] for r in results)/len(results):.3f})"
            )

    except Exception as exc:
        db.rollback()
        logger.error(f"score_sentiment failed: {exc}")
        raise
    finally:
        db.close()

    return total_scored


def main() -> None:
    parser = argparse.ArgumentParser(description="Score processed articles with FinBERT.")
    parser.add_argument("--batch-size", type=int, default=50, help="Commit every N articles.")
    parser.add_argument("--limit", type=int, default=0, help="Max articles to score (0=all).")
    args = parser.parse_args()

    logger.info(f"=== score_sentiment: batch_size={args.batch_size} limit={args.limit} ===")
    count = score_sentiment(batch_size=args.batch_size, limit=args.limit)
    logger.info(f"=== score_sentiment: done — {count} article(s) scored ===")
    print(f"Articles scored: {count}")


if __name__ == "__main__":
    main()
