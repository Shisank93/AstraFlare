# System Architecture & End-to-End Workflow

**Project:** AstraFlare  
**Document:** System Architecture Specification  
**Status:** Approved Architectural Plan  

---

## 1. High-Level Architecture Diagram

```text
       +-------------------------------------------------------+
       |                 NASA FIRMS Satellites                 |
       |             (VIIRS / MODIS Active Fires)              |
       +---------------------------+---------------------------+
                                   | REST API / CSV Ingestion
                                   v
       +-------------------------------------------------------+
       |                 Data Ingestion Pipeline                |
       |         (Validation, Deduplication, Geocoding)        |
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |             PostgreSQL + PostGIS Database             |
       |  (Hotspots, Industrial Infrastructure, Land Cover)    |
       +---------------------------+---------------------------+
                                   | Spatial Queries
                                   v
       +-------------------------------------------------------+
       |               GIS Contextual Enrichment               |
       |   - OpenStreetMap Overpass (Industrial Proximity)     |
       |   - ESA WorldCover Raster (Land Cover Classification) |
       |   - Historical Thermal Anomaly Persistence            |
       +---------------------------+---------------------------+
                                   | Enriched Feature Vector
                                   v
       +-------------------------------------------------------+
       |               Feature Engineering Engine              |
       | (FRP anomaly score, spatial cluster density, weather)  |
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |               Tabular ML Inference Engine             |
       |           (LightGBM / CatBoost Classifier)            |
       +---------------------------+---------------------------+
                                   | Class Probabilities
                                   v
       +-------------------------------------------------------+
       |             Confidence & Abstention Module            |
       | (Enforces Human Review if Max Prob < Threshold 0.65)   |
       +---------------------------+---------------------------+
                                   | Validated Prediction
                                   v
       +-------------------------------------------------------+
       |            Evidence Engine & Risk Prioritizer          |
       | (Rules-based evidence text + Risk Score 0.0 - 1.0)    |
       +---------------------------+---------------------------+
                                   | JSON / GeoJSON Payload
                                   v
       +-------------------------------------------------------+
       |                    FastAPI REST API                   |
       |           (Endpoints: /api/hotspots, /api/predict)    |
       +---------------------------+---------------------------+
                                   | HTTP / JSON / WebSockets
                                   v
       +-------------------------------------------------------+
       |                 React Analyst Dashboard               |
       |    (Interactive MapLibre GL Map, Filterable Alerts,   |
       |     Investigation Panel, SHAP & Evidence Breakdown)   |
       +-------------------------------------------------------+
```

---

## 2. Layer Responsibilities & Data Flow

### 2.1 Ingestion Layer (`data_pipeline/`)
- Polls NASA FIRMS API or reads NRT batch exports.
- Standardizes thermal anomaly attributes (latitude, longitude, FRP, brightness, acquisition date/time, satellite source).
- Deduplicates nearby spatial-temporal observations within a 375m buffer window.

### 2.2 Storage Layer (`database/`)
- Persistent storage using PostgreSQL 15+ with PostGIS 3.3+.
- Stores raw thermal observations, industrial infrastructure geometries, land-cover rasters/polygons, historical statistics, and prediction audit logs.

### 2.3 GIS Enrichment & Feature Engineering Layer (`ml/` & `data_pipeline/`)
- **Industrial Proximity:** Computes distance to nearest industrial facility (factories, refineries, power plants, flare stacks) within 5km radius via PostGIS spatial indexing.
- **Land Cover Context:** Samples land-cover category (urban/built-up, cropland, tree cover, grassland, bare ground).
- **Historical Hotspot Analysis:** Computes spatial recurrence count within a 1km radius over the past 30, 90, and 365 days.
- **FRP Anomaly Ratio:** Calculates `current_FRP / mean_historical_FRP_for_location`.

### 2.4 ML Classification Layer (`ml/`)
- Evaluates the feature vector against a trained tabular gradient boosting model (LightGBM/CatBoost).
- Predicts class probabilities across 4 target classes:
  1. `Likely Industrial Incident`
  2. `Persistent Industrial Heat`
  3. `Natural/Wildland Fire`
  4. `Human Review Required` (Abstention state when maximum class confidence is below 0.65 or conflicting evidence exists).

### 2.5 Evidence Generation & Risk Engine
- Generates natural language evidence statements based on feature contributions and SHAP values (e.g., "Detections recurred 42 times at this exact point over 12 months with stable FRP").
- Computes operational risk score based on FRP magnitude, proximity to critical infrastructure, and confidence score.

### 2.6 Backend API Layer (`backend/`)
- Built on FastAPI with Pydantic v2 data validation.
- Exposes RESTful endpoints and GeoJSON structures for map rendering.

### 2.7 Frontend Application Layer (`frontend/`)
- Built with React, TypeScript, and MapLibre GL / Leaflet.
- Renders real-time geospatial alerts, interactive map layers, investigation panels, and evidence breakdowns.

---

## 3. Security, Logging, and Error Handling Boundaries

1. **Config Management:** Environment variable resolution using `pydantic-settings` and `.env`.
2. **Graceful Service Degradation:** Fallback adapters for NASA FIRMS, Overpass API, and ML inference.
3. **Structured Logging:** JSON logs with trace correlation IDs across backend endpoints.
4. **Security Boundaries:** API authentication, CORS policies restricting frontend origins, database connection pooling with SSL mode support.
