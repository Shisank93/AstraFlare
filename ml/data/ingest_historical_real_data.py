#!/usr/bin/env python3
"""
AstraFlare Real Historical FIRMS Data Ingestion Engine.
Fetches, validates, and ingests multi-sensor 7-day real satellite active fire telemetry
into PostgreSQL/SQLite database with strict 'REAL' data governance tags.
"""
import os
import sys
import logging
from typing import Dict, Any

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database.db import db_manager
from data_pipeline.firms_ingestion import FIRMSIngestionClient

logger = logging.getLogger("astraflare.ml.ingestion")

FEEDS_7D = {
    "VIIRS_SNPP_7D": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-viirs-c2/csv/SUOMI_VIIRS_C2_South_Asia_7d.csv",
    "VIIRS_NOAA20_7D": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_Asia_7d.csv",
    "MODIS_7D": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_South_Asia_7d.csv"
}

def ingest_7day_real_firms_data() -> Dict[str, Any]:
    """
    Ingests 7-day real satellite thermal observations from NASA FIRMS feeds.
    Strict Rule: Only populates records with data_source = 'REAL'.
    """
    print("=" * 60)
    print("ASTRAFLARE HISTORICAL REAL FIRMS DATA INGESTION")
    print("=" * 60)

    db_manager.connect()
    client = FIRMSIngestionClient()
    
    total_received = 0
    total_inserted = 0
    total_rejected = 0
    sensor_stats = {}

    for sensor_key, feed_url in FEEDS_7D.items():
        print(f"\nPolling {sensor_key} 7-Day Feed: {feed_url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (AstraFlare Real-Data Ingestion Pipeline)"}
            import httpx
            with httpx.Client(timeout=35.0, headers=headers, follow_redirects=True) as http_client:
                resp = http_client.get(feed_url)
                resp.raise_for_status()
                csv_content = resp.text

            res = client._parse_and_store_firms_csv(csv_content, mock_fallback=False)
            cnt_received = max(0, len(csv_content.splitlines()) - 1)
            cnt_inserted = res.get("inserted", 0)
            cnt_rejected = res.get("rejected", 0) + res.get("duplicates", 0)

            total_received += cnt_received
            total_inserted += cnt_inserted
            total_rejected += cnt_rejected
            sensor_stats[sensor_key] = {"received": cnt_received, "inserted": cnt_inserted, "rejected": cnt_rejected}

            print(f"-> Received: {cnt_received} | Inserted: {cnt_inserted} | Rejected/Duplicates: {cnt_rejected}")
        except Exception as e:
            logger.error(f"Error fetching 7d feed {sensor_key}: {e}")
            print(f"Error fetching 7d feed {sensor_key}: {e}")

    # Query total REAL hotspots count in DB
    real_records = db_manager.execute_query("SELECT COUNT(*) as cnt FROM hotspots WHERE data_source = 'REAL';")
    total_db_real = real_records[0]["cnt"] if real_records else 0

    print("\n" + "=" * 60)
    print(f"INGESTION SUMMARY:")
    print(f"Total Raw Records Received: {total_received}")
    print(f"New Unique Records Inserted: {total_inserted}")
    print(f"Duplicates / Rejected: {total_rejected}")
    print(f"Total REAL Records in Database: {total_db_real}")
    print("=" * 60)

    return {
        "total_received": total_received,
        "total_inserted": total_inserted,
        "total_rejected": total_rejected,
        "total_db_real": total_db_real,
        "sensor_stats": sensor_stats
    }

if __name__ == "__main__":
    ingest_7day_real_firms_data()
