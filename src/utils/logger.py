"""
Loguru-based logger factory for the Credit Risk Monitor.
Call setup_logger() once per module:

    from src.utils.logger import setup_logger
    logger = setup_logger(__name__)
    logger.info("Starting collector...")
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _root_logger


# Remove the default loguru handler so we control the format globally.
_root_logger.remove()

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
    "<level>{message}</level>"
)

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}"
)

# Add a single shared console sink (stderr).
_root_logger.add(
    sys.stderr,
    format=_CONSOLE_FORMAT,
    level="INFO",
    colorize=True,
    enqueue=True,   # thread-safe output
)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
):
    """
    Return a loguru logger bound to *name*.

    Args:
        name:       Module name — use __name__ for automatic naming.
        level:      Minimum log level for console output (default INFO).
        log_file:   Optional path to write rotating log file.
                    If None, file logging is skipped.
        rotation:   Loguru rotation trigger (size or time, e.g. "10 MB", "1 day").
        retention:  How long to keep rotated log files (e.g. "7 days").

    Returns:
        A loguru logger instance bound with the given name context.

    Example:
        logger = setup_logger(__name__, log_file="logs/collector.log")
        logger.info("Fetching articles...")
    """
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _root_logger.add(
            str(log_path),
            format=_FILE_FORMAT,
            level=level,
            rotation=rotation,
            retention=retention,
            enqueue=True,
            encoding="utf-8",
        )

    return _root_logger.bind(name=name)
