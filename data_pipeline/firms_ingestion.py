"""
AstraFlare NASA FIRMS Data Ingestion Service.
Fetches, normalizes, validates, and idempotently persists active satellite thermal anomalies.
Supports both MAP_KEY REST API endpoints and NASA FIRMS 24h Public Real-Data Feeds.
Includes secret redaction to ensure MAP_KEY credentials are never logged or exposed.
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

# NASA FIRMS 24h Public Real-Data CSV Feeds (South Asia Region including India)
FIRMS_PUBLIC_FEEDS = {
    "VIIRS_SNPP_NRT": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_Asia_24h.csv",
    "VIIRS_NOAA20_NRT": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_Asia_24h.csv",
    "MODIS_NRT": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_South_Asia_24h.csv"
}

class FIRMSIngestionClient:
    def __init__(self, map_key: Optional[str] = None):
        self.map_key = map_key if map_key is not None else settings.NASA_FIRMS_MAP_KEY
        self.base_url = "https://firms.modaps.eosdis.nasa.gov/api"

    def redact_key(self, text: str) -> str:
        """Sanitizes text by replacing actual MAP_KEY values with [REDACTED_KEY]."""
        if self.map_key and len(self.map_key) > 5:
            return text.replace(self.map_key, "[REDACTED_KEY]")
        return text

    def validate_credentials(self, source: str = "VIIRS_SNPP_NRT") -> Tuple[bool, str]:
        """
        Tests whether configured MAP_KEY or Public Real-Data Feed is operational without exposing credentials.
        Returns (is_valid, status_message).
        """
        if not self.map_key:
            return False, "MAP_KEY is missing."
        if self.map_key == "YOUR_NASA_FIRMS_MAP_KEY_HERE":
            return False, "MAP_KEY is placeholder."

        headers = {"User-Agent": "Mozilla/5.0 (AstraFlare Real-Data Ingestion Pipeline)"}
        url = f"{self.base_url}/country/csv/{self.map_key}/{source}/IND/1"
        try:
            with httpx.Client(timeout=30.0, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return True, "VALID (NASA FIRMS API Key)"
                elif resp.status_code in (400, 403):
                    # Key is unactivated or rejected; fallback to public feed
                    pub_url = FIRMS_PUBLIC_FEEDS.get(source, FIRMS_PUBLIC_FEEDS["VIIRS_SNPP_NRT"])
                    pub_resp = httpx.get(pub_url, timeout=30.0, headers=headers, follow_redirects=True)
                    if pub_resp.status_code == 200:
                        return True, f"VALID (Fallback to NASA FIRMS Public Real-Data Feed: HTTP 200 OK)"
        except Exception as e:
            pass

        # Check public feed directly
        pub_url = FIRMS_PUBLIC_FEEDS.get(source, FIRMS_PUBLIC_FEEDS["VIIRS_SNPP_NRT"])
        try:
            with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(pub_url)
                if resp.status_code == 200:
                    return True, "VALID (NASA FIRMS Public Real-Data Feed)"
        except Exception as e:
            return False, f"Network Error: {self.redact_key(str(e))}"

        return False, "MAP_KEY is invalid/unactivated and Public Feed is unreachable."

    def check_data_availability(self, source: str = "VIIRS_SNPP_NRT") -> Tuple[bool, str]:
        """Queries FIRMS data availability."""
        pub_url = FIRMS_PUBLIC_FEEDS.get(source, FIRMS_PUBLIC_FEEDS["VIIRS_SNPP_NRT"])
        headers = {"User-Agent": "Mozilla/5.0 (AstraFlare Real-Data Ingestion Pipeline)"}
        try:
            with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(pub_url)
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    count = len(lines) - 1 if len(lines) > 1 else 0
                    return True, f"PASS ({count} real satellite thermal observations available in 24h feed)"
        except Exception as e:
            pass
        return False, "Data availability check failed."

    def fetch_public_real_csv(self, source: str = "VIIRS_SNPP_NRT") -> str:
        """Fetches live 24h real satellite thermal observations from NASA FIRMS Public Feed."""
        pub_url = FIRMS_PUBLIC_FEEDS.get(source, FIRMS_PUBLIC_FEEDS["VIIRS_SNPP_NRT"])
        logger.info(f"Polling NASA FIRMS Public Real-Data Feed: {pub_url}")
        headers = {"User-Agent": "Mozilla/5.0 (AstraFlare Real-Data Ingestion Pipeline)"}
        
        with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
            resp = client.get(pub_url)
            resp.raise_for_status()
            return resp.text

    def fetch_firms_area_csv(
        self, extent: str = "70,20,75,25", source: str = "VIIRS_SNPP_NRT", days: int = 1
    ) -> str:
        """Fetches raw CSV from NASA FIRMS API or Public Feed fallback."""
        headers = {"User-Agent": "Mozilla/5.0 (AstraFlare Real-Data Ingestion Pipeline)"}
        if self.map_key and self.map_key != "YOUR_NASA_FIRMS_MAP_KEY_HERE":
            url = f"{self.base_url}/area/csv/{self.map_key}/{source}/{extent}/{days}"
            try:
                with httpx.Client(timeout=30.0, headers=headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        return resp.text
            except Exception:
                pass

        # Fallback to Public Real-Data Feed
        return self.fetch_public_real_csv(source)

    def fetch_firms_country_csv(
        self, country: str = "IND", source: str = "VIIRS_SNPP_NRT", days: int = 1
    ) -> str:
        """Fetches raw CSV from NASA FIRMS Country endpoint or Public Feed fallback."""
        if self.map_key and self.map_key != "YOUR_NASA_FIRMS_MAP_KEY_HERE":
            url = f"{self.base_url}/country/csv/{self.map_key}/{source}/{country}/{days}"
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        return resp.text
            except Exception:
                pass

        # Fallback to Public Real-Data Feed
        return self.fetch_public_real_csv(source)

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
        self, country: str = "IND", extent: Optional[str] = None, source: str = "VIIRS_SNPP_NRT", days: int = 1, mock_fallback: bool = False, data_source_tag: str = "REAL"
    ) -> Dict[str, Any]:
        """Runs end-to-end FIRMS fetch, validation, normalization, and idempotent database insertion."""
        db_manager.connect()
        # Override if mock_fallback
        if mock_fallback:
            data_source_tag = "MOCK"

        csv_content = None
        if not mock_fallback:
            try:
                if extent:
                    csv_content = self.fetch_firms_area_csv(extent, source, days)
                else:
                    csv_content = self.fetch_firms_country_csv(country, source, days)
            except Exception as e:
                clean_err = self.redact_key(str(e))
                logger.error(f"Real FIRMS ingestion failed: {clean_err}")
                raise RuntimeError(clean_err)

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

        return self._parse_and_store_firms_csv(csv_content, data_source_tag=data_source_tag, mock_fallback=mock_fallback)

    def _parse_and_store_firms_csv(self, csv_content: str, data_source_tag: str = "REAL", mock_fallback: bool = False) -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_content))
        inserted, duplicates, rejected = 0, 0, 0

        db_manager.connect()

        for row in reader:
            record = self.parse_and_normalize_row(row, data_source_tag=data_source_tag)
            if not record:
                rejected += 1
                continue

            if db_manager.is_postgres and db_manager._pg_conn:
                query = """
                INSERT INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """
                with db_manager._pg_conn.cursor() as cur:
                    cur.execute(query, (
                        record["id"], record["firms_id"], record["latitude"], record["longitude"], record["geom"],
                        record["acq_timestamp"], record["satellite"], record["instrument"], record["brightness"],
                        record["frp"], record["confidence"], record["daynight"], record["data_source"]
                    ))
                    if cur.rowcount > 0:
                        inserted += 1
                    else:
                        duplicates += 1
            else:
                query = """
                INSERT OR IGNORE INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                assert db_manager._sqlite_conn is not None
                cur = db_manager._sqlite_conn.cursor()
                cur.execute(query, (
                    record["id"], record["firms_id"], record["latitude"], record["longitude"], record["geom"],
                    record["acq_timestamp"], record["satellite"], record["instrument"], record["brightness"],
                    record["frp"], record["confidence"], record["daynight"], record["data_source"]
                ))
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    duplicates += 1
                db_manager._sqlite_conn.commit()

        logger.info(f"FIRMS Ingestion Completed: {inserted} inserted, {duplicates} duplicates, {rejected} rejected, Tag: {data_source_tag}")
        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "rejected": rejected,
            "data_source": data_source_tag,
            "status": "SUCCESS"
        }

if __name__ == "__main__":
    print("Executing FIRMS Ingestion CLI (Mock Mode)...")
    client = FIRMSIngestionClient()
    res = client.ingest_firms_data(mock_fallback=True)
    print(f"Ingestion Result: {res}")
