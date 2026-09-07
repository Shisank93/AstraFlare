"""
FastAPI Physical Event Cluster Intelligence Endpoints.
Exposes comprehensive event-level geospatial intelligence, risk, evidence, history, and review context.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Path, HTTPException, status
from backend.app.services.hotspot_service import hotspot_service
from backend.risk_engine.engine import risk_engine

router = APIRouter(prefix="/api/events", tags=["Events"])

def safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def _get_event_or_404(event_id: str) -> Dict[str, Any]:
    detail = hotspot_service.get_hotspot_detail(event_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EVENT_NOT_FOUND", "message": f"Event cluster '{event_id}' not found."}}
        )
    return detail

@router.get(
    "/{event_id}",
    summary="Get Physical Event Unified Intelligence Object",
    description="Returns single coherent event intelligence object combining detection, location, industrial context, risk score, priority, evidence, and historical telemetry."
)
def get_event_detail(event_id: str = Path(..., description="Unique event cluster ID")):
    detail = _get_event_or_404(event_id)

    # Run deterministic risk engine assessment
    assessment = risk_engine.assess_event({
        "event_id": event_id,
        "event_timestamp": detail.get("acq_timestamp"),
        "centroid_lat": safe_float(detail.get("latitude") or detail.get("centroid_lat"), 0.0),
        "centroid_lon": safe_float(detail.get("longitude") or detail.get("centroid_lon"), 0.0),
        "max_frp": safe_float(detail.get("frp") or detail.get("max_frp"), 0.0),
        "mean_frp": safe_float(detail.get("mean_frp") or detail.get("frp"), 0.0),
        "max_brightness": safe_float(detail.get("brightness") or detail.get("max_brightness"), 300.0),
        "observation_count": safe_int(detail.get("observation_count"), 1),
        "duration_hours": safe_float(detail.get("duration_hours"), 0.0),
        "confidence_high_ratio": safe_float(detail.get("confidence_high_ratio"), 0.0),
        "industrial_distance_m": safe_float(detail.get("industrial_distance_m"), 10000.0),
        "industrial_site_count_250m": safe_int(detail.get("industrial_site_count_250m"), 0),
        "industrial_site_count_1km": safe_int(detail.get("industrial_count_1km") or detail.get("industrial_site_count_1km"), 0),
        "industrial_site_count_5km": safe_int(detail.get("industrial_count_5km") or detail.get("industrial_site_count_5km"), 0),
        "worldcover_class": str(detail.get("land_cover_code") or detail.get("worldcover_class") or "40")
    })

    return {
        "event_id": event_id,
        "event": {
            "event_id": event_id,
            "timestamp": detail.get("acq_timestamp"),
            "observation_count": safe_int(detail.get("observation_count"), 1),
            "duration_hours": safe_float(detail.get("duration_hours"), 0.0),
            "satellite": detail.get("satellite", "VIIRS")
        },
        "location": {
            "latitude": safe_float(detail.get("latitude") or detail.get("centroid_lat"), 0.0),
            "longitude": safe_float(detail.get("longitude") or detail.get("centroid_lon"), 0.0)
        },
        "detection": {
            "frp": safe_float(detail.get("frp") or detail.get("max_frp"), 0.0),
            "brightness": safe_float(detail.get("brightness") or detail.get("max_brightness"), 300.0),
            "confidence": detail.get("confidence", "nominal")
        },
        "industrial_context": {
            "nearest_distance_m": detail.get("industrial_distance_m"),
            "site_count_1km": detail.get("industrial_count_1km", 0),
            "nearest_site_name": detail.get("nearest_industrial_name")
        },
        "historical_context": {
            "previous_count": detail.get("historical_count_30d", 0),
            "historical_mean_frp": detail.get("historical_mean_frp"),
            "frp_anomaly_zscore": detail.get("frp_anomaly_zscore"),
            "status": detail.get("anomaly_status", "VALID")
        },
        "natural_context": {
            "land_cover_code": detail.get("land_cover_code", 40),
            "land_cover_name": detail.get("land_cover_name", "Cropland"),
            "score": assessment.natural_fire_context_score
        },
        "risk": {
            "score": assessment.overall_risk_score,
            "level": assessment.risk_level,
            "components": {
                "thermal": assessment.thermal_anomaly_score,
                "historical": assessment.historical_anomaly_score,
                "industrial": assessment.industrial_context_score,
                "natural": assessment.natural_fire_context_score,
                "quality": assessment.data_quality_score
            }
        },
        "investigation": {
            "priority": assessment.investigation_priority,
            "human_review_required": assessment.human_review_required,
            "reason_codes": assessment.human_review_reasons,
            "review_status": detail.get("review_status", "PENDING")
        },
        "provenance": {
            "data_source": detail.get("data_source", "REAL"),
            "verification_status": detail.get("verification_status", "WEAK_RULE")
        }
    }

@router.get(
    "/{event_id}/evidence",
    summary="Get Structured Traceable Evidence Statements",
    description="Returns list of human-readable evidence statements explaining dimensional contributions to operational risk."
)
def get_event_evidence(event_id: str = Path(..., description="Unique event cluster ID")):
    detail = _get_event_or_404(event_id)
    assessment = risk_engine.assess_event({
        "event_id": event_id,
        "max_frp": safe_float(detail.get("frp") or detail.get("max_frp"), 0.0),
        "industrial_distance_m": safe_float(detail.get("industrial_distance_m"), 10000.0),
        "industrial_site_count_1km": safe_int(detail.get("industrial_count_1km") or detail.get("industrial_site_count_1km"), 0),
        "worldcover_class": str(detail.get("land_cover_code") or detail.get("worldcover_class") or "40")
    })
    return {
        "event_id": event_id,
        "evidence_status": assessment.evidence_status,
        "likely_context": assessment.likely_context,
        "evidence": [ev.model_dump() for ev in assessment.evidence]
    }

@router.get(
    "/{event_id}/risk",
    summary="Get Operational Risk Prioritization Breakdown",
    description="Returns detailed operational risk score, risk level, and dimensional component contributions."
)
def get_event_risk(event_id: str = Path(..., description="Unique event cluster ID")):
    detail = _get_event_or_404(event_id)
    assessment = risk_engine.assess_event({
        "event_id": event_id,
        "max_frp": safe_float(detail.get("frp") or detail.get("max_frp"), 0.0),
        "industrial_distance_m": safe_float(detail.get("industrial_distance_m"), 10000.0),
        "worldcover_class": str(detail.get("land_cover_code") or detail.get("worldcover_class") or "40")
    })
    return {
        "event_id": event_id,
        "overall_risk_score": assessment.overall_risk_score,
        "risk_level": assessment.risk_level,
        "investigation_priority": assessment.investigation_priority,
        "components": {
            "thermal": assessment.thermal_anomaly_score,
            "historical": assessment.historical_anomaly_score,
            "industrial": assessment.industrial_context_score,
            "natural": assessment.natural_fire_context_score,
            "quality": assessment.data_quality_score
        }
    }

@router.get(
    "/{event_id}/history",
    summary="Get Temporal Recurrence & Historical FRP Statistics",
    description="Returns rolling 30-day and 365-day historical baseline FRP telemetry around event location."
)
def get_event_history(event_id: str = Path(..., description="Unique event cluster ID")):
    _get_event_or_404(event_id)
    return hotspot_service.get_hotspot_history(event_id)

@router.get(
    "/{event_id}/industrial-context",
    summary="Get Nearest Industrial Facilities & Proximity Telemetry",
    description="Returns nearest OpenStreetMap / GIHS industrial site distance and facility density."
)
def get_event_industrial_context(event_id: str = Path(..., description="Unique event cluster ID")):
    detail = _get_event_or_404(event_id)
    return {
        "event_id": event_id,
        "industrial_distance_m": detail.get("industrial_distance_m"),
        "industrial_site_count_250m": detail.get("industrial_site_count_250m", 0),
        "industrial_site_count_1km": detail.get("industrial_count_1km", 0),
        "industrial_site_count_5km": detail.get("industrial_count_5km", 0),
        "nearest_site_name": detail.get("nearest_industrial_name")
    }

@router.get(
    "/{event_id}/review",
    summary="Get Analyst Review Decision History",
    description="Returns persisted human analyst review decision and notes for target event."
)
def get_event_review(event_id: str = Path(..., description="Unique event cluster ID")):
    detail = _get_event_or_404(event_id)
    return {
        "event_id": event_id,
        "review_status": detail.get("review_status", "PENDING"),
        "classification": detail.get("classification"),
        "review_required": detail.get("review_required", False)
    }
