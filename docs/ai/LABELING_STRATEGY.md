# AstraFlare Labeling Strategy & Label Provenance Specification

**Project:** AstraFlare  
**Document:** Weak Supervision Labeling Rules, Provenance Framework, & Quality Audit  

---

## 1. Label Provenance Framework

Because ground-truth physical labels are not natively provided by satellite telemetry (e.g. NASA FIRMS detects thermal anomalies, not semantic causes), AstraFlare implements a formal **Label Provenance System**.

Each label record explicitly records:

```json
{
  "label": "LIKELY_INDUSTRIAL_INCIDENT",
  "label_source": "WEAK_RULE",
  "label_confidence": 0.85,
  "label_reason": "High FRP anomaly (Z=+2.84) within 450m of chemical industrial facility",
  "label_version": "v1.0"
}
```

### Label Sources
- `VERIFIED_EXTERNAL`: Verified physical incident ground truth (e.g., official fire department logs, verified news reports).
- `WEAK_RULE`: Multivariable rule-based weak supervision heuristic based on spatial, land-cover, and historical thermal signals.
- `MANUAL_REVIEW`: Expert human analyst validated label.
- `UNLABELED`: Ambiguous or borderline observation reserved for human review.

---

## 2. Weak Supervision Label Construction Rules

To avoid simplistic **circular labeling** (where a model learns a single trivial rule like `if dist < 1km: return INDUSTRIAL`), AstraFlare uses multi-variable composite rules combining spatial distance, historical thermal recurrence, land-cover biome, and FRP Z-score anomalies:

### Rule 1: `LIKELY_INDUSTRIAL_INCIDENT`
- **Condition:**
  - Nearby industrial site ($\text{distance} \le 2.0 \text{ km}$) **AND**
  - High FRP Anomaly Z-Score ($Z \ge 2.0$) or high absolute FRP ($FRP \ge 50.0 \text{ MW}$) **AND**
  - Land cover is `built_up` or `bare` or `cropland`.
- **Reasoning:** Sudden, high-energy thermal spike exceeding normal historical operational levels near an industrial facility.

### Rule 2: `PERSISTENT_INDUSTRIAL_HEAT`
- **Condition:**
  - Nearby industrial site ($\text{distance} \le 1.5 \text{ km}$) **AND**
  - Low or moderate FRP Anomaly ($Z < 1.0$) **AND**
  - High historical hotspot recurrence ($\text{count}_{30d} \ge 3$ or $\text{count}_{365d} \ge 5$).
- **Reasoning:** Continuous, steady thermal radiation characteristic of industrial flare stacks, kilns, or manufacturing operations.

### Rule 3: `NATURAL_WILDLAND_FIRE`
- **Condition:**
  - Non-industrial land cover (`forest`, `shrubland`, `grassland`, `wetland`, `mangroves`) **AND**
  - Far from industrial infrastructure ($\text{distance} > 5.0 \text{ km}$) **AND**
  - Moderate to high FRP ($FRP \ge 10.0 \text{ MW}$).
- **Reasoning:** Thermal anomaly occurring deep in natural vegetation without industrial heat sources nearby.

### Rule 4: `UNLABELED` (Borderline / Ambiguous)
- **Condition:** Any observation failing to meet the criteria above (e.g., high FRP anomaly in a forest 1.2 km from a refinery, or low FRP anomaly in an open field far from industry).
- **Handling:** Filtered out from supervised GBDT training or routed to analyst review.

---

## 3. Label Quality Audit & Limitations

1. **Weak Label Noise:** Weak rules carry intrinsic noise. We treat weak labels as *provisional training targets*, never as scientific absolute ground truth.
2. **Class Imbalance Audit:** Reports exact sample counts and percentages across all 3 classes.
3. **No Synthetic Contamination:** Synthetic demo records are strictly prohibited from generating training labels.
