# AstraFlare Facility Isolation Methodology

## Overview
This document specifies the facility-level train/test partitioning methodology (`FacilityGroupSplitter`) implemented in AstraFlare to eliminate industrial facility correlation leakage across multi-week historical datasets.

---

## 1. Facility Correlation Leakage Defect

In multi-pass satellite telemetry datasets spanning multiple weeks, the same industrial refinery, flare stack, or petrochemical complex (e.g. Vadodara Refinery, Jamnagar Industrial Complex) produces repeated thermal anomaly detections across satellite passes:

- If train/test splitting is performed purely at the individual detection level, multiple observations of the **exact same facility** appear in both training and test sets.
- Even if splitting is performed at the 24-hour physical event cluster level, observations of the **same refinery across different days** can still leak between train and test sets.
- This leads to artificial metric inflation because the GBDT model recognizes the specific spatial coordinates and baseline FRP of a facility it saw during training.

---

## 2. `FacilityGroupSplitter` Algorithm

To guarantee zero facility-level correlation leakage:

1. **Facility Group Assignment:**
   - Observations within $\le 3,000\text{ m}$ of a mapped industrial site are assigned a unique facility group ID (`fac_<nearest_industrial_name>`).
   - Observations not near a mapped industrial site (e.g. wildland fires) are assigned an event cluster ID (`evt_<physical_event_id>`) or spatial cell ID (`cell_<lat_grid>_<lon_grid>`).
2. **Chronological Group Partitioning:**
   - Facility and event groups are sorted chronologically by their earliest satellite detection timestamp.
   - The earliest 80% of facility/event groups form the Training set; the latest 20% form the Test set.
3. **Leakage Guarantee:**
   - $$\text{Train Facilities} \cap \text{Test Facilities} = \emptyset$$
   - Zero satellite observations from the same industrial complex appear across both training and testing splits.
