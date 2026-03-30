"""
Unit tests for SQLAlchemy ORM models.
"""

from tests.factories import article_model, obligor_model
from src.db.models import ArticleObligor


def test_article_creation(db):
    """An Article can be saved and retrieved with its fields intact."""
    article = article_model(title="Bond yields spike on Fed signal")
    db.add(article)
    db.flush()

    assert article.id is not None
    assert article.title == "Bond yields spike on Fed signal"
    assert article.source == "Reuters"
    assert article.created_at is not None


def test_obligor_creation(db):
    """An Obligor can be saved and retrieved with its fields intact."""
    obligor = obligor_model(name="Microsoft Corporation", ticker="MSFT")
    db.add(obligor)
    db.flush()

    assert obligor.id is not None
    assert obligor.name == "Microsoft Corporation"
    assert obligor.ticker == "MSFT"


def test_article_obligor_relationship(db):
    """An Article and Obligor can be linked via the ArticleObligor join table."""
    article = article_model(url="https://example.com/msft-test")
    obligor = obligor_model(name="Microsoft Corporation", ticker="MSFT")
    db.add_all([article, obligor])
    db.flush()

    link = ArticleObligor(article_id=article.id, obligor_id=obligor.id)
    db.add(link)
    db.flush()

    assert len(article.obligor_links) == 1
    assert article.obligor_links[0].obligor_id == obligor.id


def test_timestamps_auto_set(db):
    """created_at and updated_at are set automatically by the server."""
    article = article_model(url="https://example.com/timestamp-test")
    db.add(article)
    db.flush()

    assert article.created_at is not None
    assert article.updated_at is not None
