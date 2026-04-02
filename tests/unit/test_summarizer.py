"""Unit tests for LLM summarizer module."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.db.models import Article, ArticleObligor, Obligor
from src.rag.summarizer import (
    ObligorSummarizer,
    has_new_articles_since,
    call_groq_with_backoff,
    SummarizerError,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_obligor():
    """Sample obligor."""
    return Obligor(id=1, name="Tesla Inc.", ticker="TSLA", lei="", sector="Automotive", country="USA")


# ============================================================================
# Tests for has_new_articles_since()
# ============================================================================

def test_has_new_articles_since_returns_true_when_articles_exist(mock_db):
    """Test: has_new_articles_since returns True when new articles published."""
    last_summary = datetime.now(timezone.utc) - timedelta(hours=6)

    # Mock: 2 new articles found
    mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 2

    result = has_new_articles_since(obligor_id=1, last_summary_ts=last_summary, db=mock_db)

    assert result is True


def test_has_new_articles_since_returns_false_when_no_articles(mock_db):
    """Test: has_new_articles_since returns False when no new articles."""
    last_summary = datetime.now(timezone.utc) - timedelta(hours=1)

    mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

    result = has_new_articles_since(obligor_id=1, last_summary_ts=last_summary, db=mock_db)

    assert result is False


# ============================================================================
# Tests for call_groq_with_backoff()
# ============================================================================

@patch("src.rag.summarizer.Groq")
def test_call_groq_with_backoff_succeeds(mock_groq_class):
    """Test: call_groq_with_backoff returns response on success."""
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    expected = '{"summary": "Test"}'
    mock_client.chat.completions.create.return_value.choices[0].message.content = expected

    result = call_groq_with_backoff("prompt")

    assert result == expected
    mock_client.chat.completions.create.assert_called_once()


@patch("src.rag.summarizer.Groq")
@patch("src.rag.summarizer.time.sleep")
def test_call_groq_with_backoff_retries_on_rate_limit(mock_sleep, mock_groq_class):
    """Test: call_groq_with_backoff retries on 429 rate limit."""
    from groq import RateLimitError
    from unittest.mock import MagicMock as MM

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    expected = '{"summary": "Success"}'
    mock_response = MM()
    mock_response.status_code = 429

    # Create RateLimitError properly with response and body
    rate_limit_error = RateLimitError("Rate limited", response=mock_response, body=None)

    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        MagicMock(choices=[MagicMock(message=MagicMock(content=expected))]),
    ]

    result = call_groq_with_backoff("prompt", retries=3)

    assert result == expected
    assert mock_client.chat.completions.create.call_count == 2
    mock_sleep.assert_called()


@patch("src.rag.summarizer.Groq")
@patch("src.rag.summarizer.time.sleep")
def test_call_groq_with_backoff_falls_back_to_secondary_model(mock_sleep, mock_groq_class):
    """Test: call_groq_with_backoff falls back after primary model exhausted."""
    from groq import RateLimitError
    from unittest.mock import MagicMock as MM

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    expected = '{"summary": "Fallback"}'
    mock_response = MM()
    mock_response.status_code = 429

    # Create RateLimitError properly
    rate_limit_error = RateLimitError("Rate limited", response=mock_response, body=None)

    # Primary model fails 3 times, fallback succeeds on 4th call
    mock_client.chat.completions.create.side_effect = [
        rate_limit_error,
        rate_limit_error,
        rate_limit_error,
        MagicMock(choices=[MagicMock(message=MagicMock(content=expected))]),
    ]

    result = call_groq_with_backoff("prompt", retries=2)

    assert result == expected
    assert mock_client.chat.completions.create.call_count == 4


@patch("src.rag.summarizer.Groq")
@patch("src.rag.summarizer.time.sleep")
def test_call_groq_with_backoff_raises_after_exhaustion(mock_sleep, mock_groq_class):
    """Test: call_groq_with_backoff raises SummarizerError after all retries exhausted."""
    from groq import RateLimitError
    from unittest.mock import MagicMock as MM

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client

    mock_response = MM()
    mock_response.status_code = 429
    rate_limit_error = RateLimitError("Rate limited", response=mock_response, body=None)

    mock_client.chat.completions.create.side_effect = rate_limit_error

    with pytest.raises(SummarizerError):
        call_groq_with_backoff("prompt", retries=1)


# ============================================================================
# Tests for ObligorSummarizer
# ============================================================================

@patch("src.rag.summarizer.call_groq_with_backoff")
@patch("src.rag.summarizer.ArticleRetriever")
def test_summarizer_generates_summary(mock_retriever_class, mock_groq, mock_db):
    """Test: ObligorSummarizer generates structured summary."""
    mock_retriever = MagicMock()
    mock_retriever_class.return_value = mock_retriever

    mock_retriever.search_by_obligor.return_value = [
        {"chunk_text": "Tesla faces liquidity pressure", "article_id": 1, "similarity": 0.85},
    ]

    mock_groq.return_value = json.dumps({
        "summary": "Tesla facing pressure",
        "key_events": ["Q4 miss"],
        "risk_level": "high",
        "concerns": ["liquidity"],
        "positive_factors": [],
        "confidence": 0.8,
    })

    # Mock obligor query
    mock_obligor = MagicMock()
    mock_obligor.name = "Tesla Inc."

    # Setup mock for obligor lookup
    mock_db.query.return_value.filter_by.return_value.one_or_none.return_value = mock_obligor

    # Setup mock for cache lookup - return None (no cache)
    mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

    summarizer = ObligorSummarizer(db=mock_db)
    result = summarizer.summarize_obligor_risk(obligor_id=1, days=7)

    assert result["company"] == "Tesla Inc."
    assert result["risk_level"] == "high"
    assert "summary" in result
    assert "key_events" in result
    assert "confidence" in result
    assert result["cached"] is False


@patch("src.rag.summarizer.call_groq_with_backoff")
@patch("src.rag.summarizer.ArticleRetriever")
def test_summarizer_caches_summary(mock_retriever_class, mock_groq, mock_db):
    """Test: ObligorSummarizer caches summaries to avoid redundant API calls."""
    mock_retriever = MagicMock()
    mock_retriever_class.return_value = mock_retriever

    mock_retriever.search_by_obligor.return_value = [
        {"chunk_text": "Test", "article_id": 1, "similarity": 0.9},
    ]

    groq_response = json.dumps({
        "summary": "Test summary",
        "key_events": [],
        "risk_level": "low",
        "concerns": [],
        "positive_factors": [],
        "confidence": 0.7,
    })
    mock_groq.return_value = groq_response

    mock_obligor = MagicMock()
    mock_obligor.name = "Test Corp"
    mock_db.query.return_value.filter_by.return_value.one_or_none.return_value = mock_obligor

    # Mock: no valid cache on first call
    mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

    summarizer = ObligorSummarizer(db=mock_db)

    # First call should hit Groq
    result1 = summarizer.summarize_obligor_risk(obligor_id=1, days=7)
    assert mock_groq.call_count == 1
    assert result1["cached"] is False

    # Second call should use cache (mock has_new_articles_since to return False)
    with patch("src.rag.summarizer.has_new_articles_since", return_value=False):
        # Mock cached entry
        mock_cached = MagicMock()
        mock_cached.summary_json = json.loads(groq_response)
        mock_cached.created_at = datetime.now(timezone.utc)
        mock_cached.model_used = "llama-3.3-70b-versatile"
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_cached

        result2 = summarizer.summarize_obligor_risk(obligor_id=1, days=7)
        # Groq should not be called again
        assert mock_groq.call_count == 1  # Still 1, not 2
        assert result2["cached"] is True


def test_summarizer_returns_empty_when_no_articles(mock_db):
    """Test: ObligorSummarizer returns empty summary when no articles found."""
    with patch("src.rag.summarizer.ArticleRetriever") as mock_retriever_class:
        mock_retriever = MagicMock()
        mock_retriever_class.return_value = mock_retriever
        mock_retriever.search_by_obligor.return_value = []

        mock_obligor = MagicMock()
        mock_obligor.name = "Test Corp"

        # Setup mock for obligor lookup
        mock_db.query.return_value.filter_by.return_value.one_or_none.return_value = mock_obligor

        # Setup mock for cache lookup - return None (no cache)
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None

        summarizer = ObligorSummarizer(db=mock_db)
        result = summarizer.summarize_obligor_risk(obligor_id=999, days=7)

        assert result["summary"] == "No recent articles"
        assert result["risk_level"] == "low"
