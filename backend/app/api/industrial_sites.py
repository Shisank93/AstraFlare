"""
FastAPI Industrial Infrastructure Context Endpoints.
"""
import math
from typing import Optional
from fastapi import APIRouter, Query, Path, status
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.services.gis_service import gis_service
from backend.app.utils.errors import IndustrialSiteNotFoundException

router = APIRouter(prefix="/api/industrial-sites", tags=["Industrial Sites"])

@router.get(
    "",
    summary="Query Mapped Industrial Facilities",
    description="Returns OSM-mapped industrial facilities filtered by spatial bounding box and facility type, with nearby thermal detection counts."
)
def list_industrial_sites(
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Maximum longitude"),
    facility_type: Optional[str] = Query(None, description="Facility category (e.g. oil_refinery, chemical, power)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size")
):
    items, total = gis_service.get_industrial_sites(
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
        facility_type=facility_type, page=page, page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(total=total, page=page, page_size=page_size, total_pages=total_pages)

    return {"items": items, "meta": meta}

@router.get(
    "/{site_id}",
    summary="Get Industrial Facility Details",
    description="Returns site identity, coordinates, facility type, and associated nearby thermal detections within 3km."
)
def get_industrial_site_detail(site_id: str = Path(..., description="OSM ID or database site ID")):
    detail = gis_service.get_industrial_site_detail(site_id)
    if not detail:
        raise IndustrialSiteNotFoundException(site_id)
    return detail
