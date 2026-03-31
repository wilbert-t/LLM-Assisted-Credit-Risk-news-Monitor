"""
Text processing pipeline — fetches raw articles, cleans them, and stores
results in the `processed_articles` table.

Usage (scripts or scheduler):
    from src.processors.pipeline import process_articles_batch

    # Process a specific list of article IDs
    count = process_articles_batch([1, 2, 3])

    # Process all articles not yet processed (omit article_ids)
    count = process_articles_batch()
"""

from typing import List, Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Article, ProcessedArticle
from src.processors.cleaner import clean_article
from src.processors.language_filter import detect_language
from src.processors.ner_extractor import extract_entities
from src.models.classifier import classify_events, is_credit_relevant
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def _fetch_unprocessed(db: Session, article_ids: Optional[List[int]]) -> List[Article]:
    """
    Return Article rows that do not yet have a ProcessedArticle record.
    If article_ids is provided, restrict to those IDs.
    """
    query = (
        db.query(Article)
        .outerjoin(ProcessedArticle, Article.id == ProcessedArticle.article_id)
        .filter(ProcessedArticle.article_id.is_(None))
    )
    if article_ids:
        query = query.filter(Article.id.in_(article_ids))
    return query.all()


def process_articles_batch(
    article_ids: Optional[List[int]] = None,
    db: Optional[Session] = None,
) -> int:
    """
    Clean and store processed versions of articles.

    Steps per article:
        1. Combine title + content and clean (HTML strip, normalise).
        2. Extract named entities with spaCy NER.
        3. Upsert a ProcessedArticle row (skip if cleaned text is empty).

    Args:
        article_ids: Optional list of article IDs to process.  If None,
                     processes all articles not yet in processed_articles.
        db:          Optional SQLAlchemy session (injected in tests).
                     If None, a new session is created from SessionLocal.

    Returns:
        Number of articles successfully processed and stored.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    processed_count = 0
    skipped_empty = 0
    skipped_language = 0
    skipped_error = 0

    try:
        articles = _fetch_unprocessed(db, article_ids)
        total = len(articles)
        logger.info(
            f"process_articles_batch: found {total} unprocessed article(s)"
            + (f" (filtered to {len(article_ids)} IDs)" if article_ids else "")
        )

        if not articles:
            return 0

        rows: list[dict] = []
        for article in articles:
            try:
                # Language guard — skip non-English articles.
                lang = article.language
                if lang and lang != "unknown":
                    if lang != "en":
                        logger.debug(
                            f"Skipping article id={article.id} — "
                            f"language={lang!r} (DB field)."
                        )
                        skipped_language += 1
                        continue
                else:
                    raw_text = f"{article.title or ''} {article.content or ''}"
                    detected = detect_language(raw_text)
                    if detected != "en":
                        logger.debug(
                            f"Skipping article id={article.id} — "
                            f"detected language={detected!r}."
                        )
                        skipped_language += 1
                        continue

                cleaned = clean_article(article)
                if not cleaned:
                    logger.debug(f"Skipping article id={article.id} — empty after cleaning.")
                    skipped_empty += 1
                    continue

                entities = extract_entities(cleaned)
                credit_relevant = is_credit_relevant(cleaned)
                events = classify_events(cleaned) if credit_relevant else []

                rows.append({
                    "article_id":         article.id,
                    "cleaned_text":       cleaned,
                    "entities":           entities,
                    "sentiment_score":    None,
                    "sentiment_label":    None,
                    "is_credit_relevant": credit_relevant,
                    "event_types":        events if events else None,
                })

            except Exception as exc:
                logger.error(f"Error processing article id={article.id}: {exc}")
                skipped_error += 1
                continue

        # Bulk upsert — skip rows already present (idempotent).
        if rows:
            stmt = (
                pg_insert(ProcessedArticle)
                .values(rows)
                .on_conflict_do_nothing(index_elements=["article_id"])
            )
            result = db.execute(stmt)
            processed_count = result.rowcount

        if _own_session:
            db.commit()

        logger.info(
            f"process_articles_batch complete — "
            f"stored={processed_count} skipped_language={skipped_language} "
            f"skipped_empty={skipped_empty} skipped_error={skipped_error} total={total}"
        )

    except Exception as exc:
        if _own_session:
            db.rollback()
        logger.error(f"process_articles_batch failed, rolled back: {exc}")
        raise

    finally:
        if _own_session:
            db.close()

    return processed_count


# ---------------------------------------------------------------------------
# Quick test — run with: python -m src.processors.pipeline
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Running processing pipeline on first 10 unprocessed articles...")
    from src.db.connection import SessionLocal as SL
    from src.db.models import Article as A

    db = SL()
    ids = [row.id for row in db.query(A.id).limit(10).all()]
    db.close()

    n = process_articles_batch(article_ids=ids)
    logger.info(f"Done — processed {n} article(s).")
