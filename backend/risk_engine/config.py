"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Configuration.
Defines configurable weights, operational risk thresholds, proximity bounds,
and evidence scoring parameters.
"""
from pydantic import BaseModel, Field


class RiskEngineConfig(BaseModel):
    """Configuration container for operational risk scoring weights and thresholds."""

    # 1. Dimensional Risk Scoring Weights (Must sum to 1.0)
    thermal_weight: float = Field(default=0.30, description="Weight for current thermal intensity signal")
    historical_weight: float = Field(default=0.25, description="Weight for historical FRP anomaly Z-score")
    industrial_weight: float = Field(default=0.20, description="Weight for industrial proximity & site density")
    recurrence_weight: float = Field(default=0.10, description="Weight for activity persistence/recurrence")
    natural_weight: float = Field(default=0.10, description="Weight for natural/forest land cover context")
    quality_weight: float = Field(default=0.05, description="Weight for telemetry and GIS data quality")

    # 2. Operational Risk Level Thresholds
    risk_low_max: float = Field(default=0.39, description="Upper bound for LOW operational risk")
    risk_medium_max: float = Field(default=0.69, description="Upper bound for MEDIUM operational risk")
    risk_review_threshold: float = Field(default=0.65, description="Operational threshold for human review routing")

    # 3. Industrial Distance Bounds (Meters)
    dist_immediate_m: float = Field(default=250.0, description="Immediate industrial perimeter boundary")
    dist_close_m: float = Field(default=1000.0, description="Close industrial zone boundary")
    dist_moderate_m: float = Field(default=5000.0, description="Moderate industrial proximity boundary")

    # 4. Thermal Intensity FRP Bounds (MW)
    frp_extreme: float = Field(default=150.0, description="Extreme FRP magnitude baseline")
    frp_high: float = Field(default=40.0, description="High FRP magnitude baseline")
    frp_moderate: float = Field(default=15.0, description="Moderate FRP magnitude baseline")

    def validate_weights(self) -> bool:
        """Validates that dimensional weights sum to 1.0 within numerical tolerance."""
        total = (
            self.thermal_weight + self.historical_weight + self.industrial_weight +
            self.recurrence_weight + self.natural_weight + self.quality_weight
        )
        return abs(total - 1.0) < 1e-4


default_config = RiskEngineConfig()
