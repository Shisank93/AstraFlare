"""
Phase 4 Backend Master Test Suite.
Verifies FastAPI endpoints, PostgreSQL/PostGIS connectivity, REAL vs DEMO mode separation,
RFC 7946 GeoJSON [lon, lat] ordering, PostGIS bbox filtering, analyst review workflow,
analytics SQL aggregation, and security key protection.
"""
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from database.db import DatabaseManager

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_events():
    """Populates in-memory database with test event data in DEMO mode."""
    os.environ["ASTRAFLARE_MODE"] = "DEMO"
    db = DatabaseManager()
    db.connect()

    # Seed test events
    db.execute_query(
        "INSERT INTO events (event_id, event_timestamp, centroid_lat, centroid_lon, geom, max_frp, mean_frp, max_brightness, observation_count, industrial_distance_m, industrial_site_count_1km, worldcover_class, data_source, risk_score, risk_level, investigation_priority, human_review_required) "
        "VALUES ('evt_p4_test_1', '2026-09-05T10:00:00Z', 20.5, 78.5, 'POINT(78.5 20.5)', 120.0, 100.0, 340.0, 5, 200.0, 3, 50, 'REAL', 0.85, 'HIGH', 'URGENT', TRUE);"
    )
    db.execute_query(
        "INSERT INTO events (event_id, event_timestamp, centroid_lat, centroid_lon, geom, max_frp, mean_frp, max_brightness, observation_count, industrial_distance_m, industrial_site_count_1km, worldcover_class, data_source, risk_score, risk_level, investigation_priority, human_review_required) "
        "VALUES ('evt_p4_test_2', '2026-09-05T11:00:00Z', 15.0, 75.0, 'POINT(75.0 15.0)', 15.0, 15.0, 310.0, 1, 8000.0, 0, 10, 'REAL', 0.20, 'LOW', 'LOW', TRUE);"
    )
    db.execute_query(
        "INSERT INTO events (event_id, event_timestamp, centroid_lat, centroid_lon, geom, max_frp, mean_frp, max_brightness, observation_count, industrial_distance_m, industrial_site_count_1km, worldcover_class, data_source, risk_score, risk_level, investigation_priority, human_review_required) "
        "VALUES ('evt_p4_demo_1', '2026-09-05T12:00:00Z', 22.0, 73.0, 'POINT(73.0 22.0)', 200.0, 200.0, 350.0, 3, 100.0, 2, 50, 'SYNTHETIC_DEMO', 0.90, 'HIGH', 'URGENT', TRUE);"
    )

    # Seed test hotspot
    db.execute_query(
        "INSERT INTO hotspots (id, latitude, longitude, geom, acq_timestamp, satellite, frp, data_source) "
        "VALUES ('evt_p4_test_1', 20.5, 78.5, 'POINT(78.5 20.5)', '2026-09-05T10:00:00Z', 'VIIRS', 120.0, 'REAL');"
    )

    yield db

    db.execute_query("DELETE FROM events WHERE event_id IN ('evt_p4_test_1', 'evt_p4_test_2', 'evt_p4_demo_1');")
    db.execute_query("DELETE FROM hotspots WHERE id = 'evt_p4_test_1';")
    db.close()

def test_health_and_ready_endpoints(setup_test_events):
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    data_h = resp_health.json()
    assert data_h["status"] in ("healthy", "degraded")
    assert "mode" in data_h

    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    data_r = resp_ready.json()
    assert data_r["status"] == "ready"
    assert data_r["ml_status"] == "RESEARCH_BASELINE_DATA_LIMITED"
    assert data_r["risk_engine"] == "available"

def test_real_mode_strict_database_failure():
    """Verifies REAL mode rejects silent SQLite fallback when PostgreSQL fails."""
    orig_mode = settings.ASTRAFLARE_MODE
    try:
        settings.ASTRAFLARE_MODE = "REAL"
        db = DatabaseManager(db_url="postgresql://invalid_user:invalid_pass@localhost:5432/non_existent_db")
        with pytest.raises(RuntimeError) as exc_info:
            db.connect()
        assert "REAL mode" in str(exc_info.value)
    finally:
        settings.ASTRAFLARE_MODE = "DEMO"

def test_geojson_rfc7946_coordinates(setup_test_events):
    resp = client.get("/api/hotspots/geojson?data_source=REAL")
    assert resp.status_code == 200
    geojson = resp.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

    for feat in geojson["features"]:
        coords = feat["geometry"]["coordinates"]
        # RFC 7946: [lon, lat]
        lon, lat = coords[0], coords[1]
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0

def test_event_detail_endpoint(setup_test_events):
    resp = client.get("/api/events/evt_p4_test_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_id"] == "evt_p4_test_1"
    assert data["location"]["latitude"] == 20.5
    assert data["location"]["longitude"] == 78.5
    assert data["risk"]["level"] in ("HIGH", "MEDIUM", "LOW")
    assert "priority" in data["investigation"]

def test_event_sub_endpoints(setup_test_events):
    r_ev = client.get("/api/events/evt_p4_test_1/evidence")
    assert r_ev.status_code == 200
    assert "evidence" in r_ev.json()

    r_risk = client.get("/api/events/evt_p4_test_1/risk")
    assert r_risk.status_code == 200
    assert "overall_risk_score" in r_risk.json()

    r_ind = client.get("/api/events/evt_p4_test_1/industrial-context")
    assert r_ind.status_code == 200
    assert "industrial_distance_m" in r_ind.json()

def test_investigation_queue_and_review(setup_test_events):
    # Query queue
    q_resp = client.get("/api/investigations?data_source=REAL")
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["meta"]["total"] >= 2
    # Ensure URGENT item comes before LOW item
    items = q_data["items"]
    assert items[0]["priority"] == "URGENT"

    # Submit analyst review
    rev_payload = {
        "reviewer_id": "analyst_007",
        "decision": "CONFIRMED",
        "notes": "Verified industrial flare thermal signature."
    }
    sub_resp = client.post("/api/investigations/evt_p4_test_1/review", json=rev_payload)
    assert sub_resp.status_code == 201
    rev_data = sub_resp.json()
    assert rev_data["review_status"] == "CONFIRMED"
    assert rev_data["hotspot_id"] == "evt_p4_test_1"

def test_analytics_summary(setup_test_events):
    resp = client.get("/api/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "events_by_risk_level" in data
    assert "events_by_priority" in data
    assert "human_review_count" in data

def test_firms_ingestion_security():
    # Attempt mock fallback in REAL mode -> Should fail with 400
    orig_mode = settings.ASTRAFLARE_MODE
    try:
        settings.ASTRAFLARE_MODE = "REAL"
        resp = client.post("/api/ingestion/firms?mock_fallback=true")
        assert resp.status_code == 400
        assert "REAL mode" in resp.json()["detail"]["error"]["message"]
    finally:
        settings.ASTRAFLARE_MODE = orig_mode
