"""
AstraFlare Evidence Construction & Provenance Service.
Assembles structured evidence objects supporting ML classifications and human analysis.
"""
import logging
from typing import Dict, Any, List, Optional
from backend.app.services.hotspot_service import hotspot_service

logger = logging.getLogger("astraflare.backend.services.evidence")

class EvidenceService:
    def get_hotspot_evidence(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """Assembles multi-layer GIS and ground-truth evidence statements for target hotspot."""
        detail = hotspot_service.get_hotspot_detail(hotspot_id)
        if not detail:
            return None

        evidence_items = []

        # 1. Industrial Proximity Evidence
        dist_m = float(detail.get("industrial_distance_m") or 10000.0)
        fac_name = detail.get("nearest_industrial_name")
        if dist_m <= 1000.0:
            evidence_items.append({
                "evidence_type": "INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": f"{dist_m:.1f}m",
                "interpretation": f"High industrial co-location: Hotspot detected {dist_m:.0f}m from '{fac_name or 'industrial infrastructure'}'.",
                "source": "OSM_OVERPASS",
                "confidence": 0.95
            })
        elif dist_m <= 3000.0:
            evidence_items.append({
                "evidence_type": "INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": f"{dist_m:.1f}m",
                "interpretation": f"Moderate industrial proximity: Hotspot is within {dist_m:.0f}m of '{fac_name or 'industrial site'}'.",
                "source": "OSM_OVERPASS",
                "confidence": 0.80
            })
        else:
            evidence_items.append({
                "evidence_type": "INDUSTRIAL_PROXIMITY",
                "feature_name": "industrial_distance_m",
                "value": f"{dist_m:.1f}m",
                "interpretation": "Remote location: Hotspot is outside immediate industrial site buffers (>3km).",
                "source": "OSM_OVERPASS",
                "confidence": 0.90
            })

        # 2. Historical Recurrence Evidence
        hist_30d = int(detail.get("historical_count_30d") or 0)
        if hist_30d > 5:
            evidence_items.append({
                "evidence_type": "HISTORICAL_RECURRENCE",
                "feature_name": "historical_count_30d",
                "value": str(hist_30d),
                "interpretation": f"Persistent thermal hotspot: {hist_30d} historical observations detected within 1km over past 30 days.",
                "source": "POSTGIS_HOTSPOTS_ARCHIVE",
                "confidence": 0.92
            })
        else:
            evidence_items.append({
                "evidence_type": "HISTORICAL_RECURRENCE",
                "feature_name": "historical_count_30d",
                "value": str(hist_30d),
                "interpretation": f"Transient heat event: {hist_30d} prior detections within 1km over past 30 days.",
                "source": "POSTGIS_HOTSPOTS_ARCHIVE",
                "confidence": 0.85
            })

        # 3. FRP Anomaly Evidence
        frp = float(detail.get("frp", 0.0))
        zscore = detail.get("frp_anomaly_zscore")
        if zscore is not None and zscore > 2.0:
            evidence_items.append({
                "evidence_type": "FRP_ANOMALY",
                "feature_name": "frp_anomaly_zscore",
                "value": f"Z={zscore:.2f} (FRP={frp:.1f}MW)",
                "interpretation": f"Extreme thermal intensity anomaly: FRP of {frp:.1f} MW is +{zscore:.1f} standard deviations above baseline.",
                "source": "NASA_FIRMS_TELEM",
                "confidence": 0.90
            })
        else:
            evidence_items.append({
                "evidence_type": "FRP_ANOMALY",
                "feature_name": "frp",
                "value": f"{frp:.1f} MW",
                "interpretation": f"Thermal Radiative Power: Detected FRP is {frp:.1f} Megawatts.",
                "source": "NASA_FIRMS_TELEM",
                "confidence": 0.95
            })

        # 4. Land Cover Context Evidence
        lc_name = detail.get("land_cover_name", "Cropland")
        evidence_items.append({
            "evidence_type": "LAND_COVER",
            "feature_name": "land_cover_name",
            "value": str(lc_name),
            "interpretation": f"ESA WorldCover land classification at coordinates: '{lc_name}'.",
            "source": "ESA_WORLDCOVER_10M",
            "confidence": 0.88
        })

        # 5. External Corroboration / Label Provenance
        ver_status = detail.get("verification_status", "WEAK_RULE")
        evidence_items.append({
            "evidence_type": "EXTERNAL_CORROBORATION",
            "feature_name": "verification_status",
            "value": str(ver_status),
            "interpretation": f"Label provenance level: '{ver_status}'. Ground truth precedence rules applied.",
            "source": "ASTRAFLARE_PRECEDENCE_ENGINE",
            "confidence": 1.0 if ver_status == "VERIFIED_EXTERNAL" else 0.7
        })

        return {
            "hotspot_id": hotspot_id,
            "physical_event_id": detail.get("physical_event_id"),
            "verification_status": ver_status,
            "evidence_items": evidence_items
        }

evidence_service = EvidenceService()
