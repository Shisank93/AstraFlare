"""
Evidence Pydantic Schemas for AstraFlare Ground-Truth and GIS Evidence Engine.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    evidence_type: str = Field(..., description="Category of evidence (e.g. INDUSTRIAL_PROXIMITY, HISTORICAL_RECURRENCE, FRP_ANOMALY, LAND_COVER, EXTERNAL_CORROBORATION)")
    feature_name: str = Field(..., description="Key feature identifier")
    value: str = Field(..., description="Stringified value of the feature")
    interpretation: str = Field(..., description="Human-readable statement explaining the evidence contribution")
    source: str = Field(..., description="Data source provenance (e.g., OSM, ESA_WORLDCOVER, NASA_FIRMS, PESO)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Evidence confidence/reliability score")

class EvidenceResponse(BaseModel):
    hotspot_id: str = Field(..., description="Hotspot identifier")
    physical_event_id: Optional[str] = Field(None, description="Associated physical event cluster ID")
    verification_status: str = Field(..., description="Label provenance (e.g., VERIFIED_EXTERNAL, MANUAL_VERIFIED, WEAK_RULE, UNLABELED)")
    evidence_items: List[EvidenceItem] = Field(..., description="List of evidence statements")
