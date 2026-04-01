"""
Sentence-transformer embedding generator.

Usage:
    from src.models.embeddings import EmbeddingGenerator

    gen = EmbeddingGenerator()
    vector = gen.embed("Apple files for bankruptcy.")        # List[float], len=384
    vectors = gen.embed_batch(["text one", "text two"])     # List[List[float]]
"""

from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class EmbeddingGenerator:
    """
    Wraps SentenceTransformer all-MiniLM-L6-v2 for article chunk embedding.

    The model (~90MB) is lazy-loaded on first call. Pass a single instance
    around rather than creating multiple.
    """

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _load(self) -> None:
        if self._model is not None:
            return
        logger.info(f"Loading sentence-transformer {_MODEL_NAME!r}...")
        self._model = SentenceTransformer(_MODEL_NAME)
        logger.info("Embedding model loaded.")

    def embed(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Returns a list of 384 floats (cosine-comparable).
        """
        self._load()
        return self._model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts in a single forward pass.

        Returns a list of 384-dim float lists in the same order as input.
        Returns [] if texts is empty (no model load).
        """
        if not texts:
            return []
        self._load()
        return self._model.encode(
            texts, convert_to_numpy=True, batch_size=50, show_progress_bar=False
        ).tolist()
