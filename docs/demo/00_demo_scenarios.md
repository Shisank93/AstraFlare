# Demo Scenarios & Test Verification Matrix

**Project:** AstraFlare  
**Document:** SIH26162 Demonstration Scenarios & Validation Protocol  

---

## 1. Scenario A: Likely Industrial Incident

### Input Characteristics
- **Coordinates:** `22.3072° N, 73.1812° E` (Vadodara Industrial Corridor)
- **FRP:** `155.0 MW` (High thermal energy emission)
- **Brightness:** `365.2 K`
- **Acquisition Time:** `2026-09-04 14:15:00 UTC`

### Contextual Evidence
- **Distance to Industrial Site:** `180 meters` (Gujarat Refinery)
- **Land Cover:** `Built-up / Industrial`
- **Historical Recurrence (365d):** `2 detections`
- **Historical Baseline FRP:** `32.0 MW` (`Current FRP / Baseline FRP = 4.84x`)

### Expected System Outputs
- **Predicted Class:** `Likely Industrial Incident`
- **Model Confidence:** `0.92`
- **Calculated Risk Score:** `0.95` (Critical Triage Priority)
- **Generated Evidence:**
  1. "Extreme proximity (180m) to major oil refinery."
  2. "Current FRP (155.0 MW) represents a 4.84x abnormal surge above historical baseline."
  3. "Land cover confirmed as Industrial / Built-up area."
- **Analyst Workflow:** Triggers instant red marker on map, places event at top of critical alert list.

---

## 2. Scenario B: Persistent Industrial Heat

### Input Characteristics
- **Coordinates:** `22.4707° N, 70.0577° E` (Jamnagar Petrochemical Belt)
- **FRP:** `48.2 MW`
- **Brightness:** `332.0 K`
- **Acquisition Time:** `2026-09-04 12:30:00 UTC`

### Contextual Evidence
- **Distance to Industrial Site:** `120 meters` (Flare Stack Cluster)
- **Land Cover:** `Built-up / Industrial`
- **Historical Recurrence (365d):** `84 detections` (Highly persistent)
- **Historical Baseline FRP:** `46.5 MW` (`Current FRP / Baseline FRP = 1.03x`)

### Expected System Outputs
- **Predicted Class:** `Persistent Industrial Heat`
- **Model Confidence:** `0.94`
- **Calculated Risk Score:** `0.35` (Low Operational Risk - Routine Flare)
- **Generated Evidence:**
  1. "High historical persistence (84 detections in past 12 months at exact coordinates)."
  2. "FRP is stable and matches historical routine industrial flare baseline (1.03x ratio)."
  3. "Located within petrochemical manufacturing facility boundaries."

---

## 3. Scenario C: Natural / Wildland Fire

### Input Characteristics
- **Coordinates:** `30.4500° N, 78.8500° E` (Garhwal Forest Division, Uttarakhand)
- **FRP:** `88.5 MW`
- **Brightness:** `342.1 K`
- **Acquisition Time:** `2026-09-04 09:10:00 UTC`

### Contextual Evidence
- **Distance to Industrial Site:** `14,200 meters` (No industrial infrastructure within 14km)
- **Land Cover:** `Tree Cover (Dense Forest)`
- **Historical Recurrence (365d):** `1 detection`
- **Weather Context:** `Wind Speed: 18.5 km/h, Relative Humidity: 22%`

### Expected System Outputs
- **Predicted Class:** `Natural/Wildland Fire`
- **Model Confidence:** `0.91`
- **Calculated Risk Score:** `0.82` (High Forest Fire Risk)
- **Generated Evidence:**
  1. "Zero industrial infrastructure within 14.2km radius."
  2. "ESA WorldCover verifies high-density forest tree cover."
  3. "Low relative humidity (22%) and moderate wind speed favor forest fire propagation."

---

## 4. Scenario D: Ambiguous Event → Human Review Required

### Input Characteristics
- **Coordinates:** `21.1702° N, 72.8311° E` (Surat Forest-Industrial Fringe)
- **FRP:** `32.0 MW`
- **Brightness:** `324.5 K`
- **Acquisition Time:** `2026-09-04 16:45:00 UTC`

### Contextual Evidence
- **Distance to Industrial Site:** `1,100 meters` (Ambiguous distance boundary)
- **Land Cover:** `Cropland / Mixed Shrubland`
- **Historical Recurrence (365d):** `4 detections`
- **FRP Ratio:** `1.4x`

### Expected System Outputs
- **Raw Class Probabilities:** `[Industrial Incident: 0.38, Persistent Heat: 0.22, Wildland Fire: 0.40]`
- **Max Probability:** `0.40` (Below 0.65 Confidence Threshold)
- **System Action:** **Abstain & Trigger `Human Review Required`**
- **Calculated Risk Score:** `0.50`
- **Generated Evidence:**
  1. "Model confidence (0.40) below minimum required decision threshold (0.65)."
  2. "Conflicting spatial signals: Agricultural land cover adjacent to industrial zone perimeter."
  3. "Routed to human analyst queue for visual satellite verification."
