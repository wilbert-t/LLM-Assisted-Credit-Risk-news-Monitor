"""
Embedding pipeline: chunk processed articles and store vectors in the embeddings table.

Usage:
    from src.models.embedding_pipeline import embed_and_store_articles

    stored = embed_and_store_articles(article_ids=[1, 2, 3])
    print(f"Stored {stored} chunks")
"""

from __future__ import annotations

from typing import List

from src.db.models import Embedding, ProcessedArticle
from src.models.chunker import chunk_text
from src.models.embeddings import EmbeddingGenerator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def embed_and_store_articles(
    article_ids: List[int],
    db=None,
) -> int:
    """
    Chunk, embed, and store article text in the embeddings table.

    For each article_id:
      1. Load cleaned_text from processed_articles.
      2. Chunk into 300-word segments (50-word overlap).
      3. Embed all chunks in one batch call.
      4. Bulk-insert Embedding rows.

    Args:
        article_ids: List of article IDs to process.
        db:          SQLAlchemy session (created from SessionLocal if None).

    Returns:
        Total number of chunks stored across all articles.
    """
    if not article_ids:
        return 0

    from src.db.connection import SessionLocal

    own_session = db is None
    if own_session:
        db = SessionLocal()

    generator = EmbeddingGenerator()
    total_stored = 0

    try:
        rows = (
            db.query(ProcessedArticle)
            .filter(ProcessedArticle.article_id.in_(article_ids))
            .all()
        )

        already_embedded = {
            row.article_id
            for row in db.query(Embedding.article_id).filter(
                Embedding.article_id.in_(article_ids)
            ).distinct().all()
        }
        if already_embedded:
            logger.debug(f"Skipping {len(already_embedded)} already-embedded articles.")
        rows = [r for r in rows if r.article_id not in already_embedded]

        for row in rows:
            text = row.cleaned_text
            if not text:
                logger.debug(f"article_id={row.article_id}: no cleaned_text, skipping.")
                continue

            chunks = chunk_text(text)
            if not chunks:
                continue

            vectors = generator.embed_batch(chunks)

            embedding_rows = [
                Embedding(
                    article_id=row.article_id,
                    chunk_text=chunk,
                    embedding=vector,
                    chunk_index=idx,
                )
                for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
            ]
            db.bulk_save_objects(embedding_rows)
            total_stored += len(embedding_rows)
            logger.info(
                f"article_id={row.article_id}: stored {len(embedding_rows)} chunks."
            )

        if own_session:
            db.commit()

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()

    logger.info(f"Embedding pipeline complete: {total_stored} total chunks stored.")
    return total_stored
