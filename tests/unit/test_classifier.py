"""
Unit tests for src/models/classifier.py.
Pure keyword matching — no DB, no mocks, no model needed.
"""

import pytest

from src.models.classifier import classify_events, is_credit_relevant


class TestIsCreditRelevant:

    def test_returns_true_for_bankruptcy_text(self):
        text = "The company filed for bankruptcy and entered chapter 11 proceedings."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_downgrade_text(self):
        text = "Moody's downgraded the company's credit rating to junk status."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_fraud_text(self):
        text = "Executives were charged with accounting fraud and embezzlement."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_lawsuit_text(self):
        text = "The company was sued by shareholders in a class action lawsuit."
        assert is_credit_relevant(text) is True

    def test_returns_false_for_irrelevant_text(self):
        text = "The annual company picnic was held at the local park on Saturday."
        assert is_credit_relevant(text) is False

    def test_returns_false_for_empty_string(self):
        assert is_credit_relevant("") is False

    def test_case_insensitive_matching(self):
        text = "DOWNGRADED by S&P to B- with NEGATIVE OUTLOOK."
        assert is_credit_relevant(text) is True

    def test_returns_true_for_liquidity_text(self):
        text = "The company is experiencing a severe liquidity crisis and cash crunch."
        assert is_credit_relevant(text) is True


class TestClassifyEvents:

    def test_detects_bankruptcy(self):
        text = "The retailer filed for bankruptcy protection under chapter 11."
        events = classify_events(text)
        assert "bankruptcy" in events

    def test_detects_downgrade(self):
        text = "S&P downgraded the bond from BB to CCC with a negative outlook."
        events = classify_events(text)
        assert "downgrade" in events

    def test_detects_multiple_events(self):
        text = (
            "The company was downgraded by Moody's following a massive fraud scandal "
            "that led to a lawsuit from regulators."
        )
        events = classify_events(text)
        assert "downgrade" in events
        assert "fraud" in events
        assert "lawsuit" in events

    def test_returns_empty_list_for_irrelevant_text(self):
        text = "The CEO attended the annual shareholder meeting in Chicago."
        events = classify_events(text)
        assert events == []

    def test_returns_empty_list_for_empty_string(self):
        assert classify_events("") == []

    def test_no_duplicate_event_types(self):
        text = "Fraud fraud fraud accounting fraud financial fraud."
        events = classify_events(text)
        assert events.count("fraud") == 1

    def test_detects_restructuring(self):
        text = "The firm announced a debt restructuring plan with a haircut for bondholders."
        events = classify_events(text)
        assert "restructuring" in events

    def test_detects_layoffs(self):
        text = "The company announced major layoffs affecting 5,000 employees in workforce reduction."
        events = classify_events(text)
        assert "layoffs" in events

    def test_detects_liquidity_crisis(self):
        text = "Sources say the bank faces a liquidity crisis after a cash crunch last quarter."
        events = classify_events(text)
        assert "liquidity_crisis" in events

    def test_detects_earnings_miss(self):
        text = "The company issued a profit warning after missing earnings expectations."
        events = classify_events(text)
        assert "earnings_miss" in events
