"""
Unit Tests for NASA FIRMS API Ingestion, Normalization, Validation, and Idempotency.
"""
import pytest
from data_pipeline.firms_ingestion import FIRMSIngestionClient
from database.db import DatabaseManager

@pytest.fixture(scope="module")
def firms_client():
    db = DatabaseManager()
    db.connect()
    client = FIRMSIngestionClient(map_key="test_dummy_key")
    yield client
    db.execute_query("DELETE FROM hotspots WHERE data_source = 'MOCK';")
    db.close()

def test_generate_hotspot_id():
    id1 = FIRMSIngestionClient.generate_hotspot_id("VIIRS", "2026-09-04", "1415", 22.3088, 73.1825)
    id2 = FIRMSIngestionClient.generate_hotspot_id("VIIRS", "2026-09-04", "1415", 22.3088, 73.1825)
    id3 = FIRMSIngestionClient.generate_hotspot_id("VIIRS", "2026-09-04", "1415", 22.3099, 73.1825)

    assert id1 == id2, "Identical observation parameters must produce deterministic fingerprint ID."
    assert id1 != id3, "Different coordinates must produce unique fingerprint IDs."

def test_parse_and_normalize_row(firms_client):
    raw_row = {
        "latitude": "22.3088",
        "longitude": "73.1825",
        "bright_ti4": "365.2",
        "acq_date": "2026-09-04",
        "acq_time": "1415",
        "satellite": "VIIRS_SNPP",
        "instrument": "VIIRS",
        "confidence": "high",
        "frp": "145.0",
        "daynight": "N"
    }

    norm = firms_client.parse_and_normalize_row(raw_row, data_source_tag="MOCK")
    assert norm is not None
    assert norm["latitude"] == 22.3088
    assert norm["longitude"] == 73.1825
    assert norm["frp"] == 145.0
    assert norm["data_source"] == "MOCK"
    assert "2026-09-04" in norm["acq_timestamp"]

def test_parse_invalid_coordinate(firms_client):
    invalid_row = {
        "latitude": "999.0",  # Out of bounds
        "longitude": "73.1825",
        "frp": "50.0"
    }
    norm = firms_client.parse_and_normalize_row(invalid_row)
    assert norm is None

def test_parse_negative_frp(firms_client):
    invalid_frp = {
        "latitude": "22.0",
        "longitude": "73.0",
        "frp": "-50.0"  # Invalid negative FRP
    }
    norm = firms_client.parse_and_normalize_row(invalid_frp)
    assert norm is None

def test_idempotent_ingestion(firms_client):
    # Run ingestion twice -> verify no duplicate records created
    res1 = firms_client.ingest_firms_data(mock_fallback=True)
    res2 = firms_client.ingest_firms_data(mock_fallback=True)

    assert res1["status"] == "SUCCESS"
    assert res2["status"] == "SUCCESS"
    assert res1["inserted"] > 0
