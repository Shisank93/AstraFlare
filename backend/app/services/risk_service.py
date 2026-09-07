"""
AstraFlare Operational Risk Prioritization Service.
Calculates multi-factor operational risk score [0.0, 1.0] and risk level (HIGH, MEDIUM, LOW).
"""
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.services.hotspot_service import hotspot_service

logger = logging.getLogger("astraflare.backend.services.risk")

class RiskService:
    def __init__(self):
        self.high_threshold = settings.RISK_HIGH_THRESHOLD

    def calculate_risk(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """Calculates composite operational risk prioritization score and contributing factor breakdown."""
        detail = hotspot_service.get_hotspot_detail(hotspot_id)
        if not detail:
            return None

        frp = float(detail.get("frp", 0.0))
        dist_m = float(detail.get("industrial_distance_m") or 10000.0)
        hist_30d = int(detail.get("historical_count_30d") or 0)
        zscore = float(detail.get("frp_anomaly_zscore") or 0.0)

        # 1. Industrial Proximity Factor (Weight = 0.40)
        if dist_m <= 500.0:
            prox_score = 1.0
        elif dist_m <= 1000.0:
            prox_score = 0.85
        elif dist_m <= 3000.0:
            prox_score = 0.50
        elif dist_m <= 5000.0:
            prox_score = 0.25
        else:
            prox_score = 0.0

        # 2. FRP Intensity Factor (Weight = 0.35)
        frp_score = min(1.0, max(0.0, frp / 150.0))

        # 3. FRP Anomaly Factor (Weight = 0.15)
        anomaly_score = min(1.0, max(0.0, zscore / 3.0)) if zscore > 0 else 0.0

        # 4. Historical Recurrence Factor (Weight = 0.10)
        rec_score = min(1.0, hist_30d / 10.0)

        # Weighted Composite Score
        composite_score = (prox_score * 0.40) + (frp_score * 0.35) + (anomaly_score * 0.15) + (rec_score * 0.10)
        composite_score = round(min(1.0, max(0.0, composite_score)), 4)

        if composite_score >= self.high_threshold:
            risk_level = "HIGH"
        elif composite_score >= 0.45:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        factors = [
            {
                "factor": "INDUSTRIAL_PROXIMITY",
                "weight": 0.40,
                "score": round(prox_score, 2),
                "description": f"Proximity to industrial infrastructure: {dist_m:.0f} meters."
            },
            {
                "factor": "FRP_SEVERITY",
                "weight": 0.35,
                "score": round(frp_score, 2),
                "description": f"Fire Radiative Power: {frp:.1f} MW."
            },
            {
                "factor": "FRP_ANOMALY",
                "weight": 0.15,
                "score": round(anomaly_score, 2),
                "description": f"Intensity Z-score: +{zscore:.2f}."
            },
            {
                "factor": "HISTORICAL_RECURRENCE",
                "weight": 0.10,
                "score": round(rec_score, 2),
                "description": f"30-day historical count within 1km: {hist_30d} detections."
            }
        ]

        explanation = (
            f"Hotspot assigned {risk_level} operational priority (score: {composite_score:.2f}) "
            f"based on industrial proximity ({dist_m:.0f}m) and thermal intensity ({frp:.1f} MW)."
        )

        limitations = (
            "Operational risk score is a deterministic heuristic for analyst alert prioritization. "
            "It is NOT a scientifically validated probabilistic hazard risk index."
        )

        return {
            "hotspot_id": hotspot_id,
            "risk_score": composite_score,
            "risk_level": risk_level,
            "contributing_factors": factors,
            "explanation": explanation,
            "limitations": limitations
        }

risk_service = RiskService()
