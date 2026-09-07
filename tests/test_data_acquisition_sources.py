"""
Unit & Integration Tests for Phase 3.6 Data Acquisition Infrastructure & Governance.
"""
import pytest
from data_pipeline.sources.normalized_event import NormalizedEvent, ProvenanceStatus, LabelProvenance
from data_pipeline.sources.circularity_auditor import circularity_auditor
from data_pipeline.sources.firms_adapter import firms_adapter
from data_pipeline.sources.gfw_adapter import gfw_adapter
from ml.splitter import EventGroupSplitter, FacilityGroupSplitter

def test_provenance_tagging():
    """Verify that NormalizedEvent preserves data provenance tags and schema fields."""
    event = NormalizedEvent(
        event_id="test_01",
        source_name="PESO_Registry",
        source_type="GOVERNMENT_REGISTRY",
        timestamp_start="2026-09-01T12:00:00Z",
        latitude=22.3088,
        longitude=73.1825,
        provenance_status=ProvenanceStatus.VERIFIED_EXTERNAL
    )
    assert event.source_name == "PESO_Registry"
    assert event.provenance_status == ProvenanceStatus.VERIFIED_EXTERNAL
    assert event.country == "IND"

def test_synthetic_data_exclusion():
    """Verify that synthetic demo records retain SYNTHETIC_DEMO status."""
    demo_event = NormalizedEvent(
        event_id="demo_01",
        source_name="Synthetic_Generator",
        source_type="DEMO",
        timestamp_start="2026-09-01T12:00:00Z",
        latitude=22.3088,
        longitude=73.1825,
        provenance_status=ProvenanceStatus.SYNTHETIC_DEMO
    )
    assert demo_event.provenance_status == ProvenanceStatus.SYNTHETIC_DEMO

def test_circularity_auditor():
    """Verify that circularity auditor correctly detects label-feature overlap."""
    result = circularity_auditor.audit_label_construction(
        label="LIKELY_INDUSTRIAL_INCIDENT",
        rule_features_used=["industrial_distance_m", "frp"]
    )
    assert result["label_feature_overlap"] is True
    assert "industrial_distance_m" in result["overlapping_features"]
    assert "frp" in result["overlapping_features"]

def test_firms_adapter_aggregation():
    """Verify physical event aggregation across satellite observations."""
    obs_list = [
        {"id": "obs1", "latitude": 22.308, "longitude": 73.182, "frp": 150.0, "satellite": "VIIRS_SNPP", "data_source": "REAL"},
        {"id": "obs2", "latitude": 22.309, "longitude": 73.183, "frp": 160.0, "satellite": "NOAA20", "data_source": "REAL"}
    ]
    agg = firms_adapter.aggregate_event_cluster("cluster_101", obs_list)
    assert agg["observation_count"] == 2
    assert agg["max_frp"] == 160.0
    assert agg["mean_frp"] == 155.0
    assert agg["satellite_count"] == 2

def test_event_group_splitter_no_leakage():
    """Verify EventGroupSplitter prevents physical event cluster leakage across splits."""
    records = [
        {"id": "h1", "physical_event_id": "evt_A", "frp": 10},
        {"id": "h2", "physical_event_id": "evt_A", "frp": 12},
        {"id": "h3", "physical_event_id": "evt_B", "frp": 50},
        {"id": "h4", "physical_event_id": "evt_C", "frp": 90},
    ]
    splitter = EventGroupSplitter(train_ratio=0.5)
    train_recs, test_recs = splitter.split(records)

    train_events = set(r["physical_event_id"] for r in train_recs)
    test_events = set(r["physical_event_id"] for r in test_recs)

    assert len(train_events.intersection(test_events)) == 0
