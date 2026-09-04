# ADR-008: Selection of MapLibre GL / Leaflet for Geospatial Visualization

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
The frontend requires responsive rendering of hundreds of thermal anomaly markers, industrial buffer polygons, and raster tile overlays.

**Decision:**  
Use **MapLibre GL JS** (with Leaflet as fallback) for map rendering.

**Alternatives Considered:**  
1. **Mapbox GL JS v2+:** Requires proprietary API token and billing account.
2. **Google Maps API:** Lacks native GeoJSON vector styling and high-density geospatial point clustering performance without complex wrappers.

**Trade-offs & Rationale:**  
MapLibre GL JS is open-source, uses WebGL hardware acceleration for smooth 60fps panning/zooming over vector tile layers, and requires no proprietary API keys for base vector styling.
