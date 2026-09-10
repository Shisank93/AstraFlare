"""
FastAPI Analytics Intelligence Endpoints.
Serves real database-derived analytics across thermal activity, ML metrics, geospatial distribution,
operational risk, and analyst review investigations.
"""
from fastapi import APIRouter
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary", summary="Get Executive Overview Analytics")
def get_summary():
    return analytics_service.get_summary_analytics()

@router.get("/thermal", summary="Get Thermal Activity Analytics")
def get_thermal():
    return analytics_service.get_thermal_analytics()

@router.get("/ml", summary="Get ML Model Intelligence & Offline Evaluation")
def get_ml():
    return analytics_service.get_ml_analytics()

@router.get("/geospatial", summary="Get Geospatial & Land-Cover Intelligence")
def get_geospatial():
    return analytics_service.get_geospatial_analytics()

@router.get("/risk", summary="Get Operational Prioritization Risk Analytics")
def get_risk():
    return analytics_service.get_risk_analytics()

@router.get("/investigations", summary="Get Analyst Review Queue & Decisions")
def get_investigations():
    return analytics_service.get_investigations_analytics()
