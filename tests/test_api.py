"""
Comprehensive Integration & Contract Unit Tests for AstraFlare FastAPI Backend.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from database.db import DatabaseManager

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    db = DatabaseManager()
    db.connect()
    
    # Ensure test database contains REAL hotspots for isolated SQLite runs
    existing = db.execute_query("SELECT COUNT(*) as cnt FROM hotspots WHERE data_source = 'REAL';")
    if not existing or existing[0]["cnt"] == 0:
        for i in range(1, 20):
            hs_id = f"test_hs_{i:03d}"
            lat, lon = (22.3088, 73.1825) if i % 2 == 0 else (30.4500, 78.8500)
            frp = 120.0 if i % 2 == 0 else 45.0
            ts = f"2026-09-04T10:{i%60:02d}:00Z"
            if db.is_postgres:
                db.execute_query(
                    "INSERT INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                    (hs_id, hs_id, lat, lon, f"POINT({lon} {lat})", ts, "VIIRS", "VIIRS", 340.0, frp, "nominal", "D", "REAL")
                )
            else:
                db.execute_query(
                    "INSERT OR IGNORE INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    (hs_id, hs_id, lat, lon, f"POINT({lon} {lat})", ts, "VIIRS", "VIIRS", 340.0, frp, "nominal", "D", "REAL")
                )
    yield db
    db.close()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "postgis" in data
    assert "ml_model" in data
    assert data["version"] == "0.4.0"

def test_list_hotspots():
    response = client.get("/api/hotspots?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10
    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "id" in item
        assert "latitude" in item
        assert "longitude" in item
        assert "frp" in item
        assert "data_source" in item

def test_list_hotspots_filtering():
    response = client.get("/api/hotspots?min_frp=50.0&data_source=REAL")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["frp"] >= 50.0
        assert item["data_source"] == "REAL"

def test_geojson_coordinate_ordering():
    """
    CRITICAL TEST: Verifies RFC 7946 GeoJSON coordinate ordering.
    Coordinates MUST BE [longitude, latitude] (longitude first, latitude second).
    """
    response = client.get("/api/hotspots/geojson?limit=10")
    assert response.status_code == 200
    geojson = response.json()
    assert geojson["type"] == "FeatureCollection"
    assert "features" in geojson

    for feat in geojson["features"]:
        assert feat["type"] == "Feature"
        geom = feat["geometry"]
        assert geom["type"] == "Point"
        coords = geom["coordinates"]
        assert len(coords) == 2, "GeoJSON Point coordinates must contain exactly 2 numbers [lon, lat]."
        
        lon, lat = coords[0], coords[1]
        props = feat["properties"]
        
        # Verify coordinates match property values in correct order: coords[0] == lon, coords[1] == lat
        assert math.isclose(lon, float(props["longitude"]), rel_tol=1e-4), "First coordinate in GeoJSON Point MUST be Longitude."
        assert math.isclose(lat, float(props["latitude"]), rel_tol=1e-4), "Second coordinate in GeoJSON Point MUST be Latitude."

import math

def test_hotspot_detail():
    # Fetch first hotspot ID
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    response = client.get(f"/api/hotspots/{hs_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == hs_id
    assert "nearest_industrial_name" in detail
    assert "industrial_distance_m" in detail
    assert "historical_count_30d" in detail

def test_hotspot_not_found():
    response = client.get("/api/hotspots/non_existent_id_99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_prediction_endpoint_and_abstention():
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    response = client.get(f"/api/hotspots/{hs_id}/prediction")
    assert response.status_code == 200
    pred = response.json()
    assert pred["hotspot_id"] == hs_id
    assert "predicted_class" in pred
    assert "probabilities" in pred
    assert "review_required" in pred
    assert pred["model_status"] == "RESEARCH BASELINE"

def test_evidence_endpoint():
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    response = client.get(f"/api/hotspots/{hs_id}/evidence")
    assert response.status_code == 200
    ev = response.json()
    assert ev["hotspot_id"] == hs_id
    assert "evidence_items" in ev
    assert len(ev["evidence_items"]) > 0

def test_risk_endpoint():
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    response = client.get(f"/api/hotspots/{hs_id}/risk")
    assert response.status_code == 200
    rk = response.json()
    assert rk["hotspot_id"] == hs_id
    assert 0.0 <= rk["risk_score"] <= 1.0
    assert rk["risk_level"] in ("HIGH", "MEDIUM", "LOW")
    assert len(rk["contributing_factors"]) > 0

def test_history_endpoint():
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    response = client.get(f"/api/hotspots/{hs_id}/history")
    assert response.status_code == 200
    hist = response.json()
    assert hist["hotspot_id"] == hs_id
    assert "recurrence_count_30d" in hist

def test_industrial_sites_api():
    response = client.get("/api/industrial-sites?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    if len(data["items"]) > 0:
        site = data["items"][0]
        assert "osm_id" in site
        assert "facility_type" in site

def test_analytics_summary_api():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_hotspots" in data
    assert "hotspots_by_classification" in data
    assert "sensor_distribution" in data
    assert data["data_source_governance"]["SYNTHETIC_DEMO"] == 0

def test_investigation_workflow():
    list_res = client.get("/api/hotspots?page=1&page_size=1")
    items = list_res.json()["items"]
    if not items:
        pytest.skip("No hotspots in test database.")

    hs_id = items[0]["id"]
    payload = {
        "decision": "CONFIRMED",
        "reviewer_id": "test_analyst_01",
        "notes": "Verified against test telemetry."
    }
    response = client.post(f"/api/investigations/{hs_id}/review", json=payload)
    assert response.status_code == 201
    rev = response.json()
    assert rev["hotspot_id"] == hs_id
    assert rev["review_status"] == "CONFIRMED"

    # List investigations
    list_rev = client.get("/api/investigations?review_status=CONFIRMED")
    assert list_rev.status_code == 200
    revs = list_rev.json()["items"]
    assert len(revs) > 0

def test_ingestion_api():
    payload = {"country": "IND", "source": "VIIRS_SNPP_NRT", "mock_fallback": True}
    response = client.post("/api/ingestion/firms?mock_fallback=true")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
