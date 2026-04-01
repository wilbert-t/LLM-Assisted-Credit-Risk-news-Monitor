"""
Unit tests for src/rag/retriever.py.
DB and EmbeddingGenerator are mocked — no model download, no real DB.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.rag.retriever import ArticleRetriever


def _make_embedding_row(chunk_text: str, article_id: int, distance: float) -> MagicMock:
    row = MagicMock()
    row.chunk_text = chunk_text
    row.article_id = article_id
    row.distance = distance
    return row


class TestArticleRetriever:

    def test_search_returns_list_of_dicts(self):
        """search() returns a list of dicts with chunk_text, article_id, similarity."""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            _make_embedding_row("Apple bond defaults.", 1, 0.1),
        ]

        with patch("src.rag.retriever.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            mock_gen.embed.return_value = [0.0] * 384
            MockGen.return_value = mock_gen

            retriever = ArticleRetriever(db=mock_db)
            results = retriever.search("Apple liquidity crisis", top_k=5)

        assert len(results) == 1
        assert results[0]["chunk_text"] == "Apple bond defaults."
        assert results[0]["article_id"] == 1
        assert "similarity" in results[0]

    def test_similarity_is_one_minus_distance(self):
        """similarity = round(1 - cosine_distance, 6)."""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            _make_embedding_row("text", 1, 0.3),
        ]

        with patch("src.rag.retriever.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            mock_gen.embed.return_value = [0.0] * 384
            MockGen.return_value = mock_gen

            retriever = ArticleRetriever(db=mock_db)
            results = retriever.search("query")

        assert results[0]["similarity"] == round(1 - 0.3, 6)

    def test_search_results_ordered_by_similarity_descending(self):
        """Results list is in descending similarity order (DB sorts by distance ASC)."""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            _make_embedding_row("best match", 1, 0.05),
            _make_embedding_row("ok match", 2, 0.3),
            _make_embedding_row("weak match", 3, 0.7),
        ]

        with patch("src.rag.retriever.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            mock_gen.embed.return_value = [0.0] * 384
            MockGen.return_value = mock_gen

            retriever = ArticleRetriever(db=mock_db)
            results = retriever.search("credit risk", top_k=3)

        sims = [r["similarity"] for r in results]
        assert sims == sorted(sims, reverse=True)

    def test_search_empty_db_returns_empty_list(self):
        """search() returns [] when DB has no matching rows."""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch("src.rag.retriever.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            mock_gen.embed.return_value = [0.0] * 384
            MockGen.return_value = mock_gen

            retriever = ArticleRetriever(db=mock_db)
            results = retriever.search("Apple")

        assert results == []

    def test_search_by_obligor_filters_by_obligor_id(self):
        """search_by_obligor() calls _search_obligor_chunks with correct args."""
        with patch("src.rag.retriever.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            MockGen.return_value = mock_gen

            retriever = ArticleRetriever(db=MagicMock())
            with patch.object(retriever, "_search_obligor_chunks") as mock_search:
                mock_search.return_value = [{"chunk_text": "x", "article_id": 1}]
                results = retriever.search_by_obligor(obligor_id=3, days=7, top_k=5)

            mock_search.assert_called_once_with(obligor_id=3, days=7, top_k=5)
            assert len(results) == 1
