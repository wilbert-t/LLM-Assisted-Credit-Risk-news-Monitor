"""
FastAPI application entry point.

Includes all API routers and configurations.
"""

from fastapi import FastAPI
from src.api.alerts import router as alerts_router

app = FastAPI(
    title="Credit Risk Monitoring API",
    description="Automated monitoring and alerting for credit risk signals",
    version="1.0.0",
)

# Include routers
app.include_router(alerts_router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
