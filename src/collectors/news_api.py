"""
NewsAPI collector — fetches news articles for a given query and date range.

Free tier limits:
  - 100 requests/day
  - 1 month lookback max
  - 100 articles per page, up to page 5 (500 total per query)

Usage:
    collector = NewsAPICollector(api_key=settings.NEWSAPI_KEY)
    articles = collector.fetch_news("Apple Inc.", from_date="2026-03-20")
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

NEWSAPI_BASE_URL = "https://newsapi.org/v2"
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2    # waits 2, 4, 8 seconds between retries


class NewsAPIError(Exception):
    """Raised when NewsAPI returns a non-OK status or unexpected response."""


class RateLimitError(NewsAPIError):
    """Raised when the API rate limit (429) is hit."""


class NewsAPICollector:
    """
    Thin wrapper around the NewsAPI /everything endpoint.

    Handles:
      - Retry with exponential backoff on transient errors (5xx, connection errors)
      - Rate limit detection (429)
      - Request timeout (30s)
      - Structured logging of every request
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = NEWSAPI_BASE_URL,
    ) -> None:
        self.api_key = api_key or settings.NEWSAPI_KEY
        self.base_url = base_url.rstrip("/")

        if not self.api_key:
            raise ValueError("NEWSAPI_KEY is not set. Add it to your .env file.")

        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Create a requests Session with automatic retry on transient failures."""
        session = requests.Session()
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch_news(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        page_size: int = 100,
        page: int = 1,
    ) -> list[dict]:
        """
        Fetch articles from the /everything endpoint.

        Args:
            query:      Search query — company name, ticker, or boolean expression.
            from_date:  Start date as 'YYYY-MM-DD'. Defaults to 7 days ago.
            to_date:    End date as 'YYYY-MM-DD'. Defaults to today.
            language:   ISO 639-1 language code (default 'en').
            page_size:  Articles per page, max 100 (free tier).
            page:       Page number (free tier allows up to page 5).

        Returns:
            List of article dicts with keys:
              title, description, content, url, source, publishedAt, author

        Raises:
            RateLimitError: API rate limit exceeded.
            NewsAPIError:   API returned an error status.
        """
        if from_date is None:
            from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        if to_date is None:
            to_date = datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "q":        query,
            "from":     from_date,
            "to":       to_date,
            "language": language,
            "pageSize": min(page_size, 100),
            "page":     page,
            "sortBy":   "publishedAt",
            "apiKey":   self.api_key,
        }

        url = f"{self.base_url}/everything"
        logger.info(f"NewsAPI request | query={query!r} from={from_date} to={to_date} page={page}")

        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            logger.error(f"NewsAPI request timed out after {REQUEST_TIMEOUT}s for query={query!r}")
            raise NewsAPIError(f"Request timed out after {REQUEST_TIMEOUT}s")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"NewsAPI connection error: {e}")
            raise NewsAPIError(f"Connection error: {e}")

        if response.status_code == 429:
            logger.warning("NewsAPI rate limit hit (429). Slow down requests.")
            raise RateLimitError("NewsAPI daily rate limit exceeded.")

        if response.status_code == 401:
            raise NewsAPIError("Invalid NewsAPI key. Check NEWSAPI_KEY in .env.")

        if response.status_code != 200:
            raise NewsAPIError(
                f"NewsAPI returned HTTP {response.status_code}: {response.text[:200]}"
            )

        data = response.json()

        if data.get("status") != "ok":
            code = data.get("code", "unknown")
            message = data.get("message", "No message")
            raise NewsAPIError(f"NewsAPI error [{code}]: {message}")

        articles = data.get("articles", [])
        total = data.get("totalResults", 0)
        logger.info(
            f"NewsAPI response | query={query!r} total_results={total} returned={len(articles)}"
        )
        return articles

    def fetch_all_pages(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        max_pages: int = 3,
    ) -> list[dict]:
        """
        Fetch multiple pages for a query, respecting the free-tier 5-page limit.
        Adds a 1-second delay between pages to avoid hammering the API.

        Args:
            max_pages: Max number of pages to fetch (default 3 = 300 articles).
                       Free tier hard limit is 5 pages.
        """
        all_articles: list[dict] = []
        for page in range(1, min(max_pages, 5) + 1):
            try:
                articles = self.fetch_news(
                    query=query,
                    from_date=from_date,
                    to_date=to_date,
                    language=language,
                    page_size=100,
                    page=page,
                )
                if not articles:
                    break
                all_articles.extend(articles)
                if len(articles) < 100:
                    break                   # last page — no need to continue
                if page < max_pages:
                    time.sleep(1)           # polite delay between pages
            except RateLimitError:
                logger.warning(f"Rate limit hit at page {page}. Stopping pagination.")
                break

        logger.info(f"fetch_all_pages | query={query!r} total_fetched={len(all_articles)}")
        return all_articles


# ---------------------------------------------------------------------------
# Quick test — run with: python -m src.collectors.news_api
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    collector = NewsAPICollector()

    print("\n--- Fetching news for 'Apple Inc.' (last 7 days) ---\n")
    articles = collector.fetch_news(
        query="Apple Inc.",
        from_date=(datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
        page_size=10,
    )

    if not articles:
        print("No articles returned. Check your NEWSAPI_KEY and date range.")
    else:
        print(f"Total returned: {len(articles)}\n")
        for i, article in enumerate(articles[:3], 1):
            print(f"[{i}] {article.get('title')}")
            print(f"    Source : {article.get('source', {}).get('name')}")
            print(f"    URL    : {article.get('url')}")
            print(f"    Date   : {article.get('publishedAt')}")
            print(f"    Content: {str(article.get('content', ''))[:120]}...")
            print()

        # Verify expected keys are present
        expected_keys = {"title", "url", "publishedAt", "source", "content", "description"}
        actual_keys = set(articles[0].keys())
        missing = expected_keys - actual_keys
        if missing:
            print(f"⚠️  Missing expected keys: {missing}")
        else:
            print("✅ Article structure OK — all expected keys present.")
