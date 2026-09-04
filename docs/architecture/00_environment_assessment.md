# Environment Assessment & Setup Report

**Project:** AstraFlare  
**Date:** September 4, 2026  
**Target Event:** Smart India Hackathon 2026 — Problem Statement SIH26162  

---

## 1. Executive Summary

This document captures the empirical inspection of the local environment, existing runtimes, system dependencies, database services, and external API prerequisites for AstraFlare.

The target directory `/Users/shisank_/Desktop/AstraFlame` was initially an empty directory. Git repository initialization and full monorepo directory scaffolding have been established.

---

## 2. Environment Telemetry & Runtime Audit

| Component / Tool | Detected Version / Status | Requirements | Action Required |
| :--- | :--- | :--- | :--- |
| **Operating System** | macOS (Darwin arm64) | macOS / Linux | Compatible |
| **Python** | `3.12.7` | Python 3.10+ | Available & Compatible |
| **Node.js** | `v23.8.0` | Node.js 18+ | Available & Compatible |
| **npm** | `10.9.2` | npm 9+ / pnpm / yarn | Available & Compatible |
| **Git** | Initialized (`main` branch) | Git 2.x+ | Repository initialized |
| **PostgreSQL** | `psql 18.4` installed; daemon STOPPED | PostgreSQL 14+ with PostGIS 3+ | Start local service or launch via Docker |
| **Docker** | Command not found | Docker & Docker Compose | Optional for local dev; recommended for deployment |

---

## 3. Python Dependency Audit

A audit of the active Python environment was performed:

### Available Core Libraries
- **API Backend:** `fastapi`, `uvicorn`, `pydantic`
- **Data & Math:** `pandas`, `scipy`
- **Machine Learning:** `scikit-learn` (`1.8.0`)
- **Database & HTTP:** `psycopg2`, `sqlalchemy`, `httpx`, `requests`, `python-dotenv`

### Missing Specialized Libraries (To Be Installed)
- **GIS / Spatial:** `geopandas`, `shapely`, `geoalchemy2`
- **Tabular ML Boosters:** `lightgbm`, `xgboost`, `catboost`
- **Explainability:** `shap`
- **Async Database:** `asyncpg`

---

## 4. Responsibility Matrix

### Automatable by Antigravity (AI / System)
- Generation of full source code (Backend, Frontend, ML pipeline, GIS enrichment modules).
- Scaffolding database schemas and PostGIS migration scripts.
- Creation of RESTful APIs, OpenAPI definitions, and GeoJSON transformers.
- React + TypeScript dashboard initialization and component construction.
- Unit and integration test suite creation.
- Docker Compose configuration and `.env.example` templating.

### Manual User Action Required
- **NASA FIRMS MAP_KEY:** Obtaining a personal API key from NASA FIRMS (`https://firms.modaps.eosdis.nasa.gov/api/map_key/`).
- **PostgreSQL / PostGIS Service Startup:** Starting the local PostgreSQL daemon (`brew services start postgresql`) or running `docker-compose up -d database`.
- **Environment Configuration:** Copying `.env.example` to `.env` and setting local secrets.
- **External Network Access:** Ensuring internet connectivity to reach OpenStreetMap Overpass API and NASA FIRMS endpoints.

---

## 5. Local Execution vs. Fallback Strategy

To ensure zero downtime during offline testing or when API keys are missing:

1. **NASA FIRMS Fallback:** If `NASA_FIRMS_MAP_KEY` is not provided or API calls fail, AstraFlare utilizes an isolated mock adapter with historical CSV datasets.
2. **OpenStreetMap Overpass Fallback:** If OSM Overpass times out, a local spatial index of key industrial facilities is queried.
3. **PostGIS Fallback:** SQLite with SpatiaLite capability or in-memory GeoPandas fallback can be leveraged for minimal isolated testing if PostGIS daemon is inactive.
