# PHASE 3.11 — ASTRAFLARE EVIDENCE-BASED THERMAL ANOMALY RISK ENGINE

**Operational Status**: **`DETERMINISTIC EVIDENCE-BASED OPERATIONAL RISK ENGINE`**  
**Document Date**: `2026-09-05`  
**Repository**: AstraFlare Geospatial Intelligence Platform (India Thermal Anomalies)

---

## Mandatory Operational Disclaimer

> **IMPORTANT**: The risk score produced by the AstraFlare Risk Engine is a **deterministic operational prioritization score**, NOT a scientifically calibrated probability of an industrial accident. It provides structured, evidence-fusion ranking to assist human analysts in prioritizing thermal anomaly investigations.

---

## 1. Objective & Background

Phase 3.10 and Phase 3.10.1 established that supervised 3-class machine-learning classifiers (`RandomForestClassifier` / `GBDT`) are currently **DATA-LIMITED and NOT production-validated** due to an absence of training-eligible `LIKELY_INDUSTRIAL_INCIDENT` events in the development dataset (0 dev training samples; 10 independent test events across Vizag and Dahej).

To deliver reliable operational intelligence without depending on unvalidated ML probabilities or hallucinating LLMs, Phase 3.11 introduces the **AstraFlare Evidence-Based Thermal Anomaly Risk Engine**.

### Core Architecture Flow
```
NASA FIRMS Satellite Observation
               ↓
Physical Event Cluster Construction
               ↓
GIS Proximity Enrichment (OSM / GIHS Industrial Nodes)
               ↓
Historical Anomaly Baseline (Past-Only 30-Day FRP Z-Scores)
               ↓
Multi-Factor Dimensional Evidence Extraction & Scoring
               ↓
Deterministic Overall Risk Score & Operational Sub-Scores
               ↓
Investigation Priority (LOW, MEDIUM, HIGH, URGENT)
               ↓
Conflict Detection & Human Review Abstention Gate
               ↓
Structured Traceable Evidence JSON (Ready for Future LLM Analyst Copilot)
```

---

## 2. Evidence Dimensions & Input Contract

The engine accepts event feature vectors conforming to the existing 25-feature schema (or `RiskInput` Pydantic model):

| Dimension | Primary Input Features | Output Metric | Description |
|---|---|---|---|
| **Thermal Intensity** | `max_frp`, `max_brightness`, `confidence_high_ratio`, `observation_count` | `thermal_anomaly_score` $\in [0, 1]$ | Measures thermal radiative power magnitude and channel brightness |
| **Historical Anomaly** | `frp_anomaly_z`, `previous_detection_count`, `history_status` | `historical_anomaly_score` $\in [0, 1]$ | Evaluates FRP Z-score relative to past-only 30-day baseline |
| **Industrial Proximity** | `industrial_distance_m` | `industrial_proximity_score` $\in [0, 1]$ | Evaluates geodesic distance to nearest GIHS industrial site |
| **Industrial Density** | `industrial_site_count_250m`, `1km`, `5km` | `industrial_density_score` $\in [0, 1]$ | Evaluates nearby industrial site density without double-counting |
| **Natural / Wildland Context** | `worldcover_class` | `natural_fire_context_score` $\in [0, 1]$ | Categorizes 10m ESA WorldCover land use (Forest, Shrubland, Cropland, Built-up) |
| **Recurrence & Persistence** | `previous_detection_count`, `duration_hours`, `observation_count` | `recurrence_score`, `persistence_score` $\in [0, 1]$ | Distinguishes persistent heat from rare/unusual thermal spikes |
| **Data Quality** | `observation_count`, `satellite_count`, `confidence_high_ratio`, `history_status` | `data_quality_score` $\in [0, 1]$ | Evaluates telemetry completeness and GIS baseline quality |

---

## 3. Deterministic Scoring Methodology & Exact Formula

The overall risk score is calculated as a weighted composite of normalized dimensional scores:

$$\text{Overall Risk Score} = (S_{\text{thermal}} \cdot w_{\text{thermal}}) + (S_{\text{hist}} \cdot w_{\text{hist}}) + (S_{\text{ind\_prox}} \cdot w_{\text{ind\_prox}}) + (S_{\text{ind\_dens}} \cdot w_{\text{ind\_dens}}) + (S_{\text{rec}} \cdot w_{\text{rec}}) + (S_{\text{nat}} \cdot w_{\text{nat}}) + (S_{\text{qual}} \cdot w_{\text{qual}})$$

### Configured Operational Weights (`RiskEngineConfig`)
```python
thermal_weight    = 0.30  # Thermal Radiative Power & Radiance
historical_weight = 0.25  # FRP Anomaly Z-Score
industrial_weight = 0.20  # Proximity (0.14) + Site Density (0.06)
recurrence_weight = 0.10  # Activity Persistence/Recurrence
natural_weight    = 0.10  # Natural/Forest Vegetation Context
quality_weight    = 0.05  # Telemetry & GIS Quality Baseline
```
*(Sum of weights = $0.30 + 0.25 + 0.14 + 0.06 + 0.10 + 0.10 + 0.05 = 1.00$)*

---

## 4. Operational Risk Thresholds & Investigation Priority

### Risk Level Categorization
- **`LOW` Risk**: $0.00 \le \text{Overall Risk Score} \le 0.39$
- **`MEDIUM` Risk**: $0.40 \le \text{Overall Risk Score} \le 0.69$
- **`HIGH` Risk**: $0.70 \le \text{Overall Risk Score} \le 1.00$

### Investigation Priority Assignment
- **`URGENT`**: Risk Score $\ge 0.70$ **AND** Evidence Status $\in$ (`STRONG_INDUSTRIAL_CONTEXT`, `UNUSUAL_THERMAL_ACTIVITY`, `CONFLICTING_EVIDENCE`) **AND** Data Quality is `HIGH` or `MEDIUM`.
- **`HIGH`**: Risk Score $\ge 0.65$ **OR** Industrial Proximity Score $\ge 0.75$ **OR** (Natural Context $\ge 0.80$ and Thermal Score $\ge 0.50$).
- **`MEDIUM`**: Risk Score $\ge 0.40$.
- **`LOW`**: Risk Score $< 0.40$.

---

## 5. Conflict Detection & Human Review Gate

The engine automatically detects conflicting evidence signals and routes events for human analyst review when appropriate:

### Conflict Detection Rules
1. **Industrial vs Forest Conflict**: Distance to industry $\le 1000\text{m}$ **AND** land cover is dense forest (`Tree Cover / Forest (10)`) **AND** peak $FRP \ge 40.0\text{ MW}$. Sets `evidence_status = CONFLICTING_EVIDENCE`, `likely_context = AMBIGUOUS`, and `human_review_required = True`.
2. **High FRP Industrial Anomaly**: Proximity Score $\ge 0.75$ ($d \le 1000\text{m}$), $FRP \ge 40.0\text{ MW}$, and prior detection count $\le 2$. Sets `human_review_required = True` (Potential unverified industrial incident).
3. **Data Quality Deficit**: Telemetry quality is `LOW` or `INSUFFICIENT`. Sets `human_review_required = True`.
4. **High Risk Ambiguity**: Overall Risk Score $\ge 0.65$ with `likely_context == AMBIGUOUS`. Sets `human_review_required = True`.

---

## 6. Empirical Verification of Example Scenarios

The risk engine was verified across four real-world operational scenarios:

### Scenario A — Potential Industrial Anomaly
- **Inputs**: $FRP = 120\text{ MW}$, $d_{\text{ind}} = 450\text{m}$, $Z = +3.42$, prior detections $= 0$, Built-up land cover.
- **Output**:
  - **Risk Score**: `0.6236` (`MEDIUM` risk, `HIGH` priority)
  - **Evidence Status**: `STRONG_INDUSTRIAL_CONTEXT`
  - **Likely Context**: `INDUSTRIAL_CONTEXT`
  - **Human Review Required**: **`True`** (Triggered: High-intensity thermal anomaly near industrial site with low prior recurrence).

### Scenario B — Persistent Industrial Heat
- **Inputs**: $FRP = 25\text{ MW}$, $d_{\text{ind}} = 180\text{m}$, $Z = +0.20$, prior detections $= 12$, Hazira petrochemical site.
- **Output**:
  - **Risk Score**: `0.3773` (`LOW` risk, `HIGH` priority for site monitoring)
  - **Evidence Status**: `PERSISTENT_INDUSTRIAL_CONTEXT`
  - **Likely Context**: `PERSISTENT_INDUSTRIAL_CONTEXT`
  - **Human Review Required**: **`False`** (Expected operational heat behavior).

### Scenario C — Natural / Wildland Context
- **Inputs**: $FRP = 85\text{ MW}$, $d_{\text{ind}} = 8,500\text{m}$, $Z = +2.10$, Forest land cover.
- **Output**:
  - **Risk Score**: `0.4384` (`MEDIUM` risk, `MEDIUM` priority)
  - **Evidence Status**: `STRONG_NATURAL_CONTEXT`
  - **Likely Context**: `NATURAL_FIRE_CONTEXT`
  - **Human Review Required**: **`True`** (Forest fire anomaly review).

### Scenario D — Ambiguous / Conflicting Evidence
- **Inputs**: $FRP = 110\text{ MW}$, $d_{\text{ind}} = 450\text{m}$, $Z = +3.10$, Forest land cover near industrial site, prior detections $= 8$.
- **Output**:
  - **Risk Score**: `0.7460` (`HIGH` risk, `URGENT` priority)
  - **Evidence Status**: `CONFLICTING_EVIDENCE`
  - **Likely Context**: `AMBIGUOUS`
  - **Human Review Required**: **`True`** (Evidence conflict triggered).

---

## 7. Future LLM Interface Architecture

The risk engine is designed to export structured `RiskAssessment` JSON objects for future LLM integration (e.g. Gemini 2.5 via Firebase AI Logic):

```
Risk Engine (backend/risk_engine/)
               ↓
Structured RiskAssessment JSON (Deterministic Scores & Traceable Evidence)
               ↓
Gemini LLM Analyst Copilot (Zero Numerical Math, Explanation Generation Only)
               ↓
Grounded Operational Analyst Briefing
```

### Critical Governance Rule for LLM Integration
- The LLM **MUST NEVER** calculate numerical distances, FRP anomaly Z-scores, risk weights, or probabilities.
- The LLM **ONLY** consumes already-computed, deterministic evidence items to generate natural language briefings when routed for human review.

---

## 8. Summary of Package Artifacts & Test Results

### Code Modules Created
- `backend/risk_engine/config.py`: `RiskEngineConfig` Pydantic model for weights and thresholds.
- `backend/risk_engine/models.py`: `RiskInput`, `EvidenceItem`, `EvidenceBreakdown`, `RiskAssessment` Pydantic models.
- `backend/risk_engine/scoring.py`: Dimensional scoring functions for thermal, historical, industrial, land cover, and recurrence axes.
- `backend/risk_engine/quality.py`: Telemetry and GIS data quality evaluator.
- `backend/risk_engine/conflict.py`: Conflict detector and human review routing logic.
- `backend/risk_engine/evidence.py`: Evidence extractor and traceability table formatter.
- `backend/risk_engine/engine.py`: Master `EvidenceRiskEngine` entry point class.
- `backend/risk_engine/__init__.py`: Package exports.

### Test Suite Results
Created comprehensive test suite in `tests/test_phase_3_11_risk_engine.py`.  
Ran `pytest -q`:
```
121 passed, 7 warnings in 31.45s
```
- **105 existing tests**: 105 passed.
- **16 new Phase 3.11 Risk Engine tests**: 16 passed.
