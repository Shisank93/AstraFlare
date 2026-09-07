"""
Prediction Pydantic Schemas for AstraFlare ML Baseline Inference.
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field

class ClassProbabilities(BaseModel):
    LIKELY_INDUSTRIAL_INCIDENT: float = Field(..., ge=0.0, le=1.0)
    PERSISTENT_INDUSTRIAL_HEAT: float = Field(..., ge=0.0, le=1.0)
    NATURAL_WILDLAND_FIRE: float = Field(..., ge=0.0, le=1.0)

class PredictionResponse(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot identifier")
    predicted_class: str = Field(..., description="Predicted primary classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score")
    probabilities: ClassProbabilities = Field(..., description="Per-class probability distribution")
    review_required: bool = Field(..., description="Abstention flag (True if confidence < HUMAN_REVIEW_THRESHOLD)")
    human_review_threshold: float = Field(..., description="Configured operational threshold for human review")
    model_version: str = Field(..., description="Model version string")
    model_status: str = Field(..., description="Governance status (e.g., 'RESEARCH BASELINE')")
    limitations: str = Field(..., description="Scientific limitations disclaimer")
