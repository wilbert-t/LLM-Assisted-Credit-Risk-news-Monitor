"""
Unit tests for src/models/embedding_pipeline.py.
DB and EmbeddingGenerator are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.embedding_pipeline import embed_and_store_articles


class TestEmbedAndStoreArticles:

    def _make_processed(self, article_id: int, text: str) -> MagicMock:
        row = MagicMock()
        row.article_id = article_id
        row.cleaned_text = text
        return row

    def test_returns_chunk_count(self):
        """Returns the number of chunks stored."""
        mock_db = MagicMock()
        processed = [self._make_processed(1, "word " * 50)]  # 50 words → 1 chunk
        mock_db.query.return_value.filter.return_value.all.return_value = processed

        with patch("src.models.embedding_pipeline.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            mock_gen.embed_batch.return_value = [[0.0] * 384]
            MockGen.return_value = mock_gen

            count = embed_and_store_articles([1], db=mock_db)

        assert count == 1

    def test_skips_articles_with_no_cleaned_text(self):
        """Articles with None or empty cleaned_text produce 0 chunks."""
        mock_db = MagicMock()
        processed = [self._make_processed(1, None), self._make_processed(2, "")]
        mock_db.query.return_value.filter.return_value.all.return_value = processed

        with patch("src.models.embedding_pipeline.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            MockGen.return_value = mock_gen

            count = embed_and_store_articles([1, 2], db=mock_db)

        assert count == 0
        mock_gen.embed_batch.assert_not_called()

    def test_multiple_articles_produce_correct_chunk_count(self):
        """Two articles, each producing 2 chunks → returns 4."""
        mock_db = MagicMock()
        processed = [
            self._make_processed(1, "word " * 400),
            self._make_processed(2, "word " * 400),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = processed

        with patch("src.models.embedding_pipeline.EmbeddingGenerator") as MockGen:
            mock_gen = MagicMock()
            # embed_batch called once per article, each batch has 2 chunks
            mock_gen.embed_batch.side_effect = [[[0.0] * 384] * 2, [[0.0] * 384] * 2]
            MockGen.return_value = mock_gen

            count = embed_and_store_articles([1, 2], db=mock_db)

        assert count == 4

    def test_empty_article_ids_returns_zero(self):
        """Empty input returns 0 without touching DB."""
        mock_db = MagicMock()
        count = embed_and_store_articles([], db=mock_db)
        assert count == 0
        mock_db.query.assert_not_called()
