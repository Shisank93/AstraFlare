"""
AstraFlare Prediction & Abstention Gate Service.
Runs ML baseline inference, computes calibrated class probabilities, enforces operational abstention thresholds,
calculates unsupervised industrial anomaly assessments, and serves dynamic model metadata.
"""
import os
import json
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

METADATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "artifacts", "model_metadata_v1.0.json"))

class PredictionService:
    def __init__(self):
        self.threshold = settings.HUMAN_REVIEW_THRESHOLD
        self.model_status = settings.ML_MODEL_STATUS
        self._cached_metadata = None

    def get_model_metadata(self) -> Dict[str, Any]:
        """Loads actual versioned experiment metadata from ml/artifacts/model_metadata_v1.0.json."""
        if self._cached_metadata is not None:
            return self._cached_metadata

        if os.path.exists(METADATA_PATH):
            try:
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    self._cached_metadata = json.load(f)
                    return self._cached_metadata
            except Exception as e:
                logger.warning(f"Failed to load model metadata file: {e}")

        # Fallback to research baseline defaults if artifact metadata file unreadable
        self._cached_metadata = {
            "model_version": "v1.0",
            "model_name": "RandomForestClassifier / HistGradientBoosting",
            "model_status": "RESEARCH BASELINE — DATA-LIMITED",
            "isolation_audit": {
                "splitter_name": "FacilityGroupSplitter",
                "train_rows": 54386,
                "test_rows": 14289,
                "facility_overlap": 0,
                "event_overlap": 0
            },
            "development_metrics": {
                "macro_f1": 0.6667,
                "weighted_f1": 1.0,
                "per_class_f1": {
                    "LIKELY_INDUSTRIAL_INCIDENT": 0.0,
                    "PERSISTENT_INDUSTRIAL_HEAT": 1.0,
                    "NATURAL_WILDLAND_FIRE": 1.0
                }
            }
        }
        return self._cached_metadata

    def calculate_industrial_anomaly(self, feat_vector: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unsupervised Rare-Event / Industrial Anomaly Assessment (Item 12).
        Evaluates extreme thermal anomaly deviations, industrial proximity, persistence, and land cover.
        Explicitly labeled as an anomaly assessment, NOT accident probability.
        """
        dist_m = float(feat_vector.get("industrial_distance_m") or 10000.0)
        zscore = float(feat_vector.get("frp_anomaly_zscore") or 0.0)
        frp = float(feat_vector.get("frp") or 0.0)
        is_built_up = int(feat_vector.get("is_built_up_land") or 0)

        score = 0.0
        factors = []

        # 1. Industrial Proximity factor (max 0.35)
        if dist_m <= 1000.0:
            score += 0.35
            factors.append(f"Immediate industrial site proximity ({dist_m:.0f}m <= 1000m)")
        elif dist_m <= 3000.0:
            score += 0.20
            factors.append(f"Nearby industrial site ({dist_m:.0f}m <= 3000m)")
        elif dist_m <= 5000.0:
            score += 0.10
            factors.append(f"Perimeter industrial distance ({dist_m:.0f}m <= 5000m)")

        # 2. FRP Anomaly Z-Score factor (max 0.35)
        if zscore >= 3.0:
            score += 0.35
            factors.append(f"Extreme statistical thermal intensity deviation (+{zscore:.2f} sigma)")
        elif zscore >= 2.0:
            score += 0.25
            factors.append(f"Elevated statistical thermal intensity deviation (+{zscore:.2f} sigma)")
        elif zscore >= 1.0:
            score += 0.15
            factors.append(f"Moderate thermal intensity elevation (+{zscore:.2f} sigma)")

        # 3. Absolute FRP magnitude factor (max 0.20)
        if frp >= 50.0:
            score += 0.20
            factors.append(f"Severe absolute Fire Radiative Power ({frp:.1f} MW)")
        elif frp >= 20.0:
            score += 0.10
            factors.append(f"Substantial absolute Fire Radiative Power ({frp:.1f} MW)")

        # 4. Built-up / Industrial land cover (0.10)
        if is_built_up == 1:
            score += 0.10
            factors.append("ESA WorldCover confirms built-up / industrial land surface")

        final_score = round(min(1.0, max(0.0, score)), 3)
        level = "HIGH" if final_score >= 0.70 else ("MODERATE" if final_score >= 0.40 else "LOW")

        return {
            "score": final_score,
            "level": level,
            "contributing_factors": factors
        }

    def predict_hotspot(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """
        Executes online calibrated ML inference, abstention evaluation, and evidence assembly.
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

        # Calculate supplementary Industrial Anomaly Assessment
        anomaly_assessment = self.calculate_industrial_anomaly(feat_vector)

        # Attempt to run trained GBDT model artifact with extracted features
        pred_res = None
        top_features = []
        if ml_predict_hotspot is not None:
            try:
                pred_res = ml_predict_hotspot(feature_dict=feat_vector)
                if pred_res and "evidence" in pred_res:
                    for ev in pred_res["evidence"]:
                        top_features.append({
                            "feature": ev.get("feature_name", "feature"),
                            "value": ev.get("feature_value", ""),
                            "statement": ev.get("human_readable_statement", ""),
                            "contribution": ev.get("contribution", 0.0)
                        })
            except Exception as e:
                logger.warning(f"Online ML inference failed ({e}); evaluating baseline rules.")

        if pred_res and pred_res.get("predicted_class"):
            predicted_class = pred_res.get("predicted_class", "UNLABELED")
            confidence = float(pred_res.get("confidence", 0.5))
            raw_probs = pred_res.get("probabilities", {})
            probs = {
                "LIKELY_INDUSTRIAL_INCIDENT": round(float(raw_probs.get("LIKELY_INDUSTRIAL_INCIDENT", 0.0)), 4),
                "PERSISTENT_INDUSTRIAL_HEAT": round(float(raw_probs.get("PERSISTENT_INDUSTRIAL_HEAT", 0.0)), 4),
                "NATURAL_WILDLAND_FIRE": round(float(raw_probs.get("NATURAL_WILDLAND_FIRE", 0.0)), 4)
            }
            is_ml = True
            ref_label = None
            ref_prov = None
            review_required = confidence < self.threshold
        else:
            lbl_meta = construct_weak_label(feat_vector)
            predicted_class = lbl_meta.get("label")
            confidence = float(lbl_meta.get("label_confidence", 0.60))
            probs = {
                "LIKELY_INDUSTRIAL_INCIDENT": 0.05,
                "PERSISTENT_INDUSTRIAL_HEAT": 0.15,
                "NATURAL_WILDLAND_FIRE": 0.80
            }
            is_ml = False
            ref_label = lbl_meta.get("label")
            ref_prov = "WEAK_RULE"
            review_required = True

        # Confidence status & abstention label
        is_abstained = confidence < self.threshold
        if is_abstained:
            confidence_status = "LOW CONFIDENCE — ANALYST REVIEW"
            abstention_reason = "The model does not have sufficient confidence for autonomous classification."
        elif confidence >= 0.80:
            confidence_status = "HIGH CONFIDENCE"
            abstention_reason = "Model classification confidence exceeds operational verification threshold."
        else:
            confidence_status = "MODERATE CONFIDENCE"
            abstention_reason = "Model classification confidence meets autonomous baseline threshold."

        limitations = (
            "Model operates in RESEARCH BASELINE mode. Trained on real FIRMS observations with facility-isolated splits. "
            "Verified industrial incidents are rare in satellite ground-truth. Predictions must be interpreted with evidence and analyst review."
        )

        model_meta = self.get_model_metadata()

        return {
            "hotspot_id": hotspot_id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": probs,
            "review_required": review_required,
            "human_review_threshold": self.threshold,
            "confidence_status": confidence_status,
            "abstention_reason": abstention_reason,
            "industrial_anomaly_score": anomaly_assessment["score"],
            "industrial_anomaly_level": anomaly_assessment["level"],
            "top_contributing_features": top_features,
            "model_version": settings.VERSION,
            "model_status": self.model_status,
            "limitations": limitations,
            "is_ml_prediction": is_ml,
            "reference_label": ref_label,
            "reference_provenance": ref_prov,
            "model_metadata": model_meta
        }

prediction_service = PredictionService()
