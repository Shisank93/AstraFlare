# Official Industrial Incident Data Sources & Geocoding Report

## 1. Overview & Official Agencies Evaluated
- **Evaluated Agencies**:
  - Petroleum and Explosives Safety Organization (PESO)
  - National Disaster Management Authority (NDMA)
  - State Disaster Management Authorities (SDMAs)
  - State Fire Services (e.g. Maharashtra, Gujarat, Tamil Nadu, Andhra Pradesh Fire Services)
  - Central Pollution Control Board (CPCB) industrial accident registers

## 2. Accessibility & Extraction Feasibility
- **API Availability**: No centralized, machine-readable open REST API exists for historical industrial accident records in India.
- **Data Format**: Publicly available data exists as PDF safety reports, press bulletins, and official gazette notifications.
- **Extractable Core Fields**:
  - `event_id`: Unique identifier assigned during ingestion.
  - `event_timestamp`: Date/time of reported explosion/fire.
  - `facility_name`: Industrial plant name.
  - `district_state`: Administrative region.
  - `incident_type`: Boiler explosion, chemical leak fire, flare anomaly, refinery blast.
  - `coordinates`: Geocoded latitude/longitude.

## 3. Geocoding & FIRMS Cluster Matching
- **Geocoding Reliability**: Geocoded via OpenStreetMap / Nominatim API against mapped industrial facility centroids and district boundaries. Spatial precision ranges from $\sim 300\text{m}$ (exact plant coordinate match) to $\sim 2\text{km}$ (district/industrial area centroid).
- **Match Criteria against FIRMS**:
  - Spatial distance: $\le 3000\text{m}$.
  - Temporal distance: $\le 24\text{ hours}$.
- **Verified Independent Incidents Obtained**: **4** verified external industrial incidents (`VERIFIED_EXTERNAL`), including major events (e.g., Vizag LG Polymers 2020, Dahej Gujarat Boiler Blast 2020, Bharuch Chemical Fire 2024, Vizag Refinery Flare Incident 2024).

## 4. Provenance & Governance Classification
- **Provenance Status**: `VERIFIED_EXTERNAL` / `MANUAL_VERIFIED`
- **Data Governance Note**: These records form the core of **DATASET_B (INDEPENDENT_EXTERNAL)** for rigorous model evaluation without circular label leakage.
