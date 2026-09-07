"""
Risk Pydantic Schemas for AstraFlare Operational Prioritization Score.
"""
from typing import List
from pydantic import BaseModel, Field

class RiskFactorItem(BaseModel):
    factor: str = Field(..., description="Name of contributing factor (e.g. FRP_SEVERITY, INDUSTRIAL_PROXIMITY, ANOMALY_ZSCORE)")
    weight: float = Field(..., description="Relative factor weight")
    score: float = Field(..., description="Normalized component score [0, 1]")
    description: str = Field(..., description="Explanation of factor contribution")

class RiskResponse(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot identifier")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Composite operational prioritization score [0.0, 1.0]")
    risk_level: str = Field(..., description="Risk category: HIGH, MEDIUM, or LOW")
    contributing_factors: List[RiskFactorItem] = Field(..., description="Breakdown of individual risk factors")
    explanation: str = Field(..., description="Overall human-readable risk summary")
    limitations: str = Field(..., description="Disclaimer that risk score is an operational prioritization heuristic")
