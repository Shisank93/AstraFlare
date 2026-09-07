"""
AstraFlare Phase 3.10 — Calibration & Operational Uncertainty Abstention Engine.
Evaluates prediction probabilities against configurable HUMAN_REVIEW_THRESHOLD (0.65)
and computes calibration metrics (Brier Score, Expected Calibration Error).
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

LABEL_HUMAN_REVIEW = "Human Review Required"
DEFAULT_HUMAN_REVIEW_THRESHOLD = 0.65


def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) for multi-class predictions.
    ECE measures the difference between predicted confidence and actual accuracy across binned confidence intervals.
    """
    if len(y_true) == 0:
        return 0.0

    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    return float(round(ece, 4))


def apply_abstention_gate(
    probabilities: Dict[str, float],
    threshold: float = DEFAULT_HUMAN_REVIEW_THRESHOLD
) -> Dict[str, Any]:
    """
    Applies operational abstention gate to class prediction probabilities.
    
    Rule:
    - max_prob >= threshold => Return predicted class
    - max_prob < threshold  => Abstain, set prediction to 'Human Review Required'
    """
    if not probabilities:
        return {
            "predicted_class": LABEL_HUMAN_REVIEW,
            "confidence": 0.0,
            "is_abstained": True,
            "risk_score": 1.0,
            "reason": "Missing prediction probabilities."
        }

    top_class = max(probabilities, key=probabilities.get)
    max_prob = probabilities[top_class]

    # Calculate operational risk score (weighted by industrial incident/wildfire hazard)
    prob_incident = probabilities.get("LIKELY_INDUSTRIAL_INCIDENT", 0.0)
    prob_wildfire = probabilities.get("NATURAL_WILDLAND_FIRE", 0.0)
    risk_score = round(float(max(prob_incident * 1.0, prob_wildfire * 0.7)), 4)

    if max_prob >= threshold:
        return {
            "predicted_class": top_class,
            "confidence": round(float(max_prob), 4),
            "is_abstained": False,
            "risk_score": risk_score,
            "reason": f"High confidence prediction (P={max_prob:.4f} >= threshold {threshold:.2f})."
        }

    return {
        "predicted_class": LABEL_HUMAN_REVIEW,
        "confidence": round(float(max_prob), 4),
        "is_abstained": True,
        "risk_score": risk_score,
        "reason": f"Uncertainty abstention (P={max_prob:.4f} < threshold {threshold:.2f}). Routed for human review."
    }


def evaluate_abstention_thresholds(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_names: List[str],
    thresholds: List[float] = [0.50, 0.60, 0.65, 0.70, 0.80, 0.90]
) -> List[Dict[str, Any]]:
    """
    Evaluates coverage vs accuracy/confidence trade-offs across operational thresholds.
    """
    results = []
    n_total = len(y_true)
    if n_total == 0:
        return results

    confidences = np.max(y_prob, axis=1)
    preds = np.argmax(y_prob, axis=1)

    for th in thresholds:
        accepted_mask = confidences >= th
        abstained_mask = ~accepted_mask

        n_accepted = int(np.sum(accepted_mask))
        n_abstained = int(np.sum(abstained_mask))
        coverage = float(n_accepted / n_total)
        abstention_rate = float(n_abstained / n_total)

        if n_accepted > 0:
            accepted_acc = float(np.mean(preds[accepted_mask] == y_true[accepted_mask]))
        else:
            accepted_acc = 0.0

        if n_abstained > 0:
            abstained_acc = float(np.mean(preds[abstained_mask] == y_true[abstained_mask]))
        else:
            abstained_acc = 0.0

        results.append({
            "threshold": th,
            "total_events": n_total,
            "accepted_events": n_accepted,
            "abstained_events": n_abstained,
            "coverage": round(coverage, 4),
            "abstention_rate": round(abstention_rate, 4),
            "accepted_accuracy": round(accepted_acc, 4),
            "abstained_accuracy": round(abstained_acc, 4),
            "overall_accuracy": round(float(np.mean(preds == y_true)), 4)
        })

    return results
