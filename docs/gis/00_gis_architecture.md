# GIS & Spatial Architecture

**Project:** AstraFlare  
**Document:** GIS & Spatial Processing Specification  

---

## 1. Spatial Reference System & Coordinate Handling

- **Primary CRS:** WGS84 (`EPSG:4326`) for geographic storage, GeoJSON transmission, and MapLibre rendering.
- **Metric Projection for Distance Calculations:** `EPSG:3857` (Web Mercator) or local UTM zones (`EPSG:32643` / `EPSG:32644` for India) within PostGIS spatial queries `ST_Distance(geom1::geography, geom2::geography)`.

---

## 2. Spatial Query Pipeline

```text
FIRMS Thermal Point (EPSG:4326)
            │
            ▼
PostGIS Spatial Index (GIST)
            │
            ├──> ST_DWithin(geography, 5000m) ──> Nearest Industrial Site & Distance
            │
            ├──> ST_Value(WorldCover Raster)  ──> Land Cover Class (Forest / Urban / Farm)
            │
            └──> ST_Buffer + ST_Contains      ──> Historical Hotspot Count (30d / 365d)
            │
            ▼
Combined Spatial Feature Vector
```

---

## 3. Core PostGIS Operations

### 3.1 Proximity to Industrial Sites
```sql
SELECT 
    h.id AS hotspot_id,
    i.id AS industrial_site_id,
    i.name AS industrial_name,
    i.industrial_type,
    ST_Distance(h.geom::geography, i.geom::geography) AS dist_meters
FROM hotspots h
CROSS JOIN LATERAL (
    SELECT id, name, industrial_type, geom
    FROM industrial_sites
    WHERE ST_DWithin(h.geom::geography, geom::geography, 5000)
    ORDER BY h.geom::geography <-> geom::geography
    LIMIT 1
) i
WHERE h.id = :target_hotspot_id;
```

### 3.2 Historical Recurrence Aggregation
```sql
SELECT 
    COUNT(*) AS recurrence_count_365d,
    COALESCE(AVG(frp), 0.0) AS historical_mean_frp,
    COALESCE(MAX(frp), 0.0) AS historical_max_frp
FROM historical_hotspots
WHERE ST_DWithin(geom::geography, :target_geom::geography, 1000)
  AND acq_date >= CURRENT_DATE - INTERVAL '365 days';
```

---

## 4. GeoJSON Serialization Standard

All spatial API outputs conform to RFC 7946 GeoJSON:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [78.9629, 20.5937]
  },
  "properties": {
    "hotspot_id": "hs_98124",
    "frp": 142.5,
    "classification": "Likely Industrial Incident",
    "confidence": 0.89,
    "dist_industrial_m": 240,
    "nearest_industrial_name": "Jamnagar Refinery Complex",
    "landcover": "Built-up / Industrial",
    "risk_score": 0.92
  }
}
```
