# AstraFlare Ground-Truth Independent Evidence Dataset Specification

## Overview
This document specifies the architecture, data sources, matching statistics, and governance rules for AstraFlare's independent real-world ground-truth dataset (`Dataset B`).

---

## 1. Integrated External Sources

| Source Identifier | Organization | Dataset / Product Name | Coverage & Resolution | Access Method | Provenance Tag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NASA_FIRMS_NRT_EVENT_CATALOG` | NASA Earthdata | VIIRS NRT Fire Event Catalog | Global / South Asia (375m pixel, satellite timestamp) | Direct API / NRT Feed | `VERIFIED_EXTERNAL` |
| `GLOBAL_FOREST_WATCH_ALERTS` | World Resources Institute (WRI) | GFW Wildfire Alert Registry | Global Tropical & Temperate Forests | API / Vector Polygon | `VERIFIED_EXTERNAL` |
| `PESO_NDMA_INDUSTRIAL_INCIDENT_REGISTRY` | Petroleum & Explosives Safety Organisation (PESO) / NDMA | Industrial Safety Incident Records | India / Regional Industrial Complexes | Public Record / Government Registry | `VERIFIED_EXTERNAL` / `MANUAL_VERIFIED` |
| `WEAK_RULE` | Internal Rule Engine | Spatial/Historical Heuristics | 8,778 FIRMS Detections | Internal Python Rule Engine | `WEAK_RULE` |

---

## 2. Dataset Records & Match Summary

```text
Total REAL Satellite Detections Processed:   8,778
Total Physical Event Clusters:             3,176
External Ground-Truth Events Retrieved:      6

Breakdown by Event Class:
- Natural Wildland Fire:
  * External Verified Events: 4 physical forest fire clusters (Garhwal, Simlipal, Chhattisgarh)
  * Matched FIRMS Hotspots:   70 satellite detections
  * Verification Status:      VERIFIED_EXTERNAL (1.0 confidence)

- Likely Industrial Incident:
  * External Verified Events: 2 government-recorded Industrial Safety Incidents (Vadodara & Hazira complexes)
  * Matched FIRMS Hotspots:   15 satellite detections
  * Verification Status:      VERIFIED_EXTERNAL (0.96 - 0.98 confidence)

- Persistent Industrial Heat:
  * External Verified Events: 11 physical industrial flare sites (Baroda Refinery, Jamnagar, Hazira)
  * Matched FIRMS Hotspots:   180 satellite detections
  * Verification Status:      FACILITY_VERIFIED / WEAK_LABEL_ONLY (Operational facility persistence)
```

---

## 3. Data Quality & Governance Gates

1. **Zero Synthetic Data:** `SYNTHETIC_DEMO` observations are strictly excluded from dataset generation, model training, and performance metrics.
2. **Precedence Hierarchy:** `VERIFIED_EXTERNAL` (1.0) > `MANUAL_VERIFIED` (0.95) > `WEAK_RULE` (0.80) > `UNLABELED` (0.0). Weak supervision rules can **NEVER** overwrite independently verified external evidence.
3. **Conflict Routing:** If competing external evidence types match the same FIRMS physical cluster, the state is set to `CONFLICTING_EVIDENCE` and routed to `HUMAN_REVIEW_REQUIRED`.
