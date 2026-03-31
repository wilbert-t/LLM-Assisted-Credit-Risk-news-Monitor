"""
LLM-based credit-relevance classifier using the configured LLM provider (Groq).

Falls back gracefully on API errors — never raises. Use as a second opinion
alongside the keyword classifier, not as a replacement.

Usage:
    from src.models.llm_classifier import classify_with_llm

    result = classify_with_llm("Company filed for bankruptcy.")
    # {"is_credit_relevant": True, "event_types": ["bankruptcy"], "error": None}
"""

from __future__ import annotations

import json
from typing import Dict, List

import requests

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """You are a credit risk analyst. Given a financial news article,
determine if it is credit-relevant (i.e., it mentions events that could affect
a company's ability to repay debt). Respond ONLY with valid JSON matching this schema:
{"is_credit_relevant": boolean, "event_types": [list of strings]}

Valid event_types: default, bankruptcy, downgrade, restructuring, rating_watch,
covenant_breach, liquidity_crisis, fraud, regulatory_action, merger_acquisition,
management_change, earnings_miss, debt_issuance, layoffs, lawsuit.
Return an empty list if no events are present."""

_FALLBACK: Dict = {"is_credit_relevant": False, "event_types": [], "error": None}


def classify_with_llm(text: str) -> Dict:
    """
    Classify a text using the configured LLM.

    Returns:
        dict with keys: is_credit_relevant (bool), event_types (List[str]), error (str|None)
        On any error: returns fallback with error message set.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("classify_with_llm: GROQ_API_KEY not set, returning fallback.")
        return {**_FALLBACK, "error": "GROQ_API_KEY not configured"}

    try:
        response = requests.post(
            _GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text[:2000]},
                ],
                "temperature": 0.0,
                "max_tokens": 150,
            },
            timeout=15,
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return {
            "is_credit_relevant": bool(parsed.get("is_credit_relevant", False)),
            "event_types": list(parsed.get("event_types", [])),
            "error": None,
        }

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning(f"classify_with_llm: could not parse LLM response: {exc}")
        return {**_FALLBACK, "error": str(exc)}
    except Exception as exc:
        logger.error(f"classify_with_llm: API call failed: {exc}")
        return {**_FALLBACK, "error": str(exc)}
