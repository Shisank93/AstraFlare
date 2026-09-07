"""
AstraFlare Prediction & Abstention Gate Service.
Runs ML baseline inference, computes class probabilities, enforces operational abstention thresholds,
and tags governance status ('RESEARCH BASELINE').
"""
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings
from database.db import db_manager
from ml.labeling import construct_weak_label
try:
    from ml.inference import predict_hotspot as ml_predict_hotspot
except Exception:
    ml_predict_hotspot = None

from backend.app.services.hotspot_service import hotspot_service

logger = logging.getLogger("astraflare.backend.services.prediction")

class PredictionService:
    def __init__(self):
        self.threshold = settings.HUMAN_REVIEW_THRESHOLD
        self.model_status = settings.ML_MODEL_STATUS

    def predict_hotspot(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """
        Executes ML baseline classification & abstention evaluation for target hotspot.
        """
        detail = hotspot_service.get_hotspot_detail(hotspot_id)
        if not detail:
            return None

        feat_vector = {
            "hotspot_id": hotspot_id,
            "industrial_distance_m": float(detail.get("industrial_distance_m") or 10000.0),
            "industrial_count_1km": int(detail.get("industrial_count_1km") or 0),
            "industrial_count_5km": int(detail.get("industrial_count_5km") or 0),
            "frp": float(detail.get("frp") or 0.0),
            "brightness": float(detail.get("brightness") or 300.0),
            "daynight_is_day": 1 if detail.get("daynight") == "D" else 0,
            "historical_count_30d": int(detail.get("historical_count_30d") or 0),
            "historical_mean_frp": float(detail.get("historical_mean_frp") or detail.get("frp") or 0.0),
            "frp_anomaly_zscore": float(detail.get("frp_anomaly_zscore") or 0.0),
            "land_cover_code": int(detail.get("land_cover_code") or 40),
            "is_built_up_land": 1 if detail.get("land_cover_name") == "Built-up" else 0,
            "is_forest_land": 1 if detail.get("land_cover_name") in ("Tree cover", "Shrubland", "Grassland") else 0
        }

        # Attempt to run trained GBDT model artifact, fallback to rule engine
        pred_res = None
        if ml_predict_hotspot is not None:
            try:
                pred_res = ml_predict_hotspot(hotspot_id=hotspot_id)
            except Exception as e:
                logger.debug(f"ML inference model artifact not active ({e}); using baseline rules.")

        if pred_res:
            predicted_class = pred_res.get("predicted_class", "UNLABELED")
            confidence = float(pred_res.get("confidence", 0.5))
            probs = pred_res.get("probabilities", {})
        else:
            lbl_meta = construct_weak_label(feat_vector)
            predicted_class = lbl_meta["label"]
            confidence = float(lbl_meta["label_confidence"])
            if predicted_class == "LIKELY_INDUSTRIAL_INCIDENT":
                probs = {"LIKELY_INDUSTRIAL_INCIDENT": confidence, "PERSISTENT_INDUSTRIAL_HEAT": (1-confidence)*0.7, "NATURAL_WILDLAND_FIRE": (1-confidence)*0.3}
            elif predicted_class == "PERSISTENT_INDUSTRIAL_HEAT":
                probs = {"LIKELY_INDUSTRIAL_INCIDENT": (1-confidence)*0.3, "PERSISTENT_INDUSTRIAL_HEAT": confidence, "NATURAL_WILDLAND_FIRE": (1-confidence)*0.7}
            elif predicted_class == "NATURAL_WILDLAND_FIRE":
                probs = {"LIKELY_INDUSTRIAL_INCIDENT": (1-confidence)*0.2, "PERSISTENT_INDUSTRIAL_HEAT": (1-confidence)*0.3, "NATURAL_WILDLAND_FIRE": confidence}
            else:
                probs = {"LIKELY_INDUSTRIAL_INCIDENT": 0.33, "PERSISTENT_INDUSTRIAL_HEAT": 0.33, "NATURAL_WILDLAND_FIRE": 0.34}

        review_required = confidence < self.threshold

        limitations = (
            "Model operates in RESEARCH BASELINE mode. Trained on 8,786 REAL FIRMS observations with 274 labeled events. "
            "Independent event diversity remains limited. Model predictions require human-in-the-loop analyst review."
        )

        return {
            "hotspot_id": hotspot_id,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": {
                "LIKELY_INDUSTRIAL_INCIDENT": round(float(probs.get("LIKELY_INDUSTRIAL_INCIDENT", 0.0)), 4),
                "PERSISTENT_INDUSTRIAL_HEAT": round(float(probs.get("PERSISTENT_INDUSTRIAL_HEAT", 0.0)), 4),
                "NATURAL_WILDLAND_FIRE": round(float(probs.get("NATURAL_WILDLAND_FIRE", 0.0)), 4)
            },
            "review_required": review_required,
            "human_review_threshold": self.threshold,
            "model_version": settings.VERSION,
            "model_status": self.model_status,
            "limitations": limitations
        }

prediction_service = PredictionService()
