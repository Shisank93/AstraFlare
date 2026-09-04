# REST API Architecture & OpenAPI Specification

**Project:** AstraFlare  
**Document:** Backend FastAPI Endpoints & Contract Specification  

---

## 1. OpenAPI Endpoint Specifications

### 1. System Health
- **`GET /api/health`**
  - **Description:** Checks API backend, PostGIS connectivity, and ML model status.
  - **Response (`200 OK`):**
    ```json
    {
      "status": "healthy",
      "version": "1.0.0",
      "database": "connected",
      "model_loaded": true
    }
    ```

---

### 2. Hotspots & Map Feature Feeds
- **`GET /api/hotspots`**
  - **Description:** Retrieves classified thermal anomaly alerts with filtering and pagination.
  - **Query Parameters:**
    - `classification` (optional): `Likely Industrial Incident`, `Persistent Industrial Heat`, `Natural/Wildland Fire`, `Human Review Required`.
    - `min_risk` (optional, float): Filter by minimum risk score (0.0 - 1.0).
    - `limit` (default: 50, max: 200).
  - **Response (`200 OK`):** Array of Hotspot Alert objects.

- **`GET /api/map/hotspots`**
  - **Description:** Returns classified thermal anomalies as a GeoJSON `FeatureCollection` optimized for MapLibre/Leaflet rendering.
  - **Response (`200 OK`):** GeoJSON FeatureCollection.

---

### 3. Detailed Event Inspection & Historical Timeline
- **`GET /api/hotspots/{id}`**
  - **Description:** Retrieves full event details, GIS contextual metrics, ML prediction breakdown, evidence list, and risk breakdown for a single hotspot.

- **`GET /api/hotspots/{id}/history`**
  - **Description:** Retrieves 12-month historical thermal anomaly observations within a 1km radius of the hotspot.

---

### 4. Real-time Ad-hoc Prediction
- **`POST /api/predict`**
  - **Description:** Accepts arbitrary thermal observation coordinate and attributes, runs GIS enrichment & ML inference, and returns real-time classification + evidence.
  - **Request Body:**
    ```json
    {
      "latitude": 22.3072,
      "longitude": 73.1812,
      "frp": 120.5,
      "brightness": 345.2,
      "satellite": "VIIRS"
    }
    ```
  - **Response (`200 OK`):**
    ```json
    {
      "hotspot_id": "adhoc_9921",
      "predicted_class": "Likely Industrial Incident",
      "confidence": 0.88,
      "is_abstained": false,
      "risk_score": 0.91,
      "evidence": [
        "Proximity to Gujarat Refinery Complex (320m) strongly indicates industrial origin.",
        "Current FRP (120.5 MW) is 3.1x higher than historical location baseline (38.8 MW).",
        "Land cover is classified as Built-up / Industrial."
      ]
    }
    ```

---

### 5. Analyst Review & Manual Override
- **`POST /api/hotspots/{id}/review`**
  - **Description:** Submits analyst override or verification status.
  - **Request Body:**
    ```json
    {
      "analyst_id": "analyst_sarah_01",
      "assigned_class": "Likely Industrial Incident",
      "review_status": "VERIFIED",
      "notes": "Verified with refinery operations log. Gas flare stack spike confirmed."
    }
    ```
