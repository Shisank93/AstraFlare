"""
NASA FIRMS Data Adapter & Physical Event Aggregator.
Converts raw satellite thermal detections into normalized physical event aggregates.
"""
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus
from data_pipeline.gis_engine import gis_engine

class FIRMSAdapter:
    def normalize_observation(self, raw_record: Dict[str, Any]) -> NormalizedEvent:
        """Converts raw FIRMS observation into NormalizedEvent schema."""
        acq_ts = str(raw_record.get("acq_timestamp") or raw_record.get("acquisition_time") or datetime.utcnow().isoformat())
        lat = float(raw_record.get("latitude", 0.0))
        lon = float(raw_record.get("longitude", 0.0))
        obs_id = str(raw_record.get("id") or raw_record.get("firms_id") or f"firms_{lat}_{lon}")

        return NormalizedEvent(
            event_id=obs_id,
            source_name="NASA_FIRMS",
            source_type="SATELLITE_NRT",
            source_record_id=obs_id,
            event_class=raw_record.get("classification"),
            timestamp_start=acq_ts,
            timestamp_end=acq_ts,
            latitude=lat,
            longitude=lon,
            country="IND",
            description=f"Satellite thermal detection (FRP: {raw_record.get('frp', 0.0)} MW)",
            source_url="https://firms.modaps.eosdis.nasa.gov/",
            provenance_status=ProvenanceStatus.REAL if raw_record.get("data_source") == "REAL" else ProvenanceStatus.SYNTHETIC_DEMO,
            confidence=float(raw_record.get("prediction_confidence") or 0.8),
            metadata=raw_record
        )

    def aggregate_event_cluster(self, cluster_id: str, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates spatio-temporal aggregate features across all satellite observations in a physical event cluster."""
        if not observations:
            return {}

        frp_vals = [float(o.get("frp", 0.0)) for o in observations]
        bright_vals = [float(o.get("brightness", 0.0)) for o in observations if o.get("brightness") is not None]
        satellites = set(o.get("satellite", "UNKNOWN") for o in observations)

        lats = [float(o["latitude"]) for o in observations]
        lons = [float(o["longitude"]) for o in observations]
        mean_lat = sum(lats) / len(lats)
        mean_lon = sum(lons) / len(lons)

        # Calculate historical stats and industrial context
        near_site, dist_m = gis_engine.get_nearest_industrial_site(mean_lat, mean_lon, max_distance_m=5000.0)

        mean_frp = sum(frp_vals) / len(frp_vals)
        variance = sum((x - mean_frp) ** 2 for x in frp_vals) / len(frp_vals) if len(frp_vals) > 1 else 0.0
        std_frp = math.sqrt(variance)

        return {
            "physical_event_id": cluster_id,
            "observation_count": len(observations),
            "mean_latitude": mean_lat,
            "mean_longitude": mean_lon,
            "max_frp": max(frp_vals),
            "mean_frp": mean_frp,
            "std_frp": std_frp,
            "max_brightness": max(bright_vals) if bright_vals else None,
            "mean_brightness": (sum(bright_vals) / len(bright_vals)) if bright_vals else None,
            "satellite_count": len(satellites),
            "satellites_list": list(satellites),
            "nearest_industrial_name": near_site["name"] if near_site else None,
            "industrial_distance_m": dist_m,
            "provenance_status": ProvenanceStatus.SATELLITE_DERIVED_CORROBORATION
        }

firms_adapter = FIRMSAdapter()
