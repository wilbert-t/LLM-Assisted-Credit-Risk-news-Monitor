"""
Unit tests for src/processors/entity_mapper.py.
Uses the real PostgreSQL test DB via the `db` fixture (transactional rollback).
"""

import pytest

from src.db.models import ArticleObligor
from src.processors.entity_mapper import FUZZY_THRESHOLD, map_articles_to_obligors, match_entity_to_obligor
from tests.factories import article_model, obligor_model, processed_article_model


# ---------------------------------------------------------------------------
# match_entity_to_obligor
# ---------------------------------------------------------------------------

class TestMatchEntityToObligor:

    def test_exact_ticker_match(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("AAPL", db) == o.id

    def test_exact_ticker_case_insensitive(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("aapl", db) == o.id

    def test_exact_name_match(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("Apple Inc.", db) == o.id

    def test_exact_name_case_insensitive(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("apple inc.", db) == o.id

    def test_fuzzy_name_match(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        # "Apple Inc" (no period) should fuzzy-match "Apple Inc."
        assert match_entity_to_obligor("Apple Inc", db) == o.id

    def test_fuzzy_match_goldman_sachs(self, db):
        o = obligor_model(name="Goldman Sachs Group", ticker="GS")
        db.add(o)
        db.flush()
        # token_set_ratio handles extra suffix tokens well
        assert match_entity_to_obligor("Goldman Sachs Group Inc.", db) == o.id

    def test_unknown_entity_returns_none(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("Banana Corp", db) is None

    def test_empty_entity_returns_none(self, db):
        assert match_entity_to_obligor("", db) is None

    def test_whitespace_entity_returns_none(self, db):
        assert match_entity_to_obligor("   ", db) is None

    def test_uses_preloaded_obligors_list(self, db):
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        from src.db.models import Obligor
        preloaded = db.query(Obligor).all()
        assert match_entity_to_obligor("AAPL", db, obligors=preloaded) == o.id

    def test_fuzzy_threshold_boundary(self, db):
        # Very different name should not match
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add(o)
        db.flush()
        assert match_entity_to_obligor("Completely Unrelated Name", db) is None


# ---------------------------------------------------------------------------
# map_articles_to_obligors
# ---------------------------------------------------------------------------

class TestMapArticlesToObligors:

    def test_creates_link_for_matching_entity(self, db):
        article = article_model(url="https://example.com/mapper-1")
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add_all([article, o])
        db.flush()

        pa = processed_article_model(
            article.id,
            entities={"ORG": [{"text": "Apple Inc.", "start": 0, "end": 10}]},
        )
        db.add(pa)
        db.flush()

        count = map_articles_to_obligors(db=db)

        assert count == 1
        link = db.query(ArticleObligor).filter_by(
            article_id=article.id, obligor_id=o.id
        ).first()
        assert link is not None

    def test_returns_zero_when_no_processed_articles(self, db):
        count = map_articles_to_obligors(db=db)
        assert count == 0

    def test_no_match_creates_no_link(self, db):
        article = article_model(url="https://example.com/mapper-2")
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add_all([article, o])
        db.flush()

        pa = processed_article_model(
            article.id,
            entities={"ORG": [{"text": "Banana Corp", "start": 0, "end": 11}]},
        )
        db.add(pa)
        db.flush()

        count = map_articles_to_obligors(db=db)
        assert count == 0

    def test_idempotent_on_rerun(self, db):
        article = article_model(url="https://example.com/mapper-3")
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add_all([article, o])
        db.flush()

        pa = processed_article_model(
            article.id,
            entities={"ORG": [{"text": "AAPL", "start": 0, "end": 4}]},
        )
        db.add(pa)
        db.flush()

        first = map_articles_to_obligors(db=db)
        second = map_articles_to_obligors(db=db)

        assert first == 1
        assert second == 0

    def test_deduplicates_same_obligor_mentioned_twice(self, db):
        article = article_model(url="https://example.com/mapper-4")
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add_all([article, o])
        db.flush()

        pa = processed_article_model(
            article.id,
            entities={"ORG": [
                {"text": "Apple Inc.", "start": 0, "end": 10},
                {"text": "AAPL", "start": 20, "end": 24},
            ]},
        )
        db.add(pa)
        db.flush()

        count = map_articles_to_obligors(db=db)

        assert count == 1
        links = db.query(ArticleObligor).filter_by(article_id=article.id).all()
        assert len(links) == 1
