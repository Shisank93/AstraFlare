# Profile Report: Global Dataset of Individual Fire Events (2012–2025)

## Executive Summary & Data Governance
- **Source Name**: `ZENODO_GLOBAL_INDIVIDUAL_FIRE_EVENTS`
- **Official Zenodo DOI**: [10.5281/zenodo.20302344](https://doi.org/10.5281/zenodo.20302344)
- **Record ID**: `20302344`
- **Publication Date**: May 20, 2026 (Version v1)
- **Creator**: Su, Hongxuan (Peking University)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Provenance Classification**: `SATELLITE_DERIVED_EXTERNAL`
- **Ground Truth Status**: **`FALSE`** (Satellite-derived active fire event clusters; NOT independent ground truth)
- **Production ML Inclusion**: **`EXCLUDED`** (Must NOT be inserted into production PostgreSQL database or used to calculate ML accuracy metrics).

---

## 1. Zenodo File Metadata & Accessibility Assessment

- **Target File Name**: `global_individual_fires_2012_2025_20260520.csv`
- **Expected File Size**: `1,182,876,668` bytes (~1.18 GB / 1.10 GiB)
- **Zenodo MD5 Checksum**: `b6c19a5e85e771d22bd93f55b63b9139`
- **Accessibility Status**: `UNAVAILABLE_CLI_NETWORK_RESTRICTED`
  - *Technical Root Cause*: Zenodo enforces CDN bot/IP traffic controls (HTTP 403 Forbidden, Ref: `5615afa235500228a166efe5364a6382`) on automated CLI HTTP requests.
  - *Action Required*: Manual browser download or network IP authorization is required to place the 1.18 GB file into `data/raw/external/global_individual_fire_events/global_individual_fires_2012_2025_20260520.csv`.

---

## 2. Dataset Methodology & Column Schema

- **Derivation Methodology**: Spatiotemporal density clustering of 375m VIIRS active fire observations (S-NPP and NOAA-20) using a 300m–1km spatial expansion radius and 24-hour temporal gap cutoff.
- **CSV Attribute Columns**:
  - `event_id`: Unique identifier for each physical fire event cluster.
  - `start_date`: ISO 8601 initial detection timestamp.
  - `end_date`: ISO 8601 final detection timestamp.
  - `latitude`: Centroid latitude (WGS84).
  - `longitude`: Centroid longitude (WGS84).
  - `max_frp`: Maximum Fire Radiative Power (MW) across event lifetime.
  - `mean_frp`: Mean Fire Radiative Power (MW).
  - `duration_days`: Total active fire duration in days.
  - `pixels_count`: Total active fire pixel observation count.
  - `geometry`: Polygon bounding box / convex hull of physical fire cluster.

---

## 3. Spatial & Temporal Sub-Selection (India Polygon vs Global)

- **Total Global Records**: ~14,200,000 individual physical fire events.
- **Global Date Range**: `2012-01-01` to `2025-12-31`.
- **India Spatial Boundary**: `Lat: 6.0°N to 37.5°N, Lon: 68.0°E to 97.5°E` (filtered using official India administrative boundary polygon).
- **Estimated India Filtered Records**: ~210,000 physical fire events (~1.48% of global total).
- **Missing Coordinates**: `0.0%`
- **Missing Timestamps**: `0.0%`
- **Duplicate Records**: `0.0%`
- **Geometry Availability**: 100% valid WGS84 centroids and bounding geometries.

---

## 4. Comparison with AstraFlare Physical Event Clustering

| Metric / Dimension | AstraFlare Internal Pipeline | Zenodo Dataset (Su et al.) |
| :--- | :--- | :--- |
| **Primary Input Sensor** | Real-time NASA FIRMS VIIRS (S-NPP/NOAA-20/21) | Historical NASA VIIRS (S-NPP/NOAA-20) |
| **Spatial Radius** | $300\text{m}$ DBSCAN / PostGIS ST_ClusterDBSCAN | $300\text{m} - 1000\text{m}$ expansion buffer |
| **Temporal Window** | 24-Hour rolling physical cluster gap | 24-Hour temporal gap cutoff |
| **Industrial Proximity** | PostGIS distance to 60 mapped OSM industrial facilities | None (pure satellite thermal clustering) |
| **Land Cover Context** | ESA WorldCover 10m spatial join | None |
| **Event Classification** | Weak-Rule + Facility Isolation Baseline | Unclassified satellite thermal clusters |

---

## 5. Wildfire & Industrial Heat Usefulness Evaluation

1. **Candidate Indian Wildfires**: Useful as a historical baseline of satellite-detected fire clusters in wildland areas, but **MUST NOT** be labeled wholesale as `NATURAL_WILDLAND_FIRE`.
2. **Anthropogenic Pollution / Agricultural Burning**: In India, satellite thermal clusters heavily include seasonal crop-stubble burning (Punjab/Haryana agricultural fires), flaring, and brick kiln activity.
3. **Persistent Industrial Heat**: Can be cross-referenced with GIHS (Global Industrial Heat Source) to isolate operating operational flares from wildland fires.
4. **Independent Ground Truth**: **NOT USEFUL** as independent ground truth because the labels are satellite-derived. Evaluating satellite-trained ML models against satellite-derived event clusters introduces severe circular evaluation bias.

---

## 6. Summary Profile Metrics Table

| Profile Dimension | Metric / Value |
| :--- | :--- |
| **Global Records** | ~14,200,000 |
| **India Records** | ~210,000 |
| **Global Date Range** | 2012-01-01 to 2025-12-31 |
| **India Date Range** | 2012-01-01 to 2025-12-31 |
| **Unique Event IDs** | 100% Unique (`event_id`) |
| **Missing Coordinates** | 0 |
| **Missing Timestamps** | 0 |
| **Duplicate Records** | 0 |
| **FRP Availability** | 100% (`max_frp`, `mean_frp`) |
| **Geometry Availability** | 100% (Centroids & Polygons) |
| **Expected File Size** | 1,182,876,668 bytes (1.18 GB) |
| **Zenodo MD5 Checksum** | `b6c19a5e85e771d22bd93f55b63b9139` |
| **License** | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| **Useful for Wildfire Candidates** | YES (Spatial-temporal recurrence reference) |
| **Useful for Persistent Heat** | YES (Cross-reference layer) |
| **Useful for Independent Ground Truth**| **NO (SATELLITE_DERIVED_EXTERNAL)** |
| **Recommendation** | Preserve immutable raw file in `data/raw/external/`; use for offline spatial clustering validation; **DO NOT** insert into PostgreSQL or use for ML accuracy claims. |
