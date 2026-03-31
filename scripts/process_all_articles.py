"""
Run the full processing pipeline on all unprocessed articles, then map
entities to obligors.

Usage:
    python -m scripts.process_all_articles
"""

from src.processors.entity_mapper import map_articles_to_obligors
from src.processors.pipeline import process_articles_batch
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("=== process_all_articles: starting ===")

    processed = process_articles_batch()
    logger.info(f"Pipeline complete — processed={processed} article(s).")
    print(f"Articles processed: {processed}")

    # Always run mapping — catches unmapped articles from previous runs too.
    new_links = map_articles_to_obligors()
    logger.info(f"Entity mapping complete — new_links={new_links}.")
    print(f"New article-obligor links: {new_links}")

    logger.info("=== process_all_articles: done ===")


if __name__ == "__main__":
    main()
