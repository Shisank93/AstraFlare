"""
Industrial Infrastructure & Energy Facility Adapter.
Parses OSM Overpass and Global Energy Monitor (GEM) oil/gas & power plant trackers.
"""
from typing import Dict, Any
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus

class IndustrialAdapter:
    def normalize_facility(self, raw_facility: Dict[str, Any]) -> NormalizedEvent:
        lat = float(raw_facility.get("latitude", 0.0))
        lon = float(raw_facility.get("longitude", 0.0))
        fac_id = str(raw_facility.get("osm_id") or raw_facility.get("gem_id") or f"facility_{lat}_{lon}")

        source_name = str(raw_facility.get("source_name") or "OpenStreetMap_GEM")

        return NormalizedEvent(
            event_id=fac_id,
            source_name=source_name,
            source_type="INDUSTRIAL_INFRASTRUCTURE_CATALOG",
            source_record_id=fac_id,
            event_class="PERSISTENT_INDUSTRIAL_HEAT",
            timestamp_start="2026-01-01T00:00:00Z",
            latitude=lat,
            longitude=lon,
            country="IND",
            description=f"Industrial facility: {raw_facility.get('name', 'Industrial Site')} ({raw_facility.get('facility_type', 'industrial')})",
            source_url="https://www.openstreetmap.org/",
            provenance_status=ProvenanceStatus.VERIFIED_EXTERNAL,
            confidence=1.0,
            metadata=raw_facility
        )

industrial_adapter = IndustrialAdapter()
