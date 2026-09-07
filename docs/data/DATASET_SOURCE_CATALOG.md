# AstraFlare Dataset Source Catalog & Real Data Discovery

## Executive Overview

This catalog documents potential, candidate, and integrated real-world data sources for AstraFlare satellite thermal observation ingestion, GIS contextual enrichment, industrial infrastructure mapping, and independent ground-truth verification.

---

## Category A: NASA FIRMS (Fire Information for Resource Management System)

### 1. NASA FIRMS NRT & Archive API
- **Organization:** NASA LANCE / EOSDIS
- **URL:** `https://firms.modaps.eosdis.nasa.gov/api/`
- **Product Name:** VIIRS NRT (SNPP, NOAA-20, NOAA-21), MODIS NRT (Terra, Aqua)
- **Spatial Coverage:** Global (South Asia bounding box: Lat `5.0` to `38.5`, Lon `60.0` to `100.0`)
- **Temporal Coverage:** 2000–present (MODIS), 2012–present (VIIRS SNPP), 2018–present (NOAA-20), 2023–present (NOAA-21)
- **Resolution:** 375m (VIIRS I-band), 1km (MODIS)
- **Key Fields:** `latitude`, `longitude`, `bright_ti4`, `bright_ti5`, `frp`, `acq_date`, `acq_time`, `satellite`, `instrument`, `confidence`, `daynight`
- **Access Method:** REST API (`/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA}/{DAYS}`) & HTTP Archive CSV downloads
- **API Key Required:** Yes (Free NASA LANCE MAP_KEY)
- **Rate Limits:** 10 requests/minute (API), Unlimited (FTP/HTTP Archive bulk downloads)
- **License:** Public Domain / NASA Open Data Policy
- **Local Storage:** Yes (Stored in PostgreSQL `hotspots` table)
- **ML Suitability:** Primary Telemetry Observation Input
- **Environment Accessibility:** ACCESSIBLE (Currently powering AstraFlare with 8,786 REAL observations)
- **Limitations:** Satellite thermal detections only; requires contextual enrichment to distinguish industrial flares from wildfires or accidents.

---

## Category B: Global Forest Watch (GFW)

### 2. Global Forest Watch Fire Alerts API
- **Organization:** World Resources Institute (WRI)
- **URL:** `https://www.globalforestwatch.org/` / `https://data-api.globalforestwatch.org/`
- **Product Name:** VIIRS Active Fire Alerts & Integrated Deforestation/Fire Alerts
- **Spatial Coverage:** Global
- **Temporal Coverage:** 2012–present
- **Resolution:** 375m
- **Key Fields:** `latitude`, `longitude`, `alert__date`, `confidence__cat`, `is__umd_tree_cover_loss`
- **Access Method:** REST API (`/dataset/gfw_active_fires/latest/query`) & GeoTIFF/CSV download
- **API Key Required:** Yes (WRI Data API Key)
- **Rate Limits:** Standard web rate limits
- **License:** Creative Commons Attribution 4.0 (CC-BY 4.0)
- **Local Storage:** Allowed
- **ML Suitability:** Secondary Corroboration & Forest Fire Filtering
- **Environment Accessibility:** ACCESSIBLE via API
- **Limitations:** Derived from VIIRS observations; cannot serve as 100% independent non-satellite ground truth.

---

## Category C: Official Indian & Regional Incident Registries

### 3. PESO Industrial Accident & Major Hazard Incident Registry
- **Organization:** Petroleum and Explosives Safety Organisation (PESO), Ministry of Commerce & Industry, Govt. of India
- **URL:** `https://peso.gov.in/`
- **Product Name:** Major Accident Hazard (MAH) Units & Incident Reports
- **Spatial Coverage:** India (National)
- **Temporal Coverage:** Multi-year historical registry
- **Resolution:** Facility-level & District-level coordinates
- **Key Fields:** `unit_name`, `state`, `district`, `hazard_category`, `accident_date`, `fatality_count`, `chemical_involved`
- **Access Method:** Web portal reports & official gazette publications
- **API Key Required:** No (Manual/Scraped Registry)
- **License:** Government Open Data / Public Domain
- **Local Storage:** Allowed
- **ML Suitability:** High-Confidence Independent Ground Truth for `LIKELY_INDUSTRIAL_INCIDENT`
- **Environment Accessibility:** LIMITED (Requires web scraping/manual parsing of PDF gazettes)
- **Limitations:** Low spatial precision in legacy text reports (often specifies city/district rather than exact lat/lon).

### 4. Forest Survey of India (FSI) Fire Monitoring System
- **Organization:** Forest Survey of India, Ministry of Environment, Forest and Climate Change (MoEFCC)
- **URL:** `https://fsi.nic.in/` / `https://fsiforestfire.gov.in/`
- **Product Name:** FSI Van Agni Geo-Portal / Large Forest Fire Events
- **Spatial Coverage:** India Forest Divisions
- **Temporal Coverage:** 2004–present
- **Resolution:** Forest beat/range polygon level
- **Key Fields:** `state`, `division`, `range`, `beat`, `fire_date`, `suppression_status`, `affected_area_ha`
- **Access Method:** Geo-Portal WMS/WFS & Daily Fire Bulletins
- **API Key Required:** No
- **License:** Government Open Data
- **Local Storage:** Allowed
- **ML Suitability:** Independent Ground Truth for `NATURAL_WILDLAND_FIRE`
- **Environment Accessibility:** ACCESSIBLE (via RSS/WFS and web scraping)
- **Limitations:** Restricted to forested administrative land; does not track industrial safety incidents.

---

## Category D: Global Wildfire & Environmental Incident Registries

### 5. GWIS (Global Wildfire Information System) & EFFIS
- **Organization:** Copernicus Emergency Management Service / GEO / NASA
- **URL:** `https://gwis.jrc.ec.europa.eu/`
- **Product Name:** GWIS Country Profile & Fire Event Database
- **Spatial Coverage:** Global
- **Temporal Coverage:** 2001–present
- **Resolution:** Individual Fire Event Polygons (spatial perimeter)
- **Key Fields:** `event_id`, `initial_date`, `final_date`, `burnt_area_ha`, `country`, `geometry`
- **Access Method:** JRC WFS Service & REST API
- **API Key Required:** No
- **License:** Open Access (Copernicus Data Policy)
- **Local Storage:** Allowed
- **ML Suitability:** High-Quality Ground Truth for `NATURAL_WILDLAND_FIRE`
- **Environment Accessibility:** ACCESSIBLE
- **Limitations:** Focuses primarily on wildland fires $> 30 \text{ ha}$.

---

## Category E: Industrial Infrastructure & Facility Geospatial Registries

### 6. OpenStreetMap (OSM) Overpass API
- **Organization:** OpenStreetMap Foundation
- **URL:** `https://overpass-api.de/api/interpreter`
- **Product Name:** OSM Landuse, Industrial Tags & Infrastructure Features
- **Spatial Coverage:** Global
- **Temporal Coverage:** Real-time / Continuously Updated
- **Resolution:** Exact Polygonal / Point Boundaries
- **Key Fields:** `osm_id`, `name`, `industrial`, `man_made`, `plant:source`, `refinery`, `generator:source`, `geometry`
- **Access Method:** Overpass QL API / Overpass Turbo
- **API Key Required:** No
- **Rate Limits:** 2 concurrent requests, max 10,000 nodes per query
- **License:** Open Database License (ODbL)
- **Local Storage:** Allowed (Stored in PostgreSQL `industrial_sites` table)
- **ML Suitability:** Spatial Context Feature Generator & Weak Label Auxiliary Input
- **Environment Accessibility:** ACCESSIBLE (Currently powering AstraFlare with 60 mapped industrial facilities)
- **Limitations:** Crowdsourced tagging completeness varies by geographic region.

### 7. Global Energy Monitor (GEM) Trackers
- **Organization:** Global Energy Monitor
- **URL:** `https://globalenergymonitor.org/`
- **Product Name:** Global Oil and Gas Plant Tracker (GOGPT), Global Power Plant Tracker (GPPT)
- **Spatial Coverage:** Global
- **Temporal Coverage:** Updated semi-annually
- **Resolution:** Exact Point Coordinates (`latitude`, `longitude`)
- **Key Fields:** `project_name`, `owner`, `capacity_mw`, `status`, `country`, `latitude`, `longitude`, `fuel_type`
- **Access Method:** Direct CSV / XLSX Open Data Download
- **API Key Required:** No
- **License:** Creative Commons Attribution 4.0 (CC-BY 4.0)
- **Local Storage:** Allowed
- **ML Suitability:** High-Precision Industrial Facility Ground-Truth Verification
- **Environment Accessibility:** ACCESSIBLE (Open CSV download)
- **Limitations:** Limited to major power and oil/gas plants; smaller manufacturing units excluded.

---

## Category F: Meteorological & Atmospheric Data

### 8. ECMWF ERA5 & ERA5-Land Reanalysis
- **Organization:** European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Climate Change Service (C3S)
- **URL:** `https://cds.climate.copernicus.eu/`
- **Product Name:** ERA5-Land Hourly Data
- **Spatial Coverage:** Global
- **Temporal Coverage:** 1950–present
- **Resolution:** 9km ($0.1^\circ \times 0.1^\circ$)
- **Key Fields:** `2m_temperature`, `10m_u_component_of_wind`, `10m_v_component_of_wind`, `total_precipitation`, `surface_pressure`
- **Access Method:** CDS API (`cdsapi` Python package)
- **API Key Required:** Yes (Free CDS User Key)
- **Rate Limits:** Queue-based batch processing
- **License:** Copernicus License
- **Local Storage:** Allowed
- **ML Suitability:** Atmospheric Feature Enrichment (wind-vector fire spread & humidity suppression)
- **Environment Accessibility:** ACCESSIBLE via CDS API
- **Limitations:** 5-day latency for ERA5-Land NRT data.
