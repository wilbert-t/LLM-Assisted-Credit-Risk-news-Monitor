"""
Unit tests for src/models/embeddings.py.
The SentenceTransformer model is mocked — no actual model download needed.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.models.embeddings import EmbeddingGenerator


class TestEmbeddingGenerator:

    def test_embed_returns_list_of_floats(self):
        """embed() returns a flat list of floats."""
        with patch("src.models.embeddings.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([0.1, 0.2, 0.3] * 128)  # 384 dims
            MockST.return_value = mock_model

            gen = EmbeddingGenerator()
            result = gen.embed("Apple files for bankruptcy.")

        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_embed_dimension_is_384(self):
        """embed() output length is 384 (all-MiniLM-L6-v2 dimension)."""
        with patch("src.models.embeddings.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.zeros(384)
            MockST.return_value = mock_model

            gen = EmbeddingGenerator()
            result = gen.embed("test text")

        assert len(result) == 384

    def test_embed_batch_returns_list_of_lists(self):
        """embed_batch() returns a list of 384-dim vectors."""
        texts = [f"text {i}" for i in range(5)]
        with patch("src.models.embeddings.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.zeros((5, 384))
            MockST.return_value = mock_model

            gen = EmbeddingGenerator()
            result = gen.embed_batch(texts)

        assert len(result) == 5
        assert all(len(v) == 384 for v in result)

    def test_embed_batch_empty_returns_empty(self):
        """embed_batch([]) returns [] without loading the model."""
        gen = EmbeddingGenerator()
        result = gen.embed_batch([])
        assert result == []

    def test_model_is_lazy_loaded(self):
        """Model is not loaded until embed() or embed_batch() is first called."""
        with patch("src.models.embeddings.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.zeros(384)
            MockST.return_value = mock_model

            gen = EmbeddingGenerator()
            assert MockST.call_count == 0   # not loaded yet

            gen.embed("hello")
            assert MockST.call_count == 1   # loaded on first call

            gen.embed("world")
            assert MockST.call_count == 1   # not reloaded on second call
