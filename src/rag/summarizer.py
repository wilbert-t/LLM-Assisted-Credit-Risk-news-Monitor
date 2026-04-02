"""
LLM-powered credit risk summarizer.

Retrieves top articles for an obligor, generates structured credit risk narratives
via Groq API, and caches results to minimize API calls.

Usage:
    summarizer = ObligorSummarizer()
    summary = summarizer.summarize_obligor_risk(obligor_id=5, days=7)
    # Returns: {company, summary, key_events, risk_level, concerns, positive_factors, confidence}
"""

import hashlib
import json
import logging
import os
import time
from datetime import UTC, date, datetime, timedelta
from typing import Dict, List, Optional

from groq import Groq, RateLimitError
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.db.models import Obligor, Summaries, Article
from src.rag.retriever import ArticleRetriever
from src.utils.constants import (
    GROQ_PRIMARY_MODEL,
    GROQ_FALLBACK_MODEL,
    GROQ_TIMEOUT_SECONDS,
    GROQ_RETRY_SLEEP_BASE,
    SUMMARY_CACHE_TTL_NORMAL,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SummarizerError(Exception):
    """Raised when summarization fails."""
    pass


def has_new_articles_since(
    obligor_id: int,
    last_summary_ts: datetime,
    db: Optional[Session] = None
) -> bool:
    """
    Check if new articles exist for an obligor since last summary.

    Args:
        obligor_id: Obligor ID
        last_summary_ts: Timestamp of last summary
        db: Database session (opens new one if None)

    Returns:
        True if new articles exist, False otherwise
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        count = (
            db.query(Article)
            .join(Article.obligor_links)
            .filter(
                Article.obligor_links.any(obligor_id=obligor_id),
                Article.published_at > last_summary_ts
            )
            .count()
        )
        return count > 0
    finally:
        if close_db:
            db.close()


def call_groq_with_backoff(
    prompt: str,
    retries: int = 3,
) -> str:
    """
    Call Groq API with intelligent retry logic and model fallback.

    Algorithm:
    1. Try primary model (llama-3.3-70b-versatile)
    2. On 429 rate limit: wait 20s * attempt, retry up to retries times
    3. If primary exhausted: switch to fallback (llama-3.1-8b-instant), reset counter
    4. Log every retry + model used
    5. Raise SummarizerError if both models fail

    Args:
        prompt: The prompt to send to Groq
        retries: Number of retries per model

    Returns:
        Response content from Groq API

    Raises:
        SummarizerError: If both models exhausted
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SummarizerError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)

    models_to_try = [
        (GROQ_PRIMARY_MODEL, "primary"),
        (GROQ_FALLBACK_MODEL, "fallback"),
    ]

    for model, tier in models_to_try:
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Groq API call (model={model}, attempt={attempt}/{retries})")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a credit risk analyst with expertise in corporate finance. "
                                "Respond ONLY with valid JSON, no preamble, no markdown backticks."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.7,
                    timeout=GROQ_TIMEOUT_SECONDS,
                )

                content = response.choices[0].message.content
                logger.info(f"Groq API success (model={model})")
                return content

            except RateLimitError as e:
                wait_time = GROQ_RETRY_SLEEP_BASE * attempt
                logger.warning(
                    f"Groq rate limit (429). Waiting {wait_time}s before retry "
                    f"(attempt {attempt}/{retries}, model={model})"
                )
                time.sleep(wait_time)

        logger.warning(f"Groq {tier} model exhausted after {retries} retries, trying next model")

    # Both models exhausted
    raise SummarizerError(
        f"Both Groq models exhausted after {retries} retries each. Cannot generate summary."
    )


class ObligorSummarizer:
    """Generate and cache credit risk summaries."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.retriever = ArticleRetriever()

    def summarize_obligor_risk(
        self,
        obligor_id: int,
        days: int = 7,
        force_refresh: bool = False,
    ) -> Dict:
        """
        Generate a credit risk summary for an obligor.

        Algorithm:
        1. Get obligor details
        2. Check cache: if valid + no new articles → return cached
        3. Retrieve top 10 articles via ArticleRetriever
        4. Format articles for prompt
        5. Call Groq with backoff
        6. Parse JSON response
        7. Store in summaries table
        8. Return structured response

        Args:
            obligor_id: Obligor ID
            days: Number of days to look back (default 7)
            force_refresh: Force fresh summary even if cache valid

        Returns:
            {
                "company": str,
                "summary": str,
                "key_events": List[str],
                "risk_level": str,
                "concerns": List[str],
                "positive_factors": List[str],
                "confidence": float,
                "model_used": str,
                "cached": bool,
            }

        Raises:
            SummarizerError: If obligor not found or Groq call fails
        """
        db, close_db = self._get_db()

        try:
            # Get obligor details
            obligor = db.query(Obligor).filter_by(id=obligor_id).one_or_none()
            if not obligor:
                raise SummarizerError(f"Obligor {obligor_id} not found")

            # Check cache
            if not force_refresh:
                cached = self._get_valid_cache(obligor_id, db)
                if cached and not has_new_articles_since(obligor_id, cached.created_at, db):
                    logger.info(f"Returning cached summary for obligor {obligor_id}")
                    return self._parse_summary_response(
                        cached.summary_json,
                        obligor.name,
                        cached.model_used,
                        cached=True,
                    )

            # Retrieve articles
            articles = self.retriever.search_by_obligor(obligor_id, days=days, top_k=10)

            if not articles:
                logger.info(f"No articles found for obligor {obligor_id}, returning empty summary")
                return {
                    "company": obligor.name,
                    "summary": "No recent articles",
                    "key_events": [],
                    "risk_level": "low",
                    "concerns": [],
                    "positive_factors": [],
                    "confidence": 0.0,
                    "model_used": None,
                    "cached": False,
                }

            # Format articles for prompt
            formatted_articles = self._format_articles_for_prompt(articles)

            # Build prompt
            prompt = self._build_prompt(obligor.name, formatted_articles)

            # Call Groq
            logger.info(f"Calling Groq for obligor {obligor_id}")
            response_text = call_groq_with_backoff(prompt)

            # Parse JSON
            try:
                summary_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise SummarizerError(f"Groq returned invalid JSON: {response_text}") from e

            # Store in cache
            article_ids = [a["article_id"] for a in articles]
            article_hash = self._hash_article_ids(article_ids)

            cache_entry = Summaries(
                obligor_id=obligor_id,
                cache_date=date.today(),
                article_hash=article_hash,
                summary_json=summary_json,
                model_used=GROQ_PRIMARY_MODEL,
            )
            db.add(cache_entry)
            db.commit()

            logger.info(f"Cached summary for obligor {obligor_id}")

            # Return response
            return self._parse_summary_response(
                summary_json,
                obligor.name,
                GROQ_PRIMARY_MODEL,
                cached=False,
            )

        finally:
            if close_db:
                db.close()

    def _get_db(self):
        """Get DB session, tracking if we need to close it."""
        if self.db is not None:
            return self.db, False
        return SessionLocal(), True

    def _get_valid_cache(self, obligor_id: int, db: Session) -> Optional[Summaries]:
        """Get cached summary if it exists and is still valid."""
        cached = db.query(Summaries).filter_by(
            obligor_id=obligor_id,
            cache_date=date.today(),
        ).order_by(Summaries.created_at.desc()).first()

        if not cached:
            return None

        # Check TTL
        ttl_minutes = SUMMARY_CACHE_TTL_NORMAL
        age_minutes = (datetime.now(UTC) - cached.created_at).total_seconds() / 60

        if age_minutes < ttl_minutes:
            return cached

        return None

    def _format_articles_for_prompt(self, articles: List[Dict]) -> str:
        """Format articles for inclusion in prompt."""
        lines = []
        for i, article in enumerate(articles, 1):
            chunk = article.get("chunk_text", "")[:200]  # Truncate
            lines.append(f"Article {i}: {chunk}...")
        return "\n".join(lines)

    def _build_prompt(self, company_name: str, formatted_articles: str) -> str:
        """Build the summarization prompt."""
        return f"""Analyze these recent articles about {company_name} for credit risk.

Provide structured JSON with exactly these fields:
- summary: 1-2 sentence credit risk narrative
- key_events: list of 3-5 most important events
- risk_level: 'low' | 'medium' | 'high' | 'critical'
- concerns: list of 3-5 credit risk factors
- positive_factors: list of any mitigating factors, or empty array
- confidence: your confidence 0.0-1.0

Articles:
{formatted_articles}

Respond only with valid JSON."""

    def _hash_article_ids(self, article_ids: List[int]) -> str:
        """Hash article IDs to create cache key."""
        sorted_ids = ",".join(str(id) for id in sorted(article_ids))
        return hashlib.sha256(sorted_ids.encode()).hexdigest()[:16]

    def _parse_summary_response(
        self,
        summary_json: Dict,
        company_name: str,
        model_used: str,
        cached: bool = False,
    ) -> Dict:
        """Parse and validate summary JSON response."""
        return {
            "company": company_name,
            "summary": summary_json.get("summary", ""),
            "key_events": summary_json.get("key_events", []),
            "risk_level": summary_json.get("risk_level", "low"),
            "concerns": summary_json.get("concerns", []),
            "positive_factors": summary_json.get("positive_factors", []),
            "confidence": float(summary_json.get("confidence", 0.7)),
            "model_used": model_used,
            "cached": cached,
        }
