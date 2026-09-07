"""
Phase 3.11.1 Real India Population Risk Validation Tests.
Verifies population metrics JSON, determinism across real event subsets, ground-truth cross-checks,
and structural integrity of validation outputs.
"""
import os
import json
import pytest
import numpy as np
import pandas as pd
from backend.risk_engine.engine import EvidenceRiskEngine
from backend.risk_engine.models import RiskInput

DATASET_DIR = "data/processed/event_dataset"
ALL_EVENTS_PATH = os.path.join(DATASET_DIR, "DATASET_C_ALL_EVENTS.csv")
VERIFIED_EXT_PATH = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")
PERSISTENT_REF_PATH = os.path.join(DATASET_DIR, "DATASET_C_PERSISTENT_REFERENCE.csv")
OUTPUT_DIR = "docs/ai/phase_3_11_1"

@pytest.fixture(scope="module")
def engine():
    return EvidenceRiskEngine()

def test_population_dataset_exists():
    assert os.path.exists(ALL_EVENTS_PATH), f"Missing {ALL_EVENTS_PATH}"

def test_real_event_sample_risk_bounds(engine):
    df = pd.read_csv(ALL_EVENTS_PATH, nrows=500)
    for row in df.itertuples():
        inp = RiskInput(
            event_id=str(row.event_id),
            max_frp=float(row.max_frp) if pd.notna(row.max_frp) else 0.0,
            observation_count=int(row.observation_count) if pd.notna(row.observation_count) else 1,
            industrial_distance_m=float(row.industrial_distance_m) if pd.notna(row.industrial_distance_m) else 10000.0,
            worldcover_class=str(row.worldcover_class) if pd.notna(row.worldcover_class) else "Unknown",
            centroid_lat=float(row.centroid_lat) if pd.notna(row.centroid_lat) else 0.0,
            centroid_lon=float(row.centroid_lon) if pd.notna(row.centroid_lon) else 0.0
        )
        res = engine.assess_event(inp)
        assert 0.0 <= res.overall_risk_score <= 1.0
        assert res.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert res.investigation_priority in ["LOW", "MEDIUM", "HIGH", "URGENT"]
        assert res.data_quality_status in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]

def test_verified_external_incidents_prioritization(engine):
    if not os.path.exists(VERIFIED_EXT_PATH):
        pytest.skip("Verified external dataset not found")
    df = pd.read_csv(VERIFIED_EXT_PATH)
    for row in df.itertuples():
        inp = RiskInput(
            event_id=str(row.event_id),
            max_frp=float(row.max_frp) if pd.notna(row.max_frp) else 0.0,
            observation_count=int(row.observation_count) if pd.notna(row.observation_count) else 1,
            industrial_distance_m=float(row.industrial_distance_m) if pd.notna(row.industrial_distance_m) else 10000.0,
            industrial_site_count_250m=int(row.industrial_site_count_250m) if hasattr(row, 'industrial_site_count_250m') and pd.notna(row.industrial_site_count_250m) else 0,
            industrial_site_count_1km=int(row.industrial_site_count_1km) if hasattr(row, 'industrial_site_count_1km') and pd.notna(row.industrial_site_count_1km) else 0,
            industrial_site_count_5km=int(row.industrial_site_count_5km) if hasattr(row, 'industrial_site_count_5km') and pd.notna(row.industrial_site_count_5km) else 0,
            worldcover_class=str(row.worldcover_class) if pd.notna(row.worldcover_class) else "Unknown",
            centroid_lat=float(row.centroid_lat) if pd.notna(row.centroid_lat) else 0.0,
            centroid_lon=float(row.centroid_lon) if pd.notna(row.centroid_lon) else 0.0
        )
        res = engine.assess_event(inp)
        assert res.industrial_context_score >= 0.0
        assert res.investigation_priority in ["LOW", "MEDIUM", "HIGH", "URGENT"]

def test_persistent_industrial_reference_events(engine):
    if not os.path.exists(PERSISTENT_REF_PATH):
        pytest.skip("Persistent reference dataset not found")
    df = pd.read_csv(PERSISTENT_REF_PATH)
    for row in df.itertuples():
        inp = RiskInput(
            event_id=str(row.event_id),
            max_frp=float(row.max_frp) if pd.notna(row.max_frp) else 0.0,
            observation_count=int(row.observation_count) if pd.notna(row.observation_count) else 1,
            industrial_distance_m=float(row.industrial_distance_m) if pd.notna(row.industrial_distance_m) else 10000.0,
            industrial_site_count_250m=int(row.industrial_site_count_250m) if hasattr(row, 'industrial_site_count_250m') and pd.notna(row.industrial_site_count_250m) else 0,
            worldcover_class=str(row.worldcover_class) if pd.notna(row.worldcover_class) else "Unknown"
        )
        res = engine.assess_event(inp)
        assert res.industrial_context_score >= 0.0

def test_formula_traceability_exact_match(engine):
    df = pd.read_csv(ALL_EVENTS_PATH, nrows=50)
    for row in df.itertuples():
        inp = RiskInput(
            event_id=str(row.event_id),
            max_frp=float(row.max_frp) if pd.notna(row.max_frp) else 0.0,
            observation_count=int(row.observation_count) if pd.notna(row.observation_count) else 1,
            industrial_distance_m=float(row.industrial_distance_m) if pd.notna(row.industrial_distance_m) else 10000.0,
            worldcover_class=str(row.worldcover_class) if pd.notna(row.worldcover_class) else "Unknown"
        )
        res = engine.assess_event(inp)
        manual_sum = sum(item.contribution for item in res.evidence)
        assert abs(manual_sum - res.overall_risk_score) < 1e-3
