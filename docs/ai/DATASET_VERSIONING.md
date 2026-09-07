# AstraFlare Dataset Versioning Specification

## Version Manifest: `astra_flare_dataset_v0.2`

| Field | Value |
| :--- | :--- |
| **Dataset Version** | `astra_flare_dataset_v0.2` |
| **Release Date** | 2026-09-04 |
| **Temporal Scope** | 2026-08-28T07:22:00Z to 2026-09-04T15:54:00Z |
| **Geographic Scope** | South Asia ($5^{\circ}\text{N}$ to $37^{\circ}\text{N}$, $60^{\circ}\text{E}$ to $98^{\circ}\text{E}$) |
| **Sensors Included** | Suomi-NPP VIIRS (4,186), NOAA-20 VIIRS (4,145), MODIS Terra (222), MODIS Aqua (233) |
| **Total REAL Observations** | 8,786 |
| **Physical Event Clusters** | 3,180 |
| **Industrial Sites Mapped** | 39 total (17 active with detections) |
| **Independent External Events** | 6 (4 Wildfire, 2 Industrial Incident) |
| **Governance Classification** | `REAL` only |

## Label Distribution Summary

### Dataset A: WEAK_BASELINE (Weak Supervision Rules)
- `LIKELY_INDUSTRIAL_INCIDENT`: 15 (0.17%)
- `PERSISTENT_INDUSTRIAL_HEAT`: 180 (2.05%)
- `NATURAL_WILDLAND_FIRE`: 70 (0.80%)
- `UNLABELED`: 8,521 (96.98%)
- **Total Labeled**: 265 (3.02%)

### Dataset B: INDEPENDENT_EXTERNAL (Verified External Sources + Precedence)
- `LIKELY_INDUSTRIAL_INCIDENT`: 54 (0.61%)
- `PERSISTENT_INDUSTRIAL_HEAT`: 150 (1.71%)
- `NATURAL_WILDLAND_FIRE`: 70 (0.80%)
- `UNLABELED`: 8,512 (96.88%)
- **Total Labeled**: 274 (3.12%)
- **Matched External Hotspots**: 41 (from 1 physical fire cluster match)

## Feature Schema Versioning
- **Feature Contract Version**: v1.2
- **Columns**: 12 tabular features (`industrial_distance_m`, `industrial_count_1km`, `industrial_count_5km`, `frp`, `brightness`, `daynight_is_day`, `historical_count_30d`, `historical_mean_frp`, `frp_anomaly_zscore`, `land_cover_code`, `is_built_up_land`, `is_forest_land`).
