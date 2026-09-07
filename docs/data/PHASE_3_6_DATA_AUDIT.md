# AstraFlare Phase 3.6 — Data & Technical Infrastructure Audit

## Executive Summary

This document provides a comprehensive scientific and technical audit of AstraFlare's current data ingestion, event clustering, ground-truth schema, feature pipeline, label hierarchy, and ML model integration as of Phase 3.6.

**Current Model Governance Status:** `RESEARCH BASELINE / DATA-LIMITED`

---

## 1. Audit of Core System Components

### 1.1 FIRMS Ingestion Pipeline (`data_pipeline/firms_ingestion.py`)
- **Status:** Operational
- **Data Feeds:** Real NASA FIRMS API (`VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `MODIS_NRT`)
- **Current Observation Count:** 8,786 REAL satellite observations
- **Temporal Window:** 7-day rolling dataset (`2026-08-28 07:22:00+05:30` to `2026-09-04 15:54:00+05:30`)
- **Governance Tagging:** Strictly tagged `data_source = 'REAL'`

### 1.2 Historical Data Capabilities (`ml/data/ingest_historical_real_data.py`)
- **Status:** Operational
- **Capabilities:** Ingests historical FIRMS archive files and populatesPostgreSQL with rolling 30-day and 365-day spatial windows.

### 1.3 Physical Event Clustering (`data_pipeline/gis_engine.py` & `event_matcher.py`)
- **Status:** Operational
- **Methodology:** Spatio-temporal DBSCAN with Haversine distance ($\le 1.0 \text{ km}$) and temporal window ($\le 24 \text{ hours}$).
- **Result:** 8,786 individual observations clustered into **3,176 physical event clusters**.

### 1.4 Ground Truth Database Schema (`database/schema.sql`)
- **Status:** Operational
- **Tables:** `ground_truth_events` (external event records) and `event_hotspot_matches` (joins external events to FIRMS physical clusters).

### 1.5 Independent Event Matching (`data_pipeline/event_matcher.py`)
- **Status:** Operational
- **Match Criteria:** Spatial proximity ($\le 5 \text{ km}$) and temporal overlap ($\le 48 \text{ hours}$). Computes multi-attribute match score.

### 1.6 Label Construction & Hierarchy (`ml/labeling.py`)
- **Status:** Operational
- **Hierarchy:**
  $$\text{VERIFIED\_EXTERNAL} > \text{MANUAL\_VERIFIED} > \text{WEAK\_RULE} > \text{UNLABELED}$$
- **Current Label Distribution (Weak Baseline):**
  - `LIKELY_INDUSTRIAL_INCIDENT`: 15
  - `PERSISTENT_INDUSTRIAL_HEAT`: 180
  - `NATURAL_WILDLAND_FIRE`: 70
  - `UNLABELED`: 8,521

### 1.7 Feature Pipeline Engine (`data_pipeline/feature_pipeline.py`)
- **Status:** Operational
- **Generated Features:** FRP, FRP Anomaly Z-Score, industrial distance ($d_{\text{industrial}}$), 1km/5km facility counts, land cover class (ESA WorldCover), 30-day historical recurrence.

### 1.8 ML Training Pipeline & Splitters (`ml/train.py` & `ml/splitter.py`)
- **Status:** Operational
- **Model:** Gradient Boosted Decision Tree (LightGBM/GBDT baseline)
- **Splitters:** `EventGroupSplitter` (prevents spatial/temporal leakage across detections of the same physical event) and `FacilityGroupSplitter` (prevents facility leakage across train/test splits).

### 1.9 Dataset Versioning
- `DATASET_A` (`WEAK_BASELINE`): 3,176 physical events with rule-assisted weak supervision.
- `DATASET_B` (`INDEPENDENT_EXTERNAL`): Verified external ground-truth dataset.

### 1.10 Model Artifact & API Integration (`backend/app/services/prediction_service.py`)
- **Artifact:** `ml/models/astraflare_gbdt.json`
- **Governance:** Labeled `RESEARCH BASELINE` across all backend responses.
- **Abstention Gate:** Enforces operational abstention (`review_required = true`) when prediction confidence is below `HUMAN_REVIEW_THRESHOLD` ($0.65$).

---

## 2. Identified Scientific Limitations

1. **Short Historical Window:** Current active observations span a 7-day NRT window.
2. **Limited Verified External Events:** Truly independent external ground-truth incidents remain small.
3. **Label-Feature Circularity Risk:** Weak supervision rules rely on features ($d_{\text{industrial}}$, FRP) that are also passed as ML inputs.

---

## 3. Data Governance Verification

- Synthetic records in ML dataset: **0**
- Real records tagged `REAL`: **8,786**
- Mapped industrial facilities (OSM): **60**
