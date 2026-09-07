"""
Hotspot Pydantic Schemas & GeoJSON Models.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class HotspotResponse(BaseModel):
    id: str = Field(..., description="Unique AstraFlare hotspot ID")
    firms_id: Optional[str] = Field(None, description="Original FIRMS ID")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude")
    acq_timestamp: str = Field(..., description="ISO 8601 acquisition timestamp")
    satellite: str = Field(..., description="Satellite identity (e.g. VIIRS_SNPP, NOAA20, MODIS)")
    instrument: Optional[str] = Field(None, description="Instrument name (e.g. VIIRS, MODIS)")
    brightness: Optional[float] = Field(None, description="Brightness temperature (K)")
    frp: float = Field(..., ge=0.0, description="Fire Radiative Power (MW)")
    confidence: Optional[str] = Field(None, description="Detection confidence level")
    daynight: Optional[str] = Field(None, description="Day/Night indicator ('D' or 'N')")
    data_source: str = Field(..., description="Governance tag ('REAL' or 'SYNTHETIC_DEMO')")
    physical_event_id: Optional[str] = Field(None, description="Associated physical event cluster ID")
    classification: Optional[str] = Field(None, description="Classification label")
    risk_level: Optional[str] = Field(None, description="Prioritization risk level: HIGH, MEDIUM, LOW")
    review_required: bool = Field(False, description="Flag indicating analyst review is required")

class HotspotDetailResponse(HotspotResponse):
    nearest_industrial_name: Optional[str] = Field(None, description="Name of nearest OSM industrial facility")
    industrial_distance_m: Optional[float] = Field(None, description="Distance to nearest industrial facility in meters")
    industrial_count_1km: Optional[int] = Field(0, description="Count of industrial facilities within 1km")
    industrial_count_5km: Optional[int] = Field(0, description="Count of industrial facilities within 5km")
    land_cover_code: Optional[int] = Field(None, description="ESA WorldCover class code")
    land_cover_name: Optional[str] = Field(None, description="ESA WorldCover class name")
    historical_count_30d: Optional[int] = Field(0, description="Hotspot count within 1km in past 30 days")
    historical_mean_frp: Optional[float] = Field(None, description="Historical mean FRP within 1km")
    frp_anomaly_zscore: Optional[float] = Field(None, description="FRP Anomaly Z-Score")
    anomaly_status: Optional[str] = Field("VALID", description="Anomaly calculation status")
    verification_status: Optional[str] = Field("WEAK_RULE", description="Label provenance hierarchy")
    prediction_confidence: Optional[float] = Field(None, description="Model prediction confidence")
    review_status: Optional[str] = Field("PENDING", description="Analyst review status")

# --- GeoJSON Schemas (RFC 7946 Compliant) ---

class GeoJSONGeometry(BaseModel):
    type: str = Field("Point", description="Geometry type (must be 'Point')")
    coordinates: List[float] = Field(..., description="[longitude, latitude] pair according to RFC 7946 specification")

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        if len(v) != 2:
            raise ValueError("GeoJSON Point coordinates must contain exactly [longitude, latitude].")
        lon, lat = v[0], v[1]
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} out of WGS84 bounds [-180, 180].")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} out of WGS84 bounds [-90, 90].")
        return v

class GeoJSONFeature(BaseModel):
    type: str = Field("Feature", description="GeoJSON type")
    geometry: GeoJSONGeometry = Field(..., description="Point geometry with [longitude, latitude]")
    properties: Dict[str, Any] = Field(..., description="Hotspot properties dictionary")

class GeoJSONFeatureCollection(BaseModel):
    type: str = Field("FeatureCollection", description="GeoJSON FeatureCollection type")
    features: List[GeoJSONFeature] = Field(..., description="List of GeoJSON features")
