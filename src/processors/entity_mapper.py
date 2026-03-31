"""
Entity-to-obligor mapper.

Matches ORG entities extracted by NER against the obligors table using:
  1. Exact match on ticker (case-insensitive)
  2. Exact match on name (case-insensitive)
  3. Fuzzy match on name via rapidfuzz token_set_ratio >= FUZZY_THRESHOLD

Public API:
    match_entity_to_obligor(entity, db, obligors=None) -> Optional[int]
    map_articles_to_obligors(db=None)                  -> int
"""

from typing import List, Optional

from rapidfuzz import fuzz
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import ArticleObligor, Obligor, ProcessedArticle
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

FUZZY_THRESHOLD = 80


def match_entity_to_obligor(
    entity: str,
    db: Session,
    obligors: Optional[List[Obligor]] = None,
) -> Optional[int]:
    """
    Match a single entity string to an obligor ID.

    Matching order:
        1. Exact ticker match (case-insensitive)
        2. Exact name match (case-insensitive)
        3. Fuzzy name match via token_set_ratio >= FUZZY_THRESHOLD

    Args:
        entity:   NER entity text, e.g. "Apple Inc." or "AAPL".
        db:       SQLAlchemy session.
        obligors: Pre-loaded Obligor list. If None, loads from DB.
                  Pass a pre-loaded list when calling in a loop.

    Returns:
        obligor.id on match, None otherwise.
    """
    if not entity or not entity.strip():
        return None

    if obligors is None:
        obligors = db.query(Obligor).all()

    entity_upper = entity.strip().upper()
    entity_lower = entity.strip().lower()

    # Pass 1 — exact ticker
    for o in obligors:
        if o.ticker and o.ticker.upper() == entity_upper:
            return o.id

    # Pass 2 — exact name
    for o in obligors:
        if o.name and o.name.lower() == entity_lower:
            return o.id

    # Pass 3 — fuzzy name
    best_id: Optional[int] = None
    best_score = 0
    for o in obligors:
        if not o.name:
            continue
        score = fuzz.token_set_ratio(entity_lower, o.name.lower())
        if score > best_score:
            best_score = score
            best_id = o.id

    if best_score >= FUZZY_THRESHOLD:
        logger.debug(
            f"Fuzzy match: {entity!r} → obligor_id={best_id} (score={best_score})"
        )
        return best_id

    return None


def map_articles_to_obligors(db: Optional[Session] = None) -> int:
    """
    For every processed article with ORG entities, match each ORG to an
    obligor and insert article_obligors rows.

    Idempotent — ON CONFLICT DO NOTHING on the composite PK.

    Args:
        db: Optional injected session. If None, creates its own.

    Returns:
        Count of newly inserted article-obligor links.
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    new_links = 0

    try:
        obligors = db.query(Obligor).all()
        if not obligors:
            logger.warning("map_articles_to_obligors: no obligors in DB.")
            return 0

        processed = (
            db.query(ProcessedArticle)
            .filter(ProcessedArticle.entities.isnot(None))
            .all()
        )
        logger.info(
            f"map_articles_to_obligors: scanning {len(processed)} processed articles."
        )

        rows: list[dict] = []
        seen: set[tuple[int, int]] = set()

        for pa in processed:
            entities = pa.entities or {}
            org_entities = entities.get("ORG", [])

            for ent in org_entities:
                text = ent.get("text", "") if isinstance(ent, dict) else str(ent)
                obligor_id = match_entity_to_obligor(text, db, obligors=obligors)
                if obligor_id is None:
                    continue

                key = (pa.article_id, obligor_id)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"article_id": pa.article_id, "obligor_id": obligor_id})

        if rows:
            stmt = (
                pg_insert(ArticleObligor)
                .values(rows)
                .on_conflict_do_nothing(index_elements=["article_id", "obligor_id"])
            )
            result = db.execute(stmt)
            new_links = result.rowcount

        if _own_session:
            db.commit()

        logger.info(
            f"map_articles_to_obligors: {new_links} new article-obligor links created."
        )

    except Exception as exc:
        if _own_session:
            db.rollback()
        logger.error(f"map_articles_to_obligors failed: {exc}")
        raise

    finally:
        if _own_session:
            db.close()

    return new_links
