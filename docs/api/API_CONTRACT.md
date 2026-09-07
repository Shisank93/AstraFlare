# AstraFlare Backend REST API Contract Documentation

## 1. Overview
This document specifies the complete REST API contract for the AstraFlare Backend service (`v0.4.0`), serving as the authoritative specification for frontend client integration.

- **Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Specification**: `/docs`
- **Raw OpenAPI JSON**: `/openapi.json`
- **Data Governance Standard**: `data_source = 'REAL'` exclusively. Zero synthetic data.

---

## 2. API Endpoints

### 2.1 System & Health
#### `GET /health`
- **Summary**: Health check & dependency availability status.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "postgis": "available",
  "ml_model": "available",
  "version": "0.4.0",
  "environment": "development"
}
```

---

### 2.2 Hotspot Telemetry & Analysis
#### `GET /api/hotspots`
- **Summary**: Paginated list of satellite thermal anomalies with optional spatial, temporal, FRP, and risk filtering.
- **Query Parameters**:
  - `start_date` (string, ISO datetime): e.g. `2026-08-28T00:00:00Z`
  - `end_date` (string, ISO datetime): e.g. `2026-09-04T23:59:59Z`
  - `min_lat`, `max_lat` (float): Bounding box latitude bounds
  - `min_lon`, `max_lon` (float): Bounding box longitude bounds
  - `min_frp`, `max_frp` (float): FRP range in Megawatts
  - `classification` (string): `LIKELY_INDUSTRIAL_INCIDENT`, `PERSISTENT_INDUSTRIAL_HEAT`, `NATURAL_WILDLAND_FIRE`
  - `risk_level` (string): `HIGH`, `MEDIUM`, `LOW`
  - `review_required` (boolean): `true` or `false`
  - `data_source` (string, default `'REAL'`)
  - `page` (int, default `1`)
  - `page_size` (int, default `50`, max `500`)
- **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "firms_0e9fac8a6cf38741",
      "firms_id": "firms_0e9fac8a6cf38741",
      "latitude": 22.3088,
      "longitude": 73.1825,
      "acq_timestamp": "2026-09-04 14:15:00+00:00",
      "satellite": "N20",
      "instrument": "VIIRS",
      "brightness": 365.2,
      "frp": 145.0,
      "confidence": "high",
      "daynight": "N",
      "data_source": "REAL",
      "classification": "LIKELY_INDUSTRIAL_INCIDENT",
      "risk_level": "HIGH",
      "review_required": false
    }
  ],
  "meta": {
    "total": 8786,
    "page": 1,
    "page_size": 50,
    "total_pages": 176
  }
}
```

#### `GET /api/hotspots/geojson`
- **Summary**: RFC 7946 compliant GeoJSON FeatureCollection for GIS map rendering.
- **CRITICAL Coordinate Specification**: Geometry coordinates MUST BE `[longitude, latitude]`.
- **Response `200 OK`**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [73.1825, 22.3088]
      },
      "properties": {
        "id": "firms_0e9fac8a6cf38741",
        "frp": 145.0,
        "satellite": "N20",
        "classification": "LIKELY_INDUSTRIAL_INCIDENT",
        "risk_level": "HIGH"
      }
    }
  ]
}
```

#### `GET /api/hotspots/{hotspot_id}`
- **Summary**: Complete investigation-oriented hotspot detailed record.
- **Path Parameter**: `hotspot_id` (string)
- **Response `200 OK`**: Includes coordinates, FRP, satellite, OSM industrial distance, land cover, historical recurrence, FRP anomaly Z-score, classification, risk level, and analyst review status.

#### `GET /api/hotspots/{hotspot_id}/prediction`
- **Summary**: ML baseline classification probabilities & operational abstention gate.
- **Response `200 OK`**:
```json
{
  "hotspot_id": "firms_0e9fac8a6cf38741",
  "predicted_class": "LIKELY_INDUSTRIAL_INCIDENT",
  "confidence": 0.8250,
  "probabilities": {
    "LIKELY_INDUSTRIAL_INCIDENT": 0.8250,
    "PERSISTENT_INDUSTRIAL_HEAT": 0.1250,
    "NATURAL_WILDLAND_FIRE": 0.0500
  },
  "review_required": false,
  "human_review_threshold": 0.65,
  "model_version": "0.4.0",
  "model_status": "RESEARCH BASELINE",
  "limitations": "Model operates in RESEARCH BASELINE mode."
}
```

#### `GET /api/hotspots/{hotspot_id}/evidence`
- **Summary**: Structured multi-layer GIS & ground-truth evidence statements.
- **Response `200 OK`**:
```json
{
  "hotspot_id": "firms_0e9fac8a6cf38741",
  "physical_event_id": "evt_cluster_0001",
  "verification_status": "VERIFIED_EXTERNAL",
  "evidence_items": [
    {
      "evidence_type": "INDUSTRIAL_PROXIMITY",
      "feature_name": "industrial_distance_m",
      "value": "45.0m",
      "interpretation": "High industrial co-location: Hotspot detected 45m from Gujarat Refinery Complex.",
      "source": "OSM_OVERPASS",
      "confidence": 0.95
    }
  ]
}
```

#### `GET /api/hotspots/{hotspot_id}/risk`
- **Summary**: Composite operational risk prioritization score [0.0, 1.0].
- **Response `200 OK`**:
```json
{
  "hotspot_id": "firms_0e9fac8a6cf38741",
  "risk_score": 0.8875,
  "risk_level": "HIGH",
  "contributing_factors": [
    {
      "factor": "INDUSTRIAL_PROXIMITY",
      "weight": 0.40,
      "score": 1.0,
      "description": "Proximity to industrial infrastructure: 45 meters."
    }
  ],
  "explanation": "Hotspot assigned HIGH operational priority based on industrial proximity.",
  "limitations": "Operational risk score is a deterministic prioritization heuristic."
}
```

#### `GET /api/hotspots/{hotspot_id}/history`
- **Summary**: Historical recurrence statistics and past nearby detections ($t - 30\text{d} < t_{\text{hist}} < t$).

---

### 2.3 Industrial Sites API
#### `GET /api/industrial-sites`
- **Summary**: Query OSM-mapped industrial facilities with spatial bounding box filter.

#### `GET /api/industrial-sites/{site_id}`
- **Summary**: Industrial facility details and associated nearby thermal detections within 3km.

---

### 2.4 Analytics API
#### `GET /api/analytics/summary`
- **Summary**: Real database-derived summary statistics (hotspots by class, risk level, review status, land cover, sensor distribution).

---

### 2.5 Investigation Human-in-the-Loop API
#### `POST /api/investigations/{hotspot_id}/review`
- **Summary**: Submit analyst review decision (`CONFIRMED`, `REJECTED`, `ESCALATED`, `CORRECTED`).
- **Request Body**:
```json
{
  "decision": "CONFIRMED",
  "reviewer_id": "analyst_john_doe",
  "notes": "Verified against refinery CCTV telemetry.",
  "corrected_classification": null
}
```

#### `GET /api/investigations`
- **Summary**: Paginated history of persisted analyst review decisions.

---

### 2.6 Administrative Ingestion API
#### `POST /api/ingestion/firms`
- **Summary**: Triggers idempotent NASA FIRMS satellite telemetry ingestion.

---

## 3. Error Handling & HTTP Status Codes
- `200 OK`: Request succeeded.
- `201 Created`: Review record created successfully.
- `404 Not Found`: Hotspot or industrial site ID does not exist.
- `422 Unprocessable Entity`: Input validation failure (e.g. invalid lat/lon values).
- `500 Internal Server Error`: Generic internal server error (sanitized, stack traces hidden from client).
