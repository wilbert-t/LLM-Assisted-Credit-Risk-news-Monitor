"""
spaCy-based Named Entity Recognition (NER) for news article text.

Public API:
    extract_entities(text)               -> Dict[str, List[Dict]]
    extract_companies_from_article(text) -> List[str]

Entity dict format (stored in processed_articles.entities):
    {
        "ORG":   [{"text": "Apple Inc.", "start": 0, "end": 10}, ...],
        "GPE":   [{"text": "US", "start": 45, "end": 47}],
        "MONEY": [{"text": "$120bn", "start": 60, "end": 66}],
    }

Model: en_core_web_sm (lazy-loaded once on first call).
To upgrade accuracy, change _MODEL_NAME to "en_core_web_lg".
"""

from typing import Dict, List, Optional

import spacy
from spacy.language import Language

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_MODEL_NAME = "en_core_web_sm"
_nlp: Optional[Language] = None


def _get_nlp() -> Language:
    """Load and cache the spaCy model on first call."""
    global _nlp
    if _nlp is None:
        logger.info(f"Loading spaCy model: {_MODEL_NAME}")
        _nlp = spacy.load(_MODEL_NAME)
    return _nlp


def extract_entities(text: str) -> Dict[str, List[Dict]]:
    """
    Run spaCy NER on text and return all named entities grouped by label.

    Each entity is a dict with keys: text, start, end (char offsets).
    Returns an empty dict for empty or whitespace-only input.

    Args:
        text: Plain text (HTML already stripped by cleaner).

    Returns:
        Dict mapping entity label -> list of {text, start, end} dicts.
        Example: {"ORG": [{"text": "Apple Inc.", "start": 0, "end": 10}]}
    """
    if not text or not text.strip():
        return {}

    nlp = _get_nlp()
    doc = nlp(text)

    result: Dict[str, List[Dict]] = {}
    for ent in doc.ents:
        result.setdefault(ent.label_, []).append({
            "text": ent.text,
            "start": ent.start_char,
            "end": ent.end_char,
        })

    return result


def extract_companies_from_article(article_text: str) -> List[str]:
    """
    Extract unique ORG entities from article text, sorted alphabetically.

    Convenience wrapper over extract_entities() for the common use-case of
    finding company names mentioned in a news article.

    Args:
        article_text: Plain text of the article.

    Returns:
        Sorted list of unique ORG entity strings. Empty list if none found.
    """
    orgs = extract_entities(article_text).get("ORG", [])
    return sorted(set(e["text"] for e in orgs))
