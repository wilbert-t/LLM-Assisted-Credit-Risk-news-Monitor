"""
Keyword-based credit-relevance classifier.

Determines whether a piece of text mentions a credit-relevant event (bankruptcy,
downgrade, fraud, etc.) and which event types are present.

Usage:
    from src.models.classifier import is_credit_relevant, classify_events

    relevant = is_credit_relevant("Company filed for bankruptcy.")  # True
    events   = classify_events("Company filed for bankruptcy.")     # ["bankruptcy"]
"""

from typing import List

from src.utils.constants import KEYWORDS


def is_credit_relevant(text: str) -> bool:
    """
    Return True if the text contains at least one credit-risk keyword.
    Matching is case-insensitive.
    """
    if not text:
        return False
    lower = text.lower()
    return any(
        kw.lower() in lower
        for keywords in KEYWORDS.values()
        for kw in keywords
    )


def classify_events(text: str) -> List[str]:
    """
    Return a list of matched event type strings (from KEYWORDS keys).
    Each event type appears at most once. Order follows KEYWORDS dict order.
    Returns an empty list if no keywords match.
    """
    if not text:
        return []
    lower = text.lower()
    return [
        event_type
        for event_type, keywords in KEYWORDS.items()
        if any(kw.lower() in lower for kw in keywords)
    ]
