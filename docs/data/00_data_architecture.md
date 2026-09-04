# Data Architecture & Pipeline Specification

**Project:** AstraFlare  
**Document:** Data Architecture & Integration  

---

## 1. Overview & Data Flow

AstraFlare unifies satellite thermal observations with contextual geospatial, infrastructure, historical, and environmental datasets.

```text
[NASA FIRMS] ──> Ingestion ──> [PostGIS] ──> GIS Engine ──> Feature Vector ──> ML Classifier
[OSM Overpass] ───────────────> Ingestion ───^
[ESA WorldCover] ─────────────> Raster Engine ──^
[Historical FIRMS] ───────────> Aggregators ─────^
[ERA5 / Weather] ─────────────> API Adapter ──────^
```

---

## 2. Dataset Inventory & Specs

### 2.1 NASA FIRMS (Fire Information for Resource Management System)
- **Source:** NASA EOSDIS FIRMS REST API / CSV exports.
- **Purpose:** Primary active thermal anomaly detection points.
- **Key Fields:** `latitude`, `longitude`, `frp` (Fire Radiative Power), `brightness`, `acq_date`, `acq_time`, `confidence`, `daynight`, `satellite`.
- **Acquisition:** Polling via HTTPS REST (`/api/country/csv/{MAP_KEY}/VIIRS_SNPP_NRT/IND/1`).
- **Update Frequency:** Real-Time / Near Real-Time (every 3 hours / 15-minute NRT feed).
- **MVP Priority:** CRITICAL (Core Trigger).
- **Failure Behavior:** Fallback to local cached FIRMS dataset or synthetic sample generator.

### 2.2 OpenStreetMap (OSM) Industrial Infrastructure
- **Source:** OpenStreetMap via Overpass API / Overpass Turbo.
- **Purpose:** Industrial infrastructure proximity context.
- **Target OSM Keys:** `landuse=industrial`, `industrial=*`, `man_made=chimney`, `man_made=petroleum_well`, `man_made=flare_stack`, `power=plant`, `refinery=*`.
- **Key Fields:** `osm_id`, `name`, `industrial_type`, `geometry` (Polygon/Point).
- **Acquisition:** PostGIS Overpass API query or pre-downloaded GeoJSON/PBF spatial index.
- **MVP Priority:** HIGH.
- **Failure Behavior:** Fallback to pre-indexed industrial facility point layer in PostGIS.

### 2.3 ESA WorldCover
- **Source:** ESA WorldCover 10m land cover product.
- **Purpose:** Identifies surface land-cover type surrounding the anomaly.
- **Land Cover Classes:**
  - `10` Tree cover (Forest)
  - `20` Shrubland
  - `30` Grassland
  - `40` Cropland
  - `50` Built-up / Urban / Industrial land
  - `60` Bare / Sparse vegetation
  - `80` Permanent water bodies
- **Acquisition:** Cloud-Optimized GeoTIFF (COG) sampling or PostGIS raster lookup.
- **MVP Priority:** HIGH.

### 2.4 Historical FIRMS Observations
- **Source:** Archived NASA FIRMS 10-year observations.
- **Purpose:** Thermal recurrence baseline, cluster persistence, and FRP anomaly ratio computation.
- **Key Aggregates:** `historical_count_30d`, `historical_count_365d`, `mean_frp_location`, `max_frp_location`.
- **MVP Priority:** HIGH.

### 2.5 ERA5 / Open-Meteo Weather Data
- **Source:** ERA5 reanalysis / Open-Meteo REST API.
- **Purpose:** Environmental context (wind speed, direction, temperature, relative humidity).
- **Key Fields:** `wind_speed_10m`, `wind_direction_10m`, `temperature_2m`, `relative_humidity_2m`.
- **MVP Priority:** MEDIUM (Extended capability).

---

## 3. Data Integrity & Validation Rules

1. **Coordinate Validation:** Latitude must be within `[-90, 90]` and Longitude within `[-180, 180]`.
2. **FRP Range Check:** `frp >= 0.0`. Negative or NaN values are rejected.
3. **Temporal Deduplication:** Anomalies within 375m radius acquired within 30 minutes of a previous observation are merged into a single cluster record.
