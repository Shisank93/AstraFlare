"""
AstraFlare Phase 3.2 Unit Test Suite.
Tests ground truth ingestion, spatial-temporal event clustering, external-to-FIRMS event matching,
label precedence hierarchy, conflict detection, and EventGroupSplitter event isolation.
"""
import pytest
import os
import sys
from datetime import datetime

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import DatabaseManager
from data_pipeline.external_ground_truth import ExternalGroundTruthEngine, STATUS_VERIFIED_EXTERNAL, STATUS_CONFLICTING_EVIDENCE
from data_pipeline.event_matcher import EventMatcher
from ml.splitter import EventGroupSplitter
from ml.dataset_generator import generate_ml_dataset

@pytest.fixture(scope="module")
def gt_engine():
    db = DatabaseManager()
    db.connect()
    engine = ExternalGroundTruthEngine(db_mgr=db)
    return engine

@pytest.fixture(scope="module")
def matcher():
    db = DatabaseManager()
    db.connect()
    m = EventMatcher(db_mgr=db)
    return m

def test_external_ground_truth_ingestion(gt_engine):
    res = gt_engine.fetch_and_persist_external_events()
    assert res["persisted_count"] > 0
    assert len(res["events"]) >= 6
    
    events = gt_engine.get_all_ground_truth_events()
    assert len(events) >= 6
    for e in events:
        assert "event_id" in e
        assert "event_type" in e
        assert "source_name" in e
        assert e["latitude"] is not None
        assert e["longitude"] is not None

def test_cluster_firms_hotspots(matcher):
    sample_hotspots = [
        {"id": "hs_01", "latitude": 22.3088, "longitude": 73.1825, "acq_timestamp": "2026-09-04T10:00:00Z"},
        {"id": "hs_02", "latitude": 22.3090, "longitude": 73.1820, "acq_timestamp": "2026-09-04T12:00:00Z"}, # Same event (<1.5km, <24h)
        {"id": "hs_03", "latitude": 30.4500, "longitude": 78.8500, "acq_timestamp": "2026-09-04T10:00:00Z"}  # Distant event
    ]
    clustered = matcher.cluster_firms_hotspots(sample_hotspots, radius_m=1500.0, time_window_hours=24.0)
    assert len(clustered) == 3
    assert clustered[0]["physical_event_id"] == clustered[1]["physical_event_id"]
    assert clustered[0]["physical_event_id"] != clustered[2]["physical_event_id"]

def test_event_matching_and_precedence(matcher):
    sample_firms = [
        {"id": "hs_fire_01", "latitude": 30.4510, "longitude": 78.8510, "acq_timestamp": "2026-09-04T10:30:00Z", "label": "UNLABELED"},
        {"id": "hs_far_01", "latitude": 10.0000, "longitude": 70.0000, "acq_timestamp": "2026-09-04T10:30:00Z", "label": "UNLABELED"}
    ]
    gt_events = [
        {
            "event_id": "gt_test_fire_01",
            "event_type": "NATURAL_WILDLAND_FIRE",
            "source_name": "TEST_NASA_FIRMS",
            "source_url": "https://example.com",
            "source_record_id": "REC_001",
            "event_timestamp": "2026-09-04T10:30:00Z",
            "latitude": 30.4500,
            "longitude": 78.8500,
            "source_confidence": 0.95,
            "verification_status": STATUS_VERIFIED_EXTERNAL
        }
    ]
    matched, stats = matcher.match_external_events_to_firms(sample_firms, gt_events, dist_threshold_m=2000.0, time_threshold_hours=24.0)
    assert stats["matched_firms_events"] == 1
    
    match_fire = [m for m in matched if m["id"] == "hs_fire_01"][0]
    assert match_fire["label"] == "NATURAL_WILDLAND_FIRE"
    assert match_fire["label_precedence"] == STATUS_VERIFIED_EXTERNAL
    assert match_fire["source_name"] == "TEST_NASA_FIRMS"
    
    match_far = [m for m in matched if m["id"] == "hs_far_01"][0]
    assert match_far["label"] == "UNLABELED"

def test_conflicting_evidence_detection(matcher):
    sample_firms = [
        {"id": "hs_conflict_01", "latitude": 22.3088, "longitude": 73.1825, "acq_timestamp": "2026-09-04T14:00:00Z", "label": "UNLABELED"}
    ]
    conflicting_gt_events = [
        {
            "event_id": "gt_fire_c1",
            "event_type": "NATURAL_WILDLAND_FIRE",
            "source_name": "SOURCE_A",
            "source_url": "https://example.com",
            "source_record_id": "REC_A",
            "event_timestamp": "2026-09-04T14:00:00Z",
            "latitude": 22.3088,
            "longitude": 73.1825,
            "source_confidence": 0.90,
            "verification_status": STATUS_VERIFIED_EXTERNAL
        },
        {
            "event_id": "gt_ind_c1",
            "event_type": "LIKELY_INDUSTRIAL_INCIDENT",
            "source_name": "SOURCE_B",
            "source_url": "https://example.com",
            "source_record_id": "REC_B",
            "event_timestamp": "2026-09-04T14:00:00Z",
            "latitude": 22.3088,
            "longitude": 73.1825,
            "source_confidence": 0.90,
            "verification_status": STATUS_VERIFIED_EXTERNAL
        }
    ]
    matched, stats = matcher.match_external_events_to_firms(sample_firms, conflicting_gt_events)
    assert stats["conflicting_events"] == 1
    res_item = matched[0]
    assert res_item["label"] == "CONFLICTING_EVIDENCE"
    assert res_item["verification_status"] == STATUS_CONFLICTING_EVIDENCE

def test_event_group_splitter_isolation():
    dataset = [
        {"id": "h1", "physical_event_id": "evt_A", "acq_timestamp": "2026-09-01T10:00:00Z"},
        {"id": "h2", "physical_event_id": "evt_A", "acq_timestamp": "2026-09-01T11:00:00Z"},
        {"id": "h3", "physical_event_id": "evt_B", "acq_timestamp": "2026-09-02T10:00:00Z"},
        {"id": "h4", "physical_event_id": "evt_C", "acq_timestamp": "2026-09-03T10:00:00Z"},
        {"id": "h5", "physical_event_id": "evt_C", "acq_timestamp": "2026-09-03T12:00:00Z"}
    ]
    splitter = EventGroupSplitter(train_ratio=0.6)
    train_set, test_set = splitter.split(dataset)
    
    train_events = set(x["physical_event_id"] for x in train_set)
    test_events = set(x["physical_event_id"] for x in test_set)
    
    # Event Isolation Assert: Zero event overlap between train and test
    assert train_events.intersection(test_events) == set()
    assert len(train_set) + len(test_set) == len(dataset)

def test_generate_ml_dataset_independent_external():
    res = generate_ml_dataset(limit=100, label_mode="INDEPENDENT_EXTERNAL")
    assert res["record_count"] > 0
    assert res["label_mode"] == "INDEPENDENT_EXTERNAL"
    assert res["match_stats"] is not None
    
    for item in res["dataset"]:
        assert "physical_event_id" in item
        assert "label" in item
        assert "label_precedence" in item
