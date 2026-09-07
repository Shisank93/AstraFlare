"""
Unit and Integration Tests for Phase 3.8 India Data Acquisition, Precedence, and Cross-Source Evidence Matching.
"""
import pytest
from data_pipeline.event_matcher import EventMatcher, PRECEDENCE_WEIGHTS, STATUS_VERIFIED_EXTERNAL, STATUS_WEAK_RULE, STATUS_CONFLICTING_EVIDENCE
from data_pipeline.sources.data_manifest import DataManifestManager

def test_label_precedence_hierarchy():
    """Verify that VERIFIED_EXTERNAL > MANUAL_VERIFIED > WEAK_RULE > UNLABELED."""
    assert PRECEDENCE_WEIGHTS[STATUS_VERIFIED_EXTERNAL] > PRECEDENCE_WEIGHTS[STATUS_WEAK_RULE]
    assert PRECEDENCE_WEIGHTS[STATUS_WEAK_RULE] > PRECEDENCE_WEIGHTS["UNLABELED"]

def test_cross_source_event_matching():
    """Verify spatial-temporal matching of external ground truth events against FIRMS physical clusters."""
    matcher = EventMatcher(db_mgr=None)
    
    firms_hotspots = [
        {"hotspot_id": "hs_01", "latitude": 17.7011, "longitude": 83.2125, "acq_timestamp": "2024-05-07T12:00:00Z", "label": "UNLABELED"},
        {"hotspot_id": "hs_02", "latitude": 28.6139, "longitude": 77.2090, "acq_timestamp": "2024-05-07T12:00:00Z", "label": "UNLABELED"}
    ]
    
    gt_events = [
        {
            "event_id": "IND_INC_001",
            "event_type": "LIKELY_INDUSTRIAL_INCIDENT",
            "latitude": 17.7015,
            "longitude": 83.2120,
            "event_timestamp": "2024-05-07T12:30:00Z",
            "source_name": "PESO_Registry",
            "source_record_id": "PESO_2024_01",
            "source_confidence": 0.95
        }
    ]

    matched_records, stats = matcher.match_external_events_to_firms(firms_hotspots, gt_events, dist_threshold_m=2000.0, time_threshold_hours=24.0)

    assert stats["total_firms_hotspots"] == 2
    assert stats["matched_firms_events"] == 1
    
    # hs_01 should be matched to LIKELY_INDUSTRIAL_INCIDENT with VERIFIED_EXTERNAL precedence
    hs01_match = [r for r in matched_records if r["hotspot_id"] == "hs_01"][0]
    assert hs01_match["label"] == "LIKELY_INDUSTRIAL_INCIDENT"
    assert hs01_match["label_precedence"] == STATUS_VERIFIED_EXTERNAL
    assert hs01_match["match_distance_m"] < 1000.0

def test_conflicting_evidence_detection():
    """Verify that overlapping external events of different types resolve to CONFLICTING_EVIDENCE."""
    matcher = EventMatcher(db_mgr=None)
    
    firms_hotspots = [
        {"hotspot_id": "hs_conflict", "latitude": 21.7108, "longitude": 72.5872, "acq_timestamp": "2024-06-03T10:00:00Z", "label": "UNLABELED"}
    ]
    
    gt_events = [
        {
            "event_id": "IND_INC_002",
            "event_type": "LIKELY_INDUSTRIAL_INCIDENT",
            "latitude": 21.7108,
            "longitude": 72.5872,
            "event_timestamp": "2024-06-03T10:00:00Z",
            "source_name": "NDMA_Report",
            "source_record_id": "NDMA_01"
        },
        {
            "event_id": "FSI_FIRE_09",
            "event_type": "NATURAL_WILDLAND_FIRE",
            "latitude": 21.7108,
            "longitude": 72.5872,
            "event_timestamp": "2024-06-03T10:00:00Z",
            "source_name": "FSI_Alert",
            "source_record_id": "FSI_09"
        }
    ]

    matched_records, stats = matcher.match_external_events_to_firms(firms_hotspots, gt_events)
    
    hs_conflict = matched_records[0]
    assert hs_conflict["label"] == "CONFLICTING_EVIDENCE"
    assert hs_conflict["label_precedence"] == STATUS_CONFLICTING_EVIDENCE
    assert stats["conflicting_events"] == 1
