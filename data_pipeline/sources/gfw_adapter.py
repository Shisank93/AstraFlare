"""
Global Forest Watch (GFW) Fire Alerts Data Adapter.
Processes GFW active fire alerts and wildfire datasets into NormalizedEvent schema.
"""
from typing import Dict, Any, List
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus

class GFWAdapter:
    def normalize_alert(self, raw_alert: Dict[str, Any]) -> NormalizedEvent:
        lat = float(raw_alert.get("latitude", 0.0))
        lon = float(raw_alert.get("longitude", 0.0))
        alert_id = str(raw_alert.get("alert_id") or f"gfw_{lat}_{lon}_{raw_alert.get('alert_date', '')}")

        return NormalizedEvent(
            event_id=alert_id,
            source_name="Global_Forest_Watch",
            source_type="WILDFIRE_ALERT_SERVICEMAP",
            source_record_id=alert_id,
            event_class="NATURAL_WILDLAND_FIRE",
            timestamp_start=str(raw_alert.get("alert_date") or raw_alert.get("acq_date") or ""),
            timestamp_end=str(raw_alert.get("alert_date") or raw_alert.get("acq_date") or ""),
            latitude=lat,
            longitude=lon,
            country=str(raw_alert.get("country") or "IND"),
            admin_region=raw_alert.get("admin_region"),
            description="Global Forest Watch active fire alert",
            source_url="https://www.globalforestwatch.org/",
            provenance_status=ProvenanceStatus.SATELLITE_DERIVED_CORROBORATION,
            confidence=0.85 if raw_alert.get("confidence") == "high" else 0.70,
            metadata=raw_alert
        )

gfw_adapter = GFWAdapter()
