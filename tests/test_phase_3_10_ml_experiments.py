"""
Unit & Integration Test Suite for AstraFlare Phase 3.10 — ML Experimentation & Benchmarking.
Verifies data contracts, feature audit, split isolation, model training, 3-class predict_proba alignment,
probability calibration, abstention gate logic, artifact serialization, and reproducibility.
"""
import os
import sys
import json
import joblib
import pytest
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.data_loader import (
    MLDataLoader, MODEL_FEATURE_COLUMNS, NUMERICAL_FEATURES, CATEGORICAL_FEATURES,
    TARGET_CLASSES, ml_data_loader
)
from ml.feature_audit import FEATURE_AUDIT_CATALOG, run_feature_audit
from ml.splitter import (
    EventGroupSplitter, FacilityGroupSplitter, TemporalSplitter, verify_split_isolation
)
from ml.abstention import (
    apply_abstention_gate, evaluate_abstention_thresholds, compute_expected_calibration_error,
    LABEL_HUMAN_REVIEW
)
from ml.explainability import explainability_engine
from ml.error_analysis import analyze_model_errors
from ml.experiment_runner import MLExperimentRunner, ARTIFACTS_DIR


def test_ml_data_loader_contract():
    """Verifies that MLDataLoader preserves the Phase 3.10 data contract and zero missing values."""
    loader = MLDataLoader()
    dev_df = loader.load_development_dataset()

    assert not dev_df.empty, "Development dataset should not be empty"
    assert len(dev_df) >= 60000, f"Expected weak labels around 68k, got {len(dev_df)}"

    required_contract_cols = [
        "event_id", "label", "provenance_status", "ground_truth_flag",
        "verification_status", "data_source", "label_feature_overlap"
    ]
    for col in required_contract_cols:
        assert col in dev_df.columns, f"Missing required data contract column: {col}"

    for col in MODEL_FEATURE_COLUMNS:
        assert col in dev_df.columns, f"Missing model feature column: {col}"
        assert dev_df[col].isnull().sum() == 0, f"Feature {col} has missing values"


def test_feature_audit_no_future_leakage():
    """Verifies that no feature in the 17-feature set has future information dependence."""
    df_audit = run_feature_audit()
    assert len(df_audit) == 17, f"Expected 17 features in audit, got {len(df_audit)}"

    for fname, meta in FEATURE_AUDIT_CATALOG.items():
        assert meta["future_dependence"] is False, f"Feature {fname} flagged with future dependence!"
        assert meta["valid_for_inference"] is True, f"Feature {fname} invalid for inference"


def test_split_integrity_and_facility_isolation():
    """Verifies that splitters guarantee zero event, facility, and duplicate overlap."""
    loader = MLDataLoader()
    dev_df = loader.load_development_dataset()

    # EventGroupSplitter
    ev_splitter = EventGroupSplitter(train_ratio=0.8, random_state=42)
    tr_ev, te_ev = ev_splitter.split(dev_df)
    v_ev = verify_split_isolation(tr_ev, te_ev, "EventGroupSplitter")
    assert v_ev["event_overlap"] == 0, "EventGroupSplitter has event overlap"

    # FacilityGroupSplitter
    fac_splitter = FacilityGroupSplitter(train_ratio=0.8, random_state=42, stratify_by_label=True)
    tr_fac, te_fac = fac_splitter.split(dev_df)
    v_fac = verify_split_isolation(tr_fac, te_fac, "FacilityGroupSplitter")
    assert v_fac["event_overlap"] == 0, "FacilityGroupSplitter has event overlap"
    assert v_fac["facility_overlap"] == 0, "FacilityGroupSplitter has facility overlap"
    assert v_fac["is_leakage_free"] is True, "FacilityGroupSplitter failed leakage-free check"

    # TemporalSplitter
    temp_splitter = TemporalSplitter(train_ratio=0.8)
    tr_tp, te_tp = temp_splitter.split(dev_df)
    v_tp = verify_split_isolation(tr_tp, te_tp, "TemporalSplitter")
    assert v_tp["event_overlap"] == 0, "TemporalSplitter has event overlap"


def test_model_training_and_predict_proba_alignment():
    """Verifies that model training produces aligned 3-class probability matrices summing to 1.0."""
    runner = MLExperimentRunner(random_state=42)
    train_df, val_df, iso = runner.prepare_data()

    bench = runner.benchmark_models(train_df, val_df)
    assert "RandomForestClassifier" in bench
    rf_meta = bench["RandomForestClassifier"]
    assert rf_meta["status"] == "AVAILABLE"
    assert "macro_f1" in rf_meta

    y_prob = rf_meta["y_prob"]
    assert y_prob.shape == (len(val_df), 3), f"Expected shape ({len(val_df)}, 3), got {y_prob.shape}"

    row_sums = y_prob.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, rtol=1e-4, err_msg="Probabilities do not sum to 1.0")


def test_probability_calibration_ece():
    """Verifies that compute_expected_calibration_error returns valid ECE score."""
    y_true = np.array([0, 1, 2, 1, 2])
    y_prob = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.7, 0.2],
        [0.2, 0.2, 0.6],
        [0.0, 0.9, 0.1],
        [0.1, 0.1, 0.8]
    ])
    ece = compute_expected_calibration_error(y_true, y_prob)
    assert 0.0 <= ece <= 1.0, f"Invalid ECE score: {ece}"


def test_abstention_gate_logic():
    """Verifies post-classification abstention gate logic under 0.65 threshold."""
    # High confidence prediction
    high_probs = {
        "LIKELY_INDUSTRIAL_INCIDENT": 0.05,
        "PERSISTENT_INDUSTRIAL_HEAT": 0.85,
        "NATURAL_WILDLAND_FIRE": 0.10
    }
    res_high = apply_abstention_gate(high_probs, threshold=0.65)
    assert res_high["predicted_class"] == "PERSISTENT_INDUSTRIAL_HEAT"
    assert res_high["is_abstained"] is False

    # Low confidence prediction -> Abstain
    low_probs = {
        "LIKELY_INDUSTRIAL_INCIDENT": 0.30,
        "PERSISTENT_INDUSTRIAL_HEAT": 0.40,
        "NATURAL_WILDLAND_FIRE": 0.30
    }
    res_low = apply_abstention_gate(low_probs, threshold=0.65)
    assert res_low["predicted_class"] == LABEL_HUMAN_REVIEW
    assert res_low["is_abstained"] is True


def test_multi_threshold_tradeoffs():
    """Verifies evaluate_abstention_thresholds computes coverage vs accuracy trade-offs."""
    y_true = np.array([0, 1, 2, 1, 2])
    y_prob = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.7, 0.2],
        [0.2, 0.2, 0.6],
        [0.0, 0.9, 0.1],
        [0.1, 0.1, 0.8]
    ])
    thresholds = [0.50, 0.65, 0.85]
    res = evaluate_abstention_thresholds(y_true, y_prob, TARGET_CLASSES, thresholds=thresholds)

    assert len(res) == 3
    # Coverage should non-increase as threshold increases
    assert res[0]["coverage"] >= res[1]["coverage"] >= res[2]["coverage"]


def test_explainability_and_evidence():
    """Verifies that ExplainabilityEngine generates factual evidence statements."""
    event_row = {
        "industrial_distance_m": 850.0,
        "max_frp": 35.5,
        "observation_count": 4,
        "duration_hours": 12.5,
        "worldcover_class": "Built-up / Industrial (50)",
        "centroid_lat": 21.71,
        "centroid_lon": 72.58
    }
    probs = {"PERSISTENT_INDUSTRIAL_HEAT": 0.80, "NATURAL_WILDLAND_FIRE": 0.20}
    evidence = explainability_engine.generate_event_evidence(event_row, probs)

    assert len(evidence) >= 3
    statements = [e["statement"] for e in evidence]
    assert any("850.0m" in s for s in statements)
    assert any("35.50 MW" in s for s in statements)


def test_artifact_serialization_and_metadata():
    """Verifies that versioned model artifacts exist and can be loaded."""
    # Ensure pipeline has run
    runner = MLExperimentRunner(random_state=42)
    runner.execute_full_pipeline(nrows_unlabeled=100)

    expected_files = [
        "gbdt_model_v1.0.joblib",
        "calibrator_v1.0.joblib",
        "preprocessor_v1.0.joblib",
        "feature_schema_v1.0.json",
        "label_mapping_v1.0.json",
        "experiment_config_v1.0.json",
        "model_metadata_v1.0.json"
    ]

    for fname in expected_files:
        fpath = os.path.join(ARTIFACTS_DIR, fname)
        assert os.path.exists(fpath), f"Artifact missing: {fpath}"

    # Verify reloading model & preprocessor
    loaded_model = joblib.load(os.path.join(ARTIFACTS_DIR, "gbdt_model_v1.0.joblib"))
    loaded_prep = joblib.load(os.path.join(ARTIFACTS_DIR, "preprocessor_v1.0.joblib"))
    assert hasattr(loaded_model, "predict"), "Loaded model lacks predict method"
    assert hasattr(loaded_prep, "transform"), "Loaded preprocessor lacks transform method"


def test_reproducibility():
    """Verifies that running MLExperimentRunner produces identical benchmark scores."""
    runner1 = MLExperimentRunner(random_state=42)
    tr1, val1, _ = runner1.prepare_data()
    bench1 = runner1.benchmark_models(tr1, val1)

    runner2 = MLExperimentRunner(random_state=42)
    tr2, val2, _ = runner2.prepare_data()
    bench2 = runner2.benchmark_models(tr2, val2)

    rf_f1_1 = bench1["RandomForestClassifier"]["macro_f1"]
    rf_f1_2 = bench2["RandomForestClassifier"]["macro_f1"]
    assert rf_f1_1 == rf_f1_2, f"Non-reproducible macro F1: {rf_f1_1} != {rf_f1_2}"
