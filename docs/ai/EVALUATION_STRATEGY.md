# AstraFlare Model Evaluation Strategy

**Project:** AstraFlare  
**Document:** Spatial-Temporal Data Splitting, Calibration, Abstention, & Metrics Specification  

---

## 1. Spatial & Temporal Leakage Prevention

Standard random splitting (`train_test_split(random_state=42)`) fails on geospatial satellite datasets because spatially adjacent or temporally contiguous observations are highly correlated. This leads to artificially inflated validation metrics ("spatial memory").

AstraFlare implements two strict evaluation splits:

### 1.1 Temporal Chronological Split
- Records are sorted chronologically by `acq_timestamp`.
- **Training Set:** Past 80% time window.
- **Test Set:** Most recent 20% time window.
- **Objective:** Evaluates how well the model predicts future thermal events based on past observation baselines.

### 1.2 Spatial GroupKFold Split
- Geometries are grouped into geographic spatial grid cells ($\approx 0.5^\circ \times 0.5^\circ$ lat/lon bounding boxes).
- Observations within the same spatial grid cell are assigned together to either train or test folds.
- **Objective:** Evaluates model generalization to completely unobserved geographic regions.

---

## 2. Model Evaluation Metrics

Performance is evaluated using multi-class metrics that account for class imbalance:

- **Per-Class Metrics:** Precision, Recall, and F1-Score for each primary class (`LIKELY_INDUSTRIAL_INCIDENT`, `PERSISTENT_INDUSTRIAL_HEAT`, `NATURAL_WILDLAND_FIRE`).
- **Global Summary Metrics:**
  - Macro F1-Score ($\text{F1}_{\text{macro}}$): Unweighted mean of class F1-scores.
  - Weighted F1-Score ($\text{F1}_{\text{weighted}}$): Class-frequency weighted mean.
  - Multi-Class Confusion Matrix: Normalized confusion matrix across all target classes.
- **Probabilistic Metrics:** Log Loss and Brier Score evaluating prediction confidence accuracy.

---

## 3. Probability Calibration & Abstention Gate

### 3.1 Probability Calibration
Uncalibrated GBDT models can output overconfident probabilities. We apply **Isotonic Regression / Sigmoid Calibration** (`CalibratedClassifierCV`) on the validation partition to calibrate output probabilities $P(Y=c|X)$.

### 3.2 Operational Abstention Gate
The platform requires high decision confidence for automated classification:
- Configurable Operational Threshold: `HUMAN_REVIEW_THRESHOLD = 0.65`.
- **Logic:**
  $$\text{confidence} = \max_{c \in C} P(Y=c|X)$$
  $$\text{If } \text{confidence} \ge 0.65 \implies \text{predicted\_class} = \arg\max_c P(Y=c|X), \quad \text{is\_abstained} = \text{False}$$
  $$\text{If } \text{confidence} < 0.65 \implies \text{predicted\_class} = \text{'Human Review Required'}, \quad \text{is\_abstained} = \text{True}$$
