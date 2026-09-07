# Global Dataset of Individual Fire Events (2012–2025) Data Profile

## 1. Overview & Provenance
- **Dataset Title**: A Global Dataset of Individual Fire Events (2012–2025) derived from VIIRS Active Fire Product
- **Zenodo DOI**: [10.5281/zenodo.21807914](https://doi.org/10.5281/zenodo.21807914) (Record ID: `20302344`)
- **Published**: August 2026 (Version v2.0)
- **Creators**: Su, Hongxuan et al.
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Provenance Classification**: `SATELLITE_DERIVED_EXTERNAL`

## 2. Dataset Methodology & Attributes
- **Derivation Method**: Spatiotemporal clustering of VIIRS 375m active fire detections (SNPP & NOAA-20) using a 300m–1km spatial expansion buffer and 24-hour temporal gap limit.
- **Attributes**:
  - `event_id`: Unique string identifier for individual physical fire events.
  - `start_date`: ISO timestamp of initial satellite observation.
  - `end_date`: ISO timestamp of final satellite observation.
  - `latitude`: Centroid latitude (WGS84).
  - `longitude`: Centroid longitude (WGS84).
  - `max_frp`: Maximum Fire Radiative Power (MW) observed during event lifetime.
  - `mean_frp`: Mean Fire Radiative Power (MW).
  - `duration_days`: Event duration in days.
  - `pixels_count`: Total active fire pixel count.
  - `geometry`: Polygon bounding spatial footprint of the fire cluster.

## 3. Spatial & Temporal Metrics
- **Global Row Count**: ~14,200,000 individual physical fire events.
- **Date Range**: 2012-01-01 to 2025-12-31.
- **India Geographic Extent**: `Lat: 6.0°N to 37.5°N, Lon: 68.0°E to 97.5°E`.
- **India Filtered Records**: ~210,000 physical fire events inside India boundary.
- **Missing Coordinates / Timestamps**: 0.0%.
- **Geometry Validity**: 100% valid WGS84 polygons/centroids.

## 4. Governance & ML Usage Guidelines
- **Not Independent Ground Truth**: Because events are clustered from VIIRS satellite detections, this dataset MUST NOT be treated as independent external ground truth for ML evaluation.
- **Role in AstraFlare**: Serves as a pre-clustered satellite reference dataset (`SATELLITE_DERIVED_EXTERNAL`) for validating physical event clustering algorithms and temporal recurrence baselines.
 