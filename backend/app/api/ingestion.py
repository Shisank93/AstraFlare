"""
FastAPI NASA FIRMS Ingestion Trigger Endpoint.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from data_pipeline.firms_ingestion import FIRMSIngestionClient
from backend.app.config import settings

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])

@router.post(
    "/firms",
    status_code=status.HTTP_200_OK,
    summary="Trigger Server-Side FIRMS Telemetry Ingestion",
    description="Triggers idempotent real FIRMS satellite thermal anomaly fetch using backend environment API key. Never accepts secrets from client."
)
def trigger_firms_ingestion(
    country: str = Query("IND", description="ISO country code (India scope)"),
    source: str = Query("VIIRS_SNPP_NRT", description="Satellite source feed"),
    mock_fallback: bool = Query(False, description="Mock fallback flag (DEMO mode only)")
):
    if settings.ASTRAFLARE_MODE == "REAL" and mock_fallback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "MOCK_NOT_PERMITTED", "message": "Synthetic/mock fallback is NOT permitted in REAL mode."}}
        )

    if country != "IND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "OUT_OF_SCOPE", "message": "AstraFlare scope is restricted to India (IND)."}}
        )

    client = FIRMSIngestionClient()
    res = client.ingest_firms_data(country=country, source=source, mock_fallback=(mock_fallback if settings.ASTRAFLARE_MODE == "DEMO" else False))

    if res.get("status") == "FAILED" and settings.ASTRAFLARE_MODE == "REAL":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": {"code": "INGESTION_FAILED", "message": f"Real FIRMS ingestion failed: {res.get('error', 'Unknown network error')}"}}
        )

    return {
        "status": res.get("status", "SUCCESS"),
        "country": country,
        "source": source,
        "inserted": res.get("inserted", 0),
        "duplicates": res.get("duplicates", 0),
        "rejected": res.get("rejected", 0),
        "data_source": res.get("data_source", settings.DATA_SOURCE_REAL)
    }

@router.post(
    "/firms/live",
    status_code=status.HTTP_200_OK,
    summary="Trigger Live NASA FIRMS Ingestion",
    description="Fetches live 24h satellite anomalies."
)
def trigger_firms_live(
    country: str = Query("IND", description="ISO country code (India scope)"),
    source: str = Query("VIIRS_SNPP_NRT", description="Satellite source feed")
):
    if country != "IND":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "OUT_OF_SCOPE", "message": "AstraFlare scope is restricted to India (IND)."}}
        )

    client = FIRMSIngestionClient()
    # Mock fallback always false for live
    res = client.ingest_firms_data(country=country, source=source, mock_fallback=False, data_source_tag="REAL_LIVE")

    if res.get("status") == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": {"code": "INGESTION_FAILED", "message": f"Real FIRMS ingestion failed: {res.get('error', 'Unknown network error')}"}}
        )
        
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = res.get("inserted", 0)
    # Estimated physical clusters formed from new satellite observations
    new_events = max(1, inserted // 2) if inserted > 0 else 0

    return {
        "status": res.get("status", "SUCCESS"),
        "country": country,
        "source": source,
        "last_updated": now_iso,
        "new_observations": inserted,
        "new_events": new_events,
        "inserted": inserted,
        "duplicates": res.get("duplicates", 0),
        "rejected": res.get("rejected", 0),
        "data_source": "REAL_LIVE"
    }
