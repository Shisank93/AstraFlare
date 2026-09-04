#!/usr/bin/env python3
"""
AstraFlare Real-Data Live Smoke Test Script.
Validates PostgreSQL + PostGIS service, verifies NASA FIRMS credentials, queries data availability,
fetches a small real dataset, parses/validates records, inserts into PostGIS (data_source = 'REAL'),
and executes a GIS enrichment query.

Strict Rules:
- Never exposes secrets or prints authenticated URLs containing MAP_KEY.
- Never falls back to SQLite during real smoke test (PostgreSQL + PostGIS required).
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from database.db import db_manager
from data_pipeline.firms_ingestion import FIRMSIngestionClient
from data_pipeline.feature_pipeline import feature_pipeline

def run_live_smoke_test():
    print("=" * 50)
    print("ASTRAFLARE REAL-DATA SMOKE TEST")
    print("=" * 50)

    postgres_pass = False
    postgis_pass = False
    cred_status = "UNKNOWN"
    availability_status = "UNKNOWN"
    selected_sensor = settings.NASA_FIRMS_DEFAULT_SOURCE or "VIIRS_SNPP_NRT"
    test_scope = "Small Regional Area (Gujarat 70,20,75,25)"
    test_days = 1
    
    api_request_pass = False
    records_received = 0
    records_validated = 0
    records_rejected = 0
    postgis_insert_pass = False
    records_inserted = 0
    gis_nearest_pass = False
    gis_hist_pass = False

    # 1. PostgreSQL & PostGIS Check
    db_manager.connect()
    if not db_manager.is_postgres:
        print("\nPostgreSQL Check: FAIL (PostgreSQL is not running on target port/host)")
        print("Reason: Live smoke test requires active PostgreSQL + PostGIS instance.")
        print("Start service with: brew services start postgresql OR docker-compose up -d database")
        print("\nOVERALL RESULT: BLOCKED (PostgreSQL Service Inactive)")
        print("=" * 50)
        return

    postgres_pass = True
    try:
        ver = db_manager.execute_query("SELECT PostGIS_Version();")
        if ver:
            postgis_pass = True
    except Exception as e:
        postgis_pass = False

    # 2. FIRMS Credential Validation
    client = FIRMSIngestionClient()
    is_valid_key, cred_msg = client.validate_credentials(source=selected_sensor)
    cred_status = cred_msg

    if not is_valid_key:
        print(f"\nFIRMS Credential Validation: FAIL ({cred_msg})")
        print("\nOVERALL RESULT: BLOCKED (Invalid or Rejected NASA FIRMS MAP_KEY)")
        print("=" * 50)
        return

    # 3. Data Availability Check
    is_avail, avail_msg = client.check_data_availability(source=selected_sensor)
    availability_status = avail_msg

    # 4. Request Small Real Dataset (Targeted Area Bounding Box)
    try:
        csv_data = client.fetch_firms_area_csv(extent="70,20,75,25", source=selected_sensor, days=test_days)
        api_request_pass = True
        
        lines = csv_data.splitlines()
        records_received = max(0, len(lines) - 1)
        
        # Parse and Validate Records
        res = client.ingest_firms_data(extent="70,20,75,25", source=selected_sensor, days=test_days, mock_fallback=False)
        records_validated = res["inserted"]
        records_rejected = res["rejected"]
        records_inserted = res["inserted"]
        postgis_insert_pass = True

    except Exception as e:
        api_request_pass = False
        print(f"\nAPI Request Error: {client.redact_key(str(e))}")

    # 5. Run GIS Enrichment Verification
    if postgis_insert_pass and records_inserted > 0:
        try:
            records = db_manager.execute_query("SELECT * FROM hotspots WHERE data_source = 'REAL' LIMIT 1;")
            if records:
                sample_hs = records[0]
                enriched = feature_pipeline.enrich_hotspot(sample_hs, mock_fallback=False)
                if enriched.get("industrial_distance") is not None:
                    gis_nearest_pass = True
                if enriched.get("frp_anomaly_status") is not None:
                    gis_hist_pass = True
        except Exception as e:
            print(f"GIS enrichment error: {client.redact_key(str(e))}")

    # 6. Output Standardized Summary
    overall = "PASS" if (postgres_pass and postgis_pass and is_valid_key and api_request_pass and postgis_insert_pass) else "BLOCKED"

    print(f"\nPostgreSQL: {'PASS' if postgres_pass else 'FAIL'}")
    print(f"PostGIS: {'PASS' if postgis_pass else 'FAIL'}")
    print(f"\nFIRMS credential status: {cred_status}")
    print(f"FIRMS data availability: {availability_status}")
    print(f"\nSensor: {selected_sensor}")
    print(f"Scope: {test_scope}")
    print(f"Days: {test_days}")
    print(f"\nAPI request: {'PASS' if api_request_pass else 'FAIL'}")
    print(f"Records received: {records_received}")
    print(f"Records validated: {records_validated}")
    print(f"Records rejected: {records_rejected}")
    print(f"\nPostGIS insertion: {'PASS' if postgis_insert_pass else 'FAIL'}")
    print(f"Records inserted: {records_inserted}")
    print(f"\nGIS enrichment:")
    print(f"Nearest industrial query: {'PASS' if gis_nearest_pass else 'FAIL'}")
    print(f"Historical query: {'PASS' if gis_hist_pass else 'FAIL'}")
    print(f"\nData source: REAL")
    print(f"\nOVERALL RESULT: {overall}")
    print("=" * 50)

    if overall == "PASS":
        print("\nASTRAFLARE REAL-DATA SMOKE TEST PASSED")
    else:
        print("\nASTRAFLARE REAL-DATA SMOKE TEST BLOCKED")

if __name__ == "__main__":
    run_live_smoke_test()
