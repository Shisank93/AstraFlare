# ADR-001: Selection of PostGIS as Primary Spatial Engine

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:**  
AstraFlare requires performant spatial indexing, point-in-polygon queries, buffer searches, and raster sampling across satellite thermal points, industrial facility boundaries, and land-cover rasters.

**Decision:**  
Use **PostgreSQL with the PostGIS extension** as the core spatial database engine.

**Alternatives Considered:**  
1. **Pure Python (Shapely/GeoPandas in-memory):** High memory overhead, lacks persistent spatial indexing for multi-million observation scaling.
2. **MongoDB Geospatial:** Limited spatial reference system support, lacks advanced spatial joins (`ST_DWithin`, `ST_Intersection`) and raster integration.

**Trade-offs & Rationale:**  
PostGIS provides enterprise spatial indexing (GIST/SP-GIST), industry-standard OGC compliance, native metric distance calculations via geography data types, and direct integration with SQLAlchemy/GeoAlchemy2.
