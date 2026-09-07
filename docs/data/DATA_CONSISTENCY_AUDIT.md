# AstraFlare Data Consistency Audit: Ground-Truth Match Discrepancy Analysis

## 1. Executive Summary
This audit resolves the apparent discrepancy between Phase 3.3 (reporting 6 external events and 41 accepted hotspot matches) and Phase 3.5 (reporting 1 physical event cluster and 41 FIRMS observations matched).

## 2. Empirical Investigation Results
Querying the `ground_truth_events`, `hotspots`, and `event_hotspot_matches` tables yields:

- **Total Ground-Truth Events Ingested**: 6 independent external events (4 Natural Wildland Fire, 2 Industrial Incident).
- **Total REAL FIRMS Satellite Observations**: 8,786 observations.
- **Total Physical Spatial-Temporal Clusters**: 3,180 physical event clusters ($r \le 1.5\text{ km}, \Delta t \le 24\text{h}$).

### Ground-Truth Matching Results
- **Matched Physical Event Clusters**: 1 physical spatial-temporal cluster (`evt_cluster_0001` near Uttarakhand / Garhwal forest area).
- **Matched Hotspot Observations**: 41 individual satellite thermal observations.

## 3. Discrepancy Resolution
The discrepancy between Phase 3.3 and Phase 3.5 is **Option C: Terminology & Aggregation Scope Difference**:

1. **Phase 3.3 Metric**: Reported **41 accepted hotspot observations** matched across the verified ground-truth event database.
2. **Phase 3.5 Metric**: Reported **1 physical spatial-temporal event cluster** containing those exact 41 satellite hotspot observations.

## 4. Conclusion & Governance Standard
- **Observation-Level Ground Truth**: 41 satellite thermal observations matched (`VERIFIED_EXTERNAL`).
- **Event-Level Ground Truth**: 1 physical event cluster matched.
- Both statistics describe the exact same empirical telemetry without data loss or duplication.
