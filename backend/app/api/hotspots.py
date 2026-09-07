"""
FastAPI Hotspot Telemetry & Analysis Endpoints.
"""
import math
from typing import Optional, List
from fastapi import APIRouter, Query, Path, status
from backend.app.schemas.hotspot import (
    HotspotResponse, HotspotDetailResponse, GeoJSONFeatureCollection
)
from backend.app.schemas.prediction import PredictionResponse
from backend.app.schemas.evidence import EvidenceResponse
from backend.app.schemas.risk import RiskResponse
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.services.hotspot_service import hotspot_service
from backend.app.services.prediction_service import prediction_service
from backend.app.services.evidence_service import evidence_service
from backend.app.services.risk_service import risk_service
from backend.app.utils.errors import HotspotNotFoundException

router = APIRouter(prefix="/api/hotspots", tags=["Hotspots"])

@router.get(
    "",
    response_model=PaginatedResponse[HotspotResponse],
    summary="Query Hotspots List",
    description="Returns paginated real satellite thermal observations filtered by date range, bounding box, FRP, classification, risk, and data source."
)
@router.get(
    "",
    response_model=PaginatedResponse[HotspotResponse],
    summary="Query Hotspots List",
    description="Returns paginated real satellite thermal observations filtered by date range, bounding box, FRP, classification, risk, priority, and data source."
)
def list_hotspots(
    start_date: Optional[str] = Query(None, description="ISO start date filter"),
    end_date: Optional[str] = Query(None, description="ISO end date filter"),
    date_from: Optional[str] = Query(None, description="Alias for start_date"),
    date_to: Optional[str] = Query(None, description="Alias for end_date"),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Maximum longitude"),
    bbox: Optional[str] = Query(None, description="Bounding box filter (minLon,minLat,maxLon,maxLat)"),
    min_frp: Optional[float] = Query(None, ge=0.0, description="Minimum FRP (MW)"),
    max_frp: Optional[float] = Query(None, ge=0.0, description="Maximum FRP (MW)"),
    confidence: Optional[str] = Query(None, description="Confidence level"),
    classification: Optional[str] = Query(None, description="Class filter: LIKELY_INDUSTRIAL_INCIDENT, PERSISTENT_INDUSTRIAL_HEAT, NATURAL_WILDLAND_FIRE"),
    risk_level: Optional[str] = Query(None, description="Risk level filter: HIGH, MEDIUM, LOW"),
    priority: Optional[str] = Query(None, description="Priority filter: URGENT, HIGH, MEDIUM, LOW"),
    review_required: Optional[bool] = Query(None, description="Filter for items requiring human review"),
    human_review_required: Optional[bool] = Query(None, description="Alias for review_required"),
    data_quality_status: Optional[str] = Query(None, description="Data quality filter: HIGH, MEDIUM, LOW"),
    evidence_status: Optional[str] = Query(None, description="Evidence status filter"),
    worldcover_class: Optional[int] = Query(None, description="WorldCover class code"),
    near_industry: Optional[bool] = Query(None, description="Filter events within 1km of industrial facility"),
    satellite: Optional[str] = Query(None, description="Satellite sensor filter"),
    data_source: str = Query("REAL", description="Governance tag filter ('REAL' or 'SYNTHETIC_DEMO')"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size (max 500)")
):
    s_date = start_date or date_from
    e_date = end_date or date_to
    rev_req = review_required if review_required is not None else human_review_required

    items, total = hotspot_service.get_hotspots(
        start_date=s_date, end_date=e_date,
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
        bbox=bbox, min_frp=min_frp, max_frp=max_frp, confidence=confidence,
        classification=classification, risk_level=risk_level, priority=priority,
        review_required=rev_req, data_quality_status=data_quality_status,
        evidence_status=evidence_status, worldcover_class=worldcover_class,
        near_industry=near_industry, satellite=satellite,
        data_source=data_source, page=page, page_size=page_size
    )

    total_val = total if total is not None else 0
    total_pages = math.ceil(total_val / page_size) if total_val > 0 else 1
    meta = PaginationMeta(total=total_val, page=page, page_size=page_size, total_pages=total_pages)

    return PaginatedResponse[HotspotResponse](items=items, meta=meta)

@router.get(
    "/geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Get Map-Ready GeoJSON FeatureCollection",
    description="Returns RFC 7946 compliant GeoJSON FeatureCollection with Point geometry formatted strictly as [longitude, latitude]. Supports PostGIS bounding box filtering."
)
def get_hotspots_geojson(
    start_date: Optional[str] = Query(None, description="ISO start date filter"),
    end_date: Optional[str] = Query(None, description="ISO end date filter"),
    date_from: Optional[str] = Query(None, description="Alias for start_date"),
    date_to: Optional[str] = Query(None, description="Alias for end_date"),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Maximum longitude"),
    bbox: Optional[str] = Query(None, description="Bounding box (minLon,minLat,maxLon,maxLat)"),
    min_frp: Optional[float] = Query(None, ge=0.0, description="Minimum FRP (MW)"),
    max_frp: Optional[float] = Query(None, ge=0.0, description="Maximum FRP (MW)"),
    risk_level: Optional[str] = Query(None, description="Risk level filter"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    review_required: Optional[bool] = Query(None, description="Human review required filter"),
    data_source: str = Query("REAL", description="Governance tag filter ('REAL' or 'SYNTHETIC_DEMO')"),
    limit: int = Query(500, ge=1, le=2000, description="Max feature count")
):
    s_date = start_date or date_from
    e_date = end_date or date_to
    return hotspot_service.get_hotspots_geojson(
        start_date=s_date, end_date=e_date,
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
        bbox=bbox, min_frp=min_frp, max_frp=max_frp,
        risk_level=risk_level, priority=priority, review_required=review_required,
        data_source=data_source, limit=limit
    )

@router.get(
    "/{hotspot_id}",
    response_model=HotspotDetailResponse,
    summary="Get Hotspot Detailed Record",
    description="Returns complete investigation object including coordinates, FRP, satellite, GIS context, prediction, evidence, risk, and review status."
)
def get_hotspot_detail(hotspot_id: str = Path(..., description="Unique hotspot ID")):
    detail = hotspot_service.get_hotspot_detail(hotspot_id)
    if not detail:
        raise HotspotNotFoundException(hotspot_id)
    return detail

@router.get(
    "/{hotspot_id}/prediction",
    response_model=PredictionResponse,
    summary="Get ML Classification & Operational Abstention",
    description="Runs ML baseline inference, returns class probabilities, confidence score, and operational abstention status."
)
def get_hotspot_prediction(hotspot_id: str = Path(..., description="Unique hotspot ID")):
    pred = prediction_service.predict_hotspot(hotspot_id)
    if not pred:
        raise HotspotNotFoundException(hotspot_id)
    return pred

@router.get(
    "/{hotspot_id}/evidence",
    response_model=EvidenceResponse,
    summary="Get Structured GIS & Ground-Truth Evidence",
    description="Returns structured evidence statements for industrial co-location, historical recurrence, FRP anomaly, land cover, and label provenance."
)
def get_hotspot_evidence(hotspot_id: str = Path(..., description="Unique hotspot ID")):
    ev = evidence_service.get_hotspot_evidence(hotspot_id)
    if not ev:
        raise HotspotNotFoundException(hotspot_id)
    return ev

@router.get(
    "/{hotspot_id}/risk",
    response_model=RiskResponse,
    summary="Get Operational Risk Prioritization Score",
    description="Calculates composite operational prioritization score [0.0, 1.0] and risk level (HIGH, MEDIUM, LOW) based on industrial proximity and severity."
)
def get_hotspot_risk(hotspot_id: str = Path(..., description="Unique hotspot ID")):
    rk = risk_service.calculate_risk(hotspot_id)
    if not rk:
        raise HotspotNotFoundException(hotspot_id)
    return rk

@router.get(
    "/{hotspot_id}/history",
    summary="Get Hotspot Historical Recurrence Telemetry",
    description="Returns past historical thermal anomaly recurrence within 1km over rolling 30-day and 365-day windows."
)
def get_hotspot_history(hotspot_id: str = Path(..., description="Unique hotspot ID")):
    hist = hotspot_service.get_hotspot_history(hotspot_id)
    if not hist.get("hotspot_id"):
        raise HotspotNotFoundException(hotspot_id)
    return hist
