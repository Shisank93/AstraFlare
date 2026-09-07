# AstraFlare Phase 4 — Backend System Architecture

**Date:** September 5, 2026  
**Status:** Implemented & Verified  

---

## 1. Overview & System Purpose

AstraFlare is an AI-powered geospatial intelligence system designed for detecting, contextualizing, prioritizing, and investigating satellite-detected thermal anomalies across India. 

Phase 4 establishes the production-grade backend connecting:
$$\text{NASA FIRMS Real Data} \longrightarrow \text{PostgreSQL + PostGIS} \longrightarrow \text{GIS / Historical Telemetry} \longrightarrow \text{Evidence-Based Risk Engine} \longrightarrow \text{Investigation Queue} \longrightarrow \text{FastAPI REST} \longrightarrow \text{React Frontend}$$

---

## 2. Core Architectural Principles

1. **Deterministic Operational Risk Engine:** Operational prioritization is driven exclusively by the bounded $[0.00, 1.00]$ Phase 3.11 Evidence-Based Risk Engine, NOT by uncalibrated ML predictions.
2. **Explicit REAL / DEMO Mode Governance:**
   * `ASTRAFLARE_MODE=REAL` (Default): Requires active PostgreSQL + PostGIS. Rejects synthetic observations. Fails clearly on connection loss with standard JSON 503 database errors. Silent SQLite fallback is strictly prohibited.
   * `ASTRAFLARE_MODE=DEMO`: Explicitly enables synthetic demo scenarios. Every demo record is tagged `data_source = 'SYNTHETIC_DEMO'`.
3. **Persisted Physical Event Clusters:** 4,310,499 physical event clusters (constructed from 4.98M FIRMS detections over 2023–2025 across India) are persisted in PostgreSQL with spatial PostGIS GiST geometry indexes (`GEOMETRY(Point, 4326)`) and B-tree indexes for fast execution without memory loading.
4. **RFC 7946 GeoJSON Standard:** Map features strictly adhere to RFC 7946 with coordinates formatted as `[longitude, latitude]`.

---

## 3. Component Architecture & Data Flow

```
[ NASA FIRMS Feed / Local Archive ]
                │
                ▼
   [ PostgreSQL + PostGIS ]  ◄──── (Physical Events Table & Spatial GiST Index)
                │
        ┌───────┴───────┐
        ▼               ▼
[ GIS Engine ]  [ History Engine ]
        │               │
        └───────┬───────┘
                ▼
  [ Evidence-Based Risk Engine ] (Composite Score [0,1], Risk Level, Priority)
                │
                ▼
  [ Analyst Investigation Queue ] (Ordered by URGENT -> HIGH -> MEDIUM -> LOW)
                │
                ▼
       [ FastAPI REST APIs ]  ◄──── (OpenAPI Docs & Pydantic Validation)
                │
                ▼
   [ React Operational UI ]
```

---

## 4. Operational Risk & Priority Rules

$$\text{Risk Score} = 0.30 \cdot \text{thermal} + 0.25 \cdot \text{historical} + 0.20 \cdot \text{industrial} + 0.10 \cdot \text{recurrence} + 0.10 \cdot \text{natural\_adjusted} + 0.05 \cdot \text{quality}$$

* **Risk Levels:** LOW ($[0.00, 0.39]$), MEDIUM ($[0.40, 0.69]$), HIGH ($[0.70, 1.00]$).
* **Investigation Priority:** Operational priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`) is distinct from risk level. High FRP ($\ge 100\text{ MW}$), industrial proximity ($\le 250\text{m}$), or Z-score ($\ge 3.0$) elevate events to `URGENT` even when overall risk level is `MEDIUM`.
