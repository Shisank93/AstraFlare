"""
AstraFlare Circularity Auditor Module.
Audits whether ground truth or weak labels rely on features passed directly to the ML model.
Flags LABEL_FEATURE_OVERLAP = TRUE when label-feature circularity exists.
"""
from typing import Dict, Any, List, Tuple

class CircularityAuditor:
    def __init__(self):
        # Features passed as inputs to GBDT ML model
        self.ml_model_features = {
            "frp",
            "brightness",
            "industrial_distance_m",
            "industrial_count_1km",
            "industrial_count_5km",
            "land_cover_code",
            "historical_count_30d",
            "historical_mean_frp",
            "frp_anomaly_zscore",
            "daynight_is_day"
        }

        # Features used by weak-rule labeling logic
        self.rule_label_features = {
            "industrial_distance_m",
            "frp",
            "historical_count_30d",
            "daynight_is_day"
        }

    def audit_label_construction(self, label: str, rule_features_used: List[str]) -> Dict[str, Any]:
        """
        Audits a label for circular feature overlap.
        Returns circularity status, overlapping features, and scientific caveat explanation.
        """
        used_set = set(rule_features_used)
        overlap = list(used_set.intersection(self.ml_model_features))
        has_overlap = len(overlap) > 0

        return {
            "label": label,
            "label_feature_overlap": has_overlap,
            "overlapping_features": overlap,
            "evaluation_warning": (
                "LABEL_FEATURE_OVERLAP = TRUE: Weak rule labels were constructed using features "
                f"{overlap} that are also inputs to the ML model. Metrics evaluated on weak labels "
                "represent rule-reconstruction accuracy rather than independent scientific ground-truth generalization."
                if has_overlap else "No circularity detected. Label is fully independent."
            )
        }

circularity_auditor = CircularityAuditor()
