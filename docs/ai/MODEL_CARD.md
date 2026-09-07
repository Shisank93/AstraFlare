# MODEL CARD: AstraFlare GBDT Research Baseline (v1.0)

## Model Details

- **Model Name**: AstraFlare Event Classification Baseline
- **Model Version**: `v1.0`
- **Architecture**: `RandomForestClassifier` with Platt Sigmoid Probability Calibration
- **Target Classes**: `LIKELY_INDUSTRIAL_INCIDENT`, `PERSISTENT_INDUSTRIAL_HEAT`, `NATURAL_WILDLAND_FIRE`
- **Abstention Gate**: `HUMAN_REVIEW_REQUIRED` (Triggered when $P_{\max} < 0.65$)

## Intended Use

- **Primary Purpose**: Research baseline for evaluating event-level feature discrimination on NASA FIRMS thermal anomalies in India.
- **Out of Scope**: Automated production alert generation without human review.

## Factors & Performance

- **Development Macro F1**: `0.6667`
- **Calibrated ECE**: `0.0003`
- **Independent External Support**: $N=10$ events

## Ethical & Operational Safeguards

- Synthetic data exclusion enforced.
- Human Review abstention layer prevents low-confidence automated predictions.
- Facility-group isolation prevents spatial correlation leakage.