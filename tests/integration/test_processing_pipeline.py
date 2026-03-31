"""
Integration tests for the full processing pipeline (Days 8–10).

Uses the real PostgreSQL test DB via the `db` fixture (transactional rollback).
Both pipeline functions accept db= directly — no SessionLocal patching needed.

Call sequence: process_articles_batch(db=db) → map_articles_to_obligors(db=db)
"""

import pytest

from src.db.models import ArticleObligor, ProcessedArticle
from src.processors.entity_mapper import map_articles_to_obligors
from src.processors.pipeline import process_articles_batch
from tests.factories import article_model, obligor_model

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_CONTENT = (
    "reported its highest ever quarterly revenue driven by strong iPhone and "
    "services sales, surpassing all analyst expectations for the period."
)


# ---------------------------------------------------------------------------
# TestProcessSingleArticle
# ---------------------------------------------------------------------------

class TestProcessSingleArticle:

    def test_stores_cleaned_text(self, db):
        article = article_model(
            url="https://example.com/integ-1",
            title="Apple reports record quarterly revenue",
            content="Apple Inc. " + _LONG_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)

        assert count == 1
        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.cleaned_text is not None
        assert len(pa.cleaned_text) >= 30
        assert "Apple" in pa.cleaned_text

    def test_extracts_org_entities(self, db):
        article = article_model(
            url="https://example.com/integ-2",
            title="Microsoft Azure outage resolved",
            content=(
                "Microsoft Corporation confirmed the Azure outage affecting EU regions "
                "was resolved after three hours of downtime across all zones."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.entities is not None
        assert "ORG" in pa.entities
        org_texts = [e["text"] for e in pa.entities["ORG"]]
        assert any("Microsoft" in t for t in org_texts)


# ---------------------------------------------------------------------------
# TestProcessBatch
# ---------------------------------------------------------------------------

class TestProcessBatch:

    def test_process_20_articles(self, db):
        articles = [
            article_model(
                url=f"https://example.com/batch-{i}",
                title=f"Goldman Sachs quarterly report number {i}",
                content=f"Goldman Sachs reported strong earnings in quarter {i} of fiscal year 2026 " + _LONG_CONTENT,
                language="en",
            )
            for i in range(20)
        ]
        db.add_all(articles)
        db.flush()

        ids = [a.id for a in articles]
        count = process_articles_batch(article_ids=ids, db=db)

        assert count == 20
        stored = db.query(ProcessedArticle).filter(
            ProcessedArticle.article_id.in_(ids)
        ).count()
        assert stored == 20

    def test_second_run_skips_already_processed(self, db):
        articles = [
            article_model(
                url=f"https://example.com/rerun-{i}",
                title=f"Bond yield rises sharply amid inflation concerns in global markets {i}",
                content="Bond yields rose sharply as investors reacted to higher-than-expected inflation data " + _LONG_CONTENT,
                language="en",
            )
            for i in range(5)
        ]
        db.add_all(articles)
        db.flush()
        ids = [a.id for a in articles]

        first = process_articles_batch(article_ids=ids, db=db)
        second = process_articles_batch(article_ids=ids, db=db)

        assert first == 5
        assert second == 0


# ---------------------------------------------------------------------------
# TestPipelineRobustness
# ---------------------------------------------------------------------------

class TestPipelineRobustness:

    def test_short_text_article_is_skipped(self, db):
        article = article_model(
            url="https://example.com/short-1",
            title="Hi",
            content="",
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)

        assert count == 0
        assert db.query(ProcessedArticle).filter_by(article_id=article.id).first() is None

    def test_html_content_is_cleaned(self, db):
        article = article_model(
            url="https://example.com/html-1",
            title="Markets update: stocks fell sharply amid global credit concerns this week",
            content="<p>Stocks <b>fell</b> sharply on Wednesday amid credit concerns in global markets.</p>",
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)

        assert count == 1
        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert "<" not in pa.cleaned_text
        assert "fell" in pa.cleaned_text

    def test_no_matching_obligor_does_not_crash(self, db):
        article = article_model(
            url="https://example.com/no-obligor-1",
            title="Banana Corp reports record banana sales across all global markets",
            content="Banana Corp announced record sales this quarter in all international markets " + _LONG_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)
        assert count == 1

        links = map_articles_to_obligors(db=db)
        assert links == 0

    def test_non_english_article_is_skipped(self, db):
        article = article_model(
            url="https://example.com/german-1",
            title="Apple meldet Rekordgewinne im dritten Quartal des Geschäftsjahres",
            content="Apple hat im dritten Quartal Rekordgewinne erzielt und alle Erwartungen übertroffen.",
            language="de",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)
        assert count == 0


# ---------------------------------------------------------------------------
# TestEndToEndWithEntityMapping
# ---------------------------------------------------------------------------

class TestEndToEndWithEntityMapping:

    def test_full_pipeline_creates_article_obligor_link(self, db):
        article = article_model(
            url="https://example.com/e2e-1",
            title="Apple Inc. reports record quarterly revenue",
            content="Apple Inc. " + _LONG_CONTENT,
            language="en",
        )
        o = obligor_model(name="Apple Inc.", ticker="AAPL")
        db.add_all([article, o])
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)
        links = map_articles_to_obligors(db=db)

        assert links >= 1
        link = db.query(ArticleObligor).filter_by(
            article_id=article.id, obligor_id=o.id
        ).first()
        assert link is not None

    def test_full_pipeline_multiple_obligors(self, db):
        article = article_model(
            url="https://example.com/e2e-2",
            title="Microsoft and Goldman Sachs partner on new financial technology platform",
            content=(
                "Microsoft Corporation and Goldman Sachs Group announced a strategic "
                "partnership to develop new financial technology solutions for institutional investors."
            ),
            language="en",
        )
        msft = obligor_model(name="Microsoft Corporation", ticker="MSFT")
        gs = obligor_model(name="Goldman Sachs Group", ticker="GS")
        db.add_all([article, msft, gs])
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)
        links = map_articles_to_obligors(db=db)

        assert links >= 1
        all_links = db.query(ArticleObligor).filter_by(article_id=article.id).all()
        obligor_ids = {lnk.obligor_id for lnk in all_links}
        assert msft.id in obligor_ids or gs.id in obligor_ids
