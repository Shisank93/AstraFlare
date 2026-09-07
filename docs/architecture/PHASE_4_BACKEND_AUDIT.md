# AstraFlare Phase 4 — Backend Architecture & Integration Audit

**Date:** September 5, 2026  
**Auditor:** AstraFlare Senior Backend Engineering Team  
**Scope:** Repository Audit for Phase 4 Master Implementation  
**Status:** Audit Completed — Implementation Plan Prepared  

---

## 1. Executive Summary

AstraFlare is an AI-powered geospatial intelligence platform designed for detecting, contextualizing, prioritizing, and investigating thermal anomalies over India. In Phase 3 (3.8 through 3.11.1), the project successfully acquired 4,985,160 real NASA FIRMS observations (2023–2025 across India), constructed 4,310,499 physical event clusters, integrated GIHS industrial heat sites, FSI forest contexts, and external ground truth incident references, and established a scientifically defensible, bounded $[0,1]$ Evidence-Based Risk Engine.

Phase 4 transitions AstraFlare from research scripts and pipeline modules into a real, production-like backend system powered by FastAPI, PostgreSQL + PostGIS, real-time spatial indexing, robust API contracts, operational risk & priority intelligence, analyst review persistence, and seamless React frontend integration.

---

## 2. Current Architecture & Component Audit

### 2.1 Backend Architecture (`backend/`)
* **Framework:** FastAPI (`backend/app/main.py`) with Pydantic configuration (`backend/app/config.py`).
* **Current Endpoints:**
  * `GET /health` and `GET /ready` (basic liveness checks).
  * `GET /api/hotspots`, `GET /api/hotspots/geojson`, `GET /api/hotspots/{hotspot_id}`.
  * `GET /api/industrial-sites`, `GET /api/industrial-sites/{site_id}`.
  * `GET /api/analytics/summary`.
  * `POST /api/investigations/{hotspot_id}/review`, `GET /api/investigations`.
  * `POST /api/ingestion/firms`.
* **State Assessment:** Working API layout exists, but `db.py` contains a silent fallback to in-memory SQLite when PostgreSQL is disconnected. This violates Phase 4 REAL mode strictness (`ASTRAFLARE_MODE=REAL`).

### 2.2 Database Layer (`database/`)
* **Engines Supported:** PostgreSQL + PostGIS (production engine) and SQLite (sandboxed unit test engine).
* **Current Schema (`database/schema.sql`):**
  * `hotspots` (observation-level FIRMS detections).
  * `industrial_sites` (OSM and GIHS industrial facilities).
  * `land_cover` (ESA WorldCover classes).
  * `weather_observations` (ERA5 meteorological data).
  * `historical_features` (FRP statistical baseline).
  * `predictions` (ML model scores).
  * `evidence` (Traceable evidence statements).
  * `reviews` (Analyst investigation decisions).
  * `ground_truth_events` and `event_hotspot_matches` (External ground truth).
* **Identified Gap:** Physical event clusters (4.31 million events) built during Phase 3.9 exist as processed Parquet/CSV artifacts in `data/processed/`. Physical persistent storage in PostgreSQL + PostGIS with spatial indexing (`GEOMETRY(Point, 4326)`) and event-level intelligence fields is required to prevent loading 4.31M rows into Python memory during API calls.

### 2.3 Evidence & Risk Engine (`backend/risk_engine/` & `data_pipeline/`)
* **Phase 3.11 Deterministic Formula:**
  $$\text{Risk Score} = 0.30 \cdot \text{thermal} + 0.25 \cdot \text{historical} + 0.20 \cdot \text{industrial} + 0.10 \cdot \text{recurrence} + 0.10 \cdot \text{natural\_adjusted} + 0.05 \cdot \text{quality}$$
* **Thresholds & Risk Levels:**
  * LOW: $[0.00, 0.39]$
  * MEDIUM: $[0.40, 0.69]$
  * HIGH: $[0.70, 1.00]$
* **Investigation Priority Engine:** Distinct operational priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`) driven by industrial proximity ($\le 250\text{m}$ or $\le 1\text{km}$), anomaly Z-score ($\ge 3.0$), high FRP ($\ge 100\text{ MW}$), and land cover context (`Built-up`).
* **State Assessment:** Bounded, verified, and completely deterministic. Fully tested across 123 pytest suites.

### 2.4 ML Classifier Status (`ml/`)
* **Status:** `RESEARCH BASELINE — DATA-LIMITED`.
* **Governance Rule:** ML prediction MUST NOT drive operational prioritization due to severe shortage of independently verified industrial incident training labels (10 verified events total). Operational risk remains driven by the Phase 3.11 Evidence Engine.

### 2.5 Frontend Integration (`frontend/`)
* **Framework:** React + Vite + Leaflet / Mapbox GIS renderer.
* **Contract Expectations:** Expects GeoJSON FeatureCollection following RFC 7946 with coordinates in `[longitude, latitude]` order, viewport bounding box filtering (`bbox`), event investigation context, priority tags, evidence breakdown, historical stats, and review form submission.

---

## 3. Risks & Structural Issues Discovered

| # | Issue Identified | Impact | Remediation Plan |
|---|------------------|--------|------------------|
| 1 | Silent SQLite Fallback in `db.py` | In `REAL` mode, a DB connection failure silently creates an empty in-memory SQLite DB instead of failing. | Introduce `ASTRAFLARE_MODE` config (`REAL` default). In `REAL` mode, fail hard with a 503/DatabaseError if PostgreSQL/PostGIS is unreachable. |
| 2 | Event Data Persistence | 4.31M physical event clusters are currently loaded from CSV/Parquet in scripts rather than indexed in PostgreSQL. | Extend `database/schema.sql` with a physical `events` table including PostGIS geometry (`geom`), spatial GiST index, and B-tree indexes on timestamp, risk, priority, and review status. |
| 3 | RFC 7946 Coordinate Ordering | Map APIs must strictly return `[longitude, latitude]` rather than `[latitude, longitude]`. | Audit `hotspots.py` and ensure PostGIS `ST_AsGeoJSON` or GeoJSON converters construct `[lon, lat]` tuples. |
| 4 | NASA FIRMS MAP_KEY Protection | API endpoints must never leak `NASA_FIRMS_MAP_KEY` in URLs, logs, or responses. | Restrict key usage to backend server-side HTTP calls only. Scrub logs and response schemas. |
| 5 | Viewport Bounding Box (`bbox`) Queries | Downloading 4.31M events into client memory crashes browsers. | Implement PostGIS spatial bounding box query (`ST_Intersects` / `ST_MakeEnvelope`) on `/api/hotspots/geojson?bbox=minLon,minLat,maxLon,maxLat`. |

---

## 4. Recommended Implementation Sequence

1. **Governance & Configuration Layer:**
   * Update `backend/app/config.py` to add `ASTRAFLARE_MODE: str = "REAL"` (values: `REAL`, `DEMO`).
   * Update `database/db.py` connection manager: In `REAL` mode, enforce PostgreSQL/PostGIS requirement and fail clearly without silent SQLite fallback. Allow SQLite ONLY when `ASTRAFLARE_MODE == "DEMO"`.

2. **Database Schema & Event Persistence Strategy:**
   * Extend `database/schema.sql` with the unified `events` physical table schema containing all Phase 3.9/3.11 event fields.
   * Add spatial GiST index `idx_events_geom` and B-tree indexes on `acq_timestamp`, `risk_score`, `risk_level`, `investigation_priority`, `human_review_required`, and `data_source`.
   * Create idempotent database initializer `data_pipeline/sources/load_events_to_postgres.py` to ingest the processed physical event clusters into PostgreSQL.

3. **FastAPI Route Refactoring & Expansion:**
   * Refactor `/health` and `/ready` to report PostgreSQL connectivity, PostGIS availability, risk engine readiness, and ML research baseline status.
   * Update `/api/hotspots` and `/api/hotspots/geojson` to support RFC 7946 `[lon, lat]`, pagination, filtering, and PostGIS `bbox` queries.
   * Implement `/api/events/{event_id}` and detail endpoints (`/evidence`, `/risk`, `/history`, `/industrial-context`, `/review`).
   * Refactor `/api/investigations` to expose the analyst investigation queue ordered by `investigation_priority` (`URGENT` $\rightarrow$ `HIGH` $\rightarrow$ `MEDIUM` $\rightarrow$ `LOW`) and `risk_score DESC`.
   * Implement `POST /api/investigations/{event_id}/review` with audit trail persistence in `reviews` table.
   * Refactor `/api/analytics/summary` to compute real-time database SQL aggregations over the real India event population.
   * Audit `POST /api/ingestion/firms` to ensure server-side FIRMS ingestion without key exposure.

4. **Security, CORS & Error Handling:**
   * Configure explicit CORS origins for React frontend (`http://localhost:5174`, `http://localhost:3000`).
   * Ensure standard JSON error format (`{"error": {"code": "...", "message": "..."}}`).
   * Ensure zero leakage of DB passwords or API keys.

5. **Testing, Verification & Documentation:**
   * Expand pytest suite (`tests/test_phase_4_backend.py`) covering health, readiness, mode separation, GeoJSON RFC 7946, PostGIS bbox filtering, queue ordering, review audit trail, analytics, and security.
   * Execute full end-to-end verification script.
   * Generate required Phase 4 documentation artifacts (`PHASE_4_BACKEND_ARCHITECTURE.md`, `PHASE_4_API_CONTRACT.md`, `PHASE_4_DATABASE.md`, `REAL_MODE_NO_SILENT_FALLBACK.md`, `PHASE_4_END_TO_END_TEST.md`, `PHASE_4_BACKEND_COMPLETION_REPORT.md`).
