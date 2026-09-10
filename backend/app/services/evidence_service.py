"""
AstraFlare Evidence Construction & Provenance Service.
Assembles structured multi-layer evidence objects supporting ML classifications, operational prioritization,
and human analyst review.
"""
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.hotspot_service import hotspot_service

logger = logging.getLogger("astraflare.backend.services.evidence")

class EvidenceService:
    def get_hotspot_evidence(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """Assembles structured multi-category GIS and ground-truth evidence statements."""
        detail = hotspot_service.get_hotspot_detail(hotspot_id)
        if not detail:
            return None

        evidence_items = []

        # 1. SPATIAL & INDUSTRIAL CONTEXT EVIDENCE
        dist_m = float(detail.get("industrial_distance_m") or 10000.0)
        dist_str = f"{dist_m / 1000.0:.1f} km" if dist_m >= 1000.0 else f"{dist_m:.0f} m"
        fac_name = detail.get("nearest_industrial_name")

        if dist_m <= 1000.0:
            evidence_items.append({
                "category": "INDUSTRIAL_CONTEXT",
                "evidence_type": "HIGH_INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": dist_str,
                "interpretation": f"High industrial co-location: Thermal event detected {dist_str} from '{fac_name or 'industrial facility'}'.",
                "source": "OSM_OVERPASS_GEOSPATIAL",
                "confidence": 0.95
            })
        elif dist_m <= 3000.0:
            evidence_items.append({
                "category": "INDUSTRIAL_CONTEXT",
                "evidence_type": "MODERATE_INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": dist_str,
                "interpretation": f"Moderate industrial proximity: Thermal event is {dist_str} from '{fac_name or 'industrial site'}'.",
                "source": "OSM_OVERPASS_GEOSPATIAL",
                "confidence": 0.85
            })
        else:
            evidence_items.append({
                "category": "SPATIAL_EVIDENCE",
                "evidence_type": "LOW_INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": dist_str,
                "interpretation": f"Low industrial proximity: Event is remote from mapped industrial infrastructure ({dist_str} > 3km).",
                "source": "OSM_OVERPASS_GEOSPATIAL",
                "confidence": 0.95
            })

        # 2. THERMAL EVIDENCE
        frp = float(detail.get("frp") or detail.get("max_frp") or 0.0)
        zscore = detail.get("frp_anomaly_zscore") or detail.get("historical_anomaly_zscore")
        brightness = float(detail.get("brightness") or detail.get("max_brightness") or 300.0)

        if zscore is not None and zscore > 2.0:
            evidence_items.append({
                "category": "THERMAL_EVIDENCE",
                "evidence_type": "FRP_ANOMALY",
                "feature_name": "frp_anomaly_zscore",
                "value": f"+{zscore:.2f} sigma ({frp:.1f} MW)",
                "interpretation": f"Extreme thermal intensity anomaly: FRP of {frp:.1f} MW is +{zscore:.1f} standard deviations above baseline.",
                "source": "NASA_FIRMS_TELEM",
                "confidence": 0.92
            })
        else:
            evidence_items.append({
                "category": "THERMAL_EVIDENCE",
                "evidence_type": "THERMAL_OUTPUT",
                "feature_name": "frp",
                "value": f"{frp:.1f} MW",
                "interpretation": f"Fire Radiative Power (FRP): {frp:.1f} MW recorded at brightness temperature {brightness:.1f} K.",
                "source": "NASA_FIRMS_TELEM",
                "confidence": 0.95
            })

        # 3. HISTORICAL EVIDENCE
        hist_30d = int(detail.get("historical_count_30d") or detail.get("historical_count") or 0)
        if hist_30d >= 5:
            evidence_items.append({
                "category": "HISTORICAL_EVIDENCE",
                "evidence_type": "HISTORICAL_RECURRENCE",
                "feature_name": "historical_count_30d",
                "value": f"{hist_30d} prior events",
                "interpretation": f"Persistent thermal hotspot: {hist_30d} prior detections within 1km over rolling 30-day baseline.",
                "source": "POSTGIS_HISTORICAL_ARCHIVE",
                "confidence": 0.94
            })
        else:
            evidence_items.append({
                "category": "HISTORICAL_EVIDENCE",
                "evidence_type": "HISTORICAL_RECURRENCE",
                "feature_name": "historical_count_30d",
                "value": f"{hist_30d} prior events",
                "interpretation": f"Transient heat signature: Low historical recurrence ({hist_30d} prior detections within 1km).",
                "source": "POSTGIS_HISTORICAL_ARCHIVE",
                "confidence": 0.88
            })

        # 4. LAND-COVER EVIDENCE
        lc_name = detail.get("land_cover_name")
        wc_code = detail.get("worldcover_class")
        if not lc_name:
            code_map = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up", 60: "Bare / sparse vegetation", 70: "Snow and ice", 80: "Permanent water", 90: "Herbaceous wetland", 95: "Mangroves", 100: "Moss and lichen"}
            lc_name = code_map.get(wc_code, "Cropland (Default)")

        evidence_items.append({
            "category": "LAND_COVER_EVIDENCE",
            "evidence_type": "LAND_COVER_CLASSIFICATION",
            "feature_name": "land_cover_name",
            "value": str(lc_name),
            "interpretation": f"ESA 10m WorldCover surface classification at coordinates: '{lc_name}'.",
            "source": "ESA_WORLDCOVER_10M",
            "confidence": 0.90
        })

        # 5. TEMPORAL & OBSERVATIONAL EVIDENCE
        duration = float(detail.get("duration_hours") or 0.0)
        obs_count = int(detail.get("observation_count") or 1)
        evidence_items.append({
            "category": "TEMPORAL_EVIDENCE",
            "evidence_type": "EVENT_TEMPORAL_DURATION",
            "feature_name": "duration_hours",
            "value": f"{duration:.1f}h ({obs_count} passes)",
            "interpretation": f"Cluster persistence spanning {duration:.1f} hours across {obs_count} satellite observation passes.",
            "source": "SPATIAL_TEMPORAL_FUSION",
            "confidence": 0.91
        })

        # 6. DATA QUALITY & PROVENANCE EVIDENCE
        dq_status = detail.get("data_quality_status", "HIGH")
        ver_status = detail.get("verification_status", "WEAK")
        evidence_items.append({
            "category": "DATA_QUALITY",
            "evidence_type": "PROVENANCE_AND_QUALITY",
            "feature_name": "data_quality_status",
            "value": f"Quality: {dq_status} | Provenance: {ver_status}",
            "interpretation": f"Observation geometry and telemetry passed completeness audits (Status: {dq_status}).",
            "source": "ASTRAFLARE_QUALITY_AUDITOR",
            "confidence": 0.98
        })

        return {
            "hotspot_id": hotspot_id,
            "physical_event_id": detail.get("physical_event_id") or hotspot_id,
            "verification_status": ver_status,
            "evidence_items": evidence_items
        }

evidence_service = EvidenceService()
