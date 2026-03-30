"""
Test data factories — produce valid model dicts and instances for tests.
"""

from src.db.models import Article, Obligor, ProcessedArticle


def article_dict(**overrides) -> dict:
    """Return a raw NewsAPI-shaped article dict (input to store_articles)."""
    data = {
        "title": "Apple reports record quarterly revenue",
        "description": "Apple Inc. reported its highest ever quarterly revenue.",
        "content": "Apple Inc. reported its highest ever quarterly revenue of $120bn.",
        "url": "https://example.com/apple-revenue-test",
        "source": {"name": "Reuters"},
        "publishedAt": "2026-03-28T10:00:00Z",
    }
    data.update(overrides)
    return data


def article_model(**overrides) -> Article:
    """Return an unsaved Article ORM instance."""
    fields = {
        "title": "Test Article",
        "content": "Some content.",
        "url": "https://example.com/test-article",
        "source": "Reuters",
        "language": "en",
    }
    fields.update(overrides)
    return Article(**fields)


def obligor_model(**overrides) -> Obligor:
    """Return an unsaved Obligor ORM instance."""
    fields = {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "country": "US",
    }
    fields.update(overrides)
    return Obligor(**fields)


def processed_article_model(article_id: int, **overrides) -> ProcessedArticle:
    """Return an unsaved ProcessedArticle ORM instance linked to an article."""
    fields = {
        "article_id": article_id,
        "cleaned_text": "Apple reported record quarterly revenue of $120bn.",
        "entities": {"ORG": ["Apple Inc."], "MONEY": ["$120bn"]},
        "sentiment_score": -0.42,
        "sentiment_label": "negative",
        "is_credit_relevant": True,
        "event_types": ["earnings", "revenue"],
    }
    fields.update(overrides)
    return ProcessedArticle(**fields)
