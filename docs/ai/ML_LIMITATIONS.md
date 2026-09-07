# AstraFlare Machine Learning Known Limitations & Risk Disclosure

**Project:** AstraFlare  
**Document:** Technical Limitations, Operational Risks, & Data Boundaries  

---

## 1. Primary Technical & Data Boundaries

1. **Weak Supervision Noise:** Labels are derived from multi-variable rule heuristics and spatial reference layers, not 100% verified ground-truth physical incident reports. The model predicts contextual likelihoods, not confirmed legal/regulatory facts.
2. **Geographic Concentration:** Initial training data is sourced from real 7-day NASA FIRMS observations covering South Asia (India, Pakistan, Bangladesh). Generalization to North America or Europe has not been benchmarked.
3. **Temporal Scope:** Baseline training is performed on a 7-day continuous satellite feed ($\approx 8,700$ real satellite detections). Seasonal variations across monsoon, winter, and agricultural burning cycles require ongoing multi-month dataset ingestion.
4. **Resolution Constraints:** Satellite thermal pixel footprint sizes range from $375\text{m} \times 375\text{m}$ (VIIRS) to $1\text{km} \times 1\text{km}$ (MODIS). Sub-pixel heat sources smaller than $10\text{m}^2$ may be blended into surrounding background pixels.
5. **OpenStreetMap Completeness:** Proximity features depend on OpenStreetMap coverage. Unmapped industrial sites or unregistered flare stacks may lead to false classification as wildland events.

---

## 2. Operational Guidelines & Safety Disclosures

- **Human-in-the-Loop Mandatory:** AstraFlare classification output is intended for decision support and event prioritization for disaster response teams and environmental analysts.
- **Abstention Flag Compliance:** Predictions flagged with `is_abstained = True` (`Human Review Required`) MUST be manually inspected prior to operational dispatch.
- **No Synthetic Model Contamination:** Synthetic demo records (`SYNTHETIC_DEMO`) are strictly prohibited from entering training datasets.
