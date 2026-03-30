"""
Unit tests for src/utils/config.py.
"""

import pytest
from pydantic import ValidationError

from src.utils.config import settings, Settings


def test_database_url_set():
    """DATABASE_URL must be set and point to a PostgreSQL instance."""
    assert settings.DATABASE_URL is not None
    assert "postgresql" in settings.DATABASE_URL


def test_newsapi_key_set():
    """NEWSAPI_KEY must be present (non-empty)."""
    assert settings.NEWSAPI_KEY
    assert len(settings.NEWSAPI_KEY) > 10


def test_batch_size_positive():
    """BATCH_SIZE must be a positive integer."""
    assert isinstance(settings.BATCH_SIZE, int)
    assert settings.BATCH_SIZE > 0


def test_max_workers_positive():
    """MAX_WORKERS must be a positive integer."""
    assert isinstance(settings.MAX_WORKERS, int)
    assert settings.MAX_WORKERS > 0


def test_log_level_valid():
    """LOG_LEVEL must be a recognised logging level string."""
    valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    assert settings.LOG_LEVEL.upper() in valid


def test_missing_required_key_raises():
    """Settings raises ValidationError when a typed field gets an invalid value."""
    with pytest.raises(ValidationError):
        Settings(BATCH_SIZE="not-a-number", _env_file=None)
