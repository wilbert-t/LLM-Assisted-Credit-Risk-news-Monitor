"""
Integration tests for sentiment scoring, credit classification, and risk scoring.
Uses real PostgreSQL test DB via the `db` fixture (transactional rollback).
"""

import pytest

from src.db.models import ProcessedArticle
from src.models.risk_scorer import score_article_risk
from src.processors.pipeline import process_articles_batch
from tests.factories import article_model, processed_article_model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BANKRUPTCY_CONTENT = (
    "The company filed for bankruptcy protection under chapter 11 after missing "
    "debt payments and experiencing a severe liquidity crisis that left creditors "
    "with no recovery options according to court filings released today."
)

_GENERIC_CONTENT = (
    "The company held its annual picnic in the park last Saturday and employees "
    "enjoyed games, food, and sunny weather throughout the afternoon event."
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSentimentScoring:

    def test_pipeline_populates_sentiment_fields_as_none(self, db):
        """
        Pipeline sets sentiment_score=None and sentiment_label=None.
        Sentiment is scored separately by score_sentiment.py — not inline.
        """
        article = article_model(
            url="https://example.com/integ-sent-1",
            title="Apple reports record quarterly revenue",
            content="Apple Inc. reported its highest ever quarterly revenue of $120bn driven by strong iPhone sales.",
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        # Sentiment is NULL until score_sentiment.py runs
        assert pa.sentiment_score is None
        assert pa.sentiment_label is None


class TestCreditRelevance:

    def test_bankruptcy_article_is_credit_relevant(self, db):
        """Article containing 'bankruptcy' and 'chapter 11' → is_credit_relevant=True."""
        article = article_model(
            url="https://example.com/integ-cr-1",
            title="Company files for bankruptcy",
            content=_BANKRUPTCY_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.is_credit_relevant is True

    def test_generic_article_is_not_credit_relevant(self, db):
        """Article about a company picnic → is_credit_relevant=False."""
        article = article_model(
            url="https://example.com/integ-cr-2",
            title="Company holds annual picnic",
            content=_GENERIC_CONTENT,
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.is_credit_relevant is False


class TestEventClassification:

    def test_downgrade_article_has_downgrade_event(self, db):
        """Article mentioning 'downgraded' → 'downgrade' in event_types."""
        article = article_model(
            url="https://example.com/integ-ev-1",
            title="S&P downgraded the company",
            content=(
                "S&P Global downgraded the company's credit rating from BB to B- "
                "citing concerns about cash flow and debt levels. The outlook remains "
                "negative according to the rating agency report."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert pa.event_types is not None
        assert "downgrade" in pa.event_types

    def test_multiple_events_detected(self, db):
        """Article with both bankruptcy and fraud keywords → both in event_types."""
        article = article_model(
            url="https://example.com/integ-ev-2",
            title="Bankruptcy filed amid fraud investigation",
            content=(
                "The company filed for bankruptcy protection under chapter 11 as federal "
                "prosecutors announced fraud charges related to accounting fraud and "
                "embezzlement by senior executives."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        assert "bankruptcy" in pa.event_types
        assert "fraud" in pa.event_types


class TestFullEnrichmentPipeline:

    def test_pipeline_populates_all_classifier_fields(self, db):
        """End-to-end: raw article → cleaned_text, entities, is_credit_relevant, event_types."""
        article = article_model(
            url="https://example.com/integ-full-1",
            title="Company faces downgrade and lawsuit",
            content=(
                "The company was downgraded by Moody's and faces a class action lawsuit "
                "from shareholders following disappointing quarterly results. The board "
                "has hired restructuring advisors to explore options."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        count = process_articles_batch(article_ids=[article.id], db=db)

        assert count == 1
        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa is not None
        # Text processing
        assert pa.cleaned_text is not None and len(pa.cleaned_text) > 0
        # Classifier fields — populated inline by pipeline
        assert pa.is_credit_relevant is True
        assert pa.event_types is not None
        assert len(pa.event_types) >= 1
        # Sentiment — still NULL (scored by separate script)
        assert pa.sentiment_score is None

    def test_risk_scorer_uses_pipeline_output(self, db):
        """score_article_risk() correctly uses fields populated by the pipeline."""
        article = article_model(
            url="https://example.com/integ-full-2",
            title="Firm defaults on debt payments",
            content=(
                "The firm failed to pay its quarterly coupon and has defaulted on "
                "its debt obligations, triggering cross-default clauses across "
                "the capital structure according to bondholders."
            ),
            language="en",
        )
        db.add(article)
        db.flush()

        process_articles_batch(article_ids=[article.id], db=db)

        pa = db.query(ProcessedArticle).filter_by(article_id=article.id).first()
        assert pa.is_credit_relevant is True

        score = score_article_risk({
            "sentiment_score":    pa.sentiment_score,   # None — no FinBERT in tests
            "is_credit_relevant": pa.is_credit_relevant,
            "event_types":        pa.event_types,
        })
        # is_credit_relevant=True (+0.5) + default event (+0.3) = 0.8 minimum
        assert score >= 0.8
