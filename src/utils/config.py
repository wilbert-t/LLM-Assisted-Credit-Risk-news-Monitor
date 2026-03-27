"""
Centralised application settings loaded from the .env file via pydantic-settings.
Import the singleton `settings` anywhere in the project:

    from src.utils.config import settings
    print(settings.DATABASE_URL)
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration — all values can be overridden via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/credit_risk",
        description="SQLAlchemy-compatible PostgreSQL connection string.",
    )

    # ------------------------------------------------------------------
    # News APIs
    # ------------------------------------------------------------------
    NEWSAPI_KEY: str = Field(
        default="",
        description="API key for NewsAPI (https://newsapi.org).",
    )
    GDELT_API: str = Field(
        default="http://api.gdeltproject.org/api/v2",
        description="Base URL for the GDELT API.",
    )

    # ------------------------------------------------------------------
    # LLM — Groq (active)
    # ------------------------------------------------------------------
    GROQ_API_KEY: str = Field(
        default="",
        description="API key for Groq (https://console.groq.com).",
    )
    LLM_PROVIDER: str = Field(
        default="groq",
        description="Active LLM provider: 'groq' or 'anthropic'.",
    )
    LLM_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Model name to use with the active LLM provider.",
    )

    # ------------------------------------------------------------------
    # LLM — Anthropic Claude (future use)
    # ------------------------------------------------------------------
    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="API key for Anthropic Claude (https://console.anthropic.com).",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Loguru log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment: development, staging, production.",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable verbose debug output.",
    )
    BATCH_SIZE: int = Field(
        default=50,
        description="Number of articles processed per job run.",
    )
    MAX_WORKERS: int = Field(
        default=4,
        description="Thread pool size for concurrent API requests.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton (loaded once at first call)."""
    return Settings()


# Module-level singleton — import this directly.
settings: Settings = get_settings()
