"""
Unit & Integration Test Suite for AstraFlare Phase 3.11 — Evidence-Based Thermal Anomaly Risk Engine.
Verifies score bounds, deterministic outputs, scenario behavior (A/B/C/D), conflict detection,
human review gates, data quality evaluation, traceability, edge cases, and artifact isolation.
"""
import os
import sys
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.risk_engine import (
    EvidenceRiskEngine, risk_engine, RiskInput, RiskAssessment, RiskEngineConfig
)
from backend.risk_engine.scoring import (
    score_thermal_intensity, score_historical_anomaly, score_industrial_proximity,
    score_industrial_density, score_natural_context, score_recurrence_and_persistence
)
from backend.risk_engine.quality import evaluate_data_quality
from backend.risk_engine.evidence import evidence_extractor


def test_config_weights_validation():
    """Verifies that RiskEngineConfig validates weight sum = 1.0."""
    cfg = RiskEngineConfig()
    assert cfg.validate_weights() is True, "Default config weights must sum to 1.0"

    invalid_cfg = RiskEngineConfig(thermal_weight=0.50, historical_weight=0.50)
    assert invalid_cfg.validate_weights() is False, "Invalid weight sum should fail validation"


def test_score_bounds_and_deterministic_output():
    """Verifies score bounds [0.0, 1.0] and deterministic reproducibility."""
    inp = RiskInput(
        event_id="evt_test_bounds_001",
        max_frp=65.0,
        industrial_distance_m=1200.0,
        industrial_site_count_1km=1,
        previous_detection_count=3,
        frp_anomaly_z=1.80,
        worldcover_class="Cropland / Agricultural (40)",
        observation_count=2,
        duration_hours=3.5
    )

    res1 = risk_engine.assess_event(inp)
    res2 = risk_engine.assess_event(inp)

    # Score bounds check
    assert 0.0 <= res1.overall_risk_score <= 1.0
    assert 0.0 <= res1.industrial_context_score <= 1.0
    assert 0.0 <= res1.natural_fire_context_score <= 1.0
    assert 0.0 <= res1.thermal_anomaly_score <= 1.0
    assert 0.0 <= res1.historical_anomaly_score <= 1.0
    assert 0.0 <= res1.recurrence_score <= 1.0
    assert 0.0 <= res1.persistence_score <= 1.0
    assert 0.0 <= res1.data_quality_score <= 1.0

    # Determinism check
    assert res1.overall_risk_score == res2.overall_risk_score
    assert res1.risk_level == res2.risk_level
    assert res1.investigation_priority == res2.investigation_priority
    assert res1.evidence_status == res2.evidence_status
    assert res1.human_review_required == res2.human_review_required


def test_scenario_a_potential_industrial_anomaly():
    """SCENARIO A: High FRP, close industrial proximity, low recurrence, high Z-score."""
    scen_a = RiskInput(
        event_id="evt_scen_a_001",
        max_frp=120.0,
        industrial_distance_m=450.0,
        industrial_site_count_1km=2,
        previous_detection_count=0,
        frp_anomaly_z=3.42,
        worldcover_class="Built-up / Industrial (50)",
        confidence_high_ratio=1.0,
        observation_count=3,
        duration_hours=2.5
    )
    res_a = risk_engine.assess_event(scen_a)

    assert res_a.evidence_status == "STRONG_INDUSTRIAL_CONTEXT"
    assert res_a.likely_context == "INDUSTRIAL_CONTEXT"
    assert res_a.investigation_priority == "HIGH"
    assert res_a.human_review_required is True
    assert len(res_a.human_review_reasons) >= 1


def test_scenario_b_persistent_industrial_heat():
    """SCENARIO B: Moderate FRP, very close to industrial facility, high recurrence, stable Z-score."""
    scen_b = RiskInput(
        event_id="evt_scen_b_001",
        max_frp=25.0,
        industrial_distance_m=180.0,
        industrial_site_count_250m=1,
        previous_detection_count=12,
        frp_anomaly_z=0.20,
        history_status="ADEQUATE_HISTORY",
        worldcover_class="Built-up / Industrial (50)",
        observation_count=4,
        duration_hours=18.0
    )
    res_b = risk_engine.assess_event(scen_b)

    assert res_b.evidence_status == "PERSISTENT_INDUSTRIAL_CONTEXT"
    assert res_b.likely_context == "PERSISTENT_INDUSTRIAL_CONTEXT"
    assert res_b.human_review_required is False


def test_scenario_c_natural_wildland_context():
    """SCENARIO C: High FRP, forest land cover, remote from industry (>5000m)."""
    scen_c = RiskInput(
        event_id="evt_scen_c_001",
        max_frp=85.0,
        industrial_distance_m=8500.0,
        previous_detection_count=1,
        frp_anomaly_z=2.10,
        worldcover_class="Tree Cover / Forest (10)",
        observation_count=2,
        duration_hours=4.0
    )
    res_c = risk_engine.assess_event(scen_c)

    assert res_c.evidence_status == "STRONG_NATURAL_CONTEXT"
    assert res_c.likely_context == "NATURAL_FIRE_CONTEXT"
    assert res_c.industrial_context_score < 0.10
    assert res_c.natural_fire_context_score >= 0.80


def test_scenario_d_conflicting_evidence():
    """SCENARIO D: High FRP, close to industry, forest land cover, conflicting behavior."""
    scen_d = RiskInput(
        event_id="evt_scen_d_001",
        max_frp=110.0,
        industrial_distance_m=450.0,
        industrial_site_count_1km=1,
        previous_detection_count=8,
        frp_anomaly_z=3.10,
        worldcover_class="Tree Cover / Forest (10)",
        observation_count=3,
        duration_hours=6.0
    )
    res_d = risk_engine.assess_event(scen_d)

    assert res_d.evidence_status == "CONFLICTING_EVIDENCE"
    assert res_d.likely_context == "AMBIGUOUS"
    assert res_d.human_review_required is True
    assert res_d.investigation_priority in ("HIGH", "URGENT")


def test_industrial_proximity_scoring_bounds():
    """Verifies distance bounds and score decay."""
    cfg = RiskEngineConfig()
    
    inp_250 = RiskInput(event_id="e1", industrial_distance_m=200.0)
    score_250, _ = score_industrial_proximity(inp_250, cfg)
    assert score_250 == 1.0

    inp_1000 = RiskInput(event_id="e2", industrial_distance_m=1000.0)
    score_1000, _ = score_industrial_proximity(inp_1000, cfg)
    assert score_1000 == 0.75

    inp_6000 = RiskInput(event_id="e3", industrial_distance_m=6000.0)
    score_6000, _ = score_industrial_proximity(inp_6000, cfg)
    assert score_6000 == 0.0


def test_no_history_does_not_zero_risk():
    """Verifies missing history baseline returns NO_PRIOR_HISTORY without setting risk to 0."""
    cfg = RiskEngineConfig()
    inp_nohist = RiskInput(
        event_id="e_nohist",
        max_frp=50.0,
        industrial_distance_m=500.0,
        previous_detection_count=0,
        frp_anomaly_z=None
    )
    score, status, ev = score_historical_anomaly(inp_nohist, cfg)
    assert status == "NO_PRIOR_HISTORY"
    assert score > 0.0, "Missing history should return a neutral baseline score, not 0"


def test_natural_context_land_cover():
    """Verifies land cover categorization across forest, shrubland, cropland, and built-up."""
    cfg = RiskEngineConfig()
    
    # Forest
    s_f, interp_f, _ = score_natural_context(RiskInput(event_id="f", worldcover_class="Tree Cover / Forest (10)"), cfg)
    assert interp_f == "TREE_COVER_FOREST"
    assert s_f == 1.0

    # Built-up
    s_b, interp_b, _ = score_natural_context(RiskInput(event_id="b", worldcover_class="Built-up / Industrial (50)"), cfg)
    assert interp_b == "BUILT_UP_INDUSTRIAL"
    assert s_b == 0.0


def test_data_quality_evaluation():
    """Verifies telemetry data quality evaluation status."""
    cfg = RiskEngineConfig()

    # High quality
    q_high, st_high, _ = evaluate_data_quality(RiskInput(event_id="q1", observation_count=4, satellite_count=2, confidence_high_ratio=1.0, history_status="ADEQUATE_HISTORY"), cfg)
    assert st_high == "HIGH"
    assert q_high >= 0.75

    # Singleton low quality
    q_low, st_low, _ = evaluate_data_quality(RiskInput(event_id="q2", observation_count=1, satellite_count=1, confidence_high_ratio=0.0, history_status="NO_PRIOR_HISTORY"), cfg)
    assert st_low in ("LOW", "INSUFFICIENT")


def test_explanation_traceability():
    """Verifies that every item in evidence list has complete traceability attributes."""
    inp = RiskInput(event_id="e_trace", max_frp=75.0, industrial_distance_m=800.0)
    res = risk_engine.assess_event(inp)

    assert len(res.evidence) >= 4
    for item in res.evidence:
        assert item.type != ""
        assert item.strength in ("LOW", "MODERATE", "HIGH", "VERY_HIGH", "INSUFFICIENT")
        assert item.input_feature != ""
        assert 0.0 <= item.normalization <= 1.0
        assert item.weight >= 0.0
        assert item.contribution == round(item.normalization * item.weight, 4)

    trace_records = evidence_extractor.format_traceability_table(res.evidence)
    assert len(trace_records) == len(res.evidence)
    assert "feature" in trace_records[0]
    assert "contribution" in trace_records[0]


def test_edge_cases_handling():
    """Verifies edge case handling (extreme FRP, 0 FRP, missing optional inputs) without crashing."""
    # 1. Extreme FRP (500 MW)
    res_ext = risk_engine.assess_event(RiskInput(event_id="e_ext", max_frp=500.0))
    assert res_ext.overall_risk_score <= 1.0

    # 2. Zero FRP (0 MW)
    res_zero = risk_engine.assess_event(RiskInput(event_id="e_zero", max_frp=0.0))
    assert res_zero.overall_risk_score >= 0.0

    # 3. Minimal fields
    res_min = risk_engine.assess_event(RiskInput(event_id="e_min"))
    assert res_min.overall_risk_score >= 0.0


def test_existing_ml_artifacts_untouched():
    """Verifies that Phase 3.10 ML artifacts remain untouched and versioned in ml/artifacts/."""
    artifacts_dir = os.path.join(REPO_ROOT, "ml", "artifacts")
    assert os.path.exists(os.path.join(artifacts_dir, "gbdt_model_v1.0.joblib"))
    assert os.path.exists(os.path.join(artifacts_dir, "calibrator_v1.0.joblib"))
    assert os.path.exists(os.path.join(artifacts_dir, "feature_schema_v1.0.json"))
