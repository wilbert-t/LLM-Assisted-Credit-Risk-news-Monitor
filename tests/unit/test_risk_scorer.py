"""
Unit tests for src/models/risk_scorer.py.
Pure unit tests — no DB, no ML model, no mocks needed.
"""

import pytest

from src.models.risk_scorer import score_article_risk


class TestScoreArticleRisk:

    def test_high_risk_article_default_event(self):
        """Negative sentiment + credit relevant + default event → near 1.0."""
        article = {
            "sentiment_score": -0.8,
            "is_credit_relevant": True,
            "event_types": ["default"],
        }
        score = score_article_risk(article)
        # 0.5 (relevant) + 0.3 (neg sentiment) + 0.3 (default) = 1.1 → clamped to 1.0
        assert score == 1.0

    def test_low_risk_article_positive_sentiment(self):
        """Positive sentiment + not credit relevant → low score."""
        article = {
            "sentiment_score": 0.7,
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == 0.0

    def test_credit_relevant_adds_0_5(self):
        """Credit relevance alone adds 0.5 to base score of 0."""
        article = {
            "sentiment_score": 0.1,  # positive, no sentiment bonus
            "is_credit_relevant": True,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.5)

    def test_negative_sentiment_adds_0_3(self):
        """Negative sentiment (< 0) adds 0.3."""
        article = {
            "sentiment_score": -0.01,  # just below zero
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.3)

    def test_positive_sentiment_no_bonus(self):
        """Positive or zero sentiment score adds nothing."""
        article = {
            "sentiment_score": 0.0,
            "is_credit_relevant": False,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.0)

    def test_downgrade_event_adds_0_2(self):
        """Downgrade event adds 0.2 on top of credit_relevant bonus."""
        article = {
            "sentiment_score": 0.1,  # positive, no sentiment bonus
            "is_credit_relevant": True,
            "event_types": ["downgrade"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.2 = 0.7
        assert score == pytest.approx(0.7)

    def test_bankruptcy_event_adds_0_2(self):
        """Bankruptcy event adds 0.2."""
        article = {
            "sentiment_score": 0.0,
            "is_credit_relevant": True,
            "event_types": ["bankruptcy"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.2 = 0.7
        assert score == pytest.approx(0.7)

    def test_multiple_events_stack(self):
        """Multiple event bonuses stack, clamped at 1.0."""
        article = {
            "sentiment_score": -0.5,
            "is_credit_relevant": True,
            "event_types": ["default", "downgrade", "fraud"],
        }
        score = score_article_risk(article)
        # 0.5 + 0.3 + 0.3 + 0.2 + 0.15 = 1.45 → clamped to 1.0
        assert score == 1.0

    def test_none_sentiment_no_sentiment_bonus(self):
        """None sentiment_score should not add the negative-sentiment bonus."""
        article = {
            "sentiment_score": None,
            "is_credit_relevant": True,
            "event_types": [],
        }
        score = score_article_risk(article)
        assert score == pytest.approx(0.5)

    def test_none_event_types_treated_as_empty(self):
        """None event_types should behave identically to []."""
        article = {
            "sentiment_score": -0.5,
            "is_credit_relevant": True,
            "event_types": None,
        }
        score = score_article_risk(article)
        # 0.5 + 0.3 = 0.8
        assert score == pytest.approx(0.8)

    def test_score_always_between_0_and_1(self):
        """Score is always in [0.0, 1.0] regardless of inputs."""
        article = {
            "sentiment_score": -1.0,
            "is_credit_relevant": True,
            "event_types": ["default", "bankruptcy", "fraud", "downgrade", "liquidity_crisis"],
        }
        score = score_article_risk(article)
        assert 0.0 <= score <= 1.0
