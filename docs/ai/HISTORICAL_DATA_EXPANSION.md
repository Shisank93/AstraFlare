# AstraFlare Historical Data Expansion & Acquisition Audit

## 1. Overview
This document logs the historical data acquisition, temporal window verification, idempotency testing, and ingestion governance for AstraFlare Phase 3.5.

## 2. Ingestion Baseline & Data Sources
- **Primary Data Sources**: NASA FIRMS NRT & Historical Feeds (Suomi-VIIRS C2, NOAA-20 VIIRS C2, MODIS C6.1).
- **Geographic Scope**: South Asia region ($5^{\circ}\text{N} \le \text{Lat} \le 37^{\circ}\text{N}$, $60^{\circ}\text{E} \le \text{Lon} \le 98^{\circ}\text{E}$).
- **Governance Tag**: `data_source = 'REAL'` exclusively. Zero synthetic/demo data allowed.

## 3. Ingestion Engine Architecture
- **Script**: `ml/data/ingest_historical_real_data.py`
- **Client**: `data_pipeline/firms_ingestion.py`
- **Deduplication Method**: SHA-256 fingerprint generated from `(satellite, acq_date, acq_time, lat, lon)`.
- **Database Handling**: PostgreSQL `ON CONFLICT (id) DO NOTHING` / SQLite `INSERT OR IGNORE`.

## 4. Empirical Verification & Idempotency
- **Baseline Record Count**: 8,786 REAL observations
- **Date Range**: 2026-08-28T07:22:00Z to 2026-09-04T15:54:00Z (7-day South Asia window)
- **Idempotency Execution**:
  - Run 1 (Initial Ingestion): 8,786 inserted, 0 duplicates.
  - Run 2 (Re-execution over identical feeds): 0 inserted, 8,786 duplicates rejected.
  - **Duplicate Count Added**: 0 (PASS).

## 5. Daily Telemetry Coverage
| Date | REAL Observations | Physical Events | Active Industrial Facilities |
| :--- | :--- | :--- | :--- |
| 2026-08-28 | 293 | 183 | 8 |
| 2026-08-29 | 949 | 433 | 9 |
| 2026-08-30 | 1,053 | 455 | 8 |
| 2026-08-31 | 1,066 | 492 | 5 |
| 2026-09-01 | 1,534 | 762 | 10 |
| 2026-09-02 | 1,149 | 581 | 10 |
| 2026-09-03 | 1,179 | 571 | 9 |
| 2026-09-04 | 1,563 | 731 | 7 |

## 6. Historical Feature Window Safeguards
- **Rolling Window Formulation**: For target observation at timestamp $t$, historical 30-day feature (`historical_count_30d`) evaluates $t - 30\text{d} < t_{\text{hist}} < t$.
- **Target Exclusion**: The target observation ID (`exclude_hotspot_id`) is explicitly omitted from baseline statistics to avoid circular feature leakage.
