"""
AstraFlare Phase 3.10 — ML Data Loader & Data Contract Verification Engine.
Loads event-level datasets from data/processed/event_dataset/ without modifying
upstream raw data, clustering logic, historical features, or label definitions.
"""
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

# Repository root pathing
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DEFAULT_DATASET_DIR = os.path.join(REPO_ROOT, "data", "processed", "event_dataset")

# 17 Event-Level Model Feature Columns
MODEL_FEATURE_COLUMNS = [
    "duration_hours",
    "observation_count",
    "centroid_lat",
    "centroid_lon",
    "spatial_extent_m",
    "max_frp",
    "mean_frp",
    "std_frp",
    "max_brightness",
    "mean_brightness",
    "confidence_high_ratio",
    "satellite_count",
    "industrial_distance_m",
    "industrial_site_count_250m",
    "industrial_site_count_1km",
    "industrial_site_count_5km",
    "worldcover_class"
]

NUMERICAL_FEATURES = [
    "duration_hours",
    "observation_count",
    "centroid_lat",
    "centroid_lon",
    "spatial_extent_m",
    "max_frp",
    "mean_frp",
    "std_frp",
    "max_brightness",
    "mean_brightness",
    "confidence_high_ratio",
    "satellite_count",
    "industrial_distance_m",
    "industrial_site_count_250m",
    "industrial_site_count_1km",
    "industrial_site_count_5km"
]

CATEGORICAL_FEATURES = ["worldcover_class"]

METADATA_COLUMNS = [
    "event_id",
    "event_start",
    "event_end",
    "label",
    "label_source",
    "label_confidence",
    "provenance_status",
    "label_feature_overlap"
]

TARGET_CLASSES = [
    "LIKELY_INDUSTRIAL_INCIDENT",
    "PERSISTENT_INDUSTRIAL_HEAT",
    "NATURAL_WILDLAND_FIRE"
]


class MLDataLoader:
    """ML Data Loading layer adhering strictly to the AstraFlare Phase 3.10 Data Contract."""

    def __init__(self, dataset_dir: str = DEFAULT_DATASET_DIR):
        self.dataset_dir = dataset_dir

    def get_filepath(self, view_name: str) -> str:
        fpath = os.path.join(self.dataset_dir, f"{view_name}.csv")
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Dataset view '{view_name}' not found at: {fpath}")
        return fpath

    def load_all_events(self, nrows: int = None) -> pd.DataFrame:
        """Loads complete event population (4,310,499 events)."""
        fpath = self.get_filepath("DATASET_C_ALL_EVENTS")
        return self._load_and_enrich_contract(fpath, nrows=nrows)

    def load_weak_labels(self, nrows: int = None) -> pd.DataFrame:
        """Loads weak-label development dataset (68,675 events)."""
        fpath = self.get_filepath("DATASET_C_WEAK_LABELS")
        return self._load_and_enrich_contract(fpath, nrows=nrows)

    def load_verified_external(self) -> pd.DataFrame:
        """Loads independent external ground-truth events (10 events)."""
        fpath = self.get_filepath("DATASET_C_VERIFIED_EXTERNAL")
        return self._load_and_enrich_contract(fpath)

    def load_persistent_reference(self) -> pd.DataFrame:
        """Loads persistent industrial heat reference events (16 events)."""
        fpath = self.get_filepath("DATASET_C_PERSISTENT_REFERENCE")
        return self._load_and_enrich_contract(fpath)

    def load_wildfire_reference(self, nrows: int = None) -> pd.DataFrame:
        """Loads official wildfire reference events (68,659 events)."""
        fpath = self.get_filepath("DATASET_C_WILDFIRE_REFERENCE")
        return self._load_and_enrich_contract(fpath, nrows=nrows)

    def load_development_dataset(self) -> pd.DataFrame:
        """
        Combines development labeled sets:
        - DATASET_C_WEAK_LABELS (68,675 events)
        Note: Independent ground-truth events (VERIFIED_EXTERNAL) are EXCLUDED
        from development model fitting to serve strictly as out-of-sample evaluation.
        """
        fpath_weak = self.get_filepath("DATASET_C_WEAK_LABELS")
        df_weak = self._load_and_enrich_contract(fpath_weak)
        # Exclude any VERIFIED_EXTERNAL if present
        dev_df = df_weak[df_weak["provenance_status"] != "VERIFIED_EXTERNAL"].copy()
        return dev_df

    def _load_and_enrich_contract(self, fpath: str, nrows: int = None) -> pd.DataFrame:
        df = pd.read_csv(fpath, nrows=nrows)
        
        # Preserve required data contract fields
        df["ground_truth_flag"] = df["provenance_status"] == "VERIFIED_EXTERNAL"
        df["verification_status"] = df["label_source"]
        df["data_source"] = "REAL_NASA_FIRMS_ARCHIVE"
        df["label_provenance"] = df["provenance_status"]

        # Ensure correct missing value handling
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("Unknown")

        return df

    def audit_dataset_contract(self, df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        """Audits dataset shape, labels, missing values, dtypes, and ranges."""
        total_count = len(df)
        unlabeled_count = int((df["label"] == "UNLABELED").sum())
        labeled_count = total_count - unlabeled_count

        class_counts = df["label"].value_counts().to_dict()
        prov_counts = df["provenance_status"].value_counts().to_dict()
        source_counts = df["label_source"].value_counts().to_dict()

        missing_values = df[MODEL_FEATURE_COLUMNS].isnull().sum().to_dict()

        feature_ranges = {}
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                feature_ranges[col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(round(df[col].mean(), 4)),
                    "std": float(round(df[col].std(), 4))
                }

        categorical_categories = {}
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                categorical_categories[col] = df[col].value_counts().to_dict()

        return {
            "dataset_name": dataset_name,
            "total_event_count": total_count,
            "labeled_count": labeled_count,
            "unlabeled_count": unlabeled_count,
            "class_counts": class_counts,
            "provenance_counts": prov_counts,
            "source_counts": source_counts,
            "missing_values_sum": int(sum(missing_values.values())),
            "missing_values_per_feature": missing_values,
            "feature_ranges": feature_ranges,
            "categorical_categories": categorical_categories
        }


ml_data_loader = MLDataLoader()

if __name__ == "__main__":
    print("Testing MLDataLoader...")
    loader = MLDataLoader()
    dev_df = loader.load_development_dataset()
    audit = loader.audit_dataset_contract(dev_df, "Development Dataset")
    print(f"Total Dev Events: {audit['total_event_count']}")
    print(f"Class Counts: {audit['class_counts']}")
    print(f"Provenance Counts: {audit['provenance_counts']}")
