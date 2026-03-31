"""
Unit tests for src/models/sentiment.py.
All tests mock the HuggingFace model — no download or GPU required.
"""

from unittest.mock import MagicMock, patch

import pytest
import torch

from src.models.sentiment import FinBERTSentiment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logits(pos: float, neg: float, neu: float) -> MagicMock:
    """Return a mock model output with the given raw logits."""
    output = MagicMock()
    output.logits = torch.tensor([[pos, neg, neu]])
    return output


def _patched_sentiment(monkeypatch):
    """
    Return a FinBERTSentiment instance with tokenizer + model mocked.
    Monkeypatches AutoTokenizer.from_pretrained and AutoModelForSequenceClassification.from_pretrained.
    """
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        "input_ids": torch.zeros((1, 10), dtype=torch.long),
        "attention_mask": torch.ones((1, 10), dtype=torch.long),
    }
    mock_model = MagicMock()

    monkeypatch.setattr(
        "src.models.sentiment.AutoTokenizer.from_pretrained",
        lambda *a, **kw: mock_tokenizer,
    )
    monkeypatch.setattr(
        "src.models.sentiment.AutoModelForSequenceClassification.from_pretrained",
        lambda *a, **kw: mock_model,
    )

    instance = FinBERTSentiment()
    instance._tokenizer = mock_tokenizer
    instance._model = mock_model
    return instance, mock_model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFinBERTSentimentPredict:

    def test_positive_sentiment_returns_positive_label(self, monkeypatch):
        """High positive logit → label='positive', score > 0."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=5.0, neg=-3.0, neu=0.0)

        result = instance.predict("Strong earnings beat and record revenue growth.")

        assert result["label"] == "positive"
        assert result["score"] > 0.5

    def test_negative_sentiment_returns_negative_label(self, monkeypatch):
        """High negative logit → label='negative', score < -0.5."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=-3.0, neg=5.0, neu=0.0)

        result = instance.predict("Company filed for bankruptcy and missed debt payments.")

        assert result["label"] == "negative"
        assert result["score"] < -0.5

    def test_neutral_sentiment_returns_neutral_label(self, monkeypatch):
        """High neutral logit → label='neutral', score near 0."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.0, neg=0.0, neu=5.0)

        result = instance.predict("The company released its quarterly filing.")

        assert result["label"] == "neutral"
        assert -0.3 < result["score"] < 0.3

    def test_predict_returns_all_keys(self, monkeypatch):
        """Result dict must contain label, score, positive, negative, neutral."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        result = instance.predict("Some financial news text.")

        assert set(result.keys()) == {"label", "score", "positive", "negative", "neutral"}

    def test_score_is_positive_minus_negative(self, monkeypatch):
        """score = positive_prob - negative_prob."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        # Use logits that give known softmax values
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        result = instance.predict("text")

        expected_score = result["positive"] - result["negative"]
        assert result["score"] == pytest.approx(expected_score, abs=1e-6)

    def test_empty_string_does_not_crash(self, monkeypatch):
        """Empty string should return a valid result dict, not raise."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.0, neg=0.0, neu=1.0)

        result = instance.predict("")

        assert "label" in result

    def test_long_text_is_truncated_to_512_tokens(self, monkeypatch):
        """Tokenizer must be called with truncation=True and max_length=512."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        instance.predict("word " * 600)

        call_kwargs = instance._tokenizer.call_args[1]
        assert call_kwargs.get("truncation") is True
        assert call_kwargs.get("max_length") == 512


class TestFinBERTSentimentBatch:

    def test_predict_batch_returns_one_result_per_text(self, monkeypatch):
        """predict_batch must return a list of the same length as the input."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=1.0, neg=0.0, neu=0.0)

        texts = ["text one", "text two", "text three"]
        results = instance.predict_batch(texts)

        assert len(results) == 3
        for r in results:
            assert "label" in r and "score" in r

    def test_predict_batch_empty_list_returns_empty(self, monkeypatch):
        """predict_batch([]) → []."""
        instance, mock_model = _patched_sentiment(monkeypatch)

        results = instance.predict_batch([])

        assert results == []

    def test_predict_batch_handles_100_texts(self, monkeypatch):
        """predict_batch should handle 100 texts without error."""
        instance, mock_model = _patched_sentiment(monkeypatch)
        mock_model.return_value = _make_logits(pos=0.5, neg=0.3, neu=0.2)

        texts = [f"Financial news article number {i}." for i in range(100)]
        results = instance.predict_batch(texts)

        assert len(results) == 100
