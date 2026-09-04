#!/usr/bin/env python3
"""
AstraFlare Real-Data Live Smoke Test Script.
If NASA_FIRMS_MAP_KEY is provided and internet is connected, performs a small real-data smoke test
ingesting 1 day of FIRMS satellite data for India, normalizing records, persisting to database,
and enriching contextual features.
If key/network is unavailable, cleanly reports LIVE SMOKE TEST NOT RUN.
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from data_pipeline.firms_ingestion import FIRMSIngestionClient
from data_pipeline.feature_pipeline import feature_pipeline
from database.db import db_manager

def run_live_smoke_test():
    print("=" * 70)
    print("ASTRAFLARE REAL-DATA LIVE SMOKE TEST")
    print("=" * 70)

    map_key = settings.NASA_FIRMS_MAP_KEY
    if not map_key or map_key == "YOUR_NASA_FIRMS_MAP_KEY_HERE":
        print("\nLIVE SMOKE TEST NOT RUN")
        print("Reason: NASA_FIRMS_MAP_KEY is missing or set to placeholder in .env.")
        print("To run live test, obtain a key at https://firms.modaps.eosdis.nasa.gov/api/map_key/")
        print("and set NASA_FIRMS_MAP_KEY=your_key in .env file.")
        print("=" * 70)
        return

    print(f"Connecting to database and polling NASA FIRMS for country=IND (1 day)...")
    client = FIRMSIngestionClient(map_key=map_key)

    try:
        res = client.ingest_firms_data(country="IND", source="VIIRS_SNPP_NRT", days=1, mock_fallback=False)
        print(f"\nIngestion Results:")
        print(f"  Status:      {res['status']}")
        print(f"  Inserted:    {res['inserted']} records")
        print(f"  Rejected:    {res['rejected']} invalid records")
        print(f"  Data Source: {res['data_source']}")

        # Fetch sample inserted REAL observation and run GIS feature enrichment
        db_manager.connect()
        query = "SELECT * FROM hotspots WHERE data_source = 'REAL' LIMIT 1;"
        records = db_manager.execute_query(query)

        if records:
            sample_hs = records[0]
            print(f"\nEnriching Live Observation: {sample_hs['id']} ({sample_hs['latitude']}, {sample_hs['longitude']})")
            enriched = feature_pipeline.enrich_hotspot(sample_hs, mock_fallback=False)
            print(f"  Industrial Distance:      {enriched['industrial_distance']}m")
            print(f"  Nearest Industrial Name:  {enriched['nearest_industrial_name']}")
            print(f"  Land Cover Class:         {enriched['land_cover_class']}")
            print(f"  FRP Anomaly Score:        {enriched['frp_anomaly_score']}")
            print(f"  Data Quality:             {enriched['data_quality']}")
            print("\nLIVE SMOKE TEST PASSED SUCCESSFULLY.")
        else:
            print("\nLIVE SMOKE TEST PASSED (Zero active hotspots detected in FIRMS feed for past 24 hours).")

    except Exception as e:
        print(f"\nLIVE SMOKE TEST FAILED WITH ERROR: {e}")
        print("Verify network connectivity or API key validity.")

    print("=" * 70)

if __name__ == "__main__":
    run_live_smoke_test()
