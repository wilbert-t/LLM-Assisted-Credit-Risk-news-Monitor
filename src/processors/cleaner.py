"""
Text cleaning utilities for raw news articles.

Pipeline:
    raw HTML/text → clean_html() → normalize_text() → clean_article()

Functions:
    clean_html(html)          Strip tags, fix encoding, remove boilerplate.
    normalize_text(text)      Whitespace, URLs, punctuation normalisation.
    clean_article(article)    Combine title + content, return cleaned string.
"""

import re
import unicodedata
from typing import Dict, Optional

from bs4 import BeautifulSoup

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Boilerplate patterns common in news article footers / disclaimers
# ---------------------------------------------------------------------------

_BOILERPLATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)this article (is|was) (originally )?published (by|in|on)\b.*"),
    re.compile(r"(?i)click here to (read|see|view)\b.*"),
    re.compile(r"(?i)sign up (for|to)\b.*newsletter.*"),
    re.compile(r"(?i)subscribe (now|today|for free)\b.*"),
    re.compile(r"(?i)all rights reserved\.?$"),
    re.compile(r"(?i)© \d{4}.*"),
    re.compile(r"(?i)read (more|full article|the full story)\b.*"),
    re.compile(r"(?i)disclosure[:\s].*"),
    re.compile(r"(?i)this (content|article) (is for|does not constitute)\b.*"),
    re.compile(r"\[\+\d+ chars?\]$"),  # NewsAPI truncation marker e.g. "[+1234 chars]"
]

# ---------------------------------------------------------------------------
# URL regex — match http/https and bare www. links
# ---------------------------------------------------------------------------

_URL_RE = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

MIN_TEXT_LENGTH = 30  # characters; shorter text is treated as empty


def clean_html(html: str) -> str:
    """
    Remove HTML tags, fix Unicode encoding issues, and strip boilerplate lines.

    Args:
        html: Raw string that may contain HTML markup.

    Returns:
        Plain text with tags removed and encoding normalised.
    """
    if not html:
        return ""

    # BeautifulSoup extracts visible text; "html.parser" ships with Python stdlib.
    soup = BeautifulSoup(html, "html.parser")

    # Remove script / style blocks entirely.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # Normalise Unicode (e.g. curly quotes, ligatures, non-breaking spaces).
    text = unicodedata.normalize("NFKC", text)

    # Remove boilerplate lines.
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(pat.search(stripped) for pat in _BOILERPLATE_PATTERNS):
            continue
        cleaned_lines.append(stripped)

    return " ".join(cleaned_lines)


def normalize_text(text: str) -> str:
    """
    Normalise whitespace, remove URLs, fix punctuation, and strip non-essential
    special characters.

    Keeps: letters, digits, basic punctuation (.,!?;:'"()-%), and spaces.

    Args:
        text: Plain text (HTML already stripped).

    Returns:
        Normalised plain text.
    """
    if not text:
        return ""

    # Remove URLs.
    text = _URL_RE.sub(" ", text)

    # Normalise typographic quotes and dashes.
    text = text.replace("\u2018", "'").replace("\u2019", "'")   # '' → '
    text = text.replace("\u201c", '"').replace("\u201d", '"')   # "" → "
    text = text.replace("\u2013", "-").replace("\u2014", "-")   # en/em dash → -
    text = text.replace("\u2026", "...")                         # … → ...

    # Remove characters outside the allowed set.
    text = re.sub(r"[^\w\s.,!?;:'\"()\-\%]", " ", text)

    # Collapse runs of whitespace to a single space.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_article(article: Dict) -> str:
    """
    Produce a single cleaned text string from a raw article dict or ORM row.

    Combines title and content, cleans HTML, normalises text, and returns the
    result.  Returns an empty string if the combined text is shorter than
    MIN_TEXT_LENGTH after cleaning.

    Args:
        article: Dict (or ORM object with .title / .content attributes) with
                 at minimum a 'title' key/attr.

    Returns:
        Cleaned text string, or "" if the article is too short.
    """
    # Support both plain dicts and SQLAlchemy model instances.
    if hasattr(article, "__dict__"):
        title = getattr(article, "title", "") or ""
        content = getattr(article, "content", "") or ""
    else:
        title = article.get("title", "") or ""
        content = article.get("content", "") or ""

    combined = f"{title}. {content}" if content.strip() else title

    cleaned = normalize_text(clean_html(combined))

    if len(cleaned) < MIN_TEXT_LENGTH:
        logger.debug(
            f"clean_article: result too short ({len(cleaned)} chars), "
            f"title={title[:60]!r}"
        )
        return ""

    return cleaned
