"""
Unit tests for src/models/llm_classifier.py.
All tests mock the HTTP call — no real API calls, no API key needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.llm_classifier import classify_with_llm


def _mock_response(content: str) -> MagicMock:
    """Return a mock requests.Response with the given JSON content string."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock


class TestClassifyWithLLM:

    def test_returns_credit_relevant_true_for_bankruptcy(self):
        """LLM returns is_credit_relevant=true → function returns True."""
        response_json = '{"is_credit_relevant": true, "event_types": ["bankruptcy"]}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Company filed for bankruptcy under chapter 11.")

        assert result["is_credit_relevant"] is True
        assert "bankruptcy" in result["event_types"]

    def test_returns_credit_relevant_false_for_generic(self):
        """LLM returns is_credit_relevant=false → function returns False."""
        response_json = '{"is_credit_relevant": false, "event_types": []}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Team holds quarterly meeting in office.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []

    def test_returns_multiple_event_types(self):
        """LLM can return multiple event types."""
        response_json = '{"is_credit_relevant": true, "event_types": ["downgrade", "fraud"]}'
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response(response_json)
            result = classify_with_llm("Downgraded amid fraud investigation.")

        assert "downgrade" in result["event_types"]
        assert "fraud" in result["event_types"]

    def test_api_error_returns_fallback(self):
        """On API error, returns fallback result (not credit relevant, empty events)."""
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.side_effect = Exception("API timeout")
            result = classify_with_llm("Some article text.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []
        assert result["error"] is not None

    def test_malformed_json_returns_fallback(self):
        """If LLM returns unparseable JSON, returns fallback."""
        with patch("src.models.llm_classifier.requests.post") as mock_post:
            mock_post.return_value = _mock_response("Sorry, I cannot classify this.")
            result = classify_with_llm("Some article text.")

        assert result["is_credit_relevant"] is False
        assert result["event_types"] == []
        assert result["error"] is not None
