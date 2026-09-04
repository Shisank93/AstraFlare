# ADR-003: Selection of Tabular Gradient Boosted Decision Trees (GBDT)

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
Thermal anomaly classification requires evaluating spatial distance, land cover category, historical recurrence counts, brightness, and FRP anomaly ratios.

**Decision:**  
Use **Tabular GBDT** algorithms (LightGBM / CatBoost) for anomaly cause classification.

**Alternatives Considered:**  
1. **Rule-based Expert Systems:** Rigid, fails to handle subtle multi-feature interactions or non-linear probability estimation.
2. **Deep Neural Networks (MLP):** Slower training, requires heavy feature scaling, poor interpretability compared to tree-based models.

**Trade-offs & Rationale:**  
GBDT models excel on heterogeneous tabular spatial features, require minimal scaling preprocessing, execute inference in < 5ms, and natively support exact TreeSHAP value calculation for analyst evidence reporting.
