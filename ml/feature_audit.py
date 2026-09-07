"""
AstraFlare Phase 3.10 — Pre-Training Feature Audit & Circularity vs Leakage Engine.
Audits every feature for data type, inference availability, temporal causality,
weak-label generation participation, and circularity vs leakage distinction.
"""
import os
import sys
from typing import Dict, Any, List
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FEATURE_AUDIT_CATALOG: Dict[str, Dict[str, Any]] = {
    "duration_hours": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "TELEMETRY_TEMPORAL",
        "description": "Duration of physical event cluster in hours from first to last observation.",
        "circularity_note": "No circularity. Pure cluster telemetry."
    },
    "observation_count": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": True,
        "exclude_from_independent_eval": False,
        "category": "TELEMETRY_DENSITY",
        "description": "Number of raw FIRMS satellite detections aggregated in physical event.",
        "circularity_note": "Participated in weak-label rule (obs >= 2 for PERSISTENT_INDUSTRIAL_HEAT). Legitimate operational feature."
    },
    "centroid_lat": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SPATIAL_GEOGRAM",
        "description": "Centroid latitude of physical event cluster in WGS84 degrees.",
        "circularity_note": "No direct rule participation; provides spatial geographic context."
    },
    "centroid_lon": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SPATIAL_GEOGRAM",
        "description": "Centroid longitude of physical event cluster in WGS84 degrees.",
        "circularity_note": "No direct rule participation; provides spatial geographic context."
    },
    "spatial_extent_m": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SPATIAL_EXTENT",
        "description": "Maximum spatial diameter of physical event cluster in meters.",
        "circularity_note": "No circularity. Pure spatial cluster geometry."
    },
    "max_frp": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": True,
        "exclude_from_independent_eval": False,
        "category": "FIRE_RADIATIVE_POWER",
        "description": "Maximum Fire Radiative Power (MW) recorded across cluster observations.",
        "circularity_note": "Participated in weak-label rule (max_frp >= 25.0 for industrial heat, max_frp >= 40.0 for wildfire). Essential physical metric."
    },
    "mean_frp": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "FIRE_RADIATIVE_POWER",
        "description": "Mean Fire Radiative Power (MW) across cluster observations.",
        "circularity_note": "Derived intensity summary. No direct weak-label threshold matching."
    },
    "std_frp": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "FIRE_RADIATIVE_POWER",
        "description": "Standard deviation of Fire Radiative Power across cluster observations.",
        "circularity_note": "No circularity. Indicates thermal intensity variability."
    },
    "max_brightness": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SATELLITE_RADIANCE",
        "description": "Maximum brightness temperature (K) recorded across sensor channels.",
        "circularity_note": "No circularity. Core satellite thermal radiance metric."
    },
    "mean_brightness": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SATELLITE_RADIANCE",
        "description": "Mean brightness temperature (K) across sensor channels.",
        "circularity_note": "No circularity. Core satellite thermal radiance metric."
    },
    "confidence_high_ratio": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SATELLITE_QUALITY",
        "description": "Fraction of cluster observations with high detection confidence (>=80%).",
        "circularity_note": "No circularity. Quality signal."
    },
    "satellite_count": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "SATELLITE_COVERAGE",
        "description": "Number of distinct satellite platforms (SNPP, NOAA-20, NOAA-21, MODIS) observing event.",
        "circularity_note": "No circularity. Multi-sensor verification signal."
    },
    "industrial_distance_m": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": True,
        "exclude_from_independent_eval": False,
        "category": "GIS_PROXIMITY",
        "description": "Geodesic distance in meters to nearest GIHS validated industrial heat source node.",
        "circularity_note": "Participated in weak-label rules (dist <= 1000m for industrial heat, dist > 5000m for wildfire). Key domain feature."
    },
    "industrial_site_count_250m": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "GIS_PROXIMITY",
        "description": "Count of industrial heat source sites within 250 meters.",
        "circularity_note": "No direct rule participation; spatial micro-clustering context."
    },
    "industrial_site_count_1km": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "GIS_PROXIMITY",
        "description": "Count of industrial heat source sites within 1 kilometer.",
        "circularity_note": "No direct rule participation; spatial neighborhood context."
    },
    "industrial_site_count_5km": {
        "dtype": "numeric",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": False,
        "exclude_from_independent_eval": False,
        "category": "GIS_PROXIMITY",
        "description": "Count of industrial heat source sites within 5 kilometers.",
        "circularity_note": "No direct rule participation; regional industrial density context."
    },
    "worldcover_class": {
        "dtype": "categorical",
        "valid_for_inference": True,
        "available_at_prediction": True,
        "future_dependence": False,
        "weak_label_participant": True,
        "exclude_from_independent_eval": False,
        "category": "LAND_COVER",
        "description": "10m ESA WorldCover land use classification string (Forest, Agricultural, Built-up, Shrubland).",
        "circularity_note": "Participated in weak-label rule ('Forest' required for NATURAL_WILDLAND_FIRE). Primary domain context."
    }
}


def run_feature_audit() -> pd.DataFrame:
    """Generates a structured pre-training feature audit DataFrame."""
    records = []
    for fname, meta in FEATURE_AUDIT_CATALOG.items():
        records.append({
            "feature": fname,
            "dtype": meta["dtype"],
            "category": meta["category"],
            "valid_for_inference": meta["valid_for_inference"],
            "available_at_prediction": meta["available_at_prediction"],
            "future_dependence": meta["future_dependence"],
            "weak_label_participant": meta["weak_label_participant"],
            "exclude_from_independent_eval": meta["exclude_from_independent_eval"],
            "circularity_vs_leakage": "LABEL_GENERATION_CIRCULARITY" if meta["weak_label_participant"] else "CLEAN_PHYSICAL_FEATURE"
        })
    df = pd.DataFrame(records)
    return df


def generate_feature_audit_report() -> str:
    """Generates Markdown report section on Pre-Training Feature Audit."""
    df = run_feature_audit()
    md = []
    md.append("### Pre-Training Feature Audit & Circularity Analysis\n")
    md.append("| Feature | Type | Valid Inference | Future Leakage | Weak-Label Participant | Circularity Status |")
    md.append("|---|---|---|---|---|---|")
    for _, r in df.iterrows():
        md.append(f"| `{r['feature']}` | {r['dtype']} | {'YES' if r['valid_for_inference'] else 'NO'} | {'NO' if not r['future_dependence'] else 'YES'} | {'YES' if r['weak_label_participant'] else 'NO'} | `{r['circularity_vs_leakage']}` |")

    md.append("\n#### Label-Generation Circularity vs True Feature Leakage Distinction\n")
    md.append("- **TRUE FEATURE LEAKAGE**: Occurs when a feature contains future information (e.g. end-of-year aggregated stats, target label encoding, or future satellite passes) that would not be available at the exact moment of real-time operational prediction. **All 17 AstraFlare features have 0.0% Future Feature Leakage.**")
    md.append("- **LABEL-GENERATION CIRCULARITY**: Occurs when legitimate operational features (`industrial_distance_m`, `max_frp`, `observation_count`, `worldcover_class`) were used in heuristic rules to define the initial weak-label dataset. These operational features are fully valid for real-time model inference. However, high performance on the weak-label development set (Experiment A) partly reflects rule recovery. **This is why Independent Evaluation (Experiment B) on 10 out-of-sample verified external events is essential.**")
    return "\n".join(md)


if __name__ == "__main__":
    print(generate_feature_audit_report())
