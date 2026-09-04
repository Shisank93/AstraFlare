"""
Unit Tests for Enriched Feature Pipeline and Feature Output Contract Conformance.
"""
import pytest
from data_pipeline.feature_pipeline import FeaturePipeline
from database.db import DatabaseManager

@pytest.fixture(scope="module")
def feature_pipeline_env():
    db = DatabaseManager()
    db.connect()
    pipeline = FeaturePipeline()
    yield pipeline
    db.close()

def test_feature_output_contract_keys(feature_pipeline_env):
    sample_hs = {
        "id": "hs_contract_test",
        "latitude": 22.3088,
        "longitude": 73.1825,
        "frp": 145.0,
        "brightness": 365.2,
        "satellite": "VIIRS_SNPP",
        "acq_timestamp": "2026-09-04T14:15:00Z",
        "data_source": "REAL"
    }

    record = feature_pipeline_env.enrich_hotspot(sample_hs, mock_fallback=True)

    expected_keys = [
        "hotspot_id", "latitude", "longitude", "frp", "brightness", "confidence",
        "satellite", "acq_timestamp", "industrial_distance", "nearest_industrial_name",
        "industrial_site_count_250m", "industrial_site_count_500m", "industrial_site_count_1000m",
        "historical_count_30d", "historical_count_365d", "historical_mean_frp",
        "historical_max_frp", "historical_std_frp", "frp_anomaly_score",
        "frp_anomaly_status", "land_cover_class", "data_source", "data_quality"
    ]

    for key in expected_keys:
        assert key in record, f"Missing key in Feature Output Contract: {key}"

    assert record["hotspot_id"] == "hs_contract_test"
    assert record["latitude"] == 22.3088
    assert record["frp"] == 145.0
    assert record["data_source"] == "REAL"
    assert record["data_quality"] in ("COMPLETE", "PARTIAL_CONTEXT", "RAW_OBSERVATION")

def test_graceful_missing_context(feature_pipeline_env):
    # Test hotspot with extreme remote coordinates (no industry nearby)
    remote_hs = {
        "id": "hs_remote_test",
        "latitude": 10.0,
        "longitude": 70.0,  # Arabian Sea coordinate
        "frp": 25.0,
        "data_source": "REAL"
    }

    record = feature_pipeline_env.enrich_hotspot(remote_hs, mock_fallback=False)
    assert record["industrial_distance"] >= 5000.0
    assert record["industrial_site_count_250m"] == 0
    assert record["data_source"] == "REAL"
