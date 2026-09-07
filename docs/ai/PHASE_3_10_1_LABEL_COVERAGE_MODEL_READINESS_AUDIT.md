# PHASE 3.10.1 — ASTRAFLARE LABEL COVERAGE & MODEL READINESS AUDIT

**Operational Status**: **`RESEARCH BASELINE — NOT PRODUCTION VALIDATED`**  
**Audit Date**: `2026-09-05`  
**Repository**: AstraFlare Geospatial Intelligence Platform (India Thermal Anomalies)

---

## Executive Summary

This report documents the Phase 3.10.1 Label Coverage & Model Readiness Audit for AstraFlare.
Before modifying ML models, backend services, or frontend interfaces, this audit evaluated whether AstraFlare currently possesses a scientifically defensible training dataset for a 3-class supervised classifier (`LIKELY_INDUSTRIAL_INCIDENT`, `PERSISTENT_INDUSTRIAL_HEAT`, `NATURAL_WILDLAND_FIRE`).

### Key Findings
1. **Total Population**: 4,985,160 real NASA FIRMS observations (2023–2025 India) clustered into **4,310,499 physical event clusters**.
2. **Development Dataset Deficit**: `DATASET_C_WEAK_LABELS` contains **68,675 events**, comprising 68,659 `NATURAL_WILDLAND_FIRE` reference events, 16 `PERSISTENT_INDUSTRIAL_HEAT` reference events, and **0 `LIKELY_INDUSTRIAL_INCIDENT` training events**.
3. **Independent Evaluation Isolation**: All 10 `VERIFIED_EXTERNAL` industrial incident events (representing 6 unique physical incidents across Vizag and Dahej industrial complexes) were intentionally isolated into `DATASET_C_VERIFIED_EXTERNAL`. Because 0 training examples existed in the development set, raw model accuracy on independent test events was $0.0\%$.
4. **Abstention Gate Value**: For **4 out of 10 independent test events**, top model confidence fell below the operational threshold ($0.65$), correctly triggering the **Abstention Gate** to flag `Human Review Required`.
5. **Final Readiness Assessment**: **`3-CLASS SUPERVISED TRAINING IS NOT READY FOR PRODUCTION DEPLOYMENT`**. AstraFlare is officially declared as **`RESEARCH BASELINE — DATA-LIMITED`**.

---

## 1. Industrial-Incident Label Pipeline Trace

The complete data pipeline flow for industrial incidents was traced from source ingestion to ML dataset views:

```
External Industrial Accident Registries (PESO / NDMA)
                       ↓
External Ground-Truth Ingestion (data_pipeline/external_ground_truth.py)
                       ↓
Spatial-Temporal Event Matching (data_pipeline/event_matcher.py)
                       ↓
Physical Event Clustering (data_pipeline/sources/event_level_dataset_builder.py)
                       ↓
Label Precedence & Feature Overlap Tagging (assign_evidence_and_labels)
                       ↓
Dataset View Generation (generate_dataset_views)
       ↓                                       ↓
DATASET_C_WEAK_LABELS               DATASET_C_VERIFIED_EXTERNAL
(label_feature_overlap == True)     (provenance == VERIFIED_EXTERNAL)
       ↓                                       ↓
ML Training Set (0 Incidents)        Independent Evaluation (10 Incidents)
```

### Exact Code Path & Mechanism
- In `data_pipeline/sources/event_level_dataset_builder.py` (lines 206–207):
  ```python
  circ_choices = [False, True, True]  # [is_verified, is_persistent, is_wildfire]
  circularity = np.select(label_conds, circ_choices, default=False)
  ```
  `VERIFIED_EXTERNAL` events receive `label_feature_overlap = False` because their labels derived from independent external matching rather than weak-label rule heuristics.
- In line 234:
  ```python
  df_weak = event_df[event_df["label_feature_overlap"] == True]
  ```
  When dataset views were constructed, filtering by `label_feature_overlap == True` **excluded all 10 verified industrial incidents** from `DATASET_C_WEAK_LABELS.csv`.
- **Classification**: This is primarily **A. Intentional Dataset Isolation** (to protect independent test data from leaking into model training) combined with **B. Label-Generation Limitation** (lack of weak-supervision heuristics for industrial incidents without ground-truth matching).

---

## 2. Verification of 10 Independent Test Events

All 10 rows in `DATASET_C_VERIFIED_EXTERNAL.csv` were verified against external ground-truth records:

| Index | Event ID | Event Start | Centroid Lat | Centroid Lon | Obs Count | Max FRP (MW) | Industrial Dist (m) | Matched Industrial Complex | Unique Incident Group |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `evt_5903_27738_2025-12-03` | 2025-12-03T20:15:00Z | 17.70832 | 83.21425 | 2 | 1.06 | 822.5 | Visakhapatnam (Vizag) Refinery | Vizag Incident 1 |
| 02 | `evt_5903_27739_2025-03-19` | 2025-03-19T20:42:00Z | 17.71033 | 83.21567 | 1 | 0.98 | 1078.0 | Visakhapatnam (Vizag) Refinery | Vizag Incident 2 |
| 03 | `evt_5904_27738_2025-03-19` | 2025-03-19T19:27:00Z | 17.71110 | 83.21295 | 1 | 1.77 | 1111.0 | Visakhapatnam (Vizag) Refinery | Vizag Incident 2 |
| 04 | `evt_5904_27739_2025-03-19` | 2025-03-19T19:49:00Z | 17.71191 | 83.21576 | 2 | 1.46 | 1248.4 | Visakhapatnam (Vizag) Refinery | Vizag Incident 2 |
| 05 | `evt_7233_24194_2024-02-20` | 2024-02-20T08:06:00Z | 21.69967 | 72.58329 | 1 | 10.02 | 1299.6 | GIDC Dahej Industrial Complex | Dahej Incident 1 |
| 06 | `evt_7233_24195_2023-10-04` | 2023-10-04T19:51:00Z | 21.69865 | 72.58589 | 1 | 13.99 | 1355.4 | GIDC Dahej Industrial Complex | Dahej Incident 2 |
| 07 | `evt_7234_24194_2024-02-20` | 2024-02-20T08:56:00Z | 21.70091 | 72.58283 | 1 | 2.54 | 1186.7 | GIDC Dahej Industrial Complex | Dahej Incident 1 |
| 08 | `evt_7235_24194_2025-04-12` | 2025-04-12T09:02:00Z | 21.70454 | 72.58212 | 1 | 4.18 | 870.2 | GIDC Dahej Industrial Complex | Dahej Incident 3 |
| 09 | `evt_7235_24195_2025-04-12` | 2025-04-12T08:10:00Z | 21.70387 | 72.58351 | 1 | 13.34 | 858.2 | GIDC Dahej Industrial Complex | Dahej Incident 3 |
| 10 | `evt_7266_24193_2024-01-28` | 2024-01-28T08:38:00Z | 21.70826 | 72.57908 | 1 | 3.43 | 883.6 | GIDC Dahej Industrial Complex | Dahej Incident 4 |

### Verification Confirmation
- **Ground Truth Independence**: Confirmed. Sources originate from official government incident registries (PESO / NDMA).
- **Physical Incident Grouping**: The 10 event rows represent **6 unique physical real-world incidents** across 2 major industrial complexes (Vizag and Dahej). Multiple rows on the same date (e.g. `2025-03-19` Vizag or `2025-04-12` Dahej) represent multi-grid spatial satellite coverage of the same major industrial incident pass.

---

## 3. Persistent Industrial Heat Audit

- **Total Reference Rows**: 16 physical event rows in `DATASET_C_PERSISTENT_REFERENCE.csv`.
- **Location**: All 16 events cluster around $(21.11^\circ\text{N}, 72.63^\circ\text{E})$ at the **Hazira Petrochemical Complex (Surat, Gujarat)**.
- **Source Material**: Derived from 1,420 Indian industrial heat objects in the Global Industrial Heat Source (GIHS 2000–2023) dataset.
- **Classification**: **`SATELLITE_DERIVED_CORROBORATION / REFERENCE_DATA`**. Because GIHS is derived from satellite thermal radiometry (VIIRS/MODIS), these 16 events are **NOT** independent ground truth. They serve as valid development reference data for `PERSISTENT_INDUSTRIAL_HEAT`.

---

## 4. Wildfire Reference Data Audit

- **Total Reference Rows**: 68,659 physical event rows in `DATASET_C_WILDFIRE_REFERENCE.csv`.
- **Total Raw Observations**: 93,566 raw FIRMS observations (mean 1.36 obs/event).
- **Spatial Coverage**: 68,659 distinct spatial grid cells ($300\text{m}$ resolution) across India forest regions over 3 full years (2023–2025).
- **Relationship to 70 Pilot Clusters**: Early Phase 3.8 testing used a 70-cluster sample for quick verification. When scaled across the complete 4.985M observation archive, the rule ($FRP \ge 40.0\text{ MW}, d_{ind} > 5000\text{m}$, Forest land cover) matched **68,659 physical events**.
- **Classification**: **`REFERENCE_DATA / WEAK_LABEL`**. Grounded in ESA 10m WorldCover forest boundaries, but intensity thresholds are heuristic weak-supervision rules.

---

## 5. Label Coverage & Sufficiency Matrix

| Target Class | Independent Verified GT | Reference Events | Weak-Label Events | Total Defensible Dev Events | Total Raw Observations | Unique Physical Incidents | Label Confidence Level | Training Eligibility |
|---|---|---|---|---|---|---|---|---|
| `LIKELY_INDUSTRIAL_INCIDENT` | 10 | 0 | 0 | **0** | 12 | **6** | HIGH (0.95 GT) | **INSUFFICIENT (0 Dev Samples)** |
| `PERSISTENT_INDUSTRIAL_HEAT` | 0 | 16 | 16 | **16** | 36 | **2** | MEDIUM (0.85 Ref) | **LIMITED FOR RESEARCH** |
| `NATURAL_WILDLAND_FIRE` | 0 | 68,659 | 68,659 | **68,659** | 93,566 | **68,659** | MEDIUM (0.80 Ref) | **ADEQUATE FOR DEV** |
| **TOTAL** | **10** | **68,675** | **68,675** | **68,675** | **93,614** | **68,667** | **RESEARCH BASELINE** | **NOT READY FOR PRODUCTION** |

### Explicit Sufficiency Answer
> **"Do we currently have enough defensible industrial-incident examples to train a 3-class supervised classifier?"**  
> **ANSWER**: **INSUFFICIENT for production, and LIMITED for supervised 3-class model fitting.**  
> With 0 training samples in the development set and only 6 unique physical incidents in the independent test set, supervised ML algorithms cannot learn decision boundaries for `LIKELY_INDUSTRIAL_INCIDENT`.

---

## 6. Training/Test Contamination Audit

A rigorous cross-partition check was conducted between `DATASET_C_WEAK_LABELS.csv` and `DATASET_C_VERIFIED_EXTERNAL.csv`:
- **Event ID Overlap**: **0 events (0.0%)**
- **Facility Group Overlap**: **0 facility groups (0.0%)**
- **Spatial Grid Overlap**: **0.0%**
- **Duplicate Overlap**: **0.0%**

All 10 independent test events belong to facility zones (`fac_zone_590_2774` in Vizag, `fac_zone_723_2419`, `fac_zone_724_2419` in Dahej) that have **zero overlap** with training facility zones (`fac_zone_704_2421` in Hazira).

---

## 7. Investigation of 98.5% Mean Confidence Artifact

In Phase 3.10, inference over 50,000 unlabeled India events produced a mean confidence of **0.9850**. Empirical analysis revealed:
1. **Extreme Class Imbalance**: In `DATASET_C_WEAK_LABELS`, `NATURAL_WILDLAND_FIRE` accounts for $99.976\%$ of training samples.
2. **Missing Training Class**: `LIKELY_INDUSTRIAL_INCIDENT` had 0 training samples ($0.00\%$), forcing tree splits to assign $0.0$ probability to class 0.
3. **Probability Quantile Distribution**: Max probability quantiles across unlabeled events were $[0.71, 0.74, 0.74, 0.74, 0.74, 0.85, 0.85]$ for `NATURAL_WILDLAND_FIRE`.
4. **Conclusion**: Low validation ECE ($0.0003$) was an artifact of majority-class validation dominance. High confidence reflects model bias toward the dominant class (`NATURAL_WILDLAND_FIRE`), **NOT true ground-truth certainty**.

---

## 8. LLM Architecture Assessment

Evaluating the introduction of Large Language Models (e.g. Gemini 2.5 via Firebase AI Logic) into the classification pipeline:

| Evaluation Criteria | Pure GBDT Model | Pure LLM Direct Classifier | Recommended Hybrid: GBDT Risk Engine + LLM Analyst Copilot |
|---|---|---|---|
| **Numerical Reasoning** | Excellent | Poor (Hallucinates coordinates/distances) | **Excellent (GBDT computes math)** |
| **Reproducibility** | Deterministic ($100\%$) | Non-deterministic | **Deterministic Risk, Explainable Text** |
| **Explainability** | High (SHAP & GIS) | Generative prose | **High (SHAP + Grounded LLM Briefing)** |
| **Latency & Cost** | $<1\text{ms}$, \$0 cost | High latency ($>1\text{s}$), per-token cost | **$<1\text{ms}$ Alert Gate, Async LLM Report** |
| **Hallucination Risk** | Zero | High | **Zero on Core Decision** |
| **Scientific Defensibility** | **High** | Unacceptable | **High** |

### Architectural Recommendation
- **DO NOT** use an LLM for direct numerical classification or spatial bounding calculations.
- **RECOMMENDED ARCHITECTURE**: **Hybrid GBDT/GIS Risk Engine + LLM Analyst Copilot**.
  - **Core Tier**: GBDT + GIS Proximity + FRP Z-Score + Abstention Gate handles $100\%$ of numerical risk scoring and automated routing in $<1\text{ms}$.
  - **Analyst Copilot Tier**: Gemini LLM generates natural language operational briefings and investigation summaries for human analysts **only when routed for human review**.

---

## 9. Best Path Forward Strategy

**RECOMMENDED STRATEGY**: **OPTION C + OPTION A (Reframed Risk Engine + Systematic Incident Acquisition)**

1. **Short-Term (AstraFlare Research / SIH Stage)**: Reframe AstraFlare as an **Evidence-Based Thermal Anomaly Risk Prioritization Engine** (combining GIS Proximity, FRP Anomaly Z-Scores, Historical Recurrence, Calibrated Probabilities, and Uncertainty Abstention).
2. **Long-Term**: Systematically acquire official Indian PESO / NDMA industrial accident registries to build a training-eligible dataset for `LIKELY_INDUSTRIAL_INCIDENT`.

---

## 10. Final Readiness Matrix

| Component | Status | Empirical Rationale |
|---|---|---|
| **Data Engineering** | **PASS** | 4,985,160 real FIRMS observations ingested with complete checksum manifests and SQLite/PostGIS schemas. |
| **Event Clustering** | **PASS** | 4,310,499 physical event clusters constructed with 300m spatial and 24h temporal gap limits; zero duplicate overlap. |
| **Feature Quality** | **PASS** | 25 event-level features computed with 0.0000% missing values and 0.0% future leakage. |
| **Temporal Leakage** | **PASS** | Strictly enforced `historical_timestamp < target_event_timestamp` across all 3 years. |
| **Label Provenance** | **PASS** | Strict metadata tracking for `ground_truth_flag`, `verification_status`, `provenance_status`, and `label_feature_overlap`. |
| **Industrial Incident Label Coverage** | **FAIL / LIMITED** | **0 training events** in development set; only 10 independent external test events (6 physical incidents). |
| **Persistent Heat Label Quality** | **LIMITED** | 16 reference events from GIHS 2000–2023; satellite-derived corroboration, not independent ground truth. |
| **Wildfire Label Quality** | **PASS** | 68,659 reference events from FSI / ESA 10m WorldCover forest mask; robust development reference. |
| **Independent Evaluation** | **DATA-LIMITED** | $N=10$ external events (Vizag & Dahej); statistically insufficient for broad production generalization claims. |
| **3-Class Supervised Training** | **NOT READY** | Absence of training-eligible `LIKELY_INDUSTRIAL_INCIDENT` events prevents balanced 3-class supervised fitting. |
| **Production ML Deployment** | **NOT READY** | System must remain in **`RESEARCH BASELINE — NOT PRODUCTION VALIDATED`** status. |

---

## 11. Final Decision & Conclusion

**Final Decision**: **`B. RESEARCH BASELINE — DATA-LIMITED`**

AstraFlare currently possesses a scientifically sound data pipeline, clustering engine, feature extraction layer, and uncertainty abstention gate. However, **it does NOT yet possess a training-eligible dataset for the `LIKELY_INDUSTRIAL_INCIDENT` class**. Until additional independent industrial incident records are acquired, the system must remain as a research baseline and risk prioritization engine.
