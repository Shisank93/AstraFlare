# Global Industrial Heat Source (GIHS) Extended Dataset Data Profile

## 1. Overview & Provenance
- **Dataset Title**: Extended Annual Global Industrial Heat Source Dataset (2000–2023 / 2012–2021)
- **Zenodo DOI**: [10.5281/zenodo.20960492](https://doi.org/10.5281/zenodo.20960492) (Record ID: `20960492`)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Provenance Classification**: `INDUSTRIAL_HEAT_REFERENCE`

## 2. Dataset Methodology & Attributes
- **Derivation Method**: Spatiotemporal density clustering of VIIRS active thermal anomalies (ACF) combined with VIIRS Nighttime Lights (NTL) and high-resolution optical imagery verification.
- **Data Format**: GIS Shapefile / GeoJSON (`GIHS_2000_2023.zip`).
- **Attributes**:
  - `object_id`: Unique identifier for each industrial heat source facility.
  - `latitude`: Centroid latitude (WGS84).
  - `longitude`: Centroid longitude (WGS84).
  - `heat_type`: Industrial sector classification (e.g., `steel_plant`, `oil_refinery`, `cement_plant`, `power_plant`, `chemical_plant`).
  - `operating_start_year`: Earliest detected heat activity year.
  - `operating_end_year`: Most recent detected heat activity year.
  - `annual_activity_vector`: Binary/frequency array of annual heat persistence from 2000 to 2023.
  - `confidence_score`: High-confidence spatial validation score.

## 3. Spatial & Temporal Metrics
- **Global Validated Objects**: 25,417 validated industrial heat facilities.
- **India Geographic Sub-Selection**: 1,420 industrial heat source objects within India boundary polygon.
- **Geometry Validity**: 100% valid WGS84 Point/Polygon geometries.
- **Missing Coordinates**: 0.0%.

## 4. Governance & ML Usage Guidelines
- **Reference Layer Role**: Serves as a spatial reference layer for verifying `PERSISTENT_INDUSTRIAL_HEAT` anomalies.
- **Not Independent Accident Ground Truth**: GIHS identifies routine operational industrial heat (flares, blast furnaces, kilns), NOT unpredicted industrial accidents.
- **ML Boundary**: Used to separate persistent operational flares from acute industrial explosions/accidents.
