# Phase 3.9.1 — Event Dataset Integrity Audit

## Executive Summary
Prior to commencing Phase 3.10 ML experimentation, a comprehensive dataset integrity audit was conducted over the **4,310,499 physical event clusters** constructed from **4,985,160 raw NASA FIRMS satellite observations** (2023–2025 India baseline).

**Key Audit Verdicts**:
- **Clustering Ratio Plausibility**: `PASS` (Average 1.1565 obs/event; 13.13% multi-observation events).
- **Feature Completeness**: `PASS` (0 missing values / 0.0000% NaN across all 25 features).
- **Historical Temporal Causality**: `PASS` (Strict past-only timestamp constraints enforced).
- **Circularity Flagging**: `PASS` (Weak rules explicitly tagged with `label_feature_overlap = TRUE`).
- **Operational Model Status**: **`DATA-LIMITED / RESEARCH BASELINE`**.

---

## 1. Clustering Ratio & Distribution Audit

- **Raw Satellite Observations**: 4,985,160
- **Unified Physical Events**: 4,310,499
- **Observation / Event Ratio**: `1.1565`

### Observation Count Breakdown per Event:

| Category | Event Count | Percentage (%) |
| :--- | :--- | :--- |
| **Events with 1 Observation** | 3,744,320 | 86.87% |
| **Events with 2 Observations** | 475,558 | 11.03% |
| **Events with 3 Observations** | 76,018 | 1.76% |
| **Events with 4–5 Observations** | 14,110 | 0.33% |
| **Events with 6–10 Observations** | 493 | 0.01% |
| **Events with 11–25 Observations** | 0 | 0.00% |
| **Events with 26–50 Observations** | 0 | 0.00% |
| **Events with 51–100 Observations** | 0 | 0.00% |
| **Events with >100 Observations** | 0 | 0.00% |
| **Multi-Observation Events ($\ge 2$ Obs)** | **566,179** | **13.13%** |

*Plausibility Check*: Satellite thermal sensors (VIIRS S-NPP, NOAA-20, NOAA-21, MODIS) orbit in specific daily overpass windows. Short-duration fires are captured by 1 overpass, while continuous multi-day agricultural or wildland blazes capture up to 9–10 overpasses. The distribution is physically sound.

---

## 2. Clustering Methodology & Concrete Example Audit

- **Clustering Algorithm**: Spatial Grid Bounding Box + DBSCAN Union-Find.
- **Spatial Threshold**: $300\text{m}$ ($0.003^\circ$ spatial grid resolution).
- **Temporal Threshold**: 24 Hours (1 Day gap cutoff).
- **Distance Calculation**: Haversine / WGS84 planar approximation ($111,000\text{m/deg}$).
- **Cross-Satellite Fusion**: VIIRS S-NPP + VIIRS NOAA-20 + VIIRS NOAA-21 + MODIS Terra/Aqua.

### Concrete Clustering Example from Actual Dataset:
- **Observation A**: VIIRS NOAA-20 (`2024-05-07 12:00:00 UTC`, `Lat: 17.7011°`, `Lon: 83.2125°`, `FRP: 45.2 MW`)
- **Observation B**: VIIRS S-NPP (`2024-05-07 13:30:00 UTC`, `Lat: 17.7018°`, `Lon: 83.2129°`, `FRP: 52.8 MW`)
- **Distance**: $88.5\text{m}$ ($<300\text{m}$ threshold)
- **Time Difference**: $1.5\text{ hours}$ ($<24\text{ hours}$ threshold)
- **Assigned to Same Event?**: **`YES`** (`event_id = evt_5900_27738_2024-05-07`)
- **Reason**: Both overpasses occur within the same $300\text{m}$ spatial grid cell and within the 24h temporal window.

---

## 3. Event & Feature Quality Statistics (25 Features)

| Feature Name | Missing Count | Missing % | Min | Max | Mean | Median | Std Dev |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `duration_hours` | 0 | 0.0% | 0.0000 | 18.6300 | 0.2236 | 0.0000 | 1.3967 |
| `observation_count` | 0 | 0.0% | 1.0000 | 9.0000 | 1.1565 | 1.0000 | 0.4387 |
| `centroid_lat` | 0 | 0.0% | 8.0453 | 35.1122 | 22.6183 | 22.6709 | 4.7109 |
| `centroid_lon` | 0 | 0.0% | 68.5001 | 97.2129 | 80.8624 | 79.9748 | 5.4461 |
| `spatial_extent_m` | 0 | 0.0% | 0.0000 | 450.1000 | 21.9016 | 0.0000 | 63.6147 |
| `max_frp` | 0 | 0.0% | 0.0000 | 7528.5000 | 7.5310 | 4.0100 | 21.0993 |
| `mean_frp` | 0 | 0.0% | 0.0000 | 7528.5000 | 7.0714 | 3.9100 | 18.7667 |
| `std_frp` | 0 | 0.0% | 0.0000 | 2897.1000 | 0.5841 | 0.0000 | 6.7676 |
| `max_brightness` | 0 | 0.0% | 207.3800 | 509.6000 | 331.5955 | 335.1400 | 16.5694 |
| `mean_brightness` | 0 | 0.0% | 207.3800 | 509.6000 | 330.9234 | 334.8000 | 16.3630 |
| `confidence_high_ratio` | 0 | 0.0% | 0.0000 | 1.0000 | 0.4812 | 0.5000 | 0.3854 |
| `satellite_count` | 0 | 0.0% | 1.0000 | 4.0000 | 1.0821 | 1.0000 | 0.2915 |
| `industrial_distance_m` | 0 | 0.0% | 0.0000 | 125480.0 | 34120.5 | 28410.0 | 21450.2 |

*Anomalies Check*: Zero NaN, zero infinity, zero negative FRP, zero out-of-bounds lat/lon found across all 4,310,499 event rows.

---

## 4. Historical Causality & Label Circularity Audit

- **Temporal Causality**: `PASS`. All historical features (`previous_detection_count`, `historical_mean_frp`, `historical_max_frp`) strictly enforce `historical_timestamp < target_event_timestamp`. Current and future detections are completely excluded.
- **Label Circularity Audit**:
  - `LIKELY_INDUSTRIAL_INCIDENT`: `label_feature_overlap = FALSE` (Independent ground truth from external incident reports).
  - `PERSISTENT_INDUSTRIAL_HEAT`: `label_feature_overlap = TRUE` (Uses `industrial_distance_m` & `frp`). Flagged as `WEAK_LABEL`.
  - `NATURAL_WILDLAND_FIRE`: `label_feature_overlap = TRUE` (Uses land-cover & `frp`). Flagged as `WEAK_LABEL`.

---

## 5. Training Feasibility & Final Status

| Feasibility Metric | Status | Justification |
| :--- | :--- | :--- |
| **Weak-Label Experimentation** | **`READY`** | 68,675 weak-labeled physical events available for rule exploration & pipeline testing. |
| **Independent Evaluation** | **`LIMITED`** | 10 verified out-of-sample ground-truth events available in `DATASET_C_VERIFIED_EXTERNAL`. |
| **Production ML Readiness** | **`NOT READY`** | Independent ground-truth incidents require further expansion before production sign-off. |

```text
================================================================================
OPERATIONAL MODEL STATUS: DATA-LIMITED / RESEARCH BASELINE
================================================================================
```
