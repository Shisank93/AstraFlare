"""
Unit Tests for Synthetic Demo Data Governance & Isolation.
Verifies data_source = 'SYNTHETIC_DEMO' separation from 'REAL' data queries.
"""
import pytest
from database.db import DatabaseManager
from backend.config import settings

@pytest.fixture(scope="module")
def demo_test_env():
    db = DatabaseManager()
    db.connect()

    # Insert one REAL hotspot and one SYNTHETIC_DEMO hotspot
    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('real_hs_100', 20.0, 75.0, 'POINT(75.0 20.0)', '2026-09-04T12:00:00Z', 'VIIRS', 45.0, 'REAL');"
    )
    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('demo_hs_100', 22.0, 70.0, 'POINT(70.0 22.0)', '2026-09-04T12:00:00Z', 'VIIRS', 150.0, 'SYNTHETIC_DEMO');"
    )

    yield db

    db.execute_query("DELETE FROM hotspots WHERE id IN ('real_hs_100', 'demo_hs_100');")
    db.close()

def test_data_source_tag_isolation(demo_test_env):
    real_records = demo_test_env.execute_query("SELECT * FROM hotspots WHERE data_source = 'REAL';")
    demo_records = demo_test_env.execute_query(f"SELECT * FROM hotspots WHERE data_source = '{settings.DATA_SOURCE_DEMO}';")

    real_ids = [r["id"] for r in real_records]
    demo_ids = [r["id"] for r in demo_records]

    assert "real_hs_100" in real_ids
    assert "real_hs_100" not in demo_ids

    assert "demo_hs_100" in demo_ids
    assert "demo_hs_100" not in real_ids

def test_real_data_filter_excludes_demo(demo_test_env):
    # Ensure production queries explicitly filtering data_source = 'REAL' NEVER return synthetic demo points
    query_prod = "SELECT COUNT(*) as cnt FROM hotspots WHERE data_source = 'REAL' AND id = 'demo_hs_100';"
    res = demo_test_env.execute_query(query_prod)
    assert res[0]["cnt"] == 0
