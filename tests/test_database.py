"""
Unit Tests for Database Initialization, Schema & Connectivity.
"""
import pytest
from database.db import DatabaseManager

@pytest.fixture(scope="module")
def test_db():
    db = DatabaseManager()
    db.connect()
    yield db
    db.close()

def test_database_connection(test_db):
    assert test_db is not None
    res = test_db.execute_query("SELECT 1 AS num;")
    assert len(res) == 1
    assert res[0]["num"] == 1

def test_table_creation(test_db):
    tables = test_db.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table';" if not test_db.is_postgres
        else "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
    )
    table_names = [t.get("name") or t.get("table_name") for t in tables]
    
    expected_tables = [
        "hotspots", "industrial_sites", "land_cover", 
        "weather_observations", "historical_features", 
        "predictions", "evidence", "reviews"
    ]
    
    for tbl in expected_tables:
        assert tbl in table_names, f"Missing table: {tbl}"

def test_hotspot_crud(test_db):
    test_db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('test_hs_1', 20.0, 78.0, 'POINT(78.0 20.0)', '2026-09-04T12:00:00Z', 'VIIRS', 50.0, 'REAL');"
    )
    
    res = test_db.execute_query("SELECT * FROM hotspots WHERE id = 'test_hs_1';")
    assert len(res) == 1
    assert res[0]["id"] == "test_hs_1"
    assert res[0]["frp"] == 50.0
    assert res[0]["data_source"] == "REAL"

    test_db.execute_query("DELETE FROM hotspots WHERE id = 'test_hs_1';")
