"""
Investigation & Human-in-the-Loop Analyst Review Pydantic Schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ReviewCreateRequest(BaseModel):
    decision: str = Field(..., description="Analyst decision: 'CONFIRMED', 'REJECTED', 'ESCALATED', or 'CORRECTED'")
    reviewer_id: str = Field(..., min_length=2, max_length=128, description="Identifier of the analyst")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional analyst notes and context")
    corrected_classification: Optional[str] = Field(
        None,
        description="Optional corrected label: 'LIKELY_INDUSTRIAL_INCIDENT', 'PERSISTENT_INDUSTRIAL_HEAT', or 'NATURAL_WILDLAND_FIRE'"
    )

class ReviewResponse(BaseModel):
    review_id: int = Field(..., description="Database review ID")
    hotspot_id: str = Field(..., description="Target hotspot ID")
    original_prediction: str = Field(..., description="Original model classification")
    final_classification: str = Field(..., description="Final persisted classification")
    review_status: str = Field(..., description="Review status: 'PENDING', 'CONFIRMED', 'REJECTED', 'ESCALATED', or 'CORRECTED'")
    analyst_note: Optional[str] = Field(None, description="Analyst notes")
    reviewer_id: Optional[str] = Field(None, description="Analyst ID")
    created_at: str = Field(..., description="Timestamp when review was created")
    updated_at: str = Field(..., description="Timestamp when review was last updated")
