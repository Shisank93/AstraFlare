# Spatial Queries & GIS Operations Guide

**Project:** AstraFlare  
**Document:** Spatial Query Optimization & GIS Function Reference  

---

## 1. PostGIS Spatial Operations Reference

### 1.1 Nearest Industrial Infrastructure Query
Finds the closest industrial facility within a search buffer (e.g. 5,000m / 10,000m) using PostGIS spatial indexing:

```sql
SELECT 
    id, osm_id, name, facility_type, tags,
    ST_Distance(
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
        geom::geography
    ) AS dist_meters
FROM industrial_sites
WHERE ST_DWithin(
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
    geom::geography, 
    :max_distance_m
)
ORDER BY ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography <-> geom::geography
LIMIT 1;
```

---

### 1.2 Industrial Site Count within Radius
Counts industrial features within a configurable metric buffer radius (e.g., 250m, 500m, 1,000m, 5,000m):

```sql
SELECT COUNT(*) AS site_count
FROM industrial_sites
WHERE ST_DWithin(
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
    geom::geography, 
    :radius_m
);
```

---

### 1.3 Historical Anomaly Recurrence & FRP Statistics
Calculates count, mean, max, and standard deviation of historical thermal anomalies within `radius_m` over `time_window_days`, **strictly excluding the target observation**:

```sql
SELECT 
    COUNT(*) AS historical_count,
    AVG(frp) AS historical_mean_frp,
    MAX(frp) AS historical_max_frp,
    STDDEV_SAMP(frp) AS historical_std_frp
FROM hotspots
WHERE ST_DWithin(
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
    geom::geography, 
    :radius_m
)
  AND acq_timestamp >= CURRENT_TIMESTAMP - INTERVAL '365 days'
  AND id != :exclude_hotspot_id;
```

---

## 2. Robust FRP Anomaly Z-Score Algorithm & Safeguards

```text
Formula: Z = (current_FRP - historical_mean) / historical_std
```

| Historical Data Condition | System Action & Output | Status Code |
| :--- | :--- | :--- |
| **Observation count = 0** | `anomaly_score = None` | `NO_HISTORY` |
| **Observation count < 3** | `anomaly_score = None` (Insufficient sample for std dev) | `INSUFFICIENT_DATA` |
| **std = 0.0 & current_FRP == mean** | `anomaly_score = 0.0` | `ZERO_STD` |
| **std = 0.0 & current_FRP > mean** | `anomaly_score = 10.0` (Capped upper limit) | `ZERO_STD` |
| **Normal case (count >= 3, std > 0)** | `anomaly_score = round(Z, 2)` | `VALID` |

---

## 3. Data Source Tagging & Governance

To ensure synthetic demo observations are **never** passed off as real NASA FIRMS satellite observations:

```sql
-- Production Query (Strictly isolates real satellite observations)
SELECT * FROM hotspots WHERE data_source = 'REAL';

-- Demo Query (Selects synthetic scenario dataset)
SELECT * FROM hotspots WHERE data_source = 'SYNTHETIC_DEMO';
```
