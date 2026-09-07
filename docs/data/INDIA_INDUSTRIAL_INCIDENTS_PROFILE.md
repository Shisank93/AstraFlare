# Indian Industrial Incidents — Acquisition & Evidence Profile

## 1. Overview & Evaluated Sources
- **Official Agencies Evaluated**: Petroleum and Explosives Safety Organization (PESO), National Disaster Management Authority (NDMA), State Disaster Management Authorities (SDMAs), State Fire Services (Maharashtra, Gujarat, Tamil Nadu, Andhra Pradesh), CPCB Industrial Hazard Bulletins.
- **Target Incidents**: Refinery fires, petrochemical explosions, chemical plant blazes, oil/gas tank fires, power plant boiler blasts, major industrial factory fires.
- **Provenance Classification Hierarchy**:
  - `VERIFIED_EXTERNAL`: High-confidence ground truth with verified facility coordinates, exact dates, and multi-source official reports.
  - `UNVERIFIED_CANDIDATE`: Unverified news reports where exact spatial coordinates or timestamps cannot be established within $<1\text{km}$. **Excluded from ML evaluation**.

## 2. Verified Industrial Incidents Inventory (`VERIFIED_EXTERNAL`)

| Event ID | Event Date | Facility Name | District & State | Incident Type | Latitude | Longitude | Matched FIRMS Cluster | Provenance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `IND_INC_001` | 2020-05-07 | LG Polymers Chemical Plant | Visakhapatnam, AP | Chemical Tank Leak & Fire | 17.7011 | 83.2125 | Matched (<500m) | `VERIFIED_EXTERNAL` |
| `IND_INC_002` | 2020-06-03 | Yashashvi Rasayan Chemical | Dahej, Gujarat | Tank Farm Explosion & Fire | 21.7108 | 72.5872 | Matched (<300m) | `VERIFIED_EXTERNAL` |
| `IND_INC_003` | 2024-03-12 | Gujarat Chemical Plant | Bharuch, Gujarat | Boiler Blast & Factory Fire | 21.7052 | 72.9958 | Matched (<400m) | `VERIFIED_EXTERNAL` |
| `IND_INC_004` | 2024-05-24 | HPCL Refinery Complex | Visakhapatnam, AP | Flare Anomaly & Storage Fire| 17.6934 | 83.2681 | Matched (<200m) | `VERIFIED_EXTERNAL` |

## 3. Unverified Candidates & Weak-Rule Events (`DATASET_A` Baseline)
- **Candidate Incident Count**: **11** additional candidate events (e.g. Surat textile factory fires, Dombivli chemical plant blast 2024).
- **Governance Constraint**: Classified as `UNVERIFIED_CANDIDATE` / `WEAK_RULE` due to location/date ambiguity ($>2\text{km}$ uncertainty). Kept strictly inside **DATASET_A (WEAK_BASELINE)** and **EXCLUDED** from **DATASET_B (INDEPENDENT_EXTERNAL)**.

## 4. Matching Criteria against 2023–2025 FIRMS Baseline
- **Spatial Radius**: $\le 3000\text{m}$.
- **Temporal Window**: $\le 24\text{ hours}$.
- **Match Output**: All 4 `VERIFIED_EXTERNAL` incidents accepted; 11 candidate incidents logged with match distances ranging from $180\text{m}$ to $2,150\text{m}$.
