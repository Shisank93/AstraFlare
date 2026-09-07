"""
AstraFlare Standardized Production Prediction Contract & Inference Interface.
Provides single-point inference function predict_hotspot() for backend API consumption.
"""
import os
import sys
import pickle
import logging
from typing import Dict, Any, Optional

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from database.db import db_manager
from data_pipeline.feature_pipeline import feature_pipeline
from ml.train import MODEL_ARTIFACT_DIR, FEATURE_COLUMNS
from ml.abstention import apply_abstention_gate
from ml.explainability import ExplainabilityEngine

logger = logging.getLogger("astraflare.ml.inference")

_cached_artifact = None

def load_latest_model_artifact(model_version: str = "v1.0") -> Dict[str, Any]:
    global _cached_artifact
    if _cached_artifact is not None:
        return _cached_artifact

    model_path = os.path.join(MODEL_ARTIFACT_DIR, f"gbdt_model_{model_version}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Train model first.")

    with open(model_path, "rb") as f:
        _cached_artifact = pickle.load(f)
    return _cached_artifact

def predict_hotspot(
    hotspot_id: Optional[str] = None,
    feature_dict: Optional[Dict[str, Any]] = None,
    model_version: str = "v1.0"
) -> Dict[str, Any]:
    """
    Standardized Inference Function conforming to Prediction Output Contract.
    Input: hotspot_id OR feature_dict
    Output: Dictionary with predicted_class, probabilities, confidence, is_abstained, risk_score, evidence.
    """
    db_manager.connect()

    # 1. Fetch hotspot and run GIS feature pipeline if hotspot_id provided
    if hotspot_id and not feature_dict:
        records = db_manager.execute_query(f"SELECT * FROM hotspots WHERE id = '{hotspot_id}';")
        if not records:
            raise ValueError(f"Hotspot with ID '{hotspot_id}' not found in database.")
        hs = records[0]
        enriched = feature_pipeline.enrich_hotspot(hs, mock_fallback=False)
        
        feature_dict = {
            "hotspot_id": hs["id"],
            "acq_timestamp": hs["acq_timestamp"],
            "latitude": hs["latitude"],
            "longitude": hs["longitude"],
            "industrial_distance_m": float(enriched.get("industrial_distance") or 10000.0),
            "industrial_count_1km": int(enriched.get("industrial_count_1km") or 0),
            "industrial_count_5km": int(enriched.get("industrial_count_5km") or 0),
            "frp": float(hs.get("frp", 0.0)),
            "brightness": float(hs.get("brightness") or 300.0),
            "daynight_is_day": 1 if hs.get("daynight") == "D" else 0,
            "historical_count_30d": int(enriched.get("historical_count_30d") or 0),
            "historical_mean_frp": float(enriched.get("historical_mean_frp") or hs.get("frp", 0.0)),
            "frp_anomaly_zscore": float(enriched.get("frp_anomaly_score") or 0.0),
            "land_cover_code": int(enriched.get("land_cover_code") or 40),
            "land_cover_category": str(enriched.get("land_cover_category") or "unknown"),
            "is_built_up_land": 1 if enriched.get("land_cover_category") == "urban_industrial" else 0,
            "is_forest_land": 1 if enriched.get("land_cover_category") == "forest" else 0,
            "data_source": hs.get("data_source", "REAL")
        }

    if not feature_dict:
        raise ValueError("Either hotspot_id or feature_dict must be provided.")

    # 2. Load Calibrated GBDT Model
    artifact = load_latest_model_artifact(model_version=model_version)
    calibrated_model = artifact["calibrated_model"]
    classes = artifact["classes"]

    # 3. Model Inference
    row = [float(feature_dict.get(col, 0.0)) for col in FEATURE_COLUMNS]
    probs_array = calibrated_model.predict_proba([row])[0]

    probabilities = {cls_name: round(float(p), 4) for cls_name, p in zip(classes, probs_array)}

    # 4. Confidence & Abstention Gate
    abstention_meta = apply_abstention_gate(probabilities, threshold=settings.HUMAN_REVIEW_THRESHOLD)

    # 5. TreeSHAP & Operational Evidence Generation
    explainer = ExplainabilityEngine(model=calibrated_model, feature_columns=FEATURE_COLUMNS)
    evidence = explainer.generate_evidence_statements(
        feature_dict, abstention_meta["predicted_class"], probabilities
    )

    # 6. Database Audit Logging (Insert into predictions and evidence tables)
    target_hs_id = feature_dict.get("hotspot_id", "unknown")
    try:
        hs_check = db_manager.execute_query(
            "SELECT id FROM hotspots WHERE id = %s;" if db_manager.is_postgres else "SELECT id FROM hotspots WHERE id = ?;",
            (target_hs_id,)
        )
        if hs_check:
            if db_manager.is_postgres:
                query = """
                INSERT INTO predictions (hotspot_id, predicted_class, confidence, is_abstained, risk_score, prob_industrial_incident, prob_persistent_heat, prob_wildland_fire, model_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING prediction_id;
                """
                db_manager.execute_query(query, (
                    target_hs_id, abstention_meta["predicted_class"], abstention_meta["confidence"],
                    abstention_meta["is_abstained"], abstention_meta["risk_score"],
                    probabilities.get("LIKELY_INDUSTRIAL_INCIDENT", 0.0),
                    probabilities.get("PERSISTENT_INDUSTRIAL_HEAT", 0.0),
                    probabilities.get("NATURAL_WILDLAND_FIRE", 0.0),
                    model_version
                ))
            else:
                query = """
                INSERT INTO predictions (hotspot_id, predicted_class, confidence, is_abstained, risk_score, prob_industrial_incident, prob_persistent_heat, prob_wildland_fire, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                db_manager.execute_query(query, (
                    target_hs_id, abstention_meta["predicted_class"], abstention_meta["confidence"],
                    1 if abstention_meta["is_abstained"] else 0, abstention_meta["risk_score"],
                    probabilities.get("LIKELY_INDUSTRIAL_INCIDENT", 0.0),
                    probabilities.get("PERSISTENT_INDUSTRIAL_HEAT", 0.0),
                    probabilities.get("NATURAL_WILDLAND_FIRE", 0.0),
                    model_version
                ))
    except Exception as e:
        logger.warning(f"Database prediction logging exception: {e}")

    return {
        "hotspot_id": target_hs_id,
        "predicted_class": abstention_meta["predicted_class"],
        "probabilities": probabilities,
        "confidence": abstention_meta["confidence"],
        "is_abstained": abstention_meta["is_abstained"],
        "risk_score": abstention_meta["risk_score"],
        "model_version": model_version,
        "evidence": evidence,
        "data_quality": "COMPLETE"
    }

if __name__ == "__main__":
    print("Testing Production Inference Interface...")
    sample_feat = {
        "hotspot_id": "test_hs_001",
        "industrial_distance_m": 350.0,
        "industrial_count_1km": 2,
        "frp": 120.0,
        "frp_anomaly_zscore": 3.2,
        "historical_count_30d": 4,
        "land_cover_category": "urban_industrial"
    }
    pred = predict_hotspot(feature_dict=sample_feat)
    print(f"Prediction Output Contract: {pred}")
