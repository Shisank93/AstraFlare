# AstraFlare Event Diversity Audit & Label Integrity

## 1. Physical Event vs Observation Separation
A critical requirement in satellite thermal anomaly ML is distinguishing raw observation count from physical event diversity.

- **Total REAL Observations**: 8,786
- **Unique Physical Event Clusters**: 3,180
- **Average Observations / Event**: 2.76
- **Median Observations / Event**: 2.0
- **Maximum Observations / Event**: 41

> **Crucial Rule**: 41 observations originating from a single Garhwal forest fire represent **1 physical event**, NOT 41 independent training examples.

## 2. Event Breakdown by Class

| Category | Physical Events | REAL Observations | Evidence Source |
| :--- | :--- | :--- | :--- |
| **Industrial Incident** | 2 external / 7 weak | 54 observations | PESO & NDMA Incident Registries |
| **Natural Wildland Fire** | 4 external / 50 weak | 70 observations | NASA FIRMS Event Catalog & GFW |
| **Persistent Industrial Heat** | 11 facility clusters | 150 observations | OSM Industrial Complex Co-location |
| **Unlabeled Anomalies** | 3,121 physical events | 8,512 observations | Unassigned satellite observations |

## 3. Sample Support & Statistically Limited Status
Because verified independent ground-truth events remain limited (6 total events), model evaluation against independent external data must be flagged as **STATISTICALLY LIMITED**.

No synthetic data, duplicate records, or oversampling may be used to artificially inflate event diversity.
