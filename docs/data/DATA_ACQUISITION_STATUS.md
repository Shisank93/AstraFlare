# AstraFlare Data Acquisition Status & ML Readiness Summary

## 1. Data Source Accessibility Matrix

| Source Name | Category | Status | Access Method | Dataset Size | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA FIRMS Archive** | Historical Thermal Anomaly | **ACQUIRED & REGISTERED** | Official CSV Download | **4,985,160 REAL obs** (3-Year Baseline) | Multi-Year Telemetry |
| **NASA FIRMS NRT** | Live Rolling Stream | **ACCESSIBLE** | REST API | 8,786 REAL obs (7-day NRT) | Real-Time Telemetry |
| **Zenodo Global Fire Events** | Pre-Clustered Fire Events | **PROFILED** | Zenodo DOI `10.5281/zenodo.20302344` | ~210,000 India events | Satellite Reference Layer |
| **GIHS Extended Dataset** | Industrial Heat Reference | **PROFILED** | Zenodo DOI `10.5281/zenodo.20960492` | 1,420 India heat sites | Persistent Heat Baseline |
| **OpenStreetMap (OSM)** | Industrial Infrastructure | **ACCESSIBLE** | Overpass API | 60 Facilities | Spatial Context |
| **ESA WorldCover** | Land-Use Classifier | **ACCESSIBLE** | Offline GeoTIFF | Global 10m Land Cover | Environmental Context |
| **PESO / SDMA Incident Registry** | Industrial Ground Truth | **LIMITED** | Gazette Parsing / Scraped | 4 Verified Incidents | Independent Validation |
| **Forest Survey India (FSI)** | Forest Fire Alerts | **ACCESSIBLE** | Geo-Portal / WFS | 70 Matched Wildfires | Independent Validation |

---

## 2. Updated Scientific & Data Acquisition Metrics

- **Accessible Sources:** NASA FIRMS Download Portal, Zenodo repositories, OSM Overpass API, ESA WorldCover, FSI Geo-Portal, GEM.
- **Total REAL Records Acquired:** **4,985,160 REAL satellite observations** (3-year historical archive 2023-01-01 to 2025-12-31) + **8,786 REAL NRT observations**.
- **Unique Physical Events (NRT):** 3,176 physical thermal event clusters.
- **Independent Industrial Incidents:** 4 verified external incidents (`VERIFIED_EXTERNAL`).
- **Independent Wildfires:** 70 physical events with FSI/ESA Forest context (`WEAK_RULE`).
- **Persistent Industrial Heat Ref Objects:** 1,420 industrial heat objects (GIHS reference layer).
- **Actual Date Range:** `2023-01-01` to `2025-12-31` (Historical Baseline) & `2026-08-28` to `2026-09-04` (Live NRT).
- **Geographic Region:** India (`Lat: 6.0°N to 37.5°N, Lon: 68.0°E to 97.5°E`).
- **Production ML Readiness:** `DATA-LIMITED / RESEARCH BASELINE` (Multi-year historical dataset acquired; independent ground truth expanding).
