# Machine Learning & AI Architecture

**Project:** AstraFlare  
**Document:** ML Model, Feature Engineering & Explainability Specification  

---

## 1. Machine Learning Strategy

AstraFlare leverages **Tabular Gradient Boosted Decision Trees (GBDT)** (specifically LightGBM / CatBoost) for anomaly cause classification.

### Why GBDT over CNN / Vision Models:
1. **Satellite FIRMS Thermal Detections are Point Observations:** NASA FIRMS outputs tabular attributes (lat, lon, FRP, brightness, acquisition timestamp) rather than dense multi-spectral raster images.
2. **High Feature Heterogeneity:** Tabular GBDT naturally handles heterogeneous features (distances in meters, categorical land-cover IDs, continuous FRP ratios, historical counts).
3. **Sub-millisecond Latency:** GBDT inference completes in < 5ms per point, enabling real-time streaming enrichment.
4. **Deterministic SHAP Explainability:** Tree SHAP provides exact per-feature contribution scores for analyst evidence reports.

---

## 2. Feature Vector Engineering

| Feature Name | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `frp` | Continuous | Current Fire Radiative Power (MW) | NASA FIRMS |
| `brightness` | Continuous | Brightness temperature (Kelvin) | NASA FIRMS |
| `dist_industrial_m` | Continuous | Distance to nearest industrial facility (meters) | OSM / PostGIS |
| `industrial_type_cat` | Categorical | Type of nearby facility (refinery, chemical, power, flare, none) | OSM |
| `land_cover_class` | Categorical | Land cover type (urban, forest, crop, grass, water) | ESA WorldCover |
| `recurrence_count_30d` | Integer | Detections within 1km radius in past 30 days | Historical FIRMS |
| `recurrence_count_365d`| Integer | Detections within 1km radius in past 365 days | Historical FIRMS |
| `frp_ratio_to_hist_mean`| Continuous | `current_frp / mean_historical_frp` | Feature Calculation |
| `day_night` | Categorical | Day ('D') or Night ('N') acquisition | NASA FIRMS |
| `wind_speed_10m` | Continuous | Local wind speed (m/s) | ERA5 / Weather |

---

## 3. Labeling Methodology & Weak Supervision Notice

> [!WARNING]
> Training labels are derived via programmatic heuristic rules (weak supervision). To avoid circular learning, feature thresholds used for provisional labeling are strictly decoupled from model inference features, and provisional labels are treated as noisy training priors, NOT absolute ground truth.

### Weak Supervision Rules (Training Dataset Generation):
- **Class 1 (Likely Industrial Incident):** `dist_industrial_m < 500m AND frp_ratio_to_hist_mean > 2.5 AND frp > 50`
- **Class 2 (Persistent Industrial Heat):** `dist_industrial_m < 800m AND recurrence_count_365d >= 10 AND frp_ratio_to_hist_mean BETWEEN 0.5 AND 1.8`
- **Class 3 (Natural/Wildland Fire):** `dist_industrial_m > 2000m AND land_cover_class IN ('tree_cover', 'shrubland', 'grassland')`
- **Class 4 (Human Review Required):** Ambiguous feature overlap or conflicting signals.

---

## 4. Confidence & Abstention Mechanism

The model outputs calibrated prediction probabilities vector \( \mathbf{P} = [p_1, p_2, p_3] \).

```text
max_prob = max(p_1, p_2, p_3)

IF max_prob < 0.65 OR (p_1 - p_2 < 0.10 for top 2 classes):
    Final_Class = "Human Review Required"
    Abstention_Flag = True
ELSE:
    Final_Class = argmax(p_1, p_2, p_3)
    Abstention_Flag = False
```

---

## 5. SHAP & Evidence Engine Integration

For each prediction, TreeSHAP calculates the contribution \( \phi_i \) for each feature. The top 3 positive feature contributions are converted into natural language evidence statements:

```python
# Conceptual Evidence Transformation
if feature == "dist_industrial_m" and val < 300:
    evidence.append(f"Proximity to industrial facility ({val:.0f}m) strongly increases industrial likelihood.")
if feature == "recurrence_count_365d" and val > 15:
    evidence.append(f"High historical recurrence ({val} events in 1 year) indicates persistent operational thermal activity.")
```
