"""
Generate and store embeddings for processed articles.

Usage:
    python -m scripts.generate_embeddings                # all articles
    python -m scripts.generate_embeddings --limit 100    # first 100 articles
    python -m scripts.generate_embeddings --limit 10     # smoke test
"""

import argparse

from src.db.connection import SessionLocal
from src.db.models import Embedding, ProcessedArticle
from src.models.embedding_pipeline import embed_and_store_articles
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main(limit: int | None = None) -> None:
    db = SessionLocal()
    try:
        already_embedded = {
            row.article_id
            for row in db.query(Embedding.article_id).distinct().all()
        }
        query = db.query(ProcessedArticle.article_id).filter(
            ProcessedArticle.cleaned_text.isnot(None),
            ProcessedArticle.article_id.notin_(already_embedded),
        )
        if limit:
            query = query.limit(limit)
        article_ids = [row.article_id for row in query.all()]
    finally:
        db.close()

    if not article_ids:
        logger.warning("No articles with cleaned_text found.")
        return

    logger.info(f"Embedding {len(article_ids)} articles...")
    stored = embed_and_store_articles(article_ids)
    logger.info(f"Done. {stored} chunks stored in embeddings table.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate article embeddings.")
    parser.add_argument("--limit", type=int, default=None, help="Max articles to embed.")
    args = parser.parse_args()
    main(limit=args.limit)
