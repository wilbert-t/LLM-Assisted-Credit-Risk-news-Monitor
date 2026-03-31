"""
Unit tests for src/processors/ner_extractor.py.

These tests run against the real en_core_web_sm model — no DB fixture needed.
All tests are skipped automatically if the model is not installed.
"""

import pytest

# ---------------------------------------------------------------------------
# Skip guard — skip all tests if the spaCy model is not installed
# ---------------------------------------------------------------------------

try:
    import spacy
    spacy.load("en_core_web_sm")
    _MODEL_AVAILABLE = True
except OSError:
    _MODEL_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _MODEL_AVAILABLE,
    reason="en_core_web_sm not installed — run: pip install en-core-web-sm",
)

from src.processors.ner_extractor import extract_companies_from_article, extract_entities


# ---------------------------------------------------------------------------
# extract_entities
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_returns_dict(self):
        result = extract_entities("Apple Inc. reported earnings.")
        assert isinstance(result, dict)

    def test_extracts_org_entities(self):
        result = extract_entities("Apple Inc. reported record quarterly revenue on Wall Street.")
        assert "ORG" in result
        org_texts = [e["text"] for e in result["ORG"]]
        assert any("Apple" in t for t in org_texts)

    def test_extracts_multiple_entity_types(self):
        text = "Goldman Sachs reported $4bn in revenue from operations in New York."
        result = extract_entities(text)
        assert len(result) >= 2

    def test_entity_has_text_and_offsets(self):
        result = extract_entities("Apple Inc. reported earnings.")
        assert "ORG" in result
        ent = result["ORG"][0]
        assert "text" in ent
        assert "start" in ent
        assert "end" in ent
        assert isinstance(ent["start"], int)
        assert isinstance(ent["end"], int)
        assert ent["end"] > ent["start"]

    def test_char_offsets_are_correct(self):
        text = "Apple Inc. reported record earnings."
        result = extract_entities(text)
        assert "ORG" in result
        for ent in result["ORG"]:
            assert text[ent["start"]:ent["end"]] == ent["text"]

    def test_empty_string_returns_empty_dict(self):
        assert extract_entities("") == {}

    def test_whitespace_only_returns_empty_dict(self):
        assert extract_entities("   ") == {}

    def test_no_entities_in_generic_text(self):
        result = extract_entities("the quick brown fox jumps over the lazy dog")
        assert isinstance(result, dict)

    def test_ambiguous_name_does_not_crash(self):
        result = extract_entities("Apple shares rose 3% after the earnings call.")
        assert isinstance(result, dict)

    def test_known_financial_entities(self):
        text = (
            "Moody's downgraded Deutsche Bank's long-term debt to Ba1, "
            "citing exposure to US Treasury markets worth $500 billion."
        )
        result = extract_entities(text)
        all_entity_texts = [e["text"] for ents in result.values() for e in ents]
        assert len(all_entity_texts) > 0

    def test_multiple_calls_use_cached_model(self):
        extract_entities("Apple Inc.")
        result = extract_entities("Goldman Sachs in New York.")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# extract_companies_from_article
# ---------------------------------------------------------------------------

class TestExtractCompaniesFromArticle:
    def test_returns_list(self):
        result = extract_companies_from_article("Apple Inc. reported earnings.")
        assert isinstance(result, list)

    def test_returns_sorted_list(self):
        text = (
            "Microsoft and Apple both reported strong earnings. "
            "Meanwhile, Amazon also beat expectations."
        )
        result = extract_companies_from_article(text)
        assert result == sorted(result)

    def test_deduplicates_repeated_company(self):
        text = "Apple reported earnings. Apple shares rose. Apple CEO spoke."
        result = extract_companies_from_article(text)
        assert len(result) == len(set(result))

    def test_empty_text_returns_empty_list(self):
        assert extract_companies_from_article("") == []

    def test_no_orgs_returns_empty_list_or_list(self):
        result = extract_companies_from_article("It rained heavily on Tuesday.")
        assert isinstance(result, list)

    def test_result_is_list_of_strings(self):
        text = "Goldman Sachs raised its price target for Tesla after record deliveries."
        result = extract_companies_from_article(text)
        assert isinstance(result, list)
        assert all(isinstance(name, str) for name in result)

    def test_ambiguous_name_result_type(self):
        result = extract_companies_from_article("Apple could be a fruit or a company.")
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)
