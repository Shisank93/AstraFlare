# AstraFlare Phase 4 — Database Architecture & Schema Specification

**Date:** September 5, 2026  
**Engine:** PostgreSQL 15+ with PostGIS 3+ (EPSG:4326 WGS84)  
**Fallback Engine:** SQLite (Isolated Unit Test & DEMO Mode Only)  

---

## 1. Overview

AstraFlare Phase 4 establishes persistent, spatially indexed database storage for 4,310,499 physical event clusters across India (constructed from 4,985,160 real NASA FIRMS satellite observations spanning 2023–2025). 

To prevent loading 4.31 million events into Python memory during API requests, Phase 4 introduces a physical `events` table with PostGIS geometry indexing (`geom`), spatial bounding box support (`ST_MakeEnvelope`), and B-tree indexes across temporal, risk, priority, and review fields.

---

## 2. Table Definitions

### 2.1 `events` (Physical Event Clusters)
Primary physical storage table for Phase 3.9 event clusters and Phase 3.11 intelligence scores.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `event_id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique physical event cluster identifier |
| `event_timestamp` | `TIMESTAMP WITH TIME ZONE` | `NOT NULL` | Event start timestamp (ISO 8601) |
| `centroid_lat` | `DOUBLE PRECISION` | `CHECK (-90 <= lat <= 90)` | Centroid latitude in WGS84 |
| `centroid_lon` | `DOUBLE PRECISION` | `CHECK (-180 <= lon <= 180)` | Centroid longitude in WGS84 |
| `geom` | `TEXT` / `GEOMETRY(Point, 4326)` | `NOT NULL` | PostGIS WKT Point geometry |
| `duration_hours` | `DOUBLE PRECISION` | `DEFAULT 0.0` | Cluster temporal duration in hours |
| `observation_count` | `INTEGER` | `NOT NULL, DEFAULT 1` | Satellite detection count in cluster |
| `spatial_extent_m` | `DOUBLE PRECISION` | `DEFAULT 0.0` | Cluster spatial bounding diameter (m) |
| `max_frp` | `DOUBLE PRECISION` | `NOT NULL` | Maximum Fire Radiative Power (MW) |
| `mean_frp` | `DOUBLE PRECISION` | `NOT NULL` | Mean Fire Radiative Power (MW) |
| `std_frp` | `DOUBLE PRECISION` | `DEFAULT 0.0` | FRP standard deviation |
| `max_brightness` | `DOUBLE PRECISION` | `DEFAULT 0.0` | Max brightness temperature (K) |
| `confidence_high_ratio` | `DOUBLE PRECISION` | `DEFAULT 0.0` | Ratio of high-confidence observations |
| `satellite_count` | `INTEGER` | `DEFAULT 1` | Distinct observing satellite sensors |
| `industrial_distance_m` | `DOUBLE PRECISION` | | Geodesic distance to nearest industrial facility |
| `industrial_site_count_250m` | `INTEGER` | `DEFAULT 0` | Industrial sites within 250m |
| `industrial_site_count_1km` | `INTEGER` | `DEFAULT 0` | Industrial sites within 1km |
| `industrial_site_count_5km` | `INTEGER` | `DEFAULT 0` | Industrial sites within 5km |
| `worldcover_class` | `INTEGER` | | ESA WorldCover 10m land cover class code |
| `historical_count` | `INTEGER` | `DEFAULT 0` | Prior detections within 1km cell |
| `historical_mean_frp` | `DOUBLE PRECISION` | | Historical mean FRP baseline |
| `historical_anomaly_zscore` | `DOUBLE PRECISION` | | Anomaly Z-score relative to baseline |
| `data_source` | `VARCHAR(32)` | `NOT NULL, DEFAULT 'REAL'` | Governance tag: `REAL` vs `SYNTHETIC_DEMO` |
| `data_quality_status` | `VARCHAR(32)` | `DEFAULT 'HIGH'` | Quality status: `HIGH`, `MEDIUM`, `LOW` |
| `evidence_status` | `VARCHAR(32)` | `DEFAULT 'SUFFICIENT'` | Traceable evidence evaluation status |
| `risk_score` | `DOUBLE PRECISION` | `NOT NULL` | Composite operational risk score $[0.0, 1.0]$ |
| `risk_level` | `VARCHAR(16)` | `NOT NULL` | Operational risk level (`HIGH`, `MEDIUM`, `LOW`) |
| `investigation_priority` | `VARCHAR(16)` | `NOT NULL` | Operational priority (`URGENT`, `HIGH`, `MEDIUM`, `LOW`) |
| `human_review_required` | `BOOLEAN` | `DEFAULT FALSE` | Flag indicating analyst review gate |

### 2.2 Indexes
```sql
CREATE INDEX idx_events_timestamp ON events (event_timestamp DESC);
CREATE INDEX idx_events_lat_lon ON events (centroid_lat, centroid_lon);
CREATE INDEX idx_events_risk_score ON events (risk_score DESC);
CREATE INDEX idx_events_risk_level ON events (risk_level);
CREATE INDEX idx_events_priority ON events (investigation_priority);
CREATE INDEX idx_events_review ON events (human_review_required);
CREATE INDEX idx_events_data_source ON events (data_source);
-- PostGIS Spatial Index:
-- CREATE INDEX idx_events_geom ON events USING GIST (geom);
```

### 2.3 `reviews` (Analyst Review Audit Trail)
| Column | Type | Description |
|--------|------|-------------|
| `review_id` | `SERIAL PRIMARY KEY` | Auto-increment review record ID |
| `event_id` | `VARCHAR(64) NOT NULL` | Target physical event cluster ID |
| `hotspot_id` | `VARCHAR(64)` | Associated hotspot ID |
| `original_prediction` | `VARCHAR(64)` | Original model/rule classification |
| `final_classification` | `VARCHAR(64) NOT NULL` | Final analyst classification decision |
| `reviewer` | `VARCHAR(128)` | Analyst identity |
| `decision` | `VARCHAR(64) NOT NULL` | Decision: `CONFIRMED`, `DISMISSED`, `ESCALATED`, `NEEDS_MORE_DATA` |
| `review_status` | `VARCHAR(32)` | Current review status |
| `notes` | `TEXT` | Analyst notes and investigation justification |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Review submission timestamp |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Last update timestamp |

---

## 3. Idempotent Data Loading Mechanism

The script `data_pipeline/sources/load_events_to_postgres.py` streams `DATASET_C_ALL_EVENTS.csv` in 25,000-row chunks and performs bulk UPSERT operations (`ON CONFLICT (event_id) DO UPDATE`).

Running the loading script multiple times produces zero duplicate event records.
