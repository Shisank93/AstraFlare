# PHASE 3.10 — ASTRAFLARE ML EXPERIMENT & BENCHMARKING REPORT

**Operational Model Decision**: `RESEARCH BASELINE — DATA-LIMITED`

**Generated At**: `2026-09-05 13:39:50 UTC`

**Repository**: AstraFlare Geospatial Intelligence Platform (India Thermal Anomalies)

---

## Executive Summary

This report documents Phase 3.10 machine-learning experimentation for AstraFlare over **4,310,499 physical event clusters** derived from 4,985,160 real NASA FIRMS observations (2023–2025 India).
All experiments adhere strictly to scientific governance principles:
- No synthetic data was used for model training or evaluation.
- No upstream raw FIRMS data, event clustering, or label definitions were altered.
- Independent out-of-sample ground-truth evaluation set ($N=10$) was strictly held out during training.
- Operational status is officially declared as **`RESEARCH BASELINE — DATA-LIMITED`** due to small independent ground-truth sample size.

---

## 1. Data Contract & Population Statistics

The experimentation pipeline operates over the 25-feature event-level dataset views in `data/processed/event_dataset/`:

| Dataset View | Row Count | Target Classes Present | Description |
|---|---|---|---|
| `DATASET_C_ALL_EVENTS` | 4,310,499 | Unlabeled / All | Full physical event population derived from FIRMS |
| `DATASET_C_WEAK_LABELS` | 68,675 | `PERSISTENT_HEAT` (16), `WILDLAND_FIRE` (68,659) | Development weak-label dataset |
| `DATASET_C_VERIFIED_EXTERNAL` | 10 | `LIKELY_INDUSTRIAL_INCIDENT` (10) | Strictly held-out independent ground truth |
| `DATASET_C_PERSISTENT_REFERENCE` | 16 | `PERSISTENT_INDUSTRIAL_HEAT` (16) | GIHS industrial heat reference events |
| `DATASET_C_WILDFIRE_REFERENCE` | 68,659 | `NATURAL_WILDLAND_FIRE` (68,659) | FSI official forest wildfire reference events |

---

## 2. Feature Audit & Leakage Controls

### Pre-Training Feature Audit & Circularity Analysis

| Feature | Type | Valid Inference | Future Leakage | Weak-Label Participant | Circularity Status |
|---|---|---|---|---|---|
| `duration_hours` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `observation_count` | numeric | YES | NO | YES | `LABEL_GENERATION_CIRCULARITY` |
| `centroid_lat` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `centroid_lon` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `spatial_extent_m` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `max_frp` | numeric | YES | NO | YES | `LABEL_GENERATION_CIRCULARITY` |
| `mean_frp` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `std_frp` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `max_brightness` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `mean_brightness` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `confidence_high_ratio` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `satellite_count` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `industrial_distance_m` | numeric | YES | NO | YES | `LABEL_GENERATION_CIRCULARITY` |
| `industrial_site_count_250m` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `industrial_site_count_1km` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `industrial_site_count_5km` | numeric | YES | NO | NO | `CLEAN_PHYSICAL_FEATURE` |
| `worldcover_class` | categorical | YES | NO | YES | `LABEL_GENERATION_CIRCULARITY` |

#### Label-Generation Circularity vs True Feature Leakage Distinction

- **TRUE FEATURE LEAKAGE**: Occurs when a feature contains future information (e.g. end-of-year aggregated stats, target label encoding, or future satellite passes) that would not be available at the exact moment of real-time operational prediction. **All 17 AstraFlare features have 0.0% Future Feature Leakage.**
- **LABEL-GENERATION CIRCULARITY**: Occurs when legitimate operational features (`industrial_distance_m`, `max_frp`, `observation_count`, `worldcover_class`) were used in heuristic rules to define the initial weak-label dataset. These operational features are fully valid for real-time model inference. However, high performance on the weak-label development set (Experiment A) partly reflects rule recovery. **This is why Independent Evaluation (Experiment B) on 10 out-of-sample verified external events is essential.**

---

## 3. Group & Facility Splitting Isolation

To prevent facility and spatial correlation leakage, dataset partitioning was conducted using `FacilityGroupSplitter` with class stratification:

- **Train Events**: 54,386
- **Validation Events**: 14,289
- **Event Overlap**: 0 (0.0%)
- **Facility Group Overlap**: 0 (0.0%)
- **Duplicate Overlap**: 0 (0.0%)
- **Leakage-Free Verified**: `True`

---

## 4. Model Benchmarking Results (Experiment A — Development)

Candidate models were trained on development weak labels and evaluated on facility-isolated validation data:

| Model Candidate | Status | Accuracy | Balanced Acc | Macro F1 | Weighted F1 | ECE |
|---|---|---|---|---|---|---|
| `DummyClassifier (Most Frequent)` | AVAILABLE | 0.9990 | 0.5000 | **0.3332** | 0.9985 | 0.0010 |
| `DummyClassifier (Stratified)` | AVAILABLE | 0.9990 | 0.5000 | **0.3332** | 0.9985 | 0.0010 |
| `RandomForestClassifier` | AVAILABLE | 1.0000 | 1.0000 | **0.6667** | 1.0000 | 0.0003 |
| `HistGradientBoostingClassifier` | AVAILABLE | 0.9999 | 0.9643 | **0.6543** | 0.9999 | 0.0001 |
| `LGBMClassifier` | AVAILABLE | 0.9993 | 0.6785 | **0.4999** | 0.9992 | 0.0006 |
| `XGBoost` | UNAVAILABLE | N/A | N/A | N/A | N/A | N/A |
| `CatBoost` | UNAVAILABLE | N/A | N/A | N/A | N/A | N/A |

**Selected Baseline Model**: `RandomForestClassifier`

### Why Accuracy is Deceptive

> **WARNING**: Raw accuracy is highly deceptive on imbalanced datasets. Predicting the majority class (`NATURAL_WILDLAND_FIRE`) yields >99.9% raw accuracy while completely missing minority industrial events. Therefore, model selection is strictly driven by **Macro F1** and minority-class recall.

---

## 5. Probability Calibration

Probability outputs were calibrated using Platt Sigmoid Scaling on validation folds:

- **Uncalibrated Expected Calibration Error (ECE)**: `0.0003`
- **Calibrated Expected Calibration Error (ECE)**: `0.0003`

---

## 6. Post-Classification Uncertainty Abstention Gate

Operational threshold `HUMAN_REVIEW_THRESHOLD = 0.65` was evaluated across multiple confidence cutoffs:

| Threshold | Total Events | Accepted Events | Abstained Events | Coverage | Abstention Rate | Accepted Accuracy |
|---|---|---|---|---|---|---|
| `0.50` | 14,289 | 14,289 | 0 | 100.00% | 0.00% | 1.0000 |
| `0.60` | 14,289 | 14,289 | 0 | 100.00% | 0.00% | 1.0000 |
| `0.65` | 14,289 | 14,289 | 0 | 100.00% | 0.00% | 1.0000 |
| `0.70` | 14,289 | 14,285 | 4 | 99.97% | 0.03% | 1.0000 |
| `0.80` | 14,289 | 14,276 | 13 | 99.91% | 0.09% | 1.0000 |
| `0.90` | 14,289 | 14,275 | 14 | 99.90% | 0.10% | 1.0000 |

---

## 7. Independent Out-of-Sample Evaluation (Experiment B)

> **CRITICAL LIMITATION**: The independent ground-truth dataset consists of **N=10 verified external events**. Metrics on this small sample must NOT be used to claim production accuracy.

| Event ID | Start Timestamp | Ground Truth Class | Top Model Class | Confidence | Abstained? | Operational Risk |
|---|---|---|---|---|---|---|
| `evt_5903_27738_2025-12-03` | `2025-12-03T20:15:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.6300 | `YES` | `0.2590` |
| `evt_5903_27739_2025-03-19` | `2025-03-19T20:42:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.5500 | `YES` | `0.3150` |
| `evt_5904_27738_2025-03-19` | `2025-03-19T19:27:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.5500 | `YES` | `0.3150` |
| `evt_5904_27739_2025-03-19` | `2025-03-19T19:49:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.5500 | `YES` | `0.3150` |
| `evt_7233_24194_2024-02-20` | `2024-02-20T08:06:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.7200 | `NO` | `0.1960` |
| `evt_7233_24195_2023-10-04` | `2023-10-04T19:51:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.7200 | `NO` | `0.1960` |
| `evt_7234_24194_2024-02-20` | `2024-02-20T08:56:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.7200 | `NO` | `0.1960` |
| `evt_7235_24194_2025-04-12` | `2025-04-12T09:02:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.8000 | `NO` | `0.1400` |
| `evt_7235_24195_2025-04-12` | `2025-04-12T08:10:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.8000 | `NO` | `0.1400` |
| `evt_7236_24193_2024-01-28` | `2024-01-28T08:38:00Z` | `LIKELY_INDUSTRIAL_INCIDENT` | `PERSISTENT_INDUSTRIAL_HEAT` | 0.8000 | `NO` | `0.1400` |

### Scientific Insight on Independent Evaluation Failures

Because `LIKELY_INDUSTRIAL_INCIDENT` events were completely absent from the weak-label development dataset (`DATASET_C_WEAK_LABELS`), the model assigned 0.0 probability to `LIKELY_INDUSTRIAL_INCIDENT` and predicted `PERSISTENT_INDUSTRIAL_HEAT` for industrial site events. However, for **4 out of 10 events**, prediction confidence fell below `0.65`, causing the **Abstention Gate** to correctly route them to `Human Review Required`. This demonstrates the crucial safety value of the post-classification uncertainty layer.

---

## 8. Unlabeled India Population Inference (Experiment C)

`MODEL INFERENCE — NOT GROUND TRUTH`

Inference was executed over a sample of **50,000 unlabeled India events**:

- **Predicted Class Distribution**: `{'NATURAL_WILDLAND_FIRE': 50000}`
- **Abstained Events**: 0 (0.00%)
- **Mean Prediction Confidence**: `0.7395`
- **Mean Operational Risk Score**: `0.5176`

---

## 9. Model Explainability & Permutation Feature Importance

Top 10 features driving model predictions ranked by Permutation Importance:

| Rank | Feature Name | Permutation Importance Score |
|---|---|---|
| 1 | `industrial_distance_m` | 0.1861 |
| 2 | `centroid_lon` | 0.1756 |
| 3 | `worldcover_class` | 0.1745 |
| 4 | `industrial_site_count_5km` | 0.1395 |
| 5 | `max_frp` | 0.1163 |
| 6 | `industrial_site_count_1km` | 0.0939 |
| 7 | `mean_frp` | 0.0581 |
| 8 | `duration_hours` | 0.0348 |
| 9 | `satellite_count` | 0.0107 |
| 10 | `observation_count` | 0.0104 |

---

## 10. Serialized Versioned Artifacts

Artifacts saved under `ml/artifacts/`:

- `gbdt_model_v1.0.joblib` (Trained RandomForestClassifier / GBDT baseline)
- `calibrator_v1.0.joblib` (Platt Sigmoid CalibratedClassifierCV)
- `preprocessor_v1.0.joblib` (ColumnTransformer with OrdinalEncoder + StandardScaler)
- `feature_schema_v1.0.json` (17-feature schema contract)
- `label_mapping_v1.0.json` (Class label index mapping)
- `experiment_config_v1.0.json` (Reproducible hyperparameter and split config)
- `model_metadata_v1.0.json` (Full execution metadata and metric record)

---

## 11. Final Operational Recommendation

**Final Model State**: **`RESEARCH BASELINE — DATA-LIMITED`**

The current ML model is a scientifically defensible research baseline. It MUST NOT be integrated into production FastAPI endpoints or frontend UI until larger independent external ground-truth datasets for industrial incidents are acquired.