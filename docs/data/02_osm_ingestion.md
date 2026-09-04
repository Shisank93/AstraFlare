# OpenStreetMap Industrial Infrastructure Ingestion

**Project:** AstraFlare  
**Document:** Overpass API Query Design, Geometry Normalization & Caching  

---

## 1. Overpass API Query Strategy

AstraFlare queries OpenStreetMap via Overpass API using a **contextual buffer search around thermal anomaly coordinates** to avoid downloading unneeded global datasets:

- **Overpass API Endpoint:** `https://overpass-api.de/api/interpreter`
- **Target OSM Keys & Values:**
  - `landuse=industrial`
  - `industrial=*` (e.g. `refinery`, `chemical`, `oil`, `gas`, `factory`, `port`)
  - `man_made=chimney` / `man_made=petroleum_well` / `man_made=flare_stack`
  - `power=plant` / `power=substation`
- **Overpass QL Template:**
  ```overpassql
  [out:json][timeout:25];
  (
    node["landuse"="industrial"](around:5000, 22.3072, 73.1812);
    way["landuse"="industrial"](around:5000, 22.3072, 73.1812);
    relation["landuse"="industrial"](around:5000, 22.3072, 73.1812);
    node["man_made"="flare_stack"](around:5000, 22.3072, 73.1812);
    way["refinery"](around:5000, 22.3072, 73.1812);
  );
  out center;
  ```

---

## 2. Geometry Normalization & PostGIS Caching

- **Geometry Support:** Normalizes OSM `Node` (Point), `Way` (Polygon/Linestring centroid), and `Relation` into PostGIS geometries (`EPSG:4326`).
- **Database-First Caching:** PostGIS `industrial_sites` table serves as the primary cache layer. Overpass API is queried only if no cached sites exist within the target search radius.
