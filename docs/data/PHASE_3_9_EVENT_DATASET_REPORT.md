# Phase 3.9 — Event-Level Dataset Construction & Quality Report

## 1. Overview & Dataset Architecture
- **Objective**: Transform 4,985,160 raw NASA FIRMS satellite observations (2023–2025 India) into a unified, physical event-level dataset (**DATASET_C_EVENT_LEVEL**).
- **Physical Event Unit**: One row represents one distinct physical fire/heat event cluster (300m spatial grid $\times$ 24h temporal gap), NOT an isolated satellite detection pass.
- **Total Processed Satellite Observations**: **4,985,160**
- **Total Unified Physical Event Clusters**: **4,310,499**
- **Temporal Coverage**: 2023-01-01 to 2025-12-31 (3 Full Years)
- **Geographic Bounds**: India (`Lat: 6.0°N to 37.5°N, Lon: 68.0°E to 97.5°E`)

---

## 2. Event Clustering & Physical Aggregation Metrics

| Metric / Attribute | Value | Description |
| :--- | :--- | :--- |
| **Spatial Radius Threshold** | $300\text{m}$ (0.003°) | DBSCAN / Spatial Grid Cell Boundary |
| **Temporal Gap Threshold** | 24 Hours (1 Day) | Physical fire event continuity cutoff |
| **Cross-Sensor Fusion** | VIIRS NOAA-20 + NOAA-21 + S-NPP + MODIS | Merged multi-satellite passes |
| **Total Physical Events** | **4,310,499** | Unified event-level records |
| **Mean Observations per Event** | **1.16** | Average satellite detections per physical event |
| **Median Observations per Event**| **1** | Median satellite detections per physical event |
| **Max Observations for an Event**| **18** | High-persistence multi-pass industrial/wildfire cluster |

---

## 3. Event-Level Feature Architecture

For every physical event cluster, 25 feature columns were extracted without temporal leakage:

1. **Temporal Features**: `event_start`, `event_end`, `duration_hours`, `observation_count`.
2. **Fire Intensity Features**: `max_frp`, `mean_frp`, `std_frp`, `max_brightness`, `mean_brightness`, `confidence_high_ratio`, `satellite_count`.
3. **Spatial Proximity Features**: `centroid_lat`, `centroid_lon`, `spatial_extent_m`, `industrial_distance_m`, `industrial_site_count_250m`, `industrial_site_count_1km`, `industrial_site_count_5km`.
4. **Land Cover Context**: `worldcover_class` (ESA 10m land cover class).
5. **Causal Historical Features**: Past-only spatial recurrence counters and FRP baseline statistics (strictly before `event_start`).

---

## 4. Provenance Hierarchy & Class Distribution

Per **AstraFlare Data Governance Rules**, labels are assigned strictly using the provenance hierarchy ($\text{VERIFIED\_EXTERNAL} > \text{MANUAL\_VERIFIED} > \text{WEAK\_RULE} > \text{UNLABELED}$):

| Class | Count | Pct (%) | Provenance Status | Label Source | Circularity Flag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`LIKELY_INDUSTRIAL_INCIDENT`** | **10** | 0.0002% | `VERIFIED_EXTERNAL` | Verified Incident Registry (LG, Dahej, etc.) | `False` (Independent) |
| **`PERSISTENT_INDUSTRIAL_HEAT`**| **16** | 0.0004% | `INDUSTRIAL_HEAT_REFERENCE` | GIHS India Reference Layer | `True` (Distance/FRP overlap) |
| **`NATURAL_WILDLAND_FIRE`** | **68,659** | 1.593% | `OFFICIAL_WILDFIRE_SOURCE` | FSI Forest Geoportal + Tree Cover | `True` (Forest land-use overlap) |
| **`UNLABELED`** | **4,241,814** | 98.406% | `UNLABELED` | Unverified satellite detections | `False` |
| **TOTAL** | **4,310,499** | **100.0%** | — | — | — |

---

## 5. Modular Dataset Views Generated

The dataset is partitioned into 5 explicit views in `data/processed/event_dataset/`:

1. **`DATASET_C_ALL_EVENTS.csv`** (854 MB): All 4,310,499 physical event clusters with full feature vectors.
2. **`DATASET_C_WEAK_LABELS.csv`** (17 MB): 68,675 events flagged with `label_feature_overlap = True`.
3. **`DATASET_C_VERIFIED_EXTERNAL.csv`** (2.8 KB): 10 verified out-of-sample ground-truth events for evaluation.
4. **`DATASET_C_PERSISTENT_REFERENCE.csv`** (4.6 KB): 16 persistent operational industrial flare clusters.
5. **`DATASET_C_WILDFIRE_REFERENCE.csv`** (17 MB): 68,659 wildland forest fire reference events.

---

## 6. Data Quality & Splitter Isolation Verification

- **Missing Coordinates**: `0.0%`
- **Missing Timestamps**: `0.0%`
- **Duplicate Event IDs**: `0.0%` (100% Unique `event_id`)
- **Provenance Completeness**: `100.0%`
- **EventGroupSplitter Leakage**: `0.0%` (Physical event clusters isolated cleanly)
- **FacilityGroupSplitter Leakage**: `0.0%` (Industrial site footprints isolated cleanly)
- **Temporal Splitter Leakage**: `0.0%` (Strict chronological split enforced)

---

## 7. Final Model Readiness Assessment

```text
================================================================================
FINAL MODEL READINESS ASSESSMENT
================================================================================
Question: Is the event-level dataset now large enough to begin ML experimentation?

Answer: YES.

Justification:
1. We have successfully constructed an event-level dataset of 4,310,499 physical events from 4.985M satellite observations spanning 3 full years (2023–2025) in India.
2. The dataset features complete 25-dimensional spatial, temporal, intensity, land-cover, and causal historical feature vectors.
3. We have established strict dataset views separating independent out-of-sample evaluation data (DATASET_C_VERIFIED_EXTERNAL) from weak-rule training data (DATASET_C_WEAK_LABELS).
4. Group splitters (EventGroupSplitter & FacilityGroupSplitter) ensure zero spatial or temporal leakage during model cross-validation.

Recommendation:
Proceed to PHASE 3.10 — ML EXPERIMENTATION & MODEL TRAINING (using Event-Level Dataset C, Facility Isolation, and Strict Independent Ground-Truth Evaluation).

Operational Model Status: DATA-LIMITED / RESEARCH BASELINE (until Phase 3.10 model validation complete).
================================================================================
```
