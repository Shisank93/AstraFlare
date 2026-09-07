"""
AstraFlare Weak Supervision Labeling & Provenance Framework.
Generates weak supervision labels for REAL satellite thermal observations based on
defensible multi-variable rules and tracks label provenance.
"""
from typing import Dict, Any, Tuple

LABEL_LIKELY_INDUSTRIAL_INCIDENT = "LIKELY_INDUSTRIAL_INCIDENT"
LABEL_PERSISTENT_INDUSTRIAL_HEAT = "PERSISTENT_INDUSTRIAL_HEAT"
LABEL_NATURAL_WILDLAND_FIRE = "NATURAL_WILDLAND_FIRE"
LABEL_UNLABELED = "UNLABELED"

SOURCE_WEAK_RULE = "WEAK_RULE"
SOURCE_VERIFIED_EXTERNAL = "VERIFIED_EXTERNAL"
SOURCE_MANUAL_REVIEW = "MANUAL_REVIEW"

def construct_weak_label(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs a weak supervision label based on multi-variable spatial, historical, and land-cover evidence.
    Tracks label provenance (label, label_source, label_confidence, label_reason, label_version).
    """
    dist_m = features.get("industrial_distance_m", 10000.0)
    frp = features.get("frp", 0.0)
    zscore = features.get("frp_anomaly_zscore")
    count_30d = features.get("historical_count_30d", 0)
    land_cover_cat = features.get("land_cover_category", "unknown")

    # 1. LIKELY_INDUSTRIAL_INCIDENT:
    # High FRP anomaly (Z >= 2.0 or FRP >= 50 MW) near industrial facility (<= 2000m)
    if dist_m <= 2000.0 and (frp >= 50.0 or (zscore is not None and zscore >= 2.0)):
        reason = f"High energy thermal anomaly (FRP={frp:.1f}MW, Z={zscore if zscore is not None else 0.0:.2f}) within {dist_m:.0f}m of industrial site."
        return {
            "label": LABEL_LIKELY_INDUSTRIAL_INCIDENT,
            "label_source": SOURCE_WEAK_RULE,
            "label_confidence": 0.85,
            "label_reason": reason,
            "label_version": "v1.0"
        }

    # 2. PERSISTENT_INDUSTRIAL_HEAT:
    # Nearby industrial facility (<= 1500m) with low FRP anomaly (Z < 1.0) and high historical recurrence (>= 3)
    if dist_m <= 1500.0 and (zscore is None or zscore < 1.0) and count_30d >= 3:
        reason = f"Recurring thermal activity ({count_30d} historical detections in 30d) within {dist_m:.0f}m of industrial facility."
        return {
            "label": LABEL_PERSISTENT_INDUSTRIAL_HEAT,
            "label_source": SOURCE_WEAK_RULE,
            "label_confidence": 0.80,
            "label_reason": reason,
            "label_version": "v1.0"
        }

    # 3. NATURAL_WILDLAND_FIRE:
    # Non-industrial land cover (forest, vegetation, wetland) far from industrial facilities (> 5000m)
    if dist_m > 5000.0 and land_cover_cat in ("forest", "vegetation", "wetland", "tundra") and frp >= 8.0:
        reason = f"Thermal observation in {land_cover_cat} biome far from industrial infrastructure ({dist_m:.0f}m)."
        return {
            "label": LABEL_NATURAL_WILDLAND_FIRE,
            "label_source": SOURCE_WEAK_RULE,
            "label_confidence": 0.90,
            "label_reason": reason,
            "label_version": "v1.0"
        }

    # 4. UNLABELED / AMBIGUOUS
    return {
        "label": LABEL_UNLABELED,
        "label_source": SOURCE_WEAK_RULE,
        "label_confidence": 0.0,
        "label_reason": "Ambiguous contextual signals; fails weak supervision thresholds.",
        "label_version": "v1.0"
    }

def audit_labels(records: list) -> Dict[str, Any]:
    """
    Performs label-quality audit across dataset records.
    Calculates sample counts, percentages, and provenance breakdown.
    """
    counts = {
        LABEL_LIKELY_INDUSTRIAL_INCIDENT: 0,
        LABEL_PERSISTENT_INDUSTRIAL_HEAT: 0,
        LABEL_NATURAL_WILDLAND_FIRE: 0,
        LABEL_UNLABELED: 0
    }
    total = len(records)
    for r in records:
        lbl = r.get("label", LABEL_UNLABELED)
        counts[lbl] = counts.get(lbl, 0) + 1

    pcts = {k: round((v / total) * 100.0, 2) if total > 0 else 0.0 for k, v in counts.items()}
    return {
        "total_records": total,
        "counts": counts,
        "percentages": pcts,
        "labeled_total": total - counts[LABEL_UNLABELED]
    }
