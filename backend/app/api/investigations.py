"""
FastAPI Human-in-the-Loop Investigation Review Endpoints.
"""
import math
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, Path, Body, status
from backend.app.schemas.investigation import ReviewCreateRequest, ReviewResponse
from backend.app.schemas.common import PaginationMeta
from backend.app.services.investigation_service import investigation_service
from backend.app.utils.errors import HotspotNotFoundException

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])

@router.post(
    "/{event_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Analyst Investigation Review",
    description="Persists human analyst review decision ('CONFIRMED', 'DISMISSED', 'ESCALATED', 'NEEDS_MORE_DATA'), notes, and reviewer ID in audit trail table."
)
def submit_analyst_review(
    event_id: str = Path(..., description="Target event/hotspot ID"),
    payload: ReviewCreateRequest = Body(..., description="Analyst review submission payload")
):
    review = investigation_service.submit_review(
        hotspot_id=event_id,
        decision=payload.decision,
        reviewer_id=payload.reviewer_id,
        notes=payload.notes,
        corrected_classification=payload.corrected_classification
    )
    if not review:
        raise HotspotNotFoundException(event_id)
    return review

@router.get(
    "",
    summary="Get Analyst Prioritized Investigation Queue or Review History",
    description="Returns analyst investigation queue (ordered by priority & risk score) or list of analyst review decisions when review_status is specified."
)
def list_investigations_or_queue(
    priority: Optional[str] = Query(None, description="Priority filter: URGENT, HIGH, MEDIUM, LOW"),
    risk_level: Optional[str] = Query(None, description="Risk level filter: HIGH, MEDIUM, LOW"),
    review_status: Optional[str] = Query(None, description="Review status filter: CONFIRMED, DISMISSED, ESCALATED, NEEDS_MORE_DATA"),
    human_review_required: Optional[bool] = Query(None, description="Filter items requiring review"),
    start_date: Optional[str] = Query(None, description="ISO start date"),
    end_date: Optional[str] = Query(None, description="ISO end date"),
    evidence_status: Optional[str] = Query(None, description="Evidence status filter"),
    data_quality_status: Optional[str] = Query(None, description="Data quality status filter"),
    data_source: str = Query("REAL", description="Governance tag ('REAL' or 'SYNTHETIC_DEMO')"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size")
):
    if review_status:
        items, total = investigation_service.list_investigations(review_status=review_status, page=page, page_size=page_size)
    else:
        items, total = investigation_service.get_investigation_queue(
            priority=priority, risk_level=risk_level, human_review_required=human_review_required,
            start_date=start_date, end_date=end_date, evidence_status=evidence_status,
            data_quality_status=data_quality_status, data_source=data_source,
            page=page, page_size=page_size
        )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(total=total, page=page, page_size=page_size, total_pages=total_pages)

    return {"items": items, "meta": meta}
