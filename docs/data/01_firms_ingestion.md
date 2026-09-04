# NASA FIRMS Data Ingestion Specification

**Project:** AstraFlare  
**Document:** NASA FIRMS API Integration, Normalization & Idempotent Ingestion  

---

## 1. NASA FIRMS API Details

- **API Endpoint:** `https://firms.modaps.eosdis.nasa.gov/api/country/csv/{MAP_KEY}/{source}/{country}/{days}`
- **Supported Sources:**
  - `VIIRS_SNPP_NRT` (VIIRS S-NPP Near Real-Time, 375m spatial resolution)
  - `VIIRS_NOAA20_NRT` (VIIRS NOAA-20 Near Real-Time, 375m spatial resolution)
  - `MODIS_NRT` (MODIS Terra/Aqua Near Real-Time, 1km spatial resolution)
- **Authentication:** `MAP_KEY` query parameter / URL path token obtained from `https://firms.modaps.eosdis.nasa.gov/api/map_key/`.
- **Response Format:** CSV string stream.
- **Key CSV Schema Fields:**
  - `latitude`: Geographic latitude (WGS84)
  - `longitude`: Geographic longitude (WGS84)
  - `bright_ti4` / `brightness`: Brightness temperature (Kelvin)
  - `scan`, `track`: Pixel dimensions
  - `acq_date`: Acquisition date (`YYYY-MM-DD`)
  - `acq_time`: Acquisition UTC time (`HHMM`)
  - `satellite`: Satellite indicator (`N`=NOAA-20, `S`=S-NPP, `T`=Terra, `A`=Aqua)
  - `instrument`: Sensing instrument (`VIIRS` / `MODIS`)
  - `confidence`: Detection confidence (`l`=low, `n`=nominal, `h`=high or percentage 0-100)
  - `frp`: Fire Radiative Power (Megawatts)
  - `daynight`: `D`=Day, `N`=Night

---

## 2. Idempotent Ingestion & Fingerprinting

To prevent duplicate record creation during repeated polling:
1. **Observation Fingerprint:**
   $$\text{fingerprint} = \text{sha256}(\text{satellite} + "|" + \text{acq\_date} + "|" + \text{acq\_time} + "|" + \text{round}(\text{lat}, 4) + "|" + \text{round}(\text{lon}, 4))$$
2. **Database Ingestion Strategy:**
   `INSERT INTO hotspots (...) VALUES (...) ON CONFLICT (id) DO NOTHING;`

---

## 3. Data Governance Tags

- `REAL`: Observations ingested directly from official NASA FIRMS API.
- `MOCK`: Generated fallback observations when mock ingestion mode is explicitly requested.
- `SYNTHETIC_DEMO`: Workaround scenario demonstration records.
