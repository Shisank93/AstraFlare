import os
import sys
import glob
import logging
import pandas as pd
import psycopg2
import psycopg2.extras
import hashlib
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import db_manager

logger = logging.getLogger("astraflare.pipeline.ingest")
logging.basicConfig(level=logging.INFO)

def generate_hotspot_id(satellite: str, acq_date: str, acq_time: str, lat: float, lon: float) -> str:
    """Generates deterministic SHA-256 fingerprint for idempotent hotspot insertion."""
    raw_key = f"{satellite}|{acq_date}|{acq_time}|{lat:.4f}|{lon:.4f}"
    return f"firms_{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:16]}"

def parse_iso_timestamp(acq_date, acq_time):
    acq_time_str = str(acq_time).zfill(4)
    time_str = f"{acq_time_str[:2]}:{acq_time_str[2:]}:00"
    iso_time = f"{acq_date}T{time_str}Z"
    return iso_time

def batch_ingest_firms_archive(data_dir: str = "data/raw/firms_archive", chunk_size: int = 100000):
    db_manager.connect()
    
    if not db_manager.is_postgres or not db_manager._pg_conn:
        raise RuntimeError("PostgreSQL connection required for batch ingestion.")
    
    csv_files = glob.glob(f"{data_dir}/*/*.csv")
    logger.info(f"Found {len(csv_files)} CSV files for ingestion.")
    
    total_inserted = 0
    start_time = time.time()
    
    for f in csv_files:
        logger.info(f"Processing {f}...")
        for chunk in pd.read_csv(f, chunksize=chunk_size):
            # Filter negative FRP
            chunk = chunk[chunk['frp'] > 0]
            
            # Prepare rows for execute_values
            rows_to_insert = []
            for _, row in chunk.iterrows():
                try:
                    lat = float(row['latitude'])
                    lon = float(row['longitude'])
                    frp = float(row['frp'])
                    brightness = float(row.get('bright_ti4') or row.get('brightness', 0.0))
                    
                    acq_date = row['acq_date']
                    acq_time = row['acq_time']
                    acq_timestamp = parse_iso_timestamp(acq_date, acq_time)
                    
                    satellite = str(row.get('satellite', 'VIIRS'))
                    instrument = str(row.get('instrument', 'VIIRS'))
                    confidence = str(row.get('confidence', 'nominal'))
                    daynight = str(row.get('daynight', 'D'))
                    
                    hotspot_id = generate_hotspot_id(satellite, acq_date, acq_time, lat, lon)
                    geom_wkt = f"POINT({lon} {lat})"
                    
                    rows_to_insert.append((
                        hotspot_id, hotspot_id, lat, lon, geom_wkt,
                        acq_timestamp, satellite, instrument, brightness, frp,
                        confidence, daynight, "REAL"
                    ))
                except Exception as e:
                    # Skip malformed rows
                    continue
            
            if rows_to_insert:
                query = """
                INSERT INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
                VALUES %s
                ON CONFLICT (id) DO NOTHING;
                """
                with db_manager._pg_conn.cursor() as cur:
                    psycopg2.extras.execute_values(cur, query, rows_to_insert, page_size=10000)
                
                db_manager._pg_conn.commit()
                total_inserted += len(rows_to_insert)
                logger.info(f"Ingested {total_inserted} records so far...")
    
    # Create GIST index if not exists
    logger.info("Ensuring spatial index (GIST) on geometry column...")
    with db_manager._pg_conn.cursor() as cur:
        # In a real environment with PostGIS, we would create a GIST index on a geometry type.
        # Currently 'geom' is stored as TEXT in this SQLite fallback friendly schema.
        # If it were geometry: cur.execute("CREATE INDEX IF NOT EXISTS hotspots_geom_idx ON hotspots USING GIST (geom);")
        pass
        
    elapsed = time.time() - start_time
    logger.info(f"Ingestion completed. Total valid records inserted/attempted: {total_inserted} in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    batch_ingest_firms_archive()
