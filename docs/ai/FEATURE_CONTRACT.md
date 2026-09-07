# AstraFlare Feature Contract & Leakage Audit Specification

**Project:** AstraFlare  
**Document:** Feature Vector Schema, Data Types, Transformation Pipeline, & Leakage Audit  

---

## 1. Feature Vector Contract

All ML training and real-time inference pipelines consume a standardized tabular feature matrix conforming to the contract below:

| Feature Name | Data Type | Source Layer | Description | Range / Units |
| :--- | :--- | :--- | :--- | :--- |
| `industrial_distance_m` | Float | OSM GIS Layer | Distance to nearest industrial facility | $[0.0, 10000.0]$ meters |
| `industrial_count_1km` | Integer | OSM GIS Layer | Count of industrial facilities within 1 km | $[0, \infty)$ |
| `industrial_count_5km` | Integer | OSM GIS Layer | Count of industrial facilities within 5 km | $[0, \infty)$ |
| `frp` | Float | FIRMS Telemetry | Fire Radiative Power | $[0.0, \infty)$ MW |
| `brightness` | Float | FIRMS Telemetry | Brightness temperature (Kelvin / Relative) | $[200.0, 500.0]$ |
| `daynight_is_day` | Integer (0/1) | FIRMS Telemetry | Binary indicator (1 = Day, 0 = Night) | $\{0, 1\}$ |
| `historical_count_30d` | Integer | Hotspots History | Recurrence count within 1km in past 30 days | $[0, \infty)$ |
| `historical_mean_frp` | Float | Hotspots History | Historical mean FRP within 1km buffer | $[0.0, \infty)$ MW |
| `frp_anomaly_zscore` | Float | GIS Engine | FRP Anomaly Z-score: $(FRP - \mu)/\sigma$ | $(-\infty, +\infty)$ |
| `land_cover_code` | Integer | ESA WorldCover | WorldCover 10m land cover class code | $\{10, 20, 30, 40, 50, \dots\}$ |
| `is_built_up_land` | Integer (0/1) | ESA WorldCover | Binary indicator for urban/built-up land (code 50) | $\{0, 1\}$ |
| `is_forest_land` | Integer (0/1) | ESA WorldCover | Binary indicator for forest/tree cover (code 10/95) | $\{0, 1\}$ |

---

## 2. Leakage Audit Table

To guarantee strict temporal and information leakage prevention, every candidate feature has been audited prior to inclusion in the production model:

| Feature | Source | Available at Inference? | Potential Leakage? | Decision | Rationale |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `frp` | NASA FIRMS | YES | NO | **KEEP** | Direct satellite sensor reading available at detection time |
| `brightness` | NASA FIRMS | YES | NO | **KEEP** | Direct satellite sensor reading available at detection time |
| `industrial_distance_m` | OSM | YES | NO | **KEEP** | Computed from static OSM spatial reference layer |
| `historical_count_30d` | History | YES | **YES if unconstrained** | **KEEP (Filtered)** | Constrained strictly to past events ($t_{hist} < t_i$) excluding target ID |
| `frp_anomaly_zscore` | History | YES | **YES if unconstrained** | **KEEP (Filtered)** | Baseline mean/std calculated strictly excluding current observation |
| `future_recurrence_7d` | Future telemetry | NO | **CRITICAL LEAKAGE** | **EXCLUDE** | Look-ahead feature unavailable at real-time inference |
| `analyst_review_status` | Database | NO | **CRITICAL LEAKAGE** | **EXCLUDE** | Downstream human review outcome created post-prediction |

---

## 3. Preprocessing & Transformation Rules

1. **Numerical Imputation:** Missing historical stats (e.g. no prior history) default to `historical_count_30d = 0`, `historical_mean_frp = current_frp`, `frp_anomaly_zscore = 0.0`.
2. **Scaler/Transformer Isolation:** Preprocessing scalers (StandardScaler / RobustScaler) are fit **ONLY on the training partition** and applied to validation/test partitions.
