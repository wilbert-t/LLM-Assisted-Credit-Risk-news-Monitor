"""
Aggregate daily obligor signals from processed articles.

Usage:
    python -m scripts.aggregate_signals
"""

from src.processors.signal_aggregator import aggregate_all_daily
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("=== aggregate_signals: starting ===")
    count = aggregate_all_daily()
    logger.info(f"aggregate_signals: done — {count} (obligor, date) pair(s) upserted.")
    print(f"Obligor-date pairs processed: {count}")


if __name__ == "__main__":
    main()
