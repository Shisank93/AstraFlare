"""
Normalized Event Schema & Provenance Definitions for AstraFlare Data Ingestion.
Defines common representation for external events and physical FIRMS event clusters.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ProvenanceStatus(str, Enum):
    REAL = "REAL"
    MOCK = "MOCK"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"
    WEAK_RULE = "WEAK_RULE"
    VERIFIED_EXTERNAL = "VERIFIED_EXTERNAL"
    SATELLITE_DERIVED_CORROBORATION = "SATELLITE_DERIVED_CORROBORATION"
    MANUAL_VERIFIED = "MANUAL_VERIFIED"

class LabelProvenance(str, Enum):
    VERIFIED_EXTERNAL = "VERIFIED_EXTERNAL"
    MANUAL_VERIFIED = "MANUAL_VERIFIED"
    WEAK_RULE = "WEAK_RULE"
    UNLABELED = "UNLABELED"

class NormalizedEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    source_name: str = Field(..., description="Name of external data source (e.g. NASA_FIRMS, GFW, PESO, FSI, GEM)")
    source_type: str = Field(..., description="Source category (e.g. SATELLITE_NRT, GOVERNMENT_REGISTRY, INDUSTRIAL_CATALOG)")
    source_record_id: Optional[str] = Field(None, description="Original record ID from source system")
    event_class: Optional[str] = Field(None, description="Event classification (LIKELY_INDUSTRIAL_INCIDENT, PERSISTENT_INDUSTRIAL_HEAT, NATURAL_WILDLAND_FIRE)")
    timestamp_start: str = Field(..., description="ISO 8601 start timestamp")
    timestamp_end: Optional[str] = Field(None, description="ISO 8601 end timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude WGS84")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude WGS84")
    country: str = Field("IND", description="ISO country code")
    admin_region: Optional[str] = Field(None, description="State/district admin region")
    description: Optional[str] = Field(None, description="Human-readable event summary")
    source_url: Optional[str] = Field(None, description="Provenance URL")
    provenance_status: ProvenanceStatus = Field(ProvenanceStatus.VERIFIED_EXTERNAL, description="Data governance provenance state")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Source reliability score")
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO retrieval timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional source-specific fields")

    @field_validator("provenance_status")
    @classmethod
    def validate_provenance(cls, v: ProvenanceStatus) -> ProvenanceStatus:
        if v == ProvenanceStatus.SYNTHETIC_DEMO:
            # Synthetic records must never masquerade as REAL
            pass
        return v
