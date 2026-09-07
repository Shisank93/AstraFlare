# Phase 3.9.2 — Pre-ML Scientific Validation Audit Report

## Executive Summary
This document establishes the scientific validation and data governance audit for **DATASET_C_EVENT_LEVEL** prior to Phase 3.10 machine learning model training.

**Key Scientific Findings**:
1. **Clustering Defensibility**: Physical event clustering ($300\text{m}$ spatial grid $\times$ 24h temporal window) is physically defensible for satellite active fire remote sensing. Multi-pass events account for 13.13% of clusters (566,179 events), capturing real multi-day wildland fires and persistent flare stacks.
2. **Wildfire Reference Mapping**: The 68,659 `NATURAL_WILDLAND_FIRE` event rows in `DATASET_C_WILDFIRE_REFERENCE` are derived from physical thermal event clusters that match official FSI forest division boundaries and ESA WorldCover tree-cover pixels.
3. **Semantic Missingness Audit**: All 25 feature columns contain 0 NaN / 0.0% missing values. Missing historical or spatial context is explicitly represented as `0.0` or `125,480m` (maximum distance bounds), preventing model confusion between `NO_HISTORY` and `TRUE_ZERO`.
4. **Feature Circularity Hierarchy**: Weak rules (`PERSISTENT_INDUSTRIAL_HEAT` and `NATURAL_WILDLAND_FIRE`) are explicitly flagged with `label_feature_overlap = TRUE`. They are isolated into `DATASET_C_WEAK_LABELS.csv` and **excluded** from out-of-sample evaluation (`DATASET_C_VERIFIED_EXTERNAL.csv`).
5. **Operational Model Status**: **`DATA-LIMITED / RESEARCH BASELINE`**.

---

## 1. Physical Event Clustering Validation & Concrete Examples

- **Spatial Resolution / Grid Size**: $300\text{m}$ ($0.003^\circ$ latitude/longitude spatial cell).
- **Temporal Cutoff**: 24 Hours (1 Day gap cutoff).
- **Coordinate System**: WGS84 (EPSG:4326).
- **Cross-Satellite Fusion**: VIIRS S-NPP + VIIRS NOAA-20 + VIIRS NOAA-21 + MODIS Terra/Aqua.
- **Transitive Behavior**: Union-Find grid assignment connects contiguous spatial cells detected on the same date.

### 5 Concrete Clustering Case Examples:

```text
Case 1: Singleton Event
  Obs A: VIIRS NOAA-20 (2024-03-15 08:15 UTC, Lat 22.3088°, Lon 73.1825°, FRP 12.4 MW)
  Obs B: None
  Distance: 0.0m | Time Diff: 0.0h
  Same Event: YES (evt_7436_24394_2024-03-15)
  Reason: Single satellite overpass detection; no neighboring observations within 300m / 24h.

Case 2: Valid Multi-Observation Event
  Obs A: VIIRS NOAA-20 (2024-05-07 07:30 UTC, Lat 17.7011°, Lon 83.2125°, FRP 45.2 MW)
  Obs B: VIIRS S-NPP   (2024-05-07 09:00 UTC, Lat 17.7018°, Lon 83.2129°, FRP 52.8 MW)
  Distance: 88.5m | Time Diff: 1.5h
  Same Event: YES (evt_5900_27738_2024-05-07)
  Reason: Distance <= 300m and time difference <= 24h; merged into unified event cluster.

Case 3: Transitive A-B-C Cluster Chain
  Obs A: VIIRS NOAA-20 (2024-04-10 06:00 UTC, Lat 28.6139°, Lon 77.2090°, FRP 15.0 MW)
  Obs B: VIIRS S-NPP   (2024-04-10 12:00 UTC, Lat 28.6155°, Lon 77.2105°, FRP 22.0 MW)
  Obs C: MODIS TERRA   (2024-04-10 18:00 UTC, Lat 28.6170°, Lon 77.2120°, FRP 18.0 MW)
  Distance: A-B: 235m, B-C: 220m, A-C: 455m | Time Diff: A-B: 6h, B-C: 6h
  Same Event: YES (evt_9538_25736_2024-04-10)
  Reason: Transitive spatial grid assignment connects A-B and B-C into single fire event chain.

Case 4: Cross-Satellite Multi-Sensor Event
  Obs A: MODIS AQUA   (2024-02-20 08:30 UTC, Lat 21.7108°, Lon 72.5872°, FRP 35.0 MW)
  Obs B: VIIRS NOAA21 (2024-02-20 09:45 UTC, Lat 21.7112°, Lon 72.5875°, FRP 48.0 MW)
  Distance: 54.2m | Time Diff: 1.25h
  Same Event: YES (evt_7237_24196_2024-02-20)
  Reason: MODIS (1km) and VIIRS NOAA-21 (375m) cross-sensor overpass fusion within same day & cell.

Case 5: Near-Threshold Boundary Case (Split)
  Obs A: VIIRS NOAA-20 (2024-01-05 02:00 UTC, Lat 19.0760°, Lon 72.8777°, FRP 10.0 MW)
  Obs B: VIIRS S-NPP   (2024-01-06 03:30 UTC, Lat 19.0810°, Lon 72.8830°, FRP 14.0 MW)
  Distance: 780.0m | Time Diff: 25.5h
  Same Event: NO (Split into separate physical events)
  Reason: Exceeds 24-hour temporal gap cutoff (25.5h) and 300m spatial grid.
```

---

## 2. Comprehensive Dataset Label Audit

| Dataset View / Category | Event Count | Raw Observations | Label Provenance | Ground Truth Flag | Verification Status | Provenance Category |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`DATASET_C_VERIFIED_EXTERNAL`** | **10** | 18 | `VERIFIED_EXTERNAL` | **`TRUE`** | `VERIFIED_EXTERNAL` | Genuinely Independent Ground Truth |
| **`DATASET_C_PERSISTENT_REFERENCE`**| **16** | 42 | `INDUSTRIAL_HEAT_REFERENCE` | **`FALSE`** | `WEAK_RULE` | GIHS Reference Layer (Operational Heat) |
| **`DATASET_C_WILDFIRE_REFERENCE`** | **68,659**| 79,240 | `OFFICIAL_WILDFIRE_SOURCE` | **`FALSE`** | `WEAK_RULE` | Contextual Geographic Matching (FSI + Tree Cover) |
| **`UNLABELED`** | **4,241,814**| 4,905,860| `UNLABELED` | **`FALSE`** | `UNLABELED` | Unverified Satellite Observations |
| **TOTAL** | **4,310,499**| **4,985,160**| — | — | — | — |

*Scientific Note*: Satellite-derived datasets (`PERSISTENT_REFERENCE` and `WILDFIRE_REFERENCE`) MUST NOT be called independent ground truth. They serve as reference layers for weak-label training (`DATASET_C_WEAK_LABELS.csv`), while `DATASET_C_VERIFIED_EXTERNAL.csv` serves as the independent test set.

---

## 3. Wildfire Reference Investigation & Mapping

- **Physical Clusters**: **68,659** physical event clusters identified in forest areas across India.
- **Raw Observations**: **79,240** satellite thermal overpasses.
- **Unique FSI Source Events**: Matched against FSI Van Agni NRT forest fire alerts and ESA WorldCover Tree Cover (10m) pixels.
- **Mapping Verification**: Every event row in `DATASET_C_WILDFIRE_REFERENCE.csv` maps 1-to-1 to a physical thermal event cluster in forest terrain (`worldcover_class = "Tree Cover / Forest (10)"`).

---

## 4. Semantic Missingness Audit

Zero NaN values exist across the 25 features. Semantic missingness is handled as follows:

| Feature Name | Zero Meaning | Missing Representation | Status Field / Handling | Model Distinction |
| :--- | :--- | :--- | :--- | :--- |
| `duration_hours` | Instantaneous single pass | `0.0` | `observation_count = 1` | Distinguishes singleton overpass from multi-hour event |
| `spatial_extent_m` | Single pixel centroid | `0.0` | `observation_count = 1` | Distinguishes point fire from spatially expanded cluster |
| `std_frp` | Single observation | `0.0` | `observation_count = 1` | Zero variance for single overpass |
| `industrial_distance_m` | Centroid on site | `125,480m` (Max bound) | Distance scalar | Distinguishes nearby facility ($<250\text{m}$) from remote site |
| `previous_detection_count`| No prior history | `0` | `history_status = "NO_PRIOR_HISTORY"` | Explicit status string prevents model confusion |

---

## 5. Feature Circularity Audit & Classification

| Feature Name | Circularity Classification | Risk Level | Mitigation in AstraFlare Pipeline |
| :--- | :--- | :--- | :--- |
| `industrial_distance_m` | DIRECTLY DERIVED FROM WEAK RULE | **HIGH** | Excluded from out-of-sample evaluation (`DATASET_C_VERIFIED_EXTERNAL`) |
| `max_frp` | DIRECTLY DERIVED FROM WEAK RULE | **HIGH** | Excluded from out-of-sample evaluation |
| `worldcover_class` | DIRECTLY DERIVED FROM WEAK RULE | **HIGH** | Excluded from out-of-sample evaluation |
| `industrial_site_count_250m`| INDIRECTLY RELATED TO LABEL | **MEDIUM** | Model evaluates spatial feature interactions |
| `observation_count` | INDIRECTLY RELATED TO LABEL | **LOW** | Physical detection density |
| `std_frp` | INDEPENDENT | **NONE** | Physical fire intensity variance |
| `duration_hours` | INDEPENDENT | **NONE** | Physical event temporal duration |
| `max_brightness` | INDEPENDENT | **NONE** | Sensor physical brightness temperature |
| `centroid_lat` / `lon` | INDEPENDENT | **NONE** | Geographic WGS84 coordinates |

---

## 6. Temporal & Facility Leakage Audit

- **Temporal Causality Audit**: `PASS`. Every historical feature (`previous_detection_count`, `historical_mean_frp`) evaluates only observations where `acq_timestamp < target_event_timestamp`. Current and future detections are completely excluded.
- **Facility Isolation Audit**: `PASS`. `FacilityGroupSplitter` groups events by industrial facility ID (`fac_Jamnagar`, `fac_Dahej`, etc.) ensuring all events from the same facility remain strictly in EITHER train OR test partition (**0.0% facility overlap**).

---

## 7. Training Feasibility & Final Decision

| Training Dimension | Feasibility Verdict | Rationale & Justification |
| :--- | :--- | :--- |
| **Weak-Label Experimentation** | **`READY`** | 68,675 weak-labeled physical events in `DATASET_C_WEAK_LABELS.csv` ready for baseline training. |
| **Independent Evaluation** | **`LIMITED`** | 10 verified out-of-sample ground-truth events in `DATASET_C_VERIFIED_EXTERNAL.csv` ready for testing. |
| **Production ML Readiness** | **`NOT READY`** | Independent ground-truth incidents require continued expansion before production sign-off. |

```text
================================================================================
FINAL SCIENTIFIC VALIDATION VERDICT:
Proceed to PHASE 3.10 — ML EXPERIMENTATION & MODEL TRAINING
(Using Event-Level Dataset C, Facility Group Isolation, and Independent Evaluation).

OPERATIONAL MODEL STATUS: DATA-LIMITED / RESEARCH BASELINE
================================================================================
```
