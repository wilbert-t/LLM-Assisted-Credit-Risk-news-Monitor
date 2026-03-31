"""
Run entity-to-obligor mapping on all processed articles.

Usage:
    python -m scripts.map_entities
"""

from src.processors.entity_mapper import map_articles_to_obligors
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("Starting entity-to-obligor mapping...")
    new_links = map_articles_to_obligors()
    logger.info(f"Mapping complete — {new_links} new article-obligor links created.")
    print(f"New article-obligor links: {new_links}")


if __name__ == "__main__":
    main()
