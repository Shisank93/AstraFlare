"""
Unit Tests for OpenStreetMap Overpass Ingestion, Geometry Normalization, and Caching.
"""
import pytest
from data_pipeline.osm_ingestion import OSMIngestionClient
from database.db import DatabaseManager

@pytest.fixture(scope="module")
def osm_client_env():
    db = DatabaseManager()
    db.connect()
    client = OSMIngestionClient()
    yield client
    db.execute_query("DELETE FROM industrial_sites WHERE osm_id LIKE 'way_mock_%';")
    db.close()

def test_build_overpass_query(osm_client_env):
    q = osm_client_env.build_overpass_query(22.3072, 73.1812, radius_m=5000.0)
    assert "landuse" in q
    assert "flare_stack" in q
    assert "5000.0" in q

def test_normalize_osm_elements(osm_client_env):
    mock_elements = [
        {
            "type": "node",
            "id": 12345,
            "lat": 22.3088,
            "lon": 73.1825,
            "tags": {"man_made": "flare_stack", "name": "Refinery Flare"}
        },
        {
            "type": "way",
            "id": 67890,
            "center": {"lat": 22.4715, "lon": 70.0583},
            "tags": {"landuse": "industrial", "name": "Jamnagar Industrial Park"}
        }
    ]

    norm = osm_client_env.normalize_osm_elements(mock_elements)
    assert len(norm) == 2
    assert norm[0]["osm_id"] == "node_12345"
    assert norm[0]["facility_type"] == "flare_stack"
    assert norm[1]["osm_id"] == "way_67890"
    assert "POINT(70.0583 22.4715)" in norm[1]["geom"]

def test_ingest_contextual_osm_caching(osm_client_env):
    # Ingest once -> inserts site into database cache
    count1 = osm_client_env.ingest_contextual_osm(22.900, 73.900, radius_m=5000.0, mock_fallback=True)
    assert count1 >= 1

    # Ingest second time at same point -> hits local cache
    count2 = osm_client_env.ingest_contextual_osm(22.900, 73.900, radius_m=5000.0, mock_fallback=False)
    assert count2 >= 1
