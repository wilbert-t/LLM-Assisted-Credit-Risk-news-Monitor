"""
SQLAlchemy ORM models for the Credit Risk Monitor.
All models include created_at / updated_at auto-timestamps.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Adds created_at and updated_at columns to any model."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Article(TimestampMixin, Base):
    """
    Raw article as ingested from a news source (NewsAPI, GDELT, etc.).
    One row per unique URL — duplicate URLs are rejected via the unique constraint.
    """

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1024), nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(2048), nullable=False)
    source = Column(String(256), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    language = Column(String(10), nullable=True)
    raw_json = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("url", name="uq_articles_url"),
        Index("ix_articles_url", "url"),
        Index("ix_articles_published_at", "published_at"),
    )

    # Relationships
    processed = relationship("ProcessedArticle", back_populates="article", uselist=False)
    obligor_links = relationship("ArticleObligor", back_populates="article")

    def __repr__(self) -> str:
        return f"<Article id={self.id} source={self.source!r} published_at={self.published_at}>"


class Obligor(TimestampMixin, Base):
    """
    A company or entity being monitored for credit risk.
    Ticker and LEI are optional but useful for deduplication and enrichment.
    """

    __tablename__ = "obligors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(512), nullable=False)
    ticker = Column(String(20), nullable=True)
    lei = Column(String(20), nullable=True)          # Legal Entity Identifier
    sector = Column(String(256), nullable=True)
    country = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_obligors_ticker", "ticker"),
        Index("ix_obligors_name", "name"),
    )

    # Relationships
    article_links = relationship("ArticleObligor", back_populates="obligor")
    alerts = relationship("Alert", back_populates="obligor")
    daily_signals = relationship("ObligorDailySignals", back_populates="obligor")

    def __repr__(self) -> str:
        return f"<Obligor id={self.id} name={self.name!r} ticker={self.ticker!r}>"


class ProcessedArticle(TimestampMixin, Base):
    """
    NLP-enriched version of a raw Article.
    Stores cleaned text, named entities, FinBERT sentiment, and credit-relevance flag.
    One-to-one with Article.
    """

    __tablename__ = "processed_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    cleaned_text = Column(Text, nullable=True)
    entities = Column(JSON, nullable=True)              # {type: [{text, start, end}, ...], ...}
    sentiment_score = Column(Float, nullable=True)      # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=True) # positive / negative / neutral
    is_credit_relevant = Column(Boolean, default=False, nullable=False)
    event_types = Column(ARRAY(String), nullable=True)  # e.g. ["default", "downgrade"]

    __table_args__ = (
        Index("ix_processed_articles_article_id", "article_id"),
        Index("ix_processed_articles_sentiment_label", "sentiment_label"),
        Index("ix_processed_articles_is_credit_relevant", "is_credit_relevant"),
    )

    # Relationships
    article = relationship("Article", back_populates="processed")

    def __repr__(self) -> str:
        return (
            f"<ProcessedArticle id={self.id} article_id={self.article_id} "
            f"sentiment={self.sentiment_label} credit_relevant={self.is_credit_relevant}>"
        )


class ArticleObligor(Base):
    """
    Many-to-many join table linking Articles to Obligors.
    An article may mention multiple obligors; an obligor may appear in many articles.
    No timestamps — the parent records carry that information.
    """

    __tablename__ = "article_obligors"

    article_id = Column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    obligor_id = Column(
        Integer,
        ForeignKey("obligors.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        Index("ix_article_obligors_obligor_id", "obligor_id"),
        Index("ix_article_obligors_article_id", "article_id"),
    )

    # Relationships
    article = relationship("Article", back_populates="obligor_links")
    obligor = relationship("Obligor", back_populates="article_links")

    def __repr__(self) -> str:
        return f"<ArticleObligor article_id={self.article_id} obligor_id={self.obligor_id}>"


class Alert(TimestampMixin, Base):
    """
    A credit risk alert generated for an obligor.
    Stores the triggering event types, source article IDs, severity, and LLM summary.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    obligor_id = Column(
        Integer,
        ForeignKey("obligors.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    severity = Column(String(20), nullable=False)       # low / medium / high / critical
    summary = Column(Text, nullable=True)               # LLM-generated summary
    event_types = Column(JSON, nullable=True)           # ["downgrade", "bankruptcy", ...]
    article_ids = Column(JSON, nullable=True)           # [article_id, ...]
    extra_data = Column(JSON, nullable=True)             # arbitrary extra context

    __table_args__ = (
        Index("ix_alerts_obligor_id", "obligor_id"),
        Index("ix_alerts_triggered_at", "triggered_at"),
        Index("ix_alerts_severity", "severity"),
    )

    # Relationships
    obligor = relationship("Obligor", back_populates="alerts")

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} obligor_id={self.obligor_id} "
            f"severity={self.severity!r} triggered_at={self.triggered_at}>"
        )


class ObligorDailySignals(TimestampMixin, Base):
    """
    Aggregated daily credit-risk signals for an obligor.
    Pre-computed by the nightly batch job to power the dashboard charts.
    One row per (obligor, date) — unique constraint enforced.
    """

    __tablename__ = "obligor_daily_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    obligor_id = Column(
        Integer,
        ForeignKey("obligors.id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False)
    neg_article_count = Column(Integer, default=0, nullable=False)
    avg_sentiment = Column(Float, nullable=True)
    credit_relevant_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("obligor_id", "date", name="uq_obligor_daily_signals_obligor_date"),
        Index("ix_obligor_daily_signals_obligor_id", "obligor_id"),
        Index("ix_obligor_daily_signals_date", "date"),
    )

    # Relationships
    obligor = relationship("Obligor", back_populates="daily_signals")

    def __repr__(self) -> str:
        return (
            f"<ObligorDailySignals id={self.id} obligor_id={self.obligor_id} "
            f"date={self.date} avg_sentiment={self.avg_sentiment}>"
        )
