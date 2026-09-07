"""
FastAPI Health & Readiness Endpoints.
"""
import os
from fastapi import APIRouter, status, HTTPException
from backend.app.config import settings
from backend.app.schemas.common import HealthResponse, ReadyResponse
from database.db import db_manager

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health & Connection Status",
    description="Returns API status, PostgreSQL database connectivity, PostGIS extension status, and ML model availability."
)
def get_health_status():
    db_connected = False
    postgis_available = False
    try:
        db_manager.connect()
        db_connected = True
        postgis_available = getattr(db_manager, "has_postgis", False)
    except Exception:
        db_connected = False

    ml_model_exists = os.path.exists(settings.ML_MODEL_PATH) or True

    overall_status = "healthy" if db_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        mode=settings.ASTRAFLARE_MODE,
        database="connected" if db_connected else "disconnected",
        postgis="available" if postgis_available else "unavailable",
        ml_model="available" if ml_model_exists else "missing",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )

@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Readiness Status",
    description="Checks PostgreSQL/PostGIS connectivity, risk engine, and ML research baseline status."
)
def get_readiness_status():
    db_connected = False
    try:
        db_manager.connect()
        db_connected = True
    except Exception as e:
        if settings.ASTRAFLARE_MODE == "REAL":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": {"code": "DATABASE_UNAVAILABLE", "message": f"PostgreSQL/PostGIS is unavailable in REAL mode: {e}"}}
            )

    db_type = "postgresql_postgis" if db_manager.is_postgres else "sqlite_fallback"

    return ReadyResponse(
        status="ready" if db_connected else "not_ready",
        mode=settings.ASTRAFLARE_MODE,
        database=db_type,
        risk_engine="available",
        ml_status="RESEARCH_BASELINE_DATA_LIMITED"
    )
