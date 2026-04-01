"""
Shared pytest fixtures for unit and integration tests.

Uses a real PostgreSQL test database (credit_risk_test) because storage.py
uses pg_insert which is PostgreSQL-specific and incompatible with SQLite.

Isolation strategy:
  - Tables are created once per test session.
  - Each test runs inside a transaction that is rolled back after the test,
    keeping the DB clean without the overhead of DROP/CREATE per test.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/credit_risk_test",
)


@pytest.fixture(scope="session")
def engine():
    """Create the test engine and tables once for the entire test session."""
    _engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    with _engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture(scope="session")
def SessionFactory(engine):
    """Session factory bound to the test engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db(engine, SessionFactory):
    """
    Yield a transactional test session. All changes are rolled back after each
    test, leaving the database clean for the next one.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionFactory(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
