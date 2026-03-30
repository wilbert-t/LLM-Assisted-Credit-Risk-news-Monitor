"""
Unit tests for src/collectors/storage.py.

store_articles() uses SessionLocal internally, so we patch it to use the
test session (already inside a rollback transaction) for isolation.
"""

from unittest.mock import patch

import pytest

from src.collectors.storage import _map_article, _parse_datetime, store_articles, get_article_count
from src.db.models import Article
from tests.factories import article_dict


# ---------------------------------------------------------------------------
# _parse_datetime
# ---------------------------------------------------------------------------

def test_parse_datetime_valid():
    result = _parse_datetime("2026-03-28T10:00:00Z")
    assert result is not None
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 28


def test_parse_datetime_none():
    assert _parse_datetime(None) is None


def test_parse_datetime_empty_string():
    assert _parse_datetime("") is None


# ---------------------------------------------------------------------------
# _map_article
# ---------------------------------------------------------------------------

def test_map_article_valid():
    raw = article_dict()
    result = _map_article(raw)
    assert result is not None
    assert result["title"] == "Apple reports record quarterly revenue"
    assert result["url"] == "https://example.com/apple-revenue-test"
    assert result["source"] == "Reuters"


def test_map_article_no_url():
    raw = article_dict(url="")
    assert _map_article(raw) is None


def test_map_article_removed():
    raw = article_dict(title="[Removed]", url="https://removed.com")
    assert _map_article(raw) is None


def test_map_article_falls_back_to_description():
    raw = article_dict(content=None)
    result = _map_article(raw)
    assert result["content"] == raw["description"]


# ---------------------------------------------------------------------------
# store_articles (uses real PostgreSQL test DB via patched SessionLocal)
# ---------------------------------------------------------------------------

def test_store_single_article(db):
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        inserted = store_articles([article_dict()])
    assert inserted == 1
    assert db.query(Article).count() == 1


def test_store_duplicate_url(db):
    """Inserting the same URL twice should insert only once."""
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        first = store_articles([article_dict()])
        second = store_articles([article_dict()])
    assert first == 1
    assert second == 0
    assert db.query(Article).count() == 1


def test_store_batch(db):
    """Multiple distinct articles are all inserted."""
    articles = [
        article_dict(url=f"https://example.com/article-{i}", title=f"Article {i}")
        for i in range(5)
    ]
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        inserted = store_articles(articles)
    assert inserted == 5
    assert db.query(Article).count() == 5


def test_store_skips_missing_url(db):
    """Articles without a URL are skipped silently."""
    articles = [
        article_dict(url=""),
        article_dict(url="https://example.com/valid-article"),
    ]
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        inserted = store_articles(articles)
    assert inserted == 1


def test_store_empty_list(db):
    """Empty input returns 0 inserts without error."""
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        inserted = store_articles([])
    assert inserted == 0


def test_get_article_count(db):
    """get_article_count reflects the number of articles in DB."""
    db.add_all([
        Article(title="A", url="https://example.com/a", language="en"),
        Article(title="B", url="https://example.com/b", language="en"),
    ])
    db.flush()
    with patch("src.collectors.storage.SessionLocal", return_value=db):
        count = get_article_count()
    assert count == 2
