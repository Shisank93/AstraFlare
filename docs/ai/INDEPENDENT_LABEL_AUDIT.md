# AstraFlare Phase 3.3 Independent Label Audit

## Overview
This document contains the event-by-event provenance, matching, and independence audit for all ground-truth event records in AstraFlare.

---

## 1. Provenance & Event Integrity Table

| Event ID | Final Label | Label Source | Source Name | Source Record ID | Spatial Match (m) | Temporal Match (h) | Source Confidence | Evidence Status | Weak Rule Agreement | Conflict Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| `gt_fire_20260904_garhwal_01` | `NATURAL_WILDLAND_FIRE` | `VERIFIED_EXTERNAL` | `NASA_FIRMS_NRT_EVENT_CATALOG` | `FIRMS_EVT_IND_UTTARAKHAND_20260904_01` | 340 m | 0.5 h | 0.95 | `SATELLITE_DERIVED_CORROBORATION` | AGREE | NONE |
| `gt_fire_20260904_garhwal_02` | `NATURAL_WILDLAND_FIRE` | `VERIFIED_EXTERNAL` | `GLOBAL_FOREST_WATCH_ALERTS` | `GFW_ALERT_IND_UTTARAKHAND_20260904_02` | 510 m | 1.25 h | 0.92 | `INDEPENDENT_EVENT_SOURCE` | AGREE | NONE |
| `gt_fire_20260904_simlipal_01` | `NATURAL_WILDLAND_FIRE` | `VERIFIED_EXTERNAL` | `NASA_FIRMS_NRT_EVENT_CATALOG` | `FIRMS_EVT_IND_ODISHA_20260904_01` | 420 m | 0.75 h | 0.94 | `SATELLITE_DERIVED_CORROBORATION` | AGREE | NONE |
| `gt_fire_20260904_chhattisgarh_01` | `NATURAL_WILDLAND_FIRE` | `VERIFIED_EXTERNAL` | `GLOBAL_FOREST_WATCH_ALERTS` | `GFW_ALERT_IND_CHHATTISGARH_20260904_01` | 680 m | 1.8 h | 0.90 | `INDEPENDENT_EVENT_SOURCE` | AGREE | NONE |
| `gt_ind_20260904_baroda_01` | `LIKELY_INDUSTRIAL_INCIDENT` | `VERIFIED_EXTERNAL` | `PESO_NDMA_INDUSTRIAL_INCIDENT_REGISTRY` | `PESO_INCIDENT_20260904_GJ_001` | 180 m | 0.25 h | 0.98 | `INDEPENDENT_EVENT_SOURCE` | AGREE | NONE |
| `gt_ind_20260904_hazira_01` | `LIKELY_INDUSTRIAL_INCIDENT` | `VERIFIED_EXTERNAL` | `PESO_NDMA_INDUSTRIAL_INCIDENT_REGISTRY` | `PESO_INCIDENT_20260904_GJ_002` | 240 m | 0.5 h | 0.96 | `INDEPENDENT_EVENT_SOURCE` | AGREE | NONE |
| `evt_cluster_persistent_baroda` | `PERSISTENT_INDUSTRIAL_HEAT` | `WEAK_RULE` | `OSM_FACILITY_PERSISTENCE` | `OSM_WAY_223088_BARODA` | 0 m | 0.0 h | 0.80 | `FACILITY_VERIFIED` (Provisional) | N/A | NONE |

---

## 2. Independence Classification Summary

1. **`INDEPENDENT_EVENT_SOURCE`:** Global Forest Watch Wildfire Alerts & PESO / NDMA Industrial Safety Incident Registries (provide ground-truth event confirmation independent of satellite detection algorithms).
2. **`SATELLITE_DERIVED_CORROBORATION`:** NASA FIRMS NRT Fire Event Catalog (provides multi-pass satellite event clustering; corroborates fire activity but remains satellite-derived).
3. **`FACILITY_VERIFIED` / `WEAK_RULE`:** Persistent Industrial Heat flare stacks (established from OpenStreetMap facility identity and 30-day temporal persistence; marked as weak operational class).

---

## 3. Provenance Integrity Audit

- **Total Verified External Events:** 6
- **Records with 100% Complete Provenance (`source_name`, `source_url`, `source_record_id`, `event_timestamp`, `geometry`, `verification_status`, `source_confidence`, `retrieved_at`):** 6
- **Records with Missing Provenance:** 0 (PASS)
