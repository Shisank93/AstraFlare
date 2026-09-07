"""
Unit Tests for Phase 3.5 Historical Dataset Expansion, Idempotency, Coverage Audit,
Sensor Preservation, Facility Grouping, and Rolling Window Integrity.
"""
import pytest
from database.db import DatabaseManager
from data_pipeline.firms_ingestion import FIRMSIngestionClient
from ml.data.ingest_historical_real_data import ingest_7day_real_firms_data
from data_pipeline.event_matcher import event_matcher
from data_pipeline.gis_engine import gis_engine
from ml.splitter import FacilityGroupSplitter, EventGroupSplitter
from data_pipeline.external_ground_truth import ground_truth_engine

@pytest.fixture(scope="module")
def db():
    manager = DatabaseManager()
    manager.connect()
    yield manager
    manager.close()

def test_idempotent_ingestion_regression(db):
    client = FIRMSIngestionClient()
    csv_mock = (
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "22.3088,73.1825,365.2,0.4,0.4,2026-09-04,1415,N20,VIIRS,h,1.0,298.0,145.0,N\n"
    )
    
    # First pass
    res1 = client._parse_and_store_firms_csv(csv_mock, data_source_tag="MOCK_IDEM")
    # Second pass
    res2 = client._parse_and_store_firms_csv(csv_mock, data_source_tag="MOCK_IDEM")

    assert res1["inserted"] == 1 or res1["duplicates"] == 1
    assert res2["inserted"] == 0, "Second execution on identical record must insert ZERO new rows."
    assert res2["duplicates"] == 1, "Second execution must count row as duplicate."

    db.execute_query("DELETE FROM hotspots WHERE data_source = 'MOCK_IDEM';")

def test_sensor_preservation_attributes(db):
    row = {
        "latitude": "21.1150",
        "longitude": "72.6450",
        "bright_ti4": "350.0",
        "acq_date": "2026-09-04",
        "acq_time": "1530",
        "satellite": "J1_VIIRS",
        "instrument": "VIIRS",
        "confidence": "high",
        "frp": "95.0",
        "daynight": "N"
    }
    client = FIRMSIngestionClient()
    norm = client.parse_and_normalize_row(row, data_source_tag="REAL")
    
    assert norm is not None
    assert norm["satellite"] == "J1_VIIRS"
    assert norm["instrument"] == "VIIRS"
    assert "2026-09-04T15:30:00" in norm["acq_timestamp"]
    assert norm["data_source"] == "REAL"

def test_physical_event_grouping(db):
    hs_list = [
        {"id": "h1", "latitude": 22.3088, "longitude": 73.1825, "acq_timestamp": "2026-09-04T10:00:00Z"},
        {"id": "h2", "latitude": 22.3090, "longitude": 73.1830, "acq_timestamp": "2026-09-04T10:30:00Z"},
        {"id": "h3", "latitude": 30.4500, "longitude": 78.8500, "acq_timestamp": "2026-09-04T12:00:00Z"}
    ]
    clustered = event_matcher.cluster_firms_hotspots(hs_list, radius_m=1500.0, time_window_hours=24.0)
    
    assert len(clustered) == 3
    assert clustered[0]["physical_event_id"] == clustered[1]["physical_event_id"]
    assert clustered[0]["physical_event_id"] != clustered[2]["physical_event_id"]

def test_facility_group_split_zero_overlap():
    ds = [
        {"id": "1", "nearest_industrial_name": "Refinery_A", "industrial_distance_m": 500, "acq_timestamp": "2026-09-01T00:00:00Z"},
        {"id": "2", "nearest_industrial_name": "Refinery_A", "industrial_distance_m": 600, "acq_timestamp": "2026-09-01T01:00:00Z"},
        {"id": "3", "nearest_industrial_name": "Plant_B", "industrial_distance_m": 400, "acq_timestamp": "2026-09-02T00:00:00Z"},
        {"id": "4", "nearest_industrial_name": "Plant_B", "industrial_distance_m": 450, "acq_timestamp": "2026-09-02T01:00:00Z"},
        {"id": "5", "nearest_industrial_name": "Chemical_C", "industrial_distance_m": 300, "acq_timestamp": "2026-09-03T00:00:00Z"}
    ]
    splitter = FacilityGroupSplitter(train_ratio=0.6)
    train_set, test_set = splitter.split(ds)

    train_facs = set(x["nearest_industrial_name"] for x in train_set)
    test_facs = set(x["nearest_industrial_name"] for x in test_set)

    assert len(train_facs.intersection(test_facs)) == 0, "Train and Test facilities MUST NOT overlap."

def test_rolling_historical_window_target_exclusion(db):
    lat, lon = 22.3088, 73.1825
    stats = gis_engine.get_historical_frp_stats(
        lat, lon, radius_m=1000.0, exclude_hotspot_id="firms_non_existent"
    )
    assert isinstance(stats, dict)
    assert "count" in stats
    assert "mean" in stats

def test_external_event_matching_precedence(db):
    gt_res = ground_truth_engine.fetch_and_persist_external_events()
    gt_events = gt_res["events"]
    assert len(gt_events) >= 6

    firms_hs = [
        {
            "id": "hs_test_fire",
            "latitude": 30.4500,
            "longitude": 78.8500,
            "acq_timestamp": "2026-09-04T10:30:00Z",
            "frp": 120.0,
            "data_source": "REAL"
        }
    ]
    matched, match_stats = event_matcher.match_external_events_to_firms(
        firms_hotspots=firms_hs,
        ground_truth_events=gt_events,
        dist_threshold_m=2000.0,
        time_threshold_hours=24.0
    )
    assert len(matched) == 1
    assert matched[0]["label"] == "NATURAL_WILDLAND_FIRE"
    assert matched[0]["verification_status"] == "VERIFIED_EXTERNAL"
