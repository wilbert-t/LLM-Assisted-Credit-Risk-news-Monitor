"""
Batch news collector — fetches and stores articles for all 50 obligors.

Costs 50 of your 100 daily NewsAPI free-tier requests (1 per obligor).
Safe to re-run — duplicate articles are silently skipped by the DB.

Usage:
    python -m scripts.collect_news_all
"""

import sys
import time
from datetime import datetime, timedelta

from src.collectors.news_api import NewsAPICollector, NewsAPIError, RateLimitError
from src.collectors.storage import get_article_count, store_articles
from src.db.connection import SessionLocal
from src.db.models import Obligor
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def build_query(obligor: Obligor) -> str:
    """Build a NewsAPI boolean query from an obligor's name and ticker."""
    if obligor.name and obligor.ticker:
        return f'"{obligor.name}" OR {obligor.ticker}'
    if obligor.name:
        return f'"{obligor.name}"'
    return obligor.ticker


def collect_news() -> None:
    """Fetch and store news for every obligor in the database."""

    # --- API key guard ---
    if not settings.NEWSAPI_KEY:
        print("ERROR: NEWSAPI_KEY is not set. Add it to your .env file and retry.")
        sys.exit(1)

    collector = NewsAPICollector(api_key=settings.NEWSAPI_KEY)

    # --- Load obligors (close session before the API loop) ---
    db = SessionLocal()
    try:
        obligors = db.query(Obligor).order_by(Obligor.id).all()
    finally:
        db.close()

    if not obligors:
        print("No obligors found in database. Run: python -m scripts.seed_obligors")
        return

    total = len(obligors)
    from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = datetime.utcnow().strftime("%Y-%m-%d")

    logger.info(f"Starting collection for {total} obligors ({from_date} → {to_date})")

    total_inserted = 0
    total_processed = 0

    try:
        for i, obligor in enumerate(obligors, start=1):
            try:
                query = build_query(obligor)
                articles = collector.fetch_news(
                    query=query,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=100,
                    page=1,
                )
                inserted = store_articles(articles)
                total_inserted += inserted
                total_processed += 1

                print(f"Collected articles for [{i}/{total}] obligors — "
                      f"{obligor.ticker}: fetched={len(articles)} new={inserted}")
                logger.info(f"[{i}/{total}] {obligor.name} ({obligor.ticker}): "
                            f"fetched={len(articles)} inserted={inserted}")

            except RateLimitError as e:
                logger.warning(f"Rate limit hit at [{i}/{total}] — stopping early. {e}")
                print(f"\nRate limit reached after {i - 1} obligors. Try again tomorrow.")
                break

            except NewsAPIError as e:
                logger.error(f"[{i}/{total}] NewsAPI error for {obligor.name}: {e} — skipping.")
                total_processed += 1
                # continue to next obligor

            if i < total:
                time.sleep(1)   # polite delay between requests

    finally:
        total_in_db = get_article_count()
        print(f"\nCollection complete.")
        print(f"  Obligors processed : {total_processed}/{total}")
        print(f"  New articles stored: {total_inserted}")
        print(f"  Total articles in DB: {total_in_db}")
        logger.info(f"collect_news finished — processed={total_processed} "
                    f"inserted={total_inserted} total_in_db={total_in_db}")


if __name__ == "__main__":
    collect_news()
