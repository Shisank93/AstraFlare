"""
Prediction Pydantic Schemas for AstraFlare ML Baseline Inference.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ClassProbabilities(BaseModel):
    LIKELY_INDUSTRIAL_INCIDENT: float = Field(..., ge=0.0, le=1.0)
    PERSISTENT_INDUSTRIAL_HEAT: float = Field(..., ge=0.0, le=1.0)
    NATURAL_WILDLAND_FIRE: float = Field(..., ge=0.0, le=1.0)

class PredictionResponse(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot identifier")
    predicted_class: Optional[str] = Field(None, description="Predicted primary classification label")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model prediction confidence score")
    probabilities: Optional[ClassProbabilities] = Field(None, description="Per-class probability distribution")
    review_required: bool = Field(..., description="Abstention flag (True if confidence < HUMAN_REVIEW_THRESHOLD)")
    human_review_threshold: float = Field(..., description="Configured operational threshold for human review")
    model_version: str = Field(..., description="Model version string")
    model_status: str = Field(..., description="Governance status (e.g., 'RESEARCH BASELINE')")
    limitations: str = Field(..., description="Scientific limitations disclaimer")
    is_ml_prediction: bool = Field(False, description="True if a genuine ML model generated this prediction")
    reference_label: Optional[str] = Field(None, description="Weak rule/reference label if ML prediction is absent")
    reference_provenance: Optional[str] = Field(None, description="Provenance of reference label")
    confidence_status: Optional[str] = Field(None, description="HIGH CONFIDENCE, MODERATE CONFIDENCE, or LOW CONFIDENCE — ANALYST REVIEW")
    abstention_reason: Optional[str] = Field(None, description="Operational explanation for abstention decision")
    industrial_anomaly_score: Optional[float] = Field(None, description="Unsupervised industrial anomaly assessment score [0.0, 1.0]")
    industrial_anomaly_level: Optional[str] = Field(None, description="HIGH, MODERATE, or LOW industrial anomaly tier")
    top_contributing_features: Optional[list] = Field(default_factory=list, description="Top TreeSHAP / operational contributing features")
    model_metadata: Optional[Dict[str, Any]] = Field(None, description="Dynamic model metadata including isolation and training stats")

