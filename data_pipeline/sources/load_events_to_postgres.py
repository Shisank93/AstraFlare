"""
AstraFlare Database Event Loader.
Idempotently loads physical event clusters into PostgreSQL + PostGIS database.
Preserves REAL provenance and calculates Phase 3.11 risk & priority intelligence.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from database.db import db_manager
from backend.app.config import settings
from backend.risk_engine.engine import risk_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("astraflare.event_loader")

CSV_PATH = os.path.join(_ROOT_DIR, "data", "processed", "event_dataset", "DATASET_C_ALL_EVENTS.csv")

def extract_worldcover_code(val: Any) -> int:
    """Extracts integer WorldCover class code from string representation."""
    if pd.isna(val):
        return 40  # Default cropland
    val_str = str(val)
    if "(" in val_str and ")" in val_str:
        try:
            return int(val_str.split("(")[-1].split(")")[0])
        except ValueError:
            pass
    try:
        return int(float(val_str))
    except ValueError:
        return 40

def run_event_loader(limit: int = None, batch_size: int = 25000):
    """
    Idempotently ingests physical events from CSV into the database.
    Calculates operational risk score, risk level, and priority.
    """
    if not os.path.exists(CSV_PATH):
        logger.error(f"Event dataset CSV not found at: {CSV_PATH}")
        return False

    logger.info(f"Connecting to database (Engine: {'PostgreSQL' if db_manager.is_postgres else 'SQLite'})...")
    db_manager.connect()

    logger.info(f"Reading event dataset from: {CSV_PATH}")
    reader = pd.read_csv(CSV_PATH, chunksize=batch_size)

    total_inserted = 0
    for chunk_idx, chunk in enumerate(reader):
        if limit and total_inserted >= limit:
            break

        rows_to_insert = []
        for _, row in chunk.iterrows():
            if limit and total_inserted >= limit:
                break

            event_id = str(row["event_id"])
            event_timestamp = str(row["event_start"])
            centroid_lat = float(row["centroid_lat"])
            centroid_lon = float(row["centroid_lon"])
            geom = f"POINT({centroid_lon} {centroid_lat})"

            duration_hours = float(row.get("duration_hours", 0.0))
            obs_cnt = int(row.get("observation_count", 1))
            spatial_extent_m = float(row.get("spatial_extent_m", 0.0))
            max_frp = float(row.get("max_frp", 0.0))
            mean_frp = float(row.get("mean_frp", 0.0))
            std_frp = float(row.get("std_frp", 0.0))
            max_brightness = float(row.get("max_brightness", 0.0))
            mean_brightness = float(row.get("mean_brightness", 0.0))
            conf_high_ratio = float(row.get("confidence_high_ratio", 0.0))
            satellite_count = int(row.get("satellite_count", 1))

            industrial_distance_m = float(row["industrial_distance_m"]) if pd.notna(row.get("industrial_distance_m")) else None
            site_cnt_250m = int(row.get("industrial_site_count_250m", 0))
            site_cnt_1km = int(row.get("industrial_site_count_1km", 0))
            site_cnt_5km = int(row.get("industrial_site_count_5km", 0))

            worldcover_class = extract_worldcover_code(row.get("worldcover_class"))

            # Determine Phase 3.11 deterministic risk & priority
            assessment = risk_engine.assess_event({
                "event_id": event_id,
                "event_timestamp": event_timestamp,
                "centroid_lat": centroid_lat,
                "centroid_lon": centroid_lon,
                "max_frp": max_frp,
                "mean_frp": mean_frp,
                "max_brightness": max_brightness,
                "mean_brightness": mean_brightness,
                "observation_count": obs_cnt,
                "duration_hours": duration_hours,
                "spatial_extent_m": spatial_extent_m,
                "satellite_count": satellite_count,
                "confidence_high_ratio": conf_high_ratio,
                "industrial_distance_m": industrial_distance_m,
                "industrial_site_count_250m": site_cnt_250m,
                "industrial_site_count_1km": site_cnt_1km,
                "industrial_site_count_5km": site_cnt_5km,
                "worldcover_class": str(worldcover_class)
            })

            risk_score = assessment.overall_risk_score
            risk_level = assessment.risk_level
            priority = assessment.investigation_priority
            human_review_req = assessment.human_review_required
            data_quality_status = assessment.data_quality_status
            evidence_status = assessment.evidence_status

            data_source = settings.DATA_SOURCE_REAL

            rows_to_insert.append((
                event_id, event_timestamp, centroid_lat, centroid_lon, geom,
                duration_hours, obs_cnt, spatial_extent_m, max_frp, mean_frp,
                std_frp, max_brightness, mean_brightness, conf_high_ratio,
                satellite_count, industrial_distance_m, site_cnt_250m, site_cnt_1km,
                site_cnt_5km, worldcover_class, 0, None, None, None, None,
                "NO_PRIOR_HISTORY", data_source, data_quality_status, evidence_status,
                risk_score, risk_level, priority, bool(human_review_req)
            ))
            total_inserted += 1

        # Bulk SQL upsert
        sql_pg = """
        INSERT INTO events (
            event_id, event_timestamp, centroid_lat, centroid_lon, geom,
            duration_hours, observation_count, spatial_extent_m, max_frp, mean_frp,
            std_frp, max_brightness, mean_brightness, confidence_high_ratio,
            satellite_count, industrial_distance_m, industrial_site_count_250m, industrial_site_count_1km,
            industrial_site_count_5km, worldcover_class, historical_count, historical_mean_frp,
            historical_max_frp, historical_std_frp, historical_anomaly_zscore,
            historical_status, data_source, data_quality_status, evidence_status,
            risk_score, risk_level, investigation_priority, human_review_required
        ) VALUES %s
        ON CONFLICT (event_id) DO UPDATE SET
            risk_score = EXCLUDED.risk_score,
            risk_level = EXCLUDED.risk_level,
            investigation_priority = EXCLUDED.investigation_priority;
        """

        sql_sqlite = """
        INSERT OR REPLACE INTO events (
            event_id, event_timestamp, centroid_lat, centroid_lon, geom,
            duration_hours, observation_count, spatial_extent_m, max_frp, mean_frp,
            std_frp, max_brightness, mean_brightness, confidence_high_ratio,
            satellite_count, industrial_distance_m, industrial_site_count_250m, industrial_site_count_1km,
            industrial_site_count_5km, worldcover_class, historical_count, historical_mean_frp,
            historical_max_frp, historical_std_frp, historical_anomaly_zscore,
            historical_status, data_source, data_quality_status, evidence_status,
            risk_score, risk_level, investigation_priority, human_review_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        if db_manager.is_postgres and db_manager._pg_conn:
            import psycopg2.extras
            with db_manager._pg_conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, sql_pg, rows_to_insert, page_size=5000)
            db_manager._pg_conn.commit()
        else:
            cur = db_manager._sqlite_conn.cursor()
            cur.executemany(sql_sqlite, rows_to_insert)
            db_manager._sqlite_conn.commit()

        logger.info(f"Processed batch {chunk_idx + 1}: Total events loaded = {total_inserted}")

    logger.info(f"Successfully loaded {total_inserted} events into database.")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load physical event clusters into PostgreSQL/SQLite.")
    parser.add_argument("limit_positional", nargs="?", type=int, default=None, help="Optional limit on number of events to load")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of events to load")
    args = parser.parse_args()
    
    limit_val = args.limit if args.limit is not None else args.limit_positional
    run_event_loader(limit=limit_val)

