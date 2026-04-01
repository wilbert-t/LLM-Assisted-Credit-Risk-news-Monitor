"""
RAG retriever: semantic search over article chunk embeddings.

Usage:
    from src.rag.retriever import ArticleRetriever

    retriever = ArticleRetriever()

    # Free-text semantic search
    results = retriever.search("Apple liquidity crisis", top_k=5)

    # All chunks for an obligor, recent first
    results = retriever.search_by_obligor(obligor_id=1, days=7, top_k=10)

Each result dict:
    {
        "chunk_text":  str,    # the matched chunk
        "article_id":  int,    # source article
        "similarity":  float,  # 1 - cosine_distance, 0.0–1.0
    }
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from src.db.models import Article, ArticleObligor, Embedding
from src.models.embeddings import EmbeddingGenerator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ArticleRetriever:
    """
    Semantic search over the embeddings table.

    Instantiate once and reuse — the embedding model is lazy-loaded.
    Pass `db` for testing; if None, a session is opened per call.
    """

    def __init__(self, db=None) -> None:
        self._generator = EmbeddingGenerator()
        self._db = db

    def _get_db(self):
        if self._db is not None:
            return self._db, False
        from src.db.connection import SessionLocal
        return SessionLocal(), True

    def search(
        self,
        query: str,
        obligor_id: Optional[int] = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Embed query and return top-k nearest chunks by cosine similarity.

        Args:
            query:       Free-text search string.
            obligor_id:  If provided, only return chunks whose article is linked
                         to this obligor in article_obligors.
            top_k:       Number of results to return.

        Returns:
            List of dicts sorted by descending similarity:
            [{"chunk_text": str, "article_id": int, "similarity": float}, ...]
        """
        query_vector = self._generator.embed(query)
        db, own_session = self._get_db()

        try:
            q = db.query(
                Embedding.chunk_text,
                Embedding.article_id,
                Embedding.embedding.cosine_distance(query_vector).label("distance"),
            )

            if obligor_id is not None:
                q = q.join(Article, Article.id == Embedding.article_id).join(
                    ArticleObligor, ArticleObligor.article_id == Article.id
                ).filter(ArticleObligor.obligor_id == obligor_id)

            rows = q.order_by("distance").limit(top_k).all()

            return [
                {
                    "chunk_text": row.chunk_text,
                    "article_id": row.article_id,
                    "similarity": round(1 - row.distance, 6),
                }
                for row in rows
            ]
        finally:
            if own_session:
                db.close()

    def search_by_obligor(
        self,
        obligor_id: int,
        days: int = 7,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Return the most recent chunks for an obligor, ordered by article date (newest first).

        Args:
            obligor_id:  Obligor to search.
            days:        Look-back window in days.
            top_k:       Max chunks to return.

        Returns:
            List of dicts: [{"chunk_text": str, "article_id": int}, ...]
        """
        return self._search_obligor_chunks(
            obligor_id=obligor_id, days=days, top_k=top_k
        )

    def _search_obligor_chunks(
        self,
        obligor_id: int,
        days: int,
        top_k: int,
    ) -> List[Dict]:
        db, own_session = self._get_db()
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

            rows = (
                db.query(Embedding.chunk_text, Embedding.article_id, Article.published_at)
                .join(Article, Article.id == Embedding.article_id)
                .join(ArticleObligor, ArticleObligor.article_id == Article.id)
                .filter(
                    ArticleObligor.obligor_id == obligor_id,
                    Article.published_at >= cutoff,
                )
                .order_by(Article.published_at.desc())
                .limit(top_k)
                .all()
            )

            return [
                {"chunk_text": row.chunk_text, "article_id": row.article_id}
                for row in rows
            ]
        finally:
            if own_session:
                db.close()
