# AstraFlare Phase 4 — API Specification & Contract

**Date:** September 5, 2026  
**Version:** 0.4.0  
**Specification:** RFC 7946 GeoJSON Compliant  

---

## 1. System Endpoints Overview

| Method | Path | Description | Access / Governance |
|--------|------|-------------|---------------------|
| `GET` | `/health` | Application liveness and connectivity status | Public |
| `GET` | `/ready` | Full readiness check (PostgreSQL/PostGIS, Risk Engine, ML baseline) | Operational |
| `GET` | `/api/hotspots` | Paginated thermal anomaly / physical event records | REAL / DEMO |
| `GET` | `/api/hotspots/geojson` | RFC 7946 GeoJSON FeatureCollection with PostGIS `bbox` filter | REAL / DEMO |
| `GET` | `/api/hotspots/{id}` | Detailed investigation context for single anomaly | REAL / DEMO |
| `GET` | `/api/events/{event_id}` | Unified physical event cluster intelligence object | REAL / DEMO |
| `GET` | `/api/events/{event_id}/evidence` | Structured traceable evidence statements | REAL / DEMO |
| `GET` | `/api/events/{event_id}/risk` | Bounded $[0,1]$ operational risk prioritization breakdown | REAL / DEMO |
| `GET` | `/api/events/{event_id}/history` | Historical baseline FRP telemetry and recurrence | REAL / DEMO |
| `GET` | `/api/events/{event_id}/industrial-context` | OpenStreetMap & GIHS facility proximity telemetry | REAL / DEMO |
| `GET` | `/api/events/{event_id}/review` | Persisted analyst review decision status | REAL / DEMO |
| `GET` | `/api/investigations` | Analyst investigation queue ordered by priority and risk | Analyst |
| `POST` | `/api/investigations/{event_id}/review` | Submit human analyst review decision with audit trail | Analyst |
| `GET` | `/api/analytics/summary` | Real-time database SQL analytical aggregations | Operational |
| `GET` | `/api/industrial-sites` | Query mapped OSM/GIHS industrial facilities | Public / Context |
| `GET` | `/api/industrial-sites/{site_id}` | Industrial facility details and nearby thermal events | Public / Context |
| `POST` | `/api/ingestion/firms` | Server-side NASA FIRMS telemetry fetch (Protected MAP_KEY) | Admin / Backend |

---

## 2. GeoJSON FeatureCollection Specification (`GET /api/hotspots/geojson`)

Follows RFC 7946. Coordinates MUST BE formatted as `[longitude, latitude]`.

### Query Parameters:
* `bbox`: `minLon,minLat,maxLon,maxLat` (e.g. `72.5,18.0,74.0,19.5`)
* `start_date` / `date_from`: ISO timestamp string
* `end_date` / `date_to`: ISO timestamp string
* `risk_level`: `HIGH` | `MEDIUM` | `LOW`
* `priority`: `URGENT` | `HIGH` | `MEDIUM` | `LOW`
* `data_source`: `REAL` | `SYNTHETIC_DEMO`
* `limit`: Max feature count (default `500`, max `2000`)

### Example Response:
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
        "id": "evt_10000_24533_2024-12-24",
        "latitude": 22.3088,
        "longitude": 73.1825,
        "acq_timestamp": "2024-12-24T08:57:00Z",
        "frp": 120.5,
        "risk_level": "HIGH",
        "priority": "URGENT",
        "review_required": true,
        "data_source": "REAL"
      }
    }
  ]
}
```

---

## 3. Physical Event Intelligence Specification (`GET /api/events/{event_id}`)

### Example Response:
```json
{
  "event_id": "evt_10000_24533_2024-12-24",
  "event": {
    "event_id": "evt_10000_24533_2024-12-24",
    "timestamp": "2024-12-24T08:57:00Z",
    "observation_count": 5,
    "duration_hours": 2.5,
    "satellite": "VIIRS"
  },
  "location": {
    "latitude": 22.3088,
    "longitude": 73.1825
  },
  "detection": {
    "frp": 120.5,
    "brightness": 345.2,
    "confidence": "high"
  },
  "industrial_context": {
    "nearest_distance_m": 250.0,
    "site_count_1km": 3,
    "nearest_site_name": "Gujarat Refinery Power Plant"
  },
  "historical_context": {
    "previous_count": 0,
    "historical_mean_frp": null,
    "frp_anomaly_zscore": null,
    "status": "NO_PRIOR_HISTORY"
  },
  "natural_context": {
    "land_cover_code": 50,
    "land_cover_name": "Built-up",
    "score": 0.10
  },
  "risk": {
    "score": 0.8540,
    "level": "HIGH",
    "components": {
      "thermal": 0.85,
      "historical": 0.0,
      "industrial": 0.95,
      "natural": 0.10,
      "quality": 1.0
    }
  },
  "investigation": {
    "priority": "URGENT",
    "human_review_required": true,
    "reason_codes": ["NEAR_INDUSTRIAL_INFRASTRUCTURE", "HIGH_THERMAL_INTENSITY"],
    "review_status": "PENDING"
  },
  "provenance": {
    "data_source": "REAL",
    "verification_status": "WEAK_RULE"
  }
}
```

---

## 4. Analyst Review Submission (`POST /api/investigations/{event_id}/review`)

### Request Body:
```json
{
  "reviewer_id": "analyst_007",
  "decision": "CONFIRMED",
  "notes": "Verified industrial flare thermal signature.",
  "corrected_classification": "PERSISTENT_INDUSTRIAL_HEAT"
}
```

### Response Schema:
```json
{
  "review_id": 1,
  "hotspot_id": "evt_10000_24533_2024-12-24",
  "original_prediction": "LIKELY_INDUSTRIAL_INCIDENT",
  "final_classification": "PERSISTENT_INDUSTRIAL_HEAT",
  "review_status": "CONFIRMED",
  "analyst_note": "Verified industrial flare thermal signature.",
  "reviewer_id": "analyst_007",
  "created_at": "2026-09-05T14:45:00Z",
  "updated_at": "2026-09-05T14:45:00Z"
}
```
