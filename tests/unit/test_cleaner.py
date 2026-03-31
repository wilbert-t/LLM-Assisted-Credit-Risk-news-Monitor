"""
Unit tests for src/processors/cleaner.py.

All three public functions are tested:
  - clean_html()      — tag removal, encoding, boilerplate
  - normalize_text()  — URLs, punctuation, whitespace
  - clean_article()   — integration of both, min-length guard
"""

import pytest

from src.processors.cleaner import (
    MIN_TEXT_LENGTH,
    clean_article,
    clean_html,
    normalize_text,
)


# ---------------------------------------------------------------------------
# clean_html
# ---------------------------------------------------------------------------

class TestCleanHtml:
    def test_strips_html_tags(self):
        result = clean_html("<p>Hello <b>world</b>.</p>")
        assert "<" not in result
        assert "Hello" in result
        assert "world" in result

    def test_removes_script_tags(self):
        result = clean_html("<p>Content</p><script>alert('xss')</script>")
        assert "alert" not in result
        assert "Content" in result

    def test_removes_style_tags(self):
        result = clean_html("<style>body{color:red}</style><p>Text</p>")
        assert "color" not in result
        assert "Text" in result

    def test_fixes_html_entities(self):
        result = clean_html("<p>AT&amp;T announced &lt;results&gt;</p>")
        assert "AT&T" in result
        assert "&amp;" not in result

    def test_unicode_normalisation(self):
        # Non-breaking space (\xa0) should become a regular space.
        result = clean_html("Hello\xa0world")
        assert "\xa0" not in result
        assert "Hello" in result

    def test_strips_newsapi_truncation_marker(self):
        result = clean_html("Some article content [+1234 chars]")
        assert "[+1234 chars]" not in result

    def test_empty_string_returns_empty(self):
        assert clean_html("") == ""

    def test_none_returns_empty(self):
        assert clean_html(None) == ""

    def test_plain_text_passes_through(self):
        text = "Apple reported record earnings."
        result = clean_html(text)
        assert "Apple" in result
        assert "earnings" in result


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_removes_http_urls(self):
        result = normalize_text("Read more at https://example.com/article today.")
        assert "https://" not in result
        assert "Read more" in result

    def test_removes_www_urls(self):
        result = normalize_text("Visit www.example.com for details.")
        assert "www." not in result

    def test_replaces_curly_quotes(self):
        result = normalize_text("\u201cHello\u201d and \u2018world\u2019")
        assert "\u201c" not in result
        assert "\u201d" not in result
        assert '"Hello"' in result

    def test_replaces_em_dash(self):
        result = normalize_text("Apple\u2014the iPhone maker\u2014reported earnings.")
        assert "\u2014" not in result
        assert "-" in result

    def test_collapses_whitespace(self):
        result = normalize_text("Too   many    spaces\there")
        assert "  " not in result
        assert "\t" not in result

    def test_empty_string_returns_empty(self):
        assert normalize_text("") == ""

    def test_strips_leading_trailing_whitespace(self):
        result = normalize_text("  hello world  ")
        assert result == result.strip()

    def test_keeps_basic_punctuation(self):
        result = normalize_text("Earnings fell 10%, down from $120bn.")
        assert "%" in result
        assert "$" not in result   # $ is not in the allowed set (\w\s.,!?;:'"()-%\)
        assert "." in result


# ---------------------------------------------------------------------------
# clean_article
# ---------------------------------------------------------------------------

class TestCleanArticle:
    def test_combines_title_and_content(self):
        article = {
            "title": "Apple earnings",
            "content": "Apple Inc. reported record quarterly revenue of $120bn.",
        }
        result = clean_article(article)
        assert "Apple" in result
        assert "revenue" in result

    def test_uses_title_only_when_no_content(self):
        article = {"title": "Apple earnings beat expectations by wide margin.", "content": ""}
        result = clean_article(article)
        assert "Apple" in result

    def test_returns_empty_for_too_short_text(self):
        article = {"title": "Hi", "content": ""}
        result = clean_article(article)
        assert result == ""

    def test_strips_html_in_content(self):
        article = {
            "title": "Markets update",
            "content": "<p>Stocks <b>fell</b> sharply on Wednesday amid credit concerns.</p>",
        }
        result = clean_article(article)
        assert "<" not in result
        assert "fell" in result

    def test_orm_object_supported(self):
        """clean_article should accept ORM-like objects with .title/.content attrs."""
        class FakeArticle:
            title = "Microsoft Azure outage resolved after three hours of downtime."
            content = "Microsoft confirmed that the Azure outage affecting EU regions was resolved."

        result = clean_article(FakeArticle())
        assert "Microsoft" in result
        assert "Azure" in result

    def test_none_content_handled(self):
        article = {
            "title": "Bond yields rise sharply on inflation concerns in global markets.",
            "content": None,
        }
        result = clean_article(article)
        assert "Bond" in result

    def test_min_length_boundary(self):
        # A string just at the boundary should not be empty.
        long_title = "a" * MIN_TEXT_LENGTH
        article = {"title": long_title, "content": ""}
        result = clean_article(article)
        assert result != ""
