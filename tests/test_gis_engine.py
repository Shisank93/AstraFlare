"""
Unit Tests for GIS Engine Functions, Spatial Distance & Recurrence.
"""
import pytest
from database.db import DatabaseManager
from data_pipeline.gis_engine import GISEngine, haversine_distance_m

@pytest.fixture(scope="module")
def gis_test_env():
    db = DatabaseManager()
    db.connect()
    engine = GISEngine(db)

    # Insert mock industrial site & historical hotspots
    db.execute_query(
        "INSERT INTO industrial_sites (osm_id, name, facility_type, geom, data_source) "
        "VALUES ('way_test_gis', 'Test Refinery', 'refinery', 'POINT(73.0 22.0)', 'OSM');"
    )

    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('hist_hs_1', 22.001, 73.001, 'POINT(73.001 22.001)', '2026-09-01T10:00:00Z', 'VIIRS', 40.0, 'REAL');"
    )
    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('hist_hs_2', 22.002, 73.002, 'POINT(73.002 22.002)', '2026-09-02T10:00:00Z', 'VIIRS', 50.0, 'REAL');"
    )
    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('target_hs_3', 22.000, 73.000, 'POINT(73.000 22.000)', '2026-09-04T10:00:00Z', 'VIIRS', 150.0, 'REAL');"
    )

    yield engine

    db.execute_query("DELETE FROM industrial_sites WHERE osm_id = 'way_test_gis';")
    db.execute_query("DELETE FROM hotspots WHERE id IN ('hist_hs_1', 'hist_hs_2', 'target_hs_3');")
    db.close()

def test_haversine_distance():
    # Distance between Vadodara (22.3072, 73.1812) and Surat (21.1702, 72.8311) is ~135 km
    dist = haversine_distance_m(22.3072, 73.1812, 21.1702, 72.8311)
    assert 130000 <= dist <= 140000

def test_nearest_industrial_site(gis_test_env):
    # Search near (22.001, 73.001) -> should find Test Refinery (22.0, 73.0) ~140m away
    site, dist = gis_test_env.get_nearest_industrial_site(22.001, 73.001, max_distance_m=5000.0)
    assert site is not None
    assert site["name"] == "Test Refinery"
    assert dist < 300.0

def test_count_industrial_sites_in_radius(gis_test_env):
    count = gis_test_env.count_industrial_sites_in_radius(22.001, 73.001, radius_m=1000.0)
    assert count >= 1

def test_historical_frp_stats_exclusion(gis_test_env):
    # Verify target observation target_hs_3 IS EXCLUDED from historical statistics calculation!
    stats = gis_test_env.get_historical_frp_stats(
        22.000, 73.000, time_window_days=365, radius_m=1000.0, exclude_hotspot_id='target_hs_3'
    )
    assert stats["count"] == 2
    assert stats["mean"] == 45.0  # (40 + 50) / 2
    assert stats["max"] == 50.0
    assert stats["std"] == 7.07  # std of [40, 50]
