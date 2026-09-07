"""
AstraFlare Phase 3.10 — Model Error Analysis & Systematic Failure Mode Audit Engine.
Inspects validation predictions against reference/ground-truth labels to isolate
misclassifications, confidence anomalies, and systematic boundary failure patterns.
"""
import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.data_loader import TARGET_CLASSES


def analyze_model_errors(
    val_df: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray, idx_to_class: Dict[int, str]
) -> Dict[str, Any]:
    """
    Analyzes misclassified and low-confidence validation samples.
    Identifies failure patterns (e.g. industrial flare vs incident, forest fire near industry).
    """
    errors = []
    correct_samples = []

    confidences = np.max(y_prob, axis=1)

    for idx, row in val_df.reset_index(drop=True).iterrows():
        t_cls = idx_to_class[y_true[idx]]
        p_cls = idx_to_class[y_pred[idx]]
        prob_dict = {idx_to_class[k]: float(round(y_prob[idx][k], 4)) for k in range(len(idx_to_class))}
        conf = float(confidences[idx])

        rec = {
            "event_id": str(row.get("event_id")),
            "true_class": t_cls,
            "predicted_class": p_cls,
            "max_confidence": round(conf, 4),
            "probabilities": prob_dict,
            "industrial_distance_m": float(row.get("industrial_distance_m", 0.0)),
            "max_frp": float(row.get("max_frp", 0.0)),
            "observation_count": int(row.get("observation_count", 1)),
            "worldcover_class": str(row.get("worldcover_class", "")),
            "provenance_status": str(row.get("provenance_status", ""))
        }

        if t_cls != p_cls:
            errors.append(rec)
        else:
            correct_samples.append(rec)

    # Classify failure modes
    failure_patterns = {
        "industrial_flare_misclassified_as_incident": 0,
        "agricultural_burn_misclassified_as_wildfire": 0,
        "wildfire_near_industry_misclassified_as_industrial": 0,
        "low_frp_singleton_excessive_confidence": 0,
        "other_misclassifications": 0
    }

    for err in errors:
        t_cls = err["true_class"]
        p_cls = err["predicted_class"]
        dist = err["industrial_distance_m"]
        frp = err["max_frp"]
        obs = err["observation_count"]

        if t_cls == "PERSISTENT_INDUSTRIAL_HEAT" and p_cls == "LIKELY_INDUSTRIAL_INCIDENT":
            failure_patterns["industrial_flare_misclassified_as_incident"] += 1
        elif t_cls == "NATURAL_WILDLAND_FIRE" and p_cls == "LIKELY_INDUSTRIAL_INCIDENT" and dist <= 5000:
            failure_patterns["wildfire_near_industry_misclassified_as_industrial"] += 1
        elif err["max_confidence"] >= 0.85 and obs == 1 and frp < 5.0:
            failure_patterns["low_frp_singleton_excessive_confidence"] += 1
        else:
            failure_patterns["other_misclassifications"] += 1

    return {
        "total_validation_events": len(val_df),
        "total_errors": len(errors),
        "error_rate": round(float(len(errors) / max(1, len(val_df))), 4),
        "failure_patterns": failure_patterns,
        "error_samples": errors[:20],  # Top 20 error details
    }
