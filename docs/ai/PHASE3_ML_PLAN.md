# AstraFlare Phase 3: Machine Learning & Explainability Architecture Plan

**Project:** AstraFlare — AI-Powered Geospatial Intelligence Platform  
**Phase:** Phase 3 ML Engine & Explainability Pipeline  
**Document:** Machine Learning Master Architecture & Implementation Plan  

---

## 1. Executive Summary & Problem Formulation

AstraFlare solves the challenge of contextualizing satellite-detected thermal anomalies. Satellites (e.g. Suomi VIIRS, NOAA-20 VIIRS, MODIS) detect pixels with high Fire Radiative Power (FRP) and brightness temperatures. However, raw satellite detections do not indicate the **underlying cause** or **operational risk**.

AstraFlare frames this as a **multiclass tabular geospatial classification problem** enriched with industrial context, land-cover classifications, historical thermal persistence, and spatial-temporal dynamics.

### Primary Operational Classes
1. `LIKELY_INDUSTRIAL_INCIDENT`: High-energy thermal anomaly ($Z$-score $\ge 2.0$) occurring in close proximity ($< 2.0 \text{ km}$) to industrial infrastructure (refineries, power plants, chemical complexes).
2. `PERSISTENT_INDUSTRIAL_HEAT`: Low-variance, recurring thermal anomaly ($Z$-score $< 1.0$) associated with continuous operational flares or industrial heating processes ($count \ge 5$ over 30/365 days).
3. `NATURAL_WILDLAND_FIRE`: High-FRP thermal anomaly occurring in non-industrial land cover (`forest`, `shrubland`, `grassland`, `wetland`) far from industrial infrastructure ($> 5.0 \text{ km}$).

### Operational Abstention Mechanism
`HUMAN_REVIEW_REQUIRED` is **NOT** treated as a synthetic learned class. Instead, a 3-class GBDT model predicts calibrated probabilities across the 3 primary classes. If maximum calibrated probability $\max_c P(Y=c|X) < \text{HUMAN\_REVIEW\_THRESHOLD}$ ($0.65$), the engine abstains (`is_abstained = True`) and routes the event for human analyst review.

---

## 2. End-to-End ML Pipeline Architecture

```text
REAL FIRMS Satellite Data (8,700+ 7-Day Observations)
                 ↓
  GIS Feature Enrichment Engine
    ├── Proximity to OSM Industrial Facilities
    ├── ESA WorldCover Land-Cover Categorization
    └── Historical FRP Anomaly Z-Score Calculation (t_hist < t_i)
                 ↓
     Weak Label Construction & Label Provenance
                 ↓
     Label Quality Audit & Class Imbalance Analysis
                 ↓
     Feature & Leakage Prevention Audit
                 ↓
  Spatial-Temporal Evaluation Split (GroupKFold Grid + Temporal)
                 ↓
    Tabular GBDT Model Training (LightGBM / XGBoost)
                 ↓
 Probability Calibration (Isotonic Regression)
                 ↓
 Operational Abstention Gate (Threshold = 0.65)
                 ↓
    TreeSHAP Feature Attribution Engine
                 ↓
 Standardized Prediction Contract & Database Audit Log
```

---

## 3. Core Principles & Governance Rules

1. **Strict REAL-Data Enforcement:** Only observations with `data_source = 'REAL'` are used for model training, validation, and testing. `SYNTHETIC_DEMO` or mock records are strictly rejected (`ValueError` raised if encountered).
2. **Strict Leakage Prevention:** Historical FRP statistics for an observation $i$ at acquisition timestamp $t_i$ strictly filter past events ($t_{hist} < t_i$) and exclude observation $i$ itself.
3. **No Circular Labeling:** Features used for model training are decoupled from simplistic single-feature rules. Labeling incorporates multi-source evidence and historical permanence.
4. **Honest Metrics & Validation:** Model evaluation uses spatial (GroupKFold spatial grid) and temporal splits to prevent spatial-temporal correlation leakage.

---

## 4. Key Artifacts & Module Layout

- `ml/data/`: Historical real dataset ingestion scripts (`ingest_historical_real_data.py`).
- `ml/labeling.py`: Weak supervision labeling, label provenance logging, and label quality audit.
- `ml/dataset_generator.py`: Feature matrix construction with REAL-only governance and leakage checks.
- `ml/splitter.py`: Spatial-Temporal splitters (`TemporalSplitter`, `SpatialGroupKFold`).
- `ml/train.py`: GBDT classifier training, probability calibration, and metric evaluation.
- `ml/abstention.py`: Operational abstention gate (`HUMAN_REVIEW_THRESHOLD = 0.65`).
- `ml/explainability.py`: TreeSHAP feature attributions and operational evidence generator.
- `ml/inference.py`: Standardized prediction engine (`predict_hotspot`).
- `scripts/run_ml_pipeline.py`: End-to-end executable workflow script.
