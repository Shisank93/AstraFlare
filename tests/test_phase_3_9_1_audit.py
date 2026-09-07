"""
Unit and Integration Tests for Phase 3.9.1 Dataset Integrity Auditor.
"""
import pytest
import pandas as pd
from data_pipeline.sources.audit_dataset_integrity import DatasetIntegrityAuditor

def test_clustering_ratio_audit_logic():
    """Verify observation count distribution calculation."""
    auditor = DatasetIntegrityAuditor()
    df_sample = pd.DataFrame({
        "observation_count": [1, 1, 1, 2, 2, 3, 5, 8]
    })
    res = auditor.run_clustering_ratio_audit(df_sample)
    
    assert res["total_observations"] == 23
    assert res["total_events"] == 8
    assert res["events_1_obs"] == 3
    assert res["events_2_obs"] == 2
    assert res["events_3_obs"] == 1
    assert res["events_4_5_obs"] == 1
    assert res["events_6_10_obs"] == 1
    assert res["multi_observation_events"] == 5
    assert res["multi_observation_pct"] == 62.5

def test_feature_quality_audit_logic():
    """Verify missing count and feature range statistics calculation."""
    auditor = DatasetIntegrityAuditor()
    df_sample = pd.DataFrame({
        "event_id": ["e1", "e2"],
        "event_start": ["2024-01-01", "2024-01-02"],
        "max_frp": [10.5, 45.0],
        "duration_hours": [0.0, 1.5],
        "label": ["UNLABELED", "LIKELY_INDUSTRIAL_INCIDENT"],
        "label_source": ["NONE", "VERIFIED_EXTERNAL"],
        "provenance_status": ["UNLABELED", "VERIFIED_EXTERNAL"],
        "worldcover_class": ["Built-up", "Tree Cover"]
    })
    
    feat_df = auditor.run_feature_quality_audit(df_sample)
    assert "max_frp" in feat_df["feature_name"].values
    assert "duration_hours" in feat_df["feature_name"].values
    
    frp_row = feat_df[feat_df["feature_name"] == "max_frp"].iloc[0]
    assert frp_row["missing_count"] == 0
    assert frp_row["min"] == 10.5
    assert frp_row["max"] == 45.0
