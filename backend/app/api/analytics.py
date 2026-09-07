"""
FastAPI Real Analytics Summary Endpoint.
"""
from fastapi import APIRouter, status
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get(
    "/summary",
    summary="Get Database Dashboard Analytics Summary",
    description="Returns real database-derived analytical breakdown across classifications, risk levels, human reviews, sensors, and land cover."
)
def get_analytics_summary():
    return analytics_service.get_summary_analytics()
