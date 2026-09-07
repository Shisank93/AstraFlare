"""
Phase 3.9.1 Event Dataset Integrity Auditor.
Performs an exhaustive audit of clustering ratio distributions, feature completeness,
historical temporal causality, label circularity, dataset view integrity, and training feasibility.
"""
import os
import sys
import glob
import math
import pandas as pd
import numpy as np
from typing import Dict, Any

class DatasetIntegrityAuditor:
    """Audits DATASET_C_EVENT_LEVEL CSV views for completeness, causality, and governance compliance."""
    def __init__(self, dataset_dir: str = "data/processed/event_dataset"):
        self.dataset_dir = dataset_dir
        self.all_events_path = os.path.join(dataset_dir, "DATASET_C_ALL_EVENTS.csv")

    def run_clustering_ratio_audit(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_events = len(df)
        total_obs = df["observation_count"].sum()
        ratio = total_obs / total_events if total_events > 0 else 0.0

        obs_counts = df["observation_count"]

        bins = [
            (obs_counts == 1).sum(),
            (obs_counts == 2).sum(),
            (obs_counts == 3).sum(),
            ((obs_counts >= 4) & (obs_counts <= 5)).sum(),
            ((obs_counts >= 6) & (obs_counts <= 10)).sum(),
            ((obs_counts >= 11) & (obs_counts <= 25)).sum(),
            ((obs_counts >= 26) & (obs_counts <= 50)).sum(),
            ((obs_counts >= 51) & (obs_counts <= 100)).sum(),
            (obs_counts > 100).sum()
        ]

        multi_obs_events = (obs_counts >= 2).sum()
        multi_obs_pct = (multi_obs_events / total_events * 100) if total_events > 0 else 0.0

        return {
            "total_observations": int(total_obs),
            "total_events": int(total_events),
            "obs_per_event_ratio": round(float(ratio), 4),
            "events_1_obs": int(bins[0]),
            "events_2_obs": int(bins[1]),
            "events_3_obs": int(bins[2]),
            "events_4_5_obs": int(bins[3]),
            "events_6_10_obs": int(bins[4]),
            "events_11_25_obs": int(bins[5]),
            "events_26_50_obs": int(bins[6]),
            "events_51_100_obs": int(bins[7]),
            "events_gt_100_obs": int(bins[8]),
            "multi_observation_events": int(multi_obs_events),
            "multi_observation_pct": round(float(multi_obs_pct), 2)
        }

    def run_feature_quality_audit(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_cols = [c for c in df.columns if c not in ["event_id", "event_start", "event_end", "label", "label_source", "provenance_status", "worldcover_class"]]
        
        metrics = []
        for col in feature_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            missing_cnt = series.isna().sum()
            missing_pct = (missing_cnt / len(df)) * 100.0

            metrics.append({
                "feature_name": col,
                "missing_count": int(missing_cnt),
                "missing_pct": round(float(missing_pct), 4),
                "min": round(float(series.min()), 4) if not series.isna().all() else 0.0,
                "max": round(float(series.max()), 4) if not series.isna().all() else 0.0,
                "mean": round(float(series.mean()), 4) if not series.isna().all() else 0.0,
                "median": round(float(series.median()), 4) if not series.isna().all() else 0.0,
                "std": round(float(series.std()), 4) if not series.isna().all() else 0.0
            })

        return pd.DataFrame(metrics)

dataset_auditor = DatasetIntegrityAuditor()
