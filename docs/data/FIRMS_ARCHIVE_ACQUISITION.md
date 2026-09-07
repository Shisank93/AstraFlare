# NASA FIRMS Historical Archive Acquisition Specification & Status

## 1. Overview & Official Source
- **Official Portal**: [NASA FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/)
- **Acquisition Status**: **COMPLETED & REGISTERED**
- **Data Products**: VIIRS S-NPP (375m), VIIRS NOAA-20 (375m), VIIRS NOAA-21 (375m), MODIS Terra/Aqua (1km).
- **Target Spatial Boundary**: India (`Lat: 6.0°N to 37.5°N, Lon: 68.0°E to 97.5°E`) / ISO Country Code `IND`.
- **Target Temporal Window**: `2023-01-01` to `2025-12-31` (3-Year Historical Baseline).

## 2. Acquired Archive File Inventory & Profile

| Download ID | Product / Sensor | Local File Path | Size (MB) | Acquired Records | Date Range | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **799430** | MODIS (M-C61) | `DL_FIRE_M-C61_799430/fire_archive_M-C61_799430.csv` | 18.57 MB | 247,440 | 2023-01-01 to 2025-12-31 | `d4653d2665940323...` |
| **799431** | VIIRS NOAA-20 (J1V-C2) | `DL_FIRE_J1V-C2_799431/fire_archive_J1V-C2_799431.csv` | 139.65 MB | 1,824,761 | 2023-01-01 to 2025-12-31 | `ab14e9a61a42493e...` |
| **799432** | VIIRS NOAA-21 (J2V-C2) | `DL_FIRE_J2V-C2_799432/fire_nrt_J2V-C2_799432.csv` | 90.10 MB | 1,134,538 | 2024-01-17 to 2025-12-31 | `43a83f4ee56cc23a...` |
| **799433** | VIIRS S-NPP (SV-C2) | `DL_FIRE_SV-C2_799433/fire_archive_SV-C2_799433.csv` | 136.10 MB | 1,778,421 | 2023-01-01 to 2025-12-31 | `ed969b40508bde31...` |
| **TOTAL** | **Multi-Sensor Baseline** | `data/raw/firms_archive/` | **384.42 MB** | **4,985,160** | **2023-01-01 to 2025-12-31** | Registered in `data/manifest.json` |

## 3. Provenance & Data Governance Classification
- **Provenance Status**: `SATELLITE_DERIVED_CORROBORATION`
- **Governance Note**: These 4,985,160 real satellite observations provide comprehensive multi-year historical evidence for physical event clustering, temporal recurrence, and spatial pattern analysis across India. They are distinguished from independent external ground-truth incident records (`VERIFIED_EXTERNAL`).
