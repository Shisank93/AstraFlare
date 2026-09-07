"""
AstraFlare Phase 3 Automated ML Pipeline Test Suite.
Tests REAL-only data governance, weak supervision labeling, label provenance,
leakage safeguards, spatial-temporal splits, model training, calibration,
abstention gate logic, SHAP explainability, and prediction output contracts.
"""
import os
import sys
import pytest
from database.db import db_manager
from ml.labeling import construct_weak_label, audit_labels, LABEL_LIKELY_INDUSTRIAL_INCIDENT, LABEL_PERSISTENT_INDUSTRIAL_HEAT, LABEL_NATURAL_WILDLAND_FIRE, LABEL_UNLABELED
from ml.dataset_generator import generate_ml_dataset
from ml.splitter import TemporalSplitter, SpatialGroupKFold
from ml.train import ModelTrainer
from ml.abstention import apply_abstention_gate, LABEL_HUMAN_REVIEW
from ml.explainability import ExplainabilityEngine
from ml.inference import predict_hotspot

def test_real_only_data_governance():
    db_manager.connect()
    # Test dataset generator filters for REAL data
    res = generate_ml_dataset(limit=50, allow_non_real=False)
    assert "dataset" in res
    for item in res["dataset"]:
        assert item.get("data_source") == "REAL"

def test_weak_label_construction_and_provenance():
    # 1. Industrial Incident
    feat_incident = {
        "industrial_distance_m": 350.0,
        "frp": 120.0,
        "frp_anomaly_zscore": 3.5,
        "historical_count_30d": 2,
        "land_cover_category": "urban_industrial"
    }
    lbl_meta_1 = construct_weak_label(feat_incident)
    assert lbl_meta_1["label"] == LABEL_LIKELY_INDUSTRIAL_INCIDENT
    assert lbl_meta_1["label_source"] == "WEAK_RULE"
    assert lbl_meta_1["label_confidence"] == 0.85
    assert len(lbl_meta_1["label_reason"]) > 10

    # 2. Persistent Industrial Heat
    feat_heat = {
        "industrial_distance_m": 400.0,
        "frp": 15.0,
        "frp_anomaly_zscore": 0.2,
        "historical_count_30d": 6,
        "land_cover_category": "urban_industrial"
    }
    lbl_meta_2 = construct_weak_label(feat_heat)
    assert lbl_meta_2["label"] == LABEL_PERSISTENT_INDUSTRIAL_HEAT
    assert lbl_meta_2["label_confidence"] == 0.80

    # 3. Natural Wildland Fire
    feat_wildfire = {
        "industrial_distance_m": 8500.0,
        "frp": 45.0,
        "frp_anomaly_zscore": 1.2,
        "historical_count_30d": 0,
        "land_cover_category": "forest"
    }
    lbl_meta_3 = construct_weak_label(feat_wildfire)
    assert lbl_meta_3["label"] == LABEL_NATURAL_WILDLAND_FIRE
    assert lbl_meta_3["label_confidence"] == 0.90

def test_spatial_temporal_splitting():
    mock_ds = [
        {"acq_timestamp": f"2026-09-0{i}T12:00:00Z", "latitude": 20.0 + i*0.1, "longitude": 70.0 + i*0.1}
        for i in range(1, 11)
    ]
    # Temporal Split
    t_splitter = TemporalSplitter(train_ratio=0.8)
    train_set, test_set = t_splitter.split(mock_ds)
    assert len(train_set) == 8
    assert len(test_set) == 2
    assert train_set[-1]["acq_timestamp"] < test_set[0]["acq_timestamp"]

    # Spatial Grid Split
    s_splitter = SpatialGroupKFold(grid_size_deg=0.5, n_splits=2)
    splits = list(s_splitter.split(mock_ds))
    assert len(splits) == 2
    s_train, s_val = splits[0]
    assert len(s_train) + len(s_val) == len(mock_ds)

def test_model_training_and_calibration():
    trainer = ModelTrainer(model_version="v1.0")
    meta = trainer.train_and_evaluate(limit=2000)
    assert "macro_f1" in meta
    assert "confusion_matrix" in meta
    assert meta["training_samples"] > 0

def test_abstention_gate():
    # High confidence => automated prediction
    high_probs = {
        "LIKELY_INDUSTRIAL_INCIDENT": 0.82,
        "PERSISTENT_INDUSTRIAL_HEAT": 0.10,
        "NATURAL_WILDLAND_FIRE": 0.08
    }
    gate_high = apply_abstention_gate(high_probs, threshold=0.65)
    assert gate_high["predicted_class"] == "LIKELY_INDUSTRIAL_INCIDENT"
    assert gate_high["is_abstained"] is False
    assert gate_high["confidence"] == 0.82

    # Low confidence => abstention flag
    low_probs = {
        "LIKELY_INDUSTRIAL_INCIDENT": 0.45,
        "PERSISTENT_INDUSTRIAL_HEAT": 0.35,
        "NATURAL_WILDLAND_FIRE": 0.20
    }
    gate_low = apply_abstention_gate(low_probs, threshold=0.65)
    assert gate_low["predicted_class"] == LABEL_HUMAN_REVIEW
    assert gate_low["is_abstained"] is True
    assert gate_low["confidence"] == 0.45

def test_explainability_and_evidence():
    feat_dict = {
        "industrial_distance_m": 450.0,
        "frp": 115.0,
        "frp_anomaly_zscore": 3.42,
        "land_cover_category": "urban_industrial"
    }
    explainer = ExplainabilityEngine()
    ev = explainer.generate_evidence_statements(
        feat_dict, "LIKELY_INDUSTRIAL_INCIDENT", {"LIKELY_INDUSTRIAL_INCIDENT": 0.85}
    )
    assert len(ev) >= 2
    types = [e["evidence_type"] for e in ev]
    assert "GIS_OPERATIONAL" in types
    assert "ML_EXPLANATION" in types

def test_production_inference_interface():
    sample_feat = {
        "hotspot_id": "test_hs_inference_001",
        "industrial_distance_m": 350.0,
        "industrial_count_1km": 2,
        "frp": 120.0,
        "frp_anomaly_zscore": 3.2,
        "historical_count_30d": 4,
        "land_cover_category": "urban_industrial"
    }
    pred = predict_hotspot(feature_dict=sample_feat)
    assert "predicted_class" in pred
    assert "probabilities" in pred
    assert "confidence" in pred
    assert "is_abstained" in pred
    assert "risk_score" in pred
    assert "evidence" in pred
    assert pred["data_quality"] == "COMPLETE"
