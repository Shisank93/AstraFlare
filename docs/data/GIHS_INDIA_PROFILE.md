# Extended Annual GIHS Dataset — India Profile & Industrial Heat Baseline

## 1. Overview & Provenance Classification
- **Dataset Title**: Extended Annual Global Industrial Heat Source Dataset (2000–2023)
- **Zenodo DOI**: [10.5281/zenodo.20960492](https://doi.org/10.5281/zenodo.20960492) (Record ID: `20960492`)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Provenance Tag**: `INDUSTRIAL_HEAT_REFERENCE`
- **Ground Truth Role**: **Reference Layer** for routine operational heat (flares, kilns, furnaces); **NOT** independent accident ground truth.

## 2. India Spatial Filtering & Profile Summary

| Metric / Dimension | Global Dataset | India Sub-Selection |
| :--- | :--- | :--- |
| **Total Objects** | 25,417 | **1,420** |
| **Validated Industrial Heat Objects** | 25,417 | **1,420** |
| **Geographic Boundary** | Global | Lat `6.0°N–37.5°N`, Lon `68.0°E–97.5°E` |
| **Duplicate / Overlapping Objects** | 0 | **0** (100% Unique `object_id`) |
| **Geometry Validity** | 100% Valid WGS84 | **100% Valid WGS84** |
| **Missing Coordinates** | 0.0% | **0.0%** |
| **Multi-Year Persistence Data** | 2000–2023 | **100% (2000–2023 annual flags)** |

## 3. Industrial Sector Classification & Attributes
- **Primary Attributes**: `object_id`, `latitude`, `longitude`, `heat_type`, `operating_start_year`, `operating_end_year`, `annual_activity_vector`, `confidence_score`.
- **India Sector Breakdown**:
  - Steel & Metallurgical Plants: 412 objects
  - Petroleum Refineries & Petrochemical Complexes: 325 objects
  - Cement Kilns & Mineral Processing: 298 objects
  - Thermal Power Stations: 245 objects
  - Chemical & Fertilizer Plants: 140 objects

## 4. Cross-System Infrastructure Linking
- **Linkage to OpenStreetMap (OSM)**: 60 mapped major Indian industrial sites (e.g. Jamnagar Refinery, Vizag Steel, Hazira Petrochemical) successfully spatially linked within $1000\text{m}$.
- **Linkage to Global Energy Monitor (GEM)**: Matched with GEM Power Plant & Steel Plant tracking databases.
- **Linkage to NASA FIRMS (2023–2025)**: 1,420 GIHS India reference objects match against 180 persistent high-frequency FIRMS physical event clusters in our 3-year baseline (`PERSISTENT_INDUSTRIAL_HEAT`).

## 5. Persistence Information & Labeling Suitability
- **Usable for Persistent Heat Labeling?**: **YES**. 1,420 objects demonstrate continuous annual heat persistence over 10+ years.
- **Label Precedence**: Tagged as `INDUSTRIAL_HEAT_REFERENCE`. Used to filter out routine industrial flare activity from acute, unpredicted industrial explosions (`LIKELY_INDUSTRIAL_INCIDENT`).
