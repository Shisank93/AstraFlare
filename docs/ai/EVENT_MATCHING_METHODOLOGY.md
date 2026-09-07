# AstraFlare Spatial-Temporal Event Matching Methodology

## Overview
This document details the spatial-temporal event clustering, external-to-FIRMS matching algorithm, and event-isolated dataset splitting (`EventGroupSplitter`) implemented in AstraFlare.

---

## 1. Physical Event Clustering Algorithm

Raw satellite observations (e.g. VIIRS, MODIS) detect thermal anomalies as discrete pixel observations. Multiple passes over the same active fire or flare stack produce redundant detections.

To prevent spatial-temporal correlation leakage, contiguous detections are grouped into single physical event clusters:

```text
Cluster Condition:
Spatial Geodesic Distance (Haversine) <= 1.5 km (1,500 meters)
AND
Temporal Acquisition Difference <= 24 hours (86,400 seconds)
```

- **Clustering Method:** Union-Find / Connected Component Analysis using spatial grid cell indexing ($0.05^\circ \times 0.05^\circ \approx 5.5\text{ km}$).
- **Result:** Each FIRMS detection is assigned a unique `physical_event_id` (e.g., `evt_cluster_0012`).

---

## 2. External Ground-Truth Event Matching

Independent real-world events (e.g., government industrial accident logs, NASA fire event catalogs) are matched against candidate physical FIRMS event clusters:

1. Calculate geodesic distance $d$ (meters) between external event coordinate $(lat_{ext}, lon_{ext})$ and hotspot coordinate $(lat_{firms}, lon_{firms})$.
2. Calculate time difference $\Delta t$ (hours) between external event timestamp $t_{ext}$ and satellite acquisition timestamp $t_{firms}$.
3. Match Criterion:
   $$\text{Match} = (d \le 2000.0\text{ m}) \land (\Delta t \le 24.0\text{ hours})$$
4. Record `match_distance_m` and `match_time_hours` in `event_hotspot_matches` table.

---

## 3. Event-Isolated Train/Test Splitting (`EventGroupSplitter`)

To eliminate spatial-temporal leakage across satellite passes:

- All observations sharing the same `physical_event_id` are kept **strictly together** in either the Training set OR the Test set.
- Events are sorted chronologically by their earliest acquisition timestamp.
- The earliest 80% of physical events form the Training set; the latest 20% form the Test set.
- **Leakage Audit:** Guarantees zero overlap of physical fire events or industrial flare sites between training and testing splits.
