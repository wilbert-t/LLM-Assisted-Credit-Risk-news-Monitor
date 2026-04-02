"""
FastAPI endpoints for alerts and risk summaries.

Endpoints:
- GET /api/alerts — list alerts with filters
- GET /api/alerts/{id} — single alert details
- GET /api/obligors/{id}/summary — risk summary for obligor
"""

from datetime import datetime, date as datetime_date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models import Alert, Obligor
from src.rag.summarizer import ObligorSummarizer, SummarizerError
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["alerts"])


class AlertResponse(BaseModel):
    """Alert response model."""

    id: int
    obligor_id: int
    triggered_at: datetime
    severity: str
    summary: Optional[str]
    event_types: Optional[List[str]]
    article_ids: Optional[List[int]]
    extra_data: Optional[dict]

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Alert list response model."""

    alerts: List[AlertResponse]
    total: int


class SummaryResponse(BaseModel):
    """Risk summary response model."""

    company: str
    summary: str
    risk_level: str
    key_events: List[str]
    concerns: List[str]
    positive_factors: List[str]
    confidence: float
    cached: bool


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    severity: Optional[str] = Query(None),
    date_from: Optional[datetime_date] = Query(None),
    date_to: Optional[datetime_date] = Query(None),
    obligor_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    """
    List alerts with optional filtering.

    Query Parameters:
    - severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
    - date_from: Filter alerts from date (inclusive)
    - date_to: Filter alerts to date (inclusive)
    - obligor_id: Filter by obligor ID
    - limit: Number of results (default 10, max 100)
    - offset: Number of results to skip (default 0)
    """
    query = db.query(Alert)

    if severity:
        query = query.filter(Alert.severity == severity)

    if date_from:
        query = query.filter(Alert.triggered_at >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        query = query.filter(Alert.triggered_at <= datetime.combine(date_to, datetime.max.time()))

    if obligor_id:
        query = query.filter(Alert.obligor_id == obligor_id)

    total = query.count()
    alerts = query.order_by(Alert.triggered_at.desc()).limit(limit).offset(offset).all()

    return AlertListResponse(
        alerts=[AlertResponse.model_validate(alert) for alert in alerts],
        total=total,
    )


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> AlertResponse:
    """
    Get a single alert by ID.

    Path Parameters:
    - alert_id: Alert ID
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse.model_validate(alert)


@router.get("/obligors/{obligor_id}/summary", response_model=SummaryResponse)
def get_obligor_summary(
    obligor_id: int,
    db: Session = Depends(get_db),
) -> SummaryResponse:
    """
    Get or generate credit risk summary for obligor.

    Checks cache first, generates fresh summary if needed.

    Path Parameters:
    - obligor_id: Obligor ID
    """
    # Check obligor exists
    obligor = db.query(Obligor).filter(Obligor.id == obligor_id).first()

    if not obligor:
        raise HTTPException(status_code=404, detail="Obligor not found")

    # Get summary
    try:
        summarizer = ObligorSummarizer(db=db)
        summary = summarizer.summarize_obligor_risk(obligor_id, days=7)
        return SummaryResponse(
            company=summary["company"],
            summary=summary["summary"],
            risk_level=summary["risk_level"],
            key_events=summary["key_events"],
            concerns=summary["concerns"],
            positive_factors=summary["positive_factors"],
            confidence=summary["confidence"],
            cached=summary["cached"],
        )
    except SummarizerError as e:
        logger.error(f"Failed to generate summary for obligor {obligor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")
