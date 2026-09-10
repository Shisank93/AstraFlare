"""
FastAPI Analytical Reports Endpoints.
Generates structured intelligence reports for individual events and multi-event analytical summaries.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException, status
from backend.app.services.hotspot_service import hotspot_service
from backend.app.services.prediction_service import prediction_service
from backend.app.services.evidence_service import evidence_service
from backend.app.services.risk_service import risk_service
from backend.app.services.analytics_service import analytics_service
from database.db import db_manager

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/event/{event_id}", summary="Generate Event Intelligence Dossier")
def get_event_report(event_id: str = Path(..., description="Unique event or hotspot ID")):
    """Generates complete structured intelligence dossier for target thermal anomaly."""
    detail = hotspot_service.get_hotspot_detail(event_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EVENT_NOT_FOUND", "message": f"Event '{event_id}' not found in database."}}
        )

    prediction = prediction_service.predict_hotspot(event_id)
    evidence = evidence_service.get_hotspot_evidence(event_id)
    risk = risk_service.calculate_risk(event_id)
    history = hotspot_service.get_hotspot_history(event_id)

    # Fetch analyst review history if any
    db_manager.connect()
    ph = "%s" if db_manager.is_postgres else "?"
    reviews_res = db_manager.execute_query(
        f"SELECT * FROM reviews WHERE hotspot_id = {ph} ORDER BY created_at DESC;",
        (event_id,)
    )

    dist_m = float(detail.get("industrial_distance_m") or 10000.0)
    dist_str = f"{dist_m / 1000.0:.1f} km" if dist_m >= 1000.0 else f"{dist_m:.0f} m"

    return {
        "event_id": event_id,
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "telemetry": {
            "latitude": detail.get("latitude") or detail.get("centroid_lat"),
            "longitude": detail.get("longitude") or detail.get("centroid_lon"),
            "acq_timestamp": detail.get("acq_timestamp") or str(detail.get("event_timestamp")),
            "satellite": detail.get("satellite", "VIIRS"),
            "frp_mw": float(detail.get("frp") or detail.get("max_frp") or 0.0),
            "brightness_k": float(detail.get("brightness") or detail.get("max_brightness") or 300.0),
            "duration_hours": float(detail.get("duration_hours") or 0.0),
            "observation_count": int(detail.get("observation_count") or 1),
            "data_source": detail.get("data_source", "REAL"),
            "data_quality_status": detail.get("data_quality_status", "HIGH")
        },
        "gis_context": {
            "industrial_distance": dist_str,
            "industrial_distance_meters": dist_m,
            "industrial_proximity_label": "Immediate Proximity (<1km)" if dist_m <= 1000.0 else ("Moderate Proximity (1-3km)" if dist_m <= 3000.0 else "Low Industrial Proximity (>3km)"),
            "nearest_facility": detail.get("nearest_industrial_name") or "None in 5km buffer",
            "land_cover": detail.get("land_cover_name") or "Cropland"
        },
        "ml_intelligence": prediction,
        "operational_risk": risk,
        "evidence_dossier": evidence.get("evidence_items") if evidence else [],
        "historical_baseline": history,
        "analyst_audit_trail": [dict(r) for r in reviews_res] if reviews_res else []
    }

@router.get("/summary", summary="Generate Analytical Intelligence Report")
def get_summary_report(
    report_type: str = Query("DAILY_THERMAL", description="DAILY_THERMAL, INDUSTRIAL_ANOMALY, HIGH_RISK, ANALYST_AUDIT, REGIONAL, HISTORICAL"),
    start_date: Optional[str] = Query(None, description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter")
):
    """Generates structured analytical report based on database events."""
    summary_analytics = analytics_service.get_summary_analytics()
    ml_analytics = analytics_service.get_ml_analytics()
    risk_analytics = analytics_service.get_risk_analytics()

    now_iso = datetime.now(timezone.utc).isoformat()

    titles = {
        "DAILY_THERMAL": "Daily Satellite Thermal Activity Intelligence Report",
        "INDUSTRIAL_ANOMALY": "Industrial Anomaly & Rare Thermal Incident Report",
        "HIGH_RISK": "High-Priority Operational Risk Prioritization Report",
        "ANALYST_AUDIT": "Analyst Investigation Audit & Verification Dossier",
        "REGIONAL": "Regional Geospatial Thermal Concentration Report",
        "HISTORICAL": "Multi-Year Historical Baseline & Recurrence Report"
    }

    rep_type = report_type if isinstance(report_type, str) else "DAILY_THERMAL"
    s_date = start_date if isinstance(start_date, str) else None
    e_date = end_date if isinstance(end_date, str) else None

    title = titles.get(rep_type, "Geospatial Thermal Intelligence Report")

    # Fetch top events for report table
    events, _ = hotspot_service.get_hotspots(
        start_date=s_date, end_date=e_date,
        page=1, page_size=15
    )

    return {
        "report_title": title,
        "report_type": report_type,
        "generated_at": now_iso,
        "dataset_scope": {
            "scope": "India Geographic Territory",
            "data_source": "REAL (NASA FIRMS MODIS/VIIRS + Sentinel ESA WorldCover + OSM Industrial)",
            "start_date": start_date or "2025-11-01",
            "end_date": end_date or "2025-11-15",
            "total_satellite_observations": summary_analytics["total_observations_ingested"],
            "active_physical_events": summary_analytics["total_events"]
        },
        "executive_summary": (
            f"This operational report summarizes wide-area thermal anomalies detected across India. "
            f"AstraFlare synthesized {summary_analytics['total_events']} active physical events with GIS context, "
            f"evaluating proximity to {summary_analytics['total_industrial_sites_mapped']} mapped industrial facilities. "
            f"Model status is {ml_analytics['model_status']} (Macro F1: {ml_analytics['offline_evaluation']['macro_f1']})."
        ),
        "key_statistics": {
            "total_events": summary_analytics["total_events"],
            "high_risk_events": summary_analytics["risk_breakdown"].get("HIGH", 0),
            "medium_risk_events": summary_analytics["risk_breakdown"].get("MEDIUM", 0),
            "low_risk_events": summary_analytics["risk_breakdown"].get("LOW", 0),
            "events_requiring_investigation": summary_analytics["human_review_queue"]["pending_review_count"],
            "completed_investigations": summary_analytics["total_reviews_submitted"]
        },
        "sample_events": events[:10],
        "ml_model_evaluation": ml_analytics["offline_evaluation"],
        "operational_risk_summary": risk_analytics["risk_level_breakdown"]
    }
