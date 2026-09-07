# AstraFlare Dual-Dataset Independent Evaluation Specification

## Overview
This document specifies the dual-dataset evaluation methodology, breaking label-feature circularity, and comparing rule-matching performance (Dataset A) against independent evidence performance (Dataset B).

---

## 1. Breaking Label-Feature Circularity

In Phase 3.1, the weak-label rule engine constructed labels using `industrial_distance_m`, `frp`, `frp_anomaly_zscore`, `historical_count_30d`, and `is_forest_land`. Supplying those exact features to the GBDT created label-feature circularity, causing the model to learn rule-matching rather than independent physical classification.

To quantify and eliminate this circularity, AstraFlare provides two evaluation datasets:

### Dataset A — Weak-Label Baseline (`label_mode="WEAK_BASELINE"`)
- **Labels:** Heuristic weak supervision rules (`ml/labeling.py`).
- **Purpose:** Measures how accurately the GBDT can mimic internal python rules.

### Dataset B — Independent-Label Dataset (`label_mode="INDEPENDENT_EXTERNAL"`)
- **Labels:** Real-world independent external ground-truth events & analyst verifications (`data_pipeline/external_ground_truth.py`).
- **Purpose:** Measures genuine real-world generalization performance on independently verified fire and industrial events.

---

## 2. Model Feature Sets

- **Model A (Full GIS Model):** Employs all 12 spatial, industrial, historical, and land-cover features.
- **Model B (Reduced Circularity Model):** Excludes features directly responsible for rule thresholds (`frp_anomaly_zscore`, `historical_count_30d`), relying solely on raw physical inputs (`industrial_distance_m`, `frp`, `brightness`, `daynight_is_day`, `land_cover_code`).

---

## 3. Evaluation Integrity & Data Quality Gates

1. **Event Isolation:** Evaluation metrics are computed strictly using `EventGroupSplitter` (80% event train, 20% event test) to ensure zero spatial-temporal event leakage.
2. **Zero Synthetic Records:** Synthetic demo inputs are completely excluded.
3. **Operational Threshold:** Predictions with calibrated confidence $< 0.65$ trigger abstention (`HUMAN_REVIEW_REQUIRED`).
