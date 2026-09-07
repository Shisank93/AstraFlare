"""
AstraFlare Phase 3.4 Facility Isolation & Splitter Test Suite.
Tests FacilityGroupSplitter to verify zero industrial facility correlation leakage across train/test splits.
"""
import pytest
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.splitter import FacilityGroupSplitter

def test_facility_group_splitter_zero_overlap():
    dataset = [
        # Facility A (Baroda Refinery) Detections across different days
        {"id": "h1", "nearest_industrial_name": "Gujarat Refinery", "industrial_distance_m": 450.0, "acq_timestamp": "2026-09-01T10:00:00Z"},
        {"id": "h2", "nearest_industrial_name": "Gujarat Refinery", "industrial_distance_m": 460.0, "acq_timestamp": "2026-09-02T10:00:00Z"},
        {"id": "h3", "nearest_industrial_name": "Gujarat Refinery", "industrial_distance_m": 440.0, "acq_timestamp": "2026-09-03T10:00:00Z"},
        # Facility B (Hazira Petrochemical) Detections
        {"id": "h4", "nearest_industrial_name": "Hazira Petrochemical Complex", "industrial_distance_m": 250.0, "acq_timestamp": "2026-09-04T10:00:00Z"},
        {"id": "h5", "nearest_industrial_name": "Hazira Petrochemical Complex", "industrial_distance_m": 270.0, "acq_timestamp": "2026-09-04T14:00:00Z"},
        # Non-facility Wildfire Event
        {"id": "h6", "nearest_industrial_name": None, "industrial_distance_m": 8500.0, "physical_event_id": "evt_wildfire_001", "acq_timestamp": "2026-09-05T10:00:00Z"}
    ]

    splitter = FacilityGroupSplitter(train_ratio=0.6, max_facility_dist_m=3000.0)
    train_set, test_set = splitter.split(dataset)

    train_facs = set(x["nearest_industrial_name"] for x in train_set if x.get("nearest_industrial_name"))
    test_facs = set(x["nearest_industrial_name"] for x in test_set if x.get("nearest_industrial_name"))

    # Zero Facility Leakage Assertion
    facility_overlap = train_facs.intersection(test_facs)
    assert facility_overlap == set()
    assert len(train_set) + len(test_set) == len(dataset)
