"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Data Models.
Defines typed Pydantic schemas for risk engine inputs, traceable evidence items,
dimensional breakdowns, and final RiskAssessment outputs.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskInput(BaseModel):
    """Event-level feature vector input model for risk engine assessment."""
    event_id: str = Field(description="Unique physical event cluster identifier")
    
    # Thermal Telemetry
    max_frp: float = Field(default=0.0, description="Maximum Fire Radiative Power (MW)")
    mean_frp: Optional[float] = Field(default=None, description="Mean Fire Radiative Power (MW)")
    std_frp: Optional[float] = Field(default=None, description="Standard deviation of Fire Radiative Power")
    max_brightness: Optional[float] = Field(default=None, description="Maximum brightness temperature (K)")
    mean_brightness: Optional[float] = Field(default=None, description="Mean brightness temperature (K)")
    observation_count: int = Field(default=1, description="Number of satellite detections in event cluster")
    duration_hours: float = Field(default=0.0, description="Duration of event cluster in hours")
    confidence_high_ratio: float = Field(default=0.0, description="Ratio of high-confidence observations")
    satellite_count: int = Field(default=1, description="Number of distinct satellite sensors observing event")

    # Industrial Context
    industrial_distance_m: float = Field(default=10000.0, description="Geodesic distance to nearest industrial node (m)")
    industrial_site_count_250m: int = Field(default=0, description="Industrial site count within 250 meters")
    industrial_site_count_1km: int = Field(default=0, description="Industrial site count within 1 kilometer")
    industrial_site_count_5km: int = Field(default=0, description="Industrial site count within 5 kilometers")

    # Historical Context
    previous_detection_count: int = Field(default=0, description="Number of historical detections in spatial cell")
    historical_mean_frp: Optional[float] = Field(default=None, description="Historical mean FRP in spatial cell")
    historical_max_frp: Optional[float] = Field(default=None, description="Historical max FRP in spatial cell")
    historical_std_frp: Optional[float] = Field(default=None, description="Historical std FRP in spatial cell")
    frp_anomaly_z: Optional[float] = Field(default=None, description="FRP intensity Z-score relative to baseline")
    history_status: Optional[str] = Field(default=None, description="Status of historical data baseline")

    # Land Cover & Location
    worldcover_class: str = Field(default="Unknown", description="10m ESA WorldCover land cover category string")
    centroid_lat: float = Field(default=0.0, description="Centroid latitude in WGS84 degrees")
    centroid_lon: float = Field(default=0.0, description="Centroid longitude in WGS84 degrees")

    # Temporal
    event_start: Optional[str] = Field(default=None, description="ISO timestamp of event start")
    event_end: Optional[str] = Field(default=None, description="ISO timestamp of event end")


class EvidenceItem(BaseModel):
    """Traceable, audit-ready evidence attribution item."""
    type: str = Field(description="Evidence category (e.g. THERMAL_ANOMALY, INDUSTRIAL_PROXIMITY, LAND_COVER)")
    strength: str = Field(description="Operational evidence strength (LOW, MODERATE, HIGH, VERY_HIGH)")
    value: str = Field(description="Human-readable formatted input metric string")
    reason: str = Field(description="Factual evidence statement explaining score contribution")
    input_feature: str = Field(description="Source feature name from input schema")
    input_value: Any = Field(description="Raw input value before normalization")
    normalization: float = Field(description="Normalized score in [0.0, 1.0]")
    weight: float = Field(description="Configured dimensional weight applied to this component")
    contribution: float = Field(description="Exact mathematical score contribution (normalization * weight)")


class EvidenceBreakdown(BaseModel):
    """Dimensional score breakdown across independent evidence axes."""
    thermal_evidence_score: float = Field(description="Normalized thermal intensity score [0.0, 1.0]")
    historical_evidence_score: float = Field(description="Normalized historical anomaly score [0.0, 1.0]")
    industrial_proximity_score: float = Field(description="Normalized industrial distance score [0.0, 1.0]")
    industrial_density_score: float = Field(description="Normalized industrial site density score [0.0, 1.0]")
    industrial_context_score: float = Field(description="Combined industrial context score [0.0, 1.0]")
    natural_context_score: float = Field(description="Normalized natural/wildland land cover score [0.0, 1.0]")
    recurrence_score: float = Field(description="Activity recurrence score [0.0, 1.0]")
    persistence_score: float = Field(description="Activity persistence score [0.0, 1.0]")
    data_quality_score: float = Field(description="Data completeness & telemetry quality score [0.0, 1.0]")


class RiskAssessment(BaseModel):
    """Complete, deterministic operational risk assessment model."""
    event_id: str = Field(description="Physical event cluster ID")
    overall_risk_score: float = Field(description="Deterministic composite operational risk score [0.0, 1.0]")
    risk_level: str = Field(description="Operational risk level (LOW, MEDIUM, HIGH)")
    investigation_priority: str = Field(description="Human analyst investigation priority (LOW, MEDIUM, HIGH, URGENT)")
    
    # Dimensional Sub-Scores
    industrial_context_score: float = Field(description="Combined industrial context score [0.0, 1.0]")
    natural_fire_context_score: float = Field(description="Natural/wildland fire context score [0.0, 1.0]")
    thermal_anomaly_score: float = Field(description="Thermal intensity anomaly score [0.0, 1.0]")
    historical_anomaly_score: float = Field(description="Historical Z-score anomaly score [0.0, 1.0]")
    recurrence_score: float = Field(description="Historical activity recurrence score [0.0, 1.0]")
    persistence_score: float = Field(description="Thermal activity persistence score [0.0, 1.0]")
    data_quality_score: float = Field(description="Telemetry and GIS data quality score [0.0, 1.0]")

    # Statuses & Routing
    history_status: str = Field(description="Historical baseline status (ADEQUATE_HISTORY, LIMITED_HISTORY, NO_PRIOR_HISTORY)")
    data_quality_status: str = Field(description="Data quality level (HIGH, MEDIUM, LOW, INSUFFICIENT)")
    evidence_status: str = Field(description="Combined evidence classification status")
    likely_context: str = Field(description="Operational context interpretation (INDUSTRIAL_CONTEXT, NATURAL_FIRE_CONTEXT, etc.)")
    human_review_required: bool = Field(description="Boolean flag indicating whether human review is required")
    human_review_reasons: List[str] = Field(default_factory=list, description="List of reasons triggering human review routing")

    # Traceable Evidence List
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Traceable, audit-ready evidence items")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), description="ISO UTC timestamp of assessment generation")
