"""
Language detection utilities for news articles.

Public API:
    detect_language(text)             -> str   (e.g. "en", "de", "unknown")
    filter_english_articles(articles) -> List[Dict]
"""

from typing import Dict, List

from langdetect import LangDetectException, detect

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_FALLBACK_LANGUAGE = "unknown"


def detect_language(text: str) -> str:
    """
    Detect the language of a plain-text string.

    Args:
        text: Plain text (HTML already stripped).

    Returns:
        ISO 639-1 language code (e.g. "en", "de") or "unknown" on failure.
    """
    if not text or not text.strip():
        return _FALLBACK_LANGUAGE

    try:
        return detect(text)
    except LangDetectException:
        logger.debug(f"Language detection failed for: {text[:60]!r}")
        return _FALLBACK_LANGUAGE


def filter_english_articles(articles: List[Dict]) -> List[Dict]:
    """
    Filter a list of article dicts, keeping only English ones.

    Uses the 'language' key if present and not "unknown"; falls back to
    running detect_language() on 'content' or 'title'.

    Args:
        articles: List of article dicts with at least a 'title' key.

    Returns:
        Filtered list containing only English articles.
    """
    english = []
    for article in articles:
        lang = article.get("language")

        if lang and lang != _FALLBACK_LANGUAGE:
            if lang == "en":
                english.append(article)
            else:
                logger.debug(
                    f"Filtered non-English article (language={lang!r}): "
                    f"{article.get('title', '')[:60]!r}"
                )
            continue

        # Fallback: detect from content or title
        text = article.get("content") or article.get("title") or ""
        detected = detect_language(text)
        if detected == "en":
            english.append(article)
        else:
            logger.debug(
                f"Filtered non-English article (detected={detected!r}): "
                f"{article.get('title', '')[:60]!r}"
            )

    return english
