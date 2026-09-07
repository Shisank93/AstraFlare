"""
Government & Official Indian Disaster/Industrial Safety Incident Adapter.
Parses official registries (PESO, FSI, NDMA, State Disaster Management Authorities) into NormalizedEvent schema.
"""
from typing import Dict, Any
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus

class GovernmentAdapter:
    def normalize_incident(self, raw_incident: Dict[str, Any]) -> NormalizedEvent:
        lat = float(raw_incident.get("latitude", 0.0))
        lon = float(raw_incident.get("longitude", 0.0))
        inc_id = str(raw_incident.get("incident_id") or raw_incident.get("record_id") or f"gov_{lat}_{lon}")

        source_name = str(raw_incident.get("source_name") or "PESO_Government_Registry")
        inc_class = str(raw_incident.get("event_class") or "LIKELY_INDUSTRIAL_INCIDENT")

        return NormalizedEvent(
            event_id=inc_id,
            source_name=source_name,
            source_type="GOVERNMENT_OFFICIAL_REGISTRY",
            source_record_id=inc_id,
            event_class=inc_class,
            timestamp_start=str(raw_incident.get("event_timestamp") or raw_incident.get("incident_date")),
            timestamp_end=str(raw_incident.get("event_timestamp") or raw_incident.get("incident_date")),
            latitude=lat,
            longitude=lon,
            country="IND",
            admin_region=raw_incident.get("state") or raw_incident.get("district"),
            description=str(raw_incident.get("description") or raw_incident.get("accident_details") or "Official government incident record"),
            source_url=raw_incident.get("source_url") or "https://peso.gov.in/",
            provenance_status=ProvenanceStatus.VERIFIED_EXTERNAL,
            confidence=0.95,
            metadata=raw_incident
        )

government_adapter = GovernmentAdapter()
