# Product Requirements Document (PRD)

**Project:** AstraFlare  
**Event:** Smart India Hackathon 2026 — Problem Statement SIH26162  
**Document Version:** 1.0 (MVP Scope)  

---

## 1. Vision & Core Value Proposition

NASA FIRMS reliably detects thermal anomalies globally but leaves analysts with a fundamental gap: **What does this thermal anomaly actually mean?**

AstraFlare transforms raw satellite thermal point detections into actionable geospatial intelligence by enriching each point with local industrial infrastructure, land cover, historical recurrence, and weather context.

---

## 2. Target Classes

1. **Likely Industrial Incident:** Unplanned, high-FRP surge near an industrial facility or refinery.
2. **Persistent Industrial Heat:** Expected, routine thermal signature (gas flares, kiln, steel mill) with high historical frequency and stable FRP.
3. **Natural/Wildland Fire:** Thermal anomaly occurring in forest, grassland, or agricultural land cover with low industrial infrastructure density.
4. **Human Review Required:** Abstention state triggered when model prediction uncertainty is high (confidence < 0.65) or when signals conflict.

---

## 3. Feature Scope Matrix

### MUST HAVE (Core MVP Requirements)
- [x] **NASA FIRMS Ingestion:** Automated ingestion and normalization of satellite thermal points (VIIRS/MODIS).
- [x] **PostgreSQL + PostGIS Database:** Spatial database schema storing hotspots, infrastructure, and land cover.
- [x] **GIS Contextual Enrichment:**
  - Distance to nearest industrial site (OSM Overpass query/cache).
  - Land cover type lookup (ESA WorldCover sampling).
  - Historical hotspot recurrence count & FRP stability ratio.
- [x] **Feature Engineering Pipeline:** Extraction of spatial, temporal, and thermal ratio features.
- [x] **Tabular ML Model:** Trained LightGBM/CatBoost classifier with probability outputs.
- [x] **Confidence & Abstention Mechanism:** Enforces "Human Review Required" state when model confidence is low.
- [x] **Evidence Generation Engine:** Explanatory text breakdown detailing why the classification was made.
- [x] **Risk Prioritization Engine:** Risk score calculation (0.0 to 1.0) for triage.
- [x] **FastAPI Backend:** Fully asynchronous REST endpoints with OpenAPI documentation.
- [x] **React + TypeScript Dashboard:**
  - Interactive MapLibre GL / Leaflet spatial viewer.
  - Triage Alert List sorted by risk and timestamp.
  - Event Investigation Panel with map focus, evidence metrics, and manual review override buttons.

### SHOULD HAVE (Extended MVP Capabilities)
- [ ] Environmental Weather Context (ERA5 / Open-Meteo wind speed, humidity, temperature).
- [ ] SHAP Feature Contribution Waterfall charts in investigation panel.
- [ ] Historical anomaly timeline for selected hotspot location.
- [ ] Aggregate analytics overview dashboard (incident distribution by region).

### NOT MVP (Out of Scope for Initial Hackathon MVP)
- Kubernetes orchestration & Kafka streaming clusters.
- Raw satellite imagery CNN segmentation or computer vision models.
- Microservice architecture split into separate micro-repos.
- Heavy enterprise multi-tenant role-based access control.

---

## 4. Non-Functional Requirements

1. **Inference Latency:** Sub-200ms end-to-end enrichment and ML classification latency per hotspot.
2. **Reliability & Offline Capability:** Local mock fallback adapters when external NASA FIRMS or OSM services are unavailable.
3. **Explainability:** 100% of classified events MUST include human-readable evidence statements.
