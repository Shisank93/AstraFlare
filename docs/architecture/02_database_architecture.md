# Database Architecture & PostGIS Schema

**Project:** AstraFlare  
**Document:** Database Schema & Entity Relationship Specification  

---

## 1. Relational Entity Relationship Diagram

```text
  +------------------+         +-------------------------+
  |     hotspots     | 1     * |       predictions       |
  |------------------|---------|-------------------------|
  | id (PK)          |         | id (PK)                 |
  | latitude         |         | hotspot_id (FK)         |
  | longitude        |         | predicted_class         |
  | frp              |         | confidence              |
  | brightness       |         | risk_score              |
  | acq_timestamp    |         | model_version           |
  | geom (Point,4326)|         | created_at              |
  +--------+---------+         +------------+------------+
           |                                | 1
           | 1                              |
           |                                | *
           v *                              v
  +------------------+         +-------------------------+
  |  gis_enrichment  |         |     evidence_logs       |
  |------------------|         |-------------------------|
  | id (PK)          |         | id (PK)                 |
  | hotspot_id (FK)  |         | prediction_id (FK)      |
  | dist_ind_m       |         | feature_name            |
  | industrial_name  |         | feature_value           |
  | land_cover_class |         | shap_impact             |
  | hist_count_365d  |         | summary_text            |
  +------------------+         +-------------------------+

  +-------------------+        +-------------------------+
  | industrial_sites  |        |     analyst_reviews     |
  |-------------------|        |-------------------------|
  | id (PK)           |        | id (PK)                 |
  | osm_id            |        | hotspot_id (FK)         |
  | name              |        | analyst_id              |
  | facility_type     |        | override_class          |
  | geom (Geometry)   |        | notes                   |
  +-------------------+        +-------------------------+
```

---

## 2. Table DDL Definitions (PostGIS SQL)

```sql
-- Enable PostGIS Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Raw Thermal Anomaly Hotspots Table
CREATE TABLE IF NOT EXISTS hotspots (
    id VARCHAR(64) PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    frp DOUBLE PRECISION NOT NULL,
    brightness DOUBLE PRECISION,
    confidence VARCHAR(16),
    satellite VARCHAR(32) NOT NULL,
    acq_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial GIST Index on Hotspot Geometries
CREATE INDEX IF NOT EXISTS idx_hotspots_geom ON hotspots USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_hotspots_timestamp ON hotspots (acq_timestamp DESC);

-- 2. Industrial Sites Reference Layer
CREATE TABLE IF NOT EXISTS industrial_sites (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR(64) UNIQUE,
    name VARCHAR(255),
    facility_type VARCHAR(64),
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industrial_geom ON industrial_sites USING GIST (geom);

-- 3. Enriched GIS Features Table
CREATE TABLE IF NOT EXISTS gis_enrichment (
    id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    dist_industrial_m DOUBLE PRECISION,
    nearest_industrial_name VARCHAR(255),
    facility_type VARCHAR(64),
    land_cover_class VARCHAR(64),
    historical_count_30d INTEGER DEFAULT 0,
    historical_count_365d INTEGER DEFAULT 0,
    historical_mean_frp DOUBLE PRECISION DEFAULT 0.0,
    frp_ratio_to_hist_mean DOUBLE PRECISION DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. ML Predictions Audit Log
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    predicted_class VARCHAR(64) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    is_abstained BOOLEAN DEFAULT FALSE,
    risk_score DOUBLE PRECISION NOT NULL,
    prob_industrial_incident DOUBLE PRECISION,
    prob_persistent_heat DOUBLE PRECISION,
    prob_wildland_fire DOUBLE PRECISION,
    model_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Evidence Detail Logs
CREATE TABLE IF NOT EXISTS evidence_logs (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    feature_name VARCHAR(64) NOT NULL,
    feature_value VARCHAR(128) NOT NULL,
    shap_impact DOUBLE PRECISION,
    summary_text TEXT NOT NULL
);

-- 6. Analyst Reviews & Overrides Table
CREATE TABLE IF NOT EXISTS analyst_reviews (
    id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    analyst_id VARCHAR(64) NOT NULL,
    assigned_class VARCHAR(64) NOT NULL,
    review_status VARCHAR(32) DEFAULT 'VERIFIED',
    notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
