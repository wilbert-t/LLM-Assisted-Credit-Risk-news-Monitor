"""
FinBERT sentiment scorer for financial news text.

Usage:
    from src.models.sentiment import FinBERTSentiment

    scorer = FinBERTSentiment()
    result = scorer.predict("Company files for bankruptcy.")
    # {"label": "negative", "score": -0.82, "positive": 0.05, "negative": 0.87, "neutral": 0.08}

    batch = scorer.predict_batch(["text one", "text two"])
"""

from __future__ import annotations

from typing import Dict, List

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_MODEL_NAME = "ProsusAI/finbert"
# FinBERT label order as defined by ProsusAI (index 0=positive, 1=negative, 2=neutral)
_LABEL_ORDER = ["positive", "negative", "neutral"]


class FinBERTSentiment:
    """
    Wrapper around ProsusAI/finbert for financial text sentiment.

    The model is lazy-loaded on first call to predict() or predict_batch().
    Pass an instance around rather than creating multiple — the model is ~440MB.
    """

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load(self) -> None:
        """Download (on first run) and cache the FinBERT model."""
        if self._model is not None:
            return
        logger.info(f"Loading FinBERT from {_MODEL_NAME!r} (device={self._device})...")
        self._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        self._model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        self._model.to(self._device)
        self._model.eval()
        logger.info("FinBERT loaded.")

    def predict(self, text: str) -> Dict[str, float]:
        """
        Score a single text string.

        Returns a dict with:
            label   — "positive", "negative", or "neutral"
            score   — float in [-1.0, 1.0] = positive_prob - negative_prob
            positive, negative, neutral — raw softmax probabilities
        """
        self._load()
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)

        probs = F.softmax(outputs.logits, dim=-1).squeeze().tolist()
        # probs order: [positive, negative, neutral]
        pos, neg, neu = probs[0], probs[1], probs[2]
        label = _LABEL_ORDER[probs.index(max(probs))]

        return {
            "label":    label,
            "score":    round(pos - neg, 6),
            "positive": round(pos, 6),
            "negative": round(neg, 6),
            "neutral":  round(neu, 6),
        }

    def predict_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Score a list of texts, calling predict() on each.
        Returns a list of result dicts in the same order as the input.
        """
        if not texts:
            return []
        return [self.predict(text) for text in texts]
