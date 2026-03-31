"""
Unit tests for src/processors/language_filter.py.
No DB fixture needed — pure text transformation.
"""

import pytest

from src.processors.language_filter import detect_language, filter_english_articles


class TestDetectLanguage:

    def test_returns_en_for_english_text(self):
        text = (
            "Apple Inc. reported its highest ever quarterly revenue of one hundred "
            "and twenty billion dollars driven by strong iPhone and services sales."
        )
        assert detect_language(text) == "en"

    def test_returns_de_for_german_text(self):
        text = (
            "Apple hat im dritten Quartal Rekordgewinne erzielt und dabei alle "
            "Erwartungen der Analysten deutlich übertroffen."
        )
        assert detect_language(text) == "de"

    def test_returns_fr_for_french_text(self):
        text = (
            "Apple a annoncé des bénéfices record au quatrième trimestre de "
            "l'exercice fiscal grâce aux ventes d'iPhone et aux services."
        )
        assert detect_language(text) == "fr"

    def test_empty_string_returns_unknown(self):
        assert detect_language("") == "unknown"

    def test_whitespace_only_returns_unknown(self):
        assert detect_language("   ") == "unknown"

    def test_returns_string(self):
        assert isinstance(detect_language("Some text here."), str)


class TestFilterEnglishArticles:

    def test_keeps_english_articles(self):
        articles = [{"title": "Apple earnings beat expectations", "language": "en"}]
        result = filter_english_articles(articles)
        assert len(result) == 1

    def test_removes_non_english_articles(self):
        articles = [
            {"title": "Article in English", "language": "en"},
            {"title": "Artikel auf Deutsch", "language": "de"},
        ]
        result = filter_english_articles(articles)
        assert len(result) == 1
        assert result[0]["language"] == "en"

    def test_fallback_to_detect_when_no_language_field(self):
        articles = [{
            "title": "Microsoft Azure outage resolved after three hours of downtime across European regions",
            "content": "Microsoft confirmed the Azure outage affecting EU regions was fully resolved.",
        }]
        result = filter_english_articles(articles)
        assert len(result) == 1

    def test_fallback_filters_non_english_content(self):
        articles = [{
            "title": "Deutsche Bank meldet erheblichen Quartalsverlust",
            "content": (
                "Die Deutsche Bank hat im dritten Quartal einen erheblichen Verlust "
                "gemeldet und die Erwartungen der Analysten deutlich verfehlt."
            ),
        }]
        result = filter_english_articles(articles)
        assert len(result) == 0

    def test_empty_list_returns_empty(self):
        assert filter_english_articles([]) == []

    def test_unknown_language_field_falls_back_to_detect(self):
        articles = [{
            "title": "Goldman Sachs reports strong quarterly results beating analyst expectations",
            "content": "Goldman Sachs has posted strong results for the quarter, beating all forecasts.",
            "language": "unknown",
        }]
        result = filter_english_articles(articles)
        assert len(result) == 1

    def test_preserves_all_article_fields(self):
        articles = [{
            "title": "Bond yields rise amid inflation concerns",
            "language": "en",
            "url": "https://example.com/bonds",
            "source": "Reuters",
        }]
        result = filter_english_articles(articles)
        assert result[0]["url"] == "https://example.com/bonds"
        assert result[0]["source"] == "Reuters"
