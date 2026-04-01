"""
Database engine, session factory, and utility functions.
Run directly to test connectivity and initialize tables:
    python -m src.db.connection
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/credit_risk",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # drops stale connections before use
    pool_size=5,
    max_overflow=10,
    echo=False,           # set True to log all SQL statements
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def get_db():
    """
    FastAPI dependency — yields a SQLAlchemy session and ensures it is closed.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context-manager version for use outside FastAPI (scripts, tests, etc.).

    Usage:
        with get_db_context() as db:
            db.query(Article).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables defined in models.py if they do not already exist.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS semantics).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created (or already exist).")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# ---------------------------------------------------------------------------
# Connectivity check
# ---------------------------------------------------------------------------

def test_connection() -> bool:
    """
    Open a raw connection, query the server version, and log the result.
    Returns True on success, False on failure.
    """
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            logger.info(f"Database connected: {version}")
            return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Connecting to: {DATABASE_URL}")

    if test_connection():
        init_db()
        logger.info("Database initialized!")
    else:
        logger.error("Could not connect to the database. Check DATABASE_URL and that Postgres is running.")
        raise SystemExit(1)
