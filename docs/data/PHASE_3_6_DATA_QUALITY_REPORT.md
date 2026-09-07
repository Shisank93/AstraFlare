# AstraFlare Phase 3.6 — Data Quality & Integrity Report

## Executive Summary

This report evaluates data completeness, provenance integrity, label precedence, event isolation, and label-feature circularity for AstraFlare's real satellite observations and external ground-truth datasets.

---

## 1. Primary Dataset Metrics

| Dataset Attribute | Value | Governance Tag |
| :--- | :--- | :--- |
| **Total REAL FIRMS Observations** | **8,786** | `REAL` |
| **Synthetic / Demo Observations** | **0** (in primary dataset) | `SYNTHETIC_DEMO` (isolated) |
| **Unique Physical FIRMS Event Clusters** | **3,176** | `SATELLITE_DERIVED_CORROBORATION` |
| **Mapped Industrial Facilities (OSM)** | **60** | `VERIFIED_EXTERNAL` |
| **Independent External Ground-Truth Events** | **4** (Verified Scenarios) | `VERIFIED_EXTERNAL` |
| **Weakly Labeled Observations** | **265** | `WEAK_RULE` |
| **Unlabeled Observations** | **8,521** | `UNLABELED` |

---

## 2. Class Distribution & Breakdown

```text
Target Learning Classes:
1. LIKELY_INDUSTRIAL_INCIDENT  :  15 physical events
2. PERSISTENT_INDUSTRIAL_HEAT : 180 physical events
3. NATURAL_WILDLAND_FIRE      :  70 physical events

Operational Abstention Gate:
- HUMAN REVIEW REQUIRED       : Abstention State (confidence < 0.65)
```

---

## 3. Label Precedence & Governance Audit

1. **Precedence Hierarchy Enforcement:**
   $$\text{VERIFIED\_EXTERNAL} > \text{MANUAL\_VERIFIED} > \text{WEAK\_RULE} > \text{UNLABELED}$$
   Higher-confidence external labels override rule-assisted weak labels automatically.
2. **Synthetic Data Exclusion:**
   Synthetic demo records (`SYNTHETIC_DEMO`) are excluded from model training, validation splits, and evaluation metric calculation.

---

## 4. Circularity Audit Result (`LABEL_FEATURE_OVERLAP`)

- **Rule Features Used for Labeling:** `industrial_distance_m`, `frp`, `historical_count_30d`, `daynight_is_day`.
- **Model Input Features:** `frp`, `brightness`, `industrial_distance_m`, `industrial_count_1km`, `industrial_count_5km`, `land_cover_code`, `historical_count_30d`, `historical_mean_frp`, `frp_anomaly_zscore`, `daynight_is_day`.
- **Circularity Audit Status:**
  ```text
  LABEL_FEATURE_OVERLAP = TRUE
  ```
- **Scientific Rationale:** Weak supervision rules rely on features ($d_{\text{industrial}}$, FRP) that are also inputs to the ML model. Therefore, weak-label metrics measure rule-reconstruction accuracy rather than independent generalization. Independent external validation requires `DATASET_B` (`INDEPENDENT_EXTERNAL`).

---

## 5. Event & Facility Isolation

- **Event-Level Isolation (`EventGroupSplitter`):** Prevents individual detections of the same physical thermal event from spanning train and test splits.
- **Facility-Level Isolation (`FacilityGroupSplitter`):** Ensures detections near the same industrial facility belong exclusively to either train or test sets, preventing facility-level memorization leakage.
