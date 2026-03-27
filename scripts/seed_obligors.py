"""
Seed the obligors table with 50 well-known companies across key sectors.
Safe to re-run — skips any ticker that already exists.

Usage:
    python -m scripts.seed_obligors
"""

from src.db.connection import SessionLocal
from src.db.models import Obligor
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OBLIGORS: list[dict] = [
    # FAANG / Big Tech
    {"name": "Apple Inc.",              "ticker": "AAPL",  "sector": "Technology",        "country": "USA"},
    {"name": "Microsoft Corporation",   "ticker": "MSFT",  "sector": "Technology",        "country": "USA"},
    {"name": "Alphabet Inc.",           "ticker": "GOOGL", "sector": "Technology",        "country": "USA"},
    {"name": "Amazon.com Inc.",         "ticker": "AMZN",  "sector": "Consumer Cyclical", "country": "USA"},
    {"name": "Meta Platforms Inc.",     "ticker": "META",  "sector": "Technology",        "country": "USA"},

    # Major Banks
    {"name": "JPMorgan Chase & Co.",    "ticker": "JPM",   "sector": "Financials",        "country": "USA"},
    {"name": "Goldman Sachs Group",     "ticker": "GS",    "sector": "Financials",        "country": "USA"},
    {"name": "Bank of America Corp.",   "ticker": "BAC",   "sector": "Financials",        "country": "USA"},
    {"name": "Citigroup Inc.",          "ticker": "C",     "sector": "Financials",        "country": "USA"},
    {"name": "Wells Fargo & Co.",       "ticker": "WFC",   "sector": "Financials",        "country": "USA"},

    # Technology
    {"name": "Tesla Inc.",              "ticker": "TSLA",  "sector": "Automotive",        "country": "USA"},
    {"name": "NVIDIA Corporation",      "ticker": "NVDA",  "sector": "Technology",        "country": "USA"},
    {"name": "Intel Corporation",       "ticker": "INTC",  "sector": "Technology",        "country": "USA"},
    {"name": "Advanced Micro Devices",  "ticker": "AMD",   "sector": "Technology",        "country": "USA"},
    {"name": "Cisco Systems Inc.",      "ticker": "CSCO",  "sector": "Technology",        "country": "USA"},

    # Pharmaceuticals
    {"name": "Pfizer Inc.",             "ticker": "PFE",   "sector": "Healthcare",        "country": "USA"},
    {"name": "Moderna Inc.",            "ticker": "MRNA",  "sector": "Healthcare",        "country": "USA"},
    {"name": "Johnson & Johnson",       "ticker": "JNJ",   "sector": "Healthcare",        "country": "USA"},
    {"name": "AbbVie Inc.",             "ticker": "ABBV",  "sector": "Healthcare",        "country": "USA"},
    {"name": "Merck & Co. Inc.",        "ticker": "MRK",   "sector": "Healthcare",        "country": "USA"},

    # Energy
    {"name": "Exxon Mobil Corporation", "ticker": "XOM",   "sector": "Energy",            "country": "USA"},
    {"name": "Chevron Corporation",     "ticker": "CVX",   "sector": "Energy",            "country": "USA"},
    {"name": "Shell plc",               "ticker": "SHEL",  "sector": "Energy",            "country": "GBR"},
    {"name": "BP plc",                  "ticker": "BP",    "sector": "Energy",            "country": "GBR"},
    {"name": "TotalEnergies SE",        "ticker": "TTE",   "sector": "Energy",            "country": "FRA"},

    # Aerospace & Defence
    {"name": "Boeing Company",          "ticker": "BA",    "sector": "Industrials",       "country": "USA"},
    {"name": "Airbus SE",               "ticker": "AIR",   "sector": "Industrials",       "country": "FRA"},
    {"name": "Lockheed Martin Corp.",   "ticker": "LMT",   "sector": "Industrials",       "country": "USA"},
    {"name": "Raytheon Technologies",   "ticker": "RTX",   "sector": "Industrials",       "country": "USA"},

    # Media & Entertainment
    {"name": "Netflix Inc.",            "ticker": "NFLX",  "sector": "Communication",     "country": "USA"},
    {"name": "Walt Disney Company",     "ticker": "DIS",   "sector": "Communication",     "country": "USA"},
    {"name": "Comcast Corporation",     "ticker": "CMCSA", "sector": "Communication",     "country": "USA"},

    # Consumer Staples
    {"name": "Coca-Cola Company",       "ticker": "KO",    "sector": "Consumer Staples",  "country": "USA"},
    {"name": "PepsiCo Inc.",            "ticker": "PEP",   "sector": "Consumer Staples",  "country": "USA"},
    {"name": "Procter & Gamble Co.",    "ticker": "PG",    "sector": "Consumer Staples",  "country": "USA"},
    {"name": "Unilever plc",            "ticker": "UL",    "sector": "Consumer Staples",  "country": "GBR"},
    {"name": "Nestlé S.A.",             "ticker": "NSRGY", "sector": "Consumer Staples",  "country": "CHE"},

    # Industrial
    {"name": "3M Company",              "ticker": "MMM",   "sector": "Industrials",       "country": "USA"},
    {"name": "Caterpillar Inc.",        "ticker": "CAT",   "sector": "Industrials",       "country": "USA"},
    {"name": "General Electric Co.",    "ticker": "GE",    "sector": "Industrials",       "country": "USA"},
    {"name": "Honeywell International", "ticker": "HON",   "sector": "Industrials",       "country": "USA"},
    {"name": "Siemens AG",              "ticker": "SIEGY", "sector": "Industrials",       "country": "DEU"},

    # Automotive
    {"name": "Ford Motor Company",      "ticker": "F",     "sector": "Automotive",        "country": "USA"},
    {"name": "General Motors Company",  "ticker": "GM",    "sector": "Automotive",        "country": "USA"},
    {"name": "Toyota Motor Corp.",      "ticker": "TM",    "sector": "Automotive",        "country": "JPN"},
    {"name": "Volkswagen AG",           "ticker": "VWAGY", "sector": "Automotive",        "country": "DEU"},

    # Retail / E-Commerce
    {"name": "Walmart Inc.",            "ticker": "WMT",   "sector": "Consumer Staples",  "country": "USA"},
    {"name": "Target Corporation",      "ticker": "TGT",   "sector": "Consumer Cyclical", "country": "USA"},

    # Telecoms
    {"name": "AT&T Inc.",               "ticker": "T",     "sector": "Communication",     "country": "USA"},
    {"name": "Verizon Communications",  "ticker": "VZ",    "sector": "Communication",     "country": "USA"},
]


def seed_obligors() -> None:
    """Insert obligors that don't already exist (idempotent by ticker)."""
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0

        for data in OBLIGORS:
            exists = db.query(Obligor).filter_by(ticker=data["ticker"]).first()
            if exists:
                skipped += 1
                continue

            db.add(Obligor(**data))
            inserted += 1

        db.commit()
        logger.info(f"Seeded {inserted} obligors ({skipped} already existed).")
    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_obligors()
