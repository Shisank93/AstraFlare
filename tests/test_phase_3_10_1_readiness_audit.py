"""
Unit & Integration Test Suite for AstraFlare Phase 3.10.1 — Label Coverage & Model Readiness Audit.
Verifies dataset isolation mechanisms, independent test event verification, persistent heat reference audits,
wildfire reference counts, zero train/test contamination, and readiness matrix assertions.
"""
import os
import sys
import pandas as pd
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.data_loader import MLDataLoader
from ml.splitter import get_facility_group_id

DATASET_DIR = os.path.join(REPO_ROOT, "data", "processed", "event_dataset")


def test_industrial_incident_pipeline_isolation():
    """Verifies that LIKELY_INDUSTRIAL_INCIDENT events are isolated from DATASET_C_WEAK_LABELS."""
    p_all = os.path.join(DATASET_DIR, "DATASET_C_ALL_EVENTS.csv")
    p_weak = os.path.join(DATASET_DIR, "DATASET_C_WEAK_LABELS.csv")
    p_ver = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")

    df_all = pd.read_csv(p_all)
    df_weak = pd.read_csv(p_weak)
    df_ver = pd.read_csv(p_ver)

    # 1. Total verified external count in ALL EVENTS
    incidents_all = df_all[df_all["label"] == "LIKELY_INDUSTRIAL_INCIDENT"]
    assert len(incidents_all) == 10, f"Expected 10 verified external incidents, got {len(incidents_all)}"

    # 2. label_feature_overlap should be False for all 10 verified incidents
    assert (incidents_all["label_feature_overlap"] == False).all(), "Verified incidents must have label_feature_overlap=False"

    # 3. DATASET_C_WEAK_LABELS must contain 0 LIKELY_INDUSTRIAL_INCIDENT rows
    weak_incidents = df_weak[df_weak["label"] == "LIKELY_INDUSTRIAL_INCIDENT"]
    assert len(weak_incidents) == 0, f"DATASET_C_WEAK_LABELS should have 0 industrial incidents, got {len(weak_incidents)}"

    # 4. DATASET_C_VERIFIED_EXTERNAL must contain all 10 rows
    assert len(df_ver) == 10, f"DATASET_C_VERIFIED_EXTERNAL should contain 10 rows, got {len(df_ver)}"


def test_independent_event_verification():
    """Verifies that the 10 independent test events represent 6 unique physical incidents across 2 complexes."""
    p_ver = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")
    df_ver = pd.read_csv(p_ver)

    assert len(df_ver) == 10

    # Vizag vs Dahej coordinate breakdown
    vizag_events = df_ver[df_ver["centroid_lat"] < 20.0]
    dahej_events = df_ver[df_ver["centroid_lat"] > 20.0]

    assert len(vizag_events) == 4, f"Expected 4 Vizag events, got {len(vizag_events)}"
    assert len(dahej_events) == 6, f"Expected 6 Dahej events, got {len(dahej_events)}"

    # Unique dates/passes
    unique_dates = df_ver.apply(lambda r: f"{r['centroid_lat']:.2f}_{r['event_start'][:10]}", axis=1).nunique()
    assert unique_dates == 6, f"Expected 6 unique physical incident dates, got {unique_dates}"


def test_persistent_heat_reference_audit():
    """Verifies that 16 persistent heat reference events belong to Hazira industrial complex."""
    p_pers = os.path.join(DATASET_DIR, "DATASET_C_PERSISTENT_REFERENCE.csv")
    df_pers = pd.read_csv(p_pers)

    assert len(df_pers) == 16, f"Expected 16 persistent heat events, got {len(df_pers)}"
    # All 16 must be located in Hazira (lat ~21.11, lon ~72.63)
    assert (df_pers["centroid_lat"] > 21.0).all() and (df_pers["centroid_lat"] < 21.2).all()
    assert (df_pers["industrial_distance_m"] <= 1000.0).all()


def test_wildfire_reference_audit():
    """Verifies that 68,659 wildfire reference events represent separate physical clusters."""
    p_wild = os.path.join(DATASET_DIR, "DATASET_C_WILDFIRE_REFERENCE.csv")
    df_wild = pd.read_csv(p_wild)

    assert len(df_wild) == 68659, f"Expected 68,659 wildfire events, got {len(df_wild)}"
    assert df_wild["observation_count"].sum() == 93566, f"Expected 93,566 raw observations, got {df_wild['observation_count'].sum()}"
    assert df_wild["event_id"].nunique() == 68659


def test_zero_train_test_contamination():
    """Verifies zero event and zero facility group overlap between weak training set and independent test set."""
    p_weak = os.path.join(DATASET_DIR, "DATASET_C_WEAK_LABELS.csv")
    p_ver = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")

    df_weak = pd.read_csv(p_weak)
    df_ver = pd.read_csv(p_ver)

    # Event ID Overlap
    tr_events = set(df_weak["event_id"])
    te_events = set(df_ver["event_id"])
    assert len(tr_events.intersection(te_events)) == 0, "Found event ID overlap between train and test"

    # Facility Group Overlap
    tr_facs = set(df_weak.apply(get_facility_group_id, axis=1))
    te_facs = set(df_ver.apply(get_facility_group_id, axis=1))
    assert len(tr_facs.intersection(te_facs)) == 0, "Found facility group overlap between train and test"


def test_readiness_audit_report_exists():
    """Verifies that PHASE_3_10_1_LABEL_COVERAGE_MODEL_READINESS_AUDIT.md report is present."""
    p_report = os.path.join(REPO_ROOT, "docs", "ai", "PHASE_3_10_1_LABEL_COVERAGE_MODEL_READINESS_AUDIT.md")
    assert os.path.exists(p_report), "Audit report missing!"

    with open(p_report, "r", encoding="utf-8") as f:
        text = f.read()

    assert "RESEARCH BASELINE — NOT PRODUCTION VALIDATED" in text
    assert "DATASET_C_WEAK_LABELS" in text
    assert "DATASET_C_VERIFIED_EXTERNAL" in text
