"""
Article storage — persists raw NewsAPI articles into the `articles` table.

Features:
  - Deduplication by URL via INSERT ... ON CONFLICT DO NOTHING
  - Batch inserts (configurable batch size, default 50)
  - Returns count of newly inserted rows
  - Full rollback on failure
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.db.connection import SessionLocal
from src.db.models import Article
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 datetime string from NewsAPI (e.g. '2026-03-28T14:32:00Z')."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.warning(f"Could not parse datetime: {value!r}")
            return None


def _map_article(raw: dict) -> Optional[dict]:
    """
    Convert a raw NewsAPI article dict to a flat dict matching the Article model.
    Returns None if the article has no URL (required field).
    """
    url = raw.get("url", "").strip()
    if not url:
        logger.debug("Skipping article with no URL.")
        return None

    title = raw.get("title") or ""
    if title == "[Removed]" or url == "https://removed.com":
        logger.debug(f"Skipping removed article: {title!r}")
        return None

    return {
        "title":        (title[:1024] if title else "Untitled"),
        "content":      raw.get("content") or raw.get("description") or None,
        "url":          url[:2048],
        "source":       (raw.get("source") or {}).get("name"),
        "published_at": _parse_datetime(raw.get("publishedAt")),
        "language":     raw.get("language") or "en",
        "raw_json":     raw,
    }


def store_articles(
    articles: list[dict],
    batch_size: int = None,
) -> int:
    """
    Persist a list of raw NewsAPI article dicts into the `articles` table.

    Deduplication is handled at the DB level with ON CONFLICT (url) DO NOTHING,
    so it is safe to call this with the same articles multiple times.

    Args:
        articles:   Raw article dicts as returned by NewsAPICollector.fetch_news().
        batch_size: Number of rows per INSERT statement. Defaults to BATCH_SIZE in settings.

    Returns:
        Number of newly inserted articles (duplicates not counted).
    """
    if not articles:
        logger.info("store_articles called with empty list — nothing to do.")
        return 0

    batch_size = batch_size or settings.BATCH_SIZE

    # Map and filter raw dicts
    mapped = [_map_article(a) for a in articles]
    valid = [m for m in mapped if m is not None]
    skipped = len(articles) - len(valid)
    if skipped:
        logger.info(f"Skipped {skipped} articles (no URL or removed).")

    if not valid:
        return 0

    db = SessionLocal()
    total_inserted = 0

    try:
        for i in range(0, len(valid), batch_size):
            batch = valid[i : i + batch_size]

            stmt = (
                pg_insert(Article)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["url"])
            )
            result = db.execute(stmt)
            inserted = result.rowcount
            total_inserted += inserted

            dupes = len(batch) - inserted
            logger.info(
                f"Batch {i // batch_size + 1}: "
                f"inserted={inserted} duplicates={dupes} "
                f"(rows {i + 1}–{i + len(batch)})"
            )

        db.commit()
        logger.info(f"store_articles complete — total inserted: {total_inserted}/{len(valid)}")

    except Exception as e:
        db.rollback()
        logger.error(f"store_articles failed, rolled back: {e}")
        raise

    finally:
        db.close()

    return total_inserted


def get_article_count() -> int:
    """
    Return the total number of articles currently in the database.
    Useful for quick sanity checks after ingestion runs.
    """
    db = SessionLocal()
    try:
        count = db.query(Article).count()
        logger.info(f"Article count: {count}")
        return count
    except Exception as e:
        logger.error(f"get_article_count failed: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Quick test — run with: python -m src.collectors.storage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulate 3 articles — 2 valid, 1 duplicate, 1 missing URL
    fake_articles = [
        {
            "title": "Apple reports record quarterly revenue",
            "description": "Apple Inc. reported its highest ever quarterly revenue...",
            "content": "Apple Inc. reported its highest ever quarterly revenue of $120bn.",
            "url": "https://example.com/apple-revenue-2026",
            "source": {"name": "Reuters"},
            "publishedAt": "2026-03-28T10:00:00Z",
        },
        {
            "title": "Apple reports record quarterly revenue",   # duplicate URL
            "description": "Duplicate article.",
            "content": "Duplicate.",
            "url": "https://example.com/apple-revenue-2026",    # same URL
            "source": {"name": "Bloomberg"},
            "publishedAt": "2026-03-28T11:00:00Z",
        },
        {
            "title": "No URL article",
            "description": "This one has no URL and should be skipped.",
            "content": "...",
            "url": "",
            "source": {"name": "Unknown"},
            "publishedAt": "2026-03-28T12:00:00Z",
        },
        {
            "title": "Microsoft Azure outage resolved",
            "description": "Microsoft confirmed an Azure outage affecting...",
            "content": "Microsoft confirmed an Azure outage affecting EU regions for 3 hours.",
            "url": "https://example.com/msft-azure-outage-2026",
            "source": {"name": "Financial Times"},
            "publishedAt": "2026-03-29T08:00:00Z",
        },
    ]

    print("\n--- Testing store_articles ---\n")
    inserted = store_articles(fake_articles)
    print(f"\nInserted: {inserted} new articles")

    count = get_article_count()
    print(f"Total in DB: {count}")

    # Run again to confirm duplicate handling
    print("\n--- Re-inserting same articles (expect 0 new) ---\n")
    inserted_again = store_articles(fake_articles)
    print(f"Inserted on re-run: {inserted_again} (should be 0)")
