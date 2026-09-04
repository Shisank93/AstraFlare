# NASA FIRMS Data Ingestion Specification

**Project:** AstraFlare  
**Document:** NASA FIRMS API Contract, Secret Redaction, Normalization & Idempotent Ingestion  

---

## 1. Verified NASA FIRMS API Contract Details

- **Base Endpoint:** `https://firms.modaps.eosdis.nasa.gov/api`
- **Authentication:** `MAP_KEY` 32-character transaction token issued via email from `https://firms.modaps.eosdis.nasa.gov/api/map_key/`.
- **Secret Redaction Policy:** The `MAP_KEY` parameter is treated as a sensitive secret. Ingestion services, loggers, and exception outputs must redact the key (e.g. `[REDACTED_KEY]`) and never log authenticated URLs.

---

## 2. API Endpoints Reference

### 2.1 Area Query Endpoint
- **URL Structure:** `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{source}/{extent}/{days}`
- **Extent Format:** `west,south,east,north` (Bounding box coordinates in WGS84, e.g., `70,20,75,25` for Western India).
- **Days:** Integer `1` to `10`.

### 2.2 Country Query Endpoint
- **URL Structure:** `https://firms.modaps.eosdis.nasa.gov/api/country/csv/{MAP_KEY}/{source}/{country}/{days}`
- **Country Code:** 3-letter ISO code (e.g., `IND` for India).

### 2.3 Data Availability Endpoint
- **URL Structure:** `https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/{source}`
- **Returns:** CSV list of dates with available satellite observations.

---

## 3. Supported Sensor Identifiers

1. `VIIRS_SNPP_NRT`: VIIRS Suomi-NPP (375m spatial resolution, Near Real-Time)
2. `VIIRS_NOAA20_NRT`: VIIRS NOAA-20 (375m spatial resolution, Near Real-Time)
3. `VIIRS_NOAA21_NRT`: VIIRS NOAA-21 (375m spatial resolution, Near Real-Time)
4. `MODIS_NRT`: MODIS Terra & Aqua (1km spatial resolution, Near Real-Time)

---

## 4. Idempotent PostGIS Persistence

- **Fingerprint Calculation:**
  $$\text{id} = \text{"firms\_"} + \text{sha256}(\text{satellite} + "|" + \text{acq\_date} + "|" + \text{acq\_time} + "|" + \text{round}(\text{lat}, 4) + "|" + \text{round}(\text{lon}, 4))[:16]$$
- **Idempotency Rule:** `INSERT INTO hotspots (...) VALUES (...) ON CONFLICT (id) DO NOTHING;`

---

## 5. Error & Gateway Diagnostics

- **HTTP 403 Forbidden ("Request not allowed by policy"):** Occurs when `MAP_KEY` is invalid, unconfirmed, mistyped, or rejected by NASA API gateway policy.
- **HTTP 400 Bad Request:** Occurs when parameter syntax (extent bounding box format or country code) is invalid.
