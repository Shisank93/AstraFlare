"""
AstraFlare NASA FIRMS Data Ingestion Service.
Fetches, normalizes, validates, and idempotently persists active satellite thermal anomalies.
"""
import os
import sys
import csv
import io
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import httpx

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from database.db import db_manager
from data_pipeline.gis_engine import validate_coordinates, validate_frp, parse_iso_timestamp

logger = logging.getLogger("astraflare.firms")

class FIRMSIngestionClient:
    def __init__(self, map_key: Optional[str] = None):
        self.map_key = map_key or settings.NASA_FIRMS_MAP_KEY
        self.base_url = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"

    def fetch_firms_csv(
        self, country: str = "IND", source: str = "VIIRS_SNPP_NRT", days: int = 1
    ) -> str:
        """Fetches raw CSV string from NASA FIRMS API with retry logic."""
        if not self.map_key:
            raise ValueError(
                "NASA_FIRMS_MAP_KEY is missing from environment. "
                "Obtain a key at https://firms.modaps.eosdis.nasa.gov/api/map_key/ and set in .env."
            )

        url = f"{self.base_url}/{self.map_key}/{source}/{country}/{days}"
        logger.info(f"Polling NASA FIRMS API endpoint: {url.replace(self.map_key, 'MAP_KEY_REDACTED')}")

        retries = 3
        backoff = 2.0
        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    return resp.text
            except Exception as e:
                logger.warning(f"FIRMS API request failed (attempt {attempt}/{retries}): {e}")
                if attempt == retries:
                    raise RuntimeError(f"NASA FIRMS API request failed after {retries} retries: {e}")

        raise RuntimeError("NASA FIRMS API fetch failed.")

    @staticmethod
    def generate_hotspot_id(satellite: str, acq_date: str, acq_time: str, lat: float, lon: float) -> str:
        """Generates deterministic SHA-256 fingerprint for idempotent hotspot insertion."""
        raw_key = f"{satellite}|{acq_date}|{acq_time}|{lat:.4f}|{lon:.4f}"
        return f"firms_{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16]}"

    def parse_and_normalize_row(
        self, row: Dict[str, str], data_source_tag: str = "REAL"
    ) -> Optional[Dict[str, Any]]:
        """Parses raw FIRMS CSV row into normalized AstraFlare hotspot record."""
        try:
            latitude = float(row.get("latitude", "nan"))
            longitude = float(row.get("longitude", "nan"))
            frp = float(row.get("frp", "0.0"))
            brightness = float(row.get("bright_ti4") or row.get("brightness") or "0.0")

            # Validate Coordinates & FRP
            valid_coords, err_c = validate_coordinates(latitude, longitude)
            if not valid_coords:
                logger.warning(f"Rejected invalid FIRMS coordinate row: {err_c}")
                return None

            valid_frp, err_f = validate_frp(frp)
            if not valid_frp:
                logger.warning(f"Rejected invalid FIRMS FRP row: {err_f}")
                return None

            acq_date = row.get("acq_date", "2026-01-01")
            acq_time = row.get("acq_time", "0000").zfill(4)
            time_str = f"{acq_time[:2]}:{acq_time[2:]}:00"
            iso_time = f"{acq_date}T{time_str}Z"
            acq_timestamp = parse_iso_timestamp(iso_time).isoformat()

            satellite = row.get("satellite", "VIIRS")
            instrument = row.get("instrument", "VIIRS")
            confidence = row.get("confidence", "nominal")
            daynight = row.get("daynight", "D")

            hotspot_id = self.generate_hotspot_id(satellite, acq_date, acq_time, latitude, longitude)
            geom_wkt = f"POINT({longitude} {latitude})"

            return {
                "id": hotspot_id,
                "firms_id": row.get("firms_id") or hotspot_id,
                "latitude": latitude,
                "longitude": longitude,
                "geom": geom_wkt,
                "acq_timestamp": acq_timestamp,
                "satellite": satellite,
                "instrument": instrument,
                "brightness": brightness,
                "frp": frp,
                "confidence": confidence,
                "daynight": daynight,
                "data_source": data_source_tag
            }
        except Exception as e:
            logger.warning(f"Failed to parse FIRMS CSV row: {e}")
            return None

    def ingest_firms_data(
        self, country: str = "IND", source: str = "VIIRS_SNPP_NRT", days: int = 1, mock_fallback: bool = False
    ) -> Dict[str, Any]:
        """Runs end-to-end FIRMS fetch, validation, normalization, and idempotent PostGIS insertion."""
        db_manager.connect()
        data_source_tag = settings.DATA_SOURCE_REAL

        csv_content = None
        if not mock_fallback and self.map_key:
            try:
                csv_content = self.fetch_firms_csv(country, source, days)
            except Exception as e:
                logger.error(f"Real FIRMS ingestion failed: {e}")
                raise

        if not csv_content and mock_fallback:
            logger.info("Explicit Mock Fallback requested; generating MOCK FIRMS observations.")
            data_source_tag = "MOCK"
            csv_content = (
                "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
                "22.3088,73.1825,365.2,0.4,0.4,2026-09-04,1415,N20,VIIRS,h,1.0,298.0,145.0,N\n"
                "22.4715,70.0583,332.0,0.4,0.4,2026-09-04,1230,N20,VIIRS,n,1.0,295.0,42.0,D\n"
                "30.4500,78.8500,342.1,0.5,0.5,2026-09-04,0910,T,MODIS,h,1.0,300.0,85.0,D\n"
            )

        if not csv_content:
            return {"inserted": 0, "duplicates": 0, "rejected": 0, "status": "FAILED", "reason": "No CSV data retrieved."}

        reader = csv.DictReader(io.StringIO(csv_content))
        inserted, duplicates, rejected = 0, 0, 0

        for row in reader:
            record = self.parse_and_normalize_row(row, data_source_tag=data_source_tag)
            if not record:
                rejected += 1
                continue

            # Idempotent Database Persistence
            if db_manager.is_postgres:
                query = """
                INSERT INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326), %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """
                res = db_manager.execute_query(query, (
                    record["id"], record["firms_id"], record["latitude"], record["longitude"], record["geom"],
                    record["acq_timestamp"], record["satellite"], record["instrument"], record["brightness"],
                    record["frp"], record["confidence"], record["daynight"], record["data_source"]
                ))
            else:
                query = """
                INSERT OR IGNORE INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                res = db_manager.execute_query(query, (
                    record["id"], record["firms_id"], record["latitude"], record["longitude"], record["geom"],
                    record["acq_timestamp"], record["satellite"], record["instrument"], record["brightness"],
                    record["frp"], record["confidence"], record["daynight"], record["data_source"]
                ))
            
            inserted += 1

        logger.info(f"FIRMS Ingestion Completed: {inserted} processed, {rejected} rejected, Tag: {data_source_tag}")
        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "rejected": rejected,
            "data_source": data_source_tag,
            "status": "SUCCESS"
        }

if __name__ == "__main__":
    print("Executing FIRMS Ingestion CLI...")
    client = FIRMSIngestionClient()
    try:
        res = client.ingest_firms_data(mock_fallback=True)
        print(f"Ingestion Result: {res}")
    except Exception as err:
        print(f"Ingestion Error: {err}")
