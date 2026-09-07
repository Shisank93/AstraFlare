"""
AstraFlare Database Connection & Execution Manager.
Provides PostgreSQL + PostGIS connectivity with safe shared SQLite fallback for sandboxed/isolated environments.
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger("astraflare.db")

class DatabaseManager:
    _shared_sqlite_conn: Optional[sqlite3.Connection] = None

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.DATABASE_URL
        self.is_postgres = self.db_url.startswith("postgresql")
        self.has_postgis = False
        self._pg_conn = None
        self._sqlite_conn = None

    def connect(self):
        """Establish connection to PostgreSQL or shared fallback SQLite."""
        mode = getattr(settings, "ASTRAFLARE_MODE", "REAL").upper()
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self._pg_conn = psycopg2.connect(self.db_url)
                self._pg_conn.autocommit = True
                logger.info("Connected to PostgreSQL database successfully.")
                
                # Check PostGIS extension availability
                try:
                    with self._pg_conn.cursor() as cur:
                        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                    self.has_postgis = True
                except Exception:
                    try:
                        with self._pg_conn.cursor() as cur:
                            cur.execute("SELECT PostGIS_Version();")
                        self.has_postgis = True
                    except Exception:
                        self.has_postgis = False

                # Ensure ground truth & events tables exist in PostgreSQL
                self._init_postgres_schema()
                return True
            except Exception as e:
                if mode == "REAL":
                    logger.error(f"ASTRAFLARE_MODE=REAL: PostgreSQL connection failed ({e}). Silent SQLite fallback IS NOT PERMITTED in REAL mode.")
                    self.is_postgres = True
                    self.has_postgis = False
                    self._pg_conn = None
                    raise RuntimeError(f"Database Error: PostgreSQL/PostGIS is required in REAL mode but connection failed: {e}")
                logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite database engine in DEMO mode.")
                self.is_postgres = False
                self.has_postgis = False
        else:
            if mode == "REAL":
                logger.error("ASTRAFLARE_MODE=REAL: DATABASE_URL does not start with 'postgresql://'. Silent SQLite fallback IS NOT PERMITTED in REAL mode.")
                raise RuntimeError("Database Error: PostgreSQL/PostGIS is required in REAL mode. DATABASE_URL must start with 'postgresql://'.")

        # Shared SQLite Fallback Engine (DEMO mode only)
        if DatabaseManager._shared_sqlite_conn is None:
            DatabaseManager._shared_sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
            DatabaseManager._shared_sqlite_conn.row_factory = sqlite3.Row
            self._sqlite_conn = DatabaseManager._shared_sqlite_conn
            self._init_sqlite_schema()
        else:
            self._sqlite_conn = DatabaseManager._shared_sqlite_conn

        logger.info("Connected to in-memory SQLite fallback engine (DEMO Mode).")
        return True

    def _init_postgres_schema(self):
        """Creates complete table definitions in PostgreSQL if they do not exist."""
        if not self._pg_conn:
            return
        import os
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                with self._pg_conn.cursor() as cur:
                    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
                    for stmt in statements:
                        try:
                            cur.execute(stmt)
                        except Exception as stmt_err:
                            logger.warning(f"Schema statement warning: {stmt_err}")
                self._pg_conn.commit()
                logger.info("Executed schema.sql in PostgreSQL successfully.")
                return
            except Exception as e:
                logger.warning(f"Could not execute full schema.sql in PostgreSQL: {e}")
        with self._pg_conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ground_truth_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(64) UNIQUE NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                source_name VARCHAR(128) NOT NULL,
                source_url VARCHAR(512),
                source_record_id VARCHAR(128),
                event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                geometry TEXT NOT NULL,
                latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
                longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
                matching_distance_m DOUBLE PRECISION,
                matching_time_hours DOUBLE PRECISION,
                source_confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
                verification_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED_EXTERNAL',
                retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS event_hotspot_matches (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(64) NOT NULL REFERENCES ground_truth_events(event_id) ON DELETE CASCADE,
                hotspot_id VARCHAR(64) NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
                match_distance_m DOUBLE PRECISION NOT NULL,
                match_time_hours DOUBLE PRECISION NOT NULL,
                match_confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, hotspot_id)
            );
            """)

    def _init_sqlite_schema(self):
        """Creates SQLite compatible table definitions for offline/sandbox testing."""
        assert self._sqlite_conn is not None
        cursor = self._sqlite_conn.cursor()
        
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS hotspots (
            id TEXT PRIMARY KEY,
            firms_id TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            geom TEXT NOT NULL,
            acq_timestamp TEXT NOT NULL,
            satellite TEXT NOT NULL,
            instrument TEXT,
            brightness REAL,
            frp REAL NOT NULL,
            confidence TEXT,
            daynight TEXT,
            data_source TEXT NOT NULL DEFAULT 'REAL',
            ingestion_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS industrial_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            osm_id TEXT UNIQUE,
            name TEXT,
            facility_type TEXT NOT NULL,
            tags TEXT,
            geom TEXT NOT NULL,
            data_source TEXT DEFAULT 'OSM',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS land_cover (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_code INTEGER UNIQUE,
            class_name TEXT NOT NULL,
            description TEXT,
            geom TEXT
        );

        CREATE TABLE IF NOT EXISTS weather_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            observation_time TEXT NOT NULL,
            temperature_c REAL,
            wind_speed_kmh REAL,
            wind_direction_deg REAL,
            relative_humidity_pct REAL,
            precipitation_mm REAL,
            source TEXT DEFAULT 'ERA5',
            ingestion_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS historical_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotspot_id TEXT REFERENCES hotspots(id),
            historical_count_30d INTEGER DEFAULT 0,
            historical_count_365d INTEGER DEFAULT 0,
            historical_mean_frp REAL,
            historical_max_frp REAL,
            historical_std_frp REAL,
            frp_anomaly_score REAL,
            history_observation_count INTEGER DEFAULT 0,
            anomaly_status TEXT DEFAULT 'VALID',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotspot_id TEXT REFERENCES hotspots(id),
            predicted_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            is_abstained INTEGER DEFAULT 0,
            risk_score REAL NOT NULL,
            prob_industrial_incident REAL,
            prob_persistent_heat REAL,
            prob_wildland_fire REAL,
            model_version TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotspot_id TEXT REFERENCES hotspots(id),
            evidence_type TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            feature_value TEXT NOT NULL,
            contribution REAL,
            human_readable_statement TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            hotspot_id TEXT,
            original_prediction TEXT DEFAULT 'UNKNOWN',
            final_classification TEXT NOT NULL,
            reviewer TEXT DEFAULT 'analyst',
            decision TEXT NOT NULL DEFAULT 'PENDING',
            review_status TEXT DEFAULT 'PENDING',
            notes TEXT,
            analyst_note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ground_truth_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT,
            source_record_id TEXT,
            event_timestamp TEXT NOT NULL,
            geometry TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            matching_distance_m REAL,
            matching_time_hours REAL,
            source_confidence REAL DEFAULT 1.0,
            verification_status TEXT DEFAULT 'VERIFIED_EXTERNAL',
            retrieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS event_hotspot_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL REFERENCES ground_truth_events(event_id) ON DELETE CASCADE,
            hotspot_id TEXT NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
            match_distance_m REAL NOT NULL,
            match_time_hours REAL NOT NULL,
            match_confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, hotspot_id)
        );

        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_timestamp TEXT NOT NULL,
            centroid_lat REAL NOT NULL,
            centroid_lon REAL NOT NULL,
            geom TEXT NOT NULL,
            duration_hours REAL DEFAULT 0.0,
            observation_count INTEGER NOT NULL DEFAULT 1,
            spatial_extent_m REAL DEFAULT 0.0,
            max_frp REAL NOT NULL DEFAULT 0.0,
            mean_frp REAL NOT NULL DEFAULT 0.0,
            std_frp REAL DEFAULT 0.0,
            max_brightness REAL DEFAULT 0.0,
            mean_brightness REAL DEFAULT 0.0,
            confidence_high_ratio REAL DEFAULT 0.0,
            satellite_count INTEGER DEFAULT 1,
            industrial_distance_m REAL,
            industrial_site_count_250m INTEGER DEFAULT 0,
            industrial_site_count_1km INTEGER DEFAULT 0,
            industrial_site_count_5km INTEGER DEFAULT 0,
            worldcover_class INTEGER,
            historical_count INTEGER DEFAULT 0,
            historical_mean_frp REAL,
            historical_max_frp REAL,
            historical_std_frp REAL,
            historical_anomaly_zscore REAL,
            historical_status TEXT DEFAULT 'NO_PRIOR_HISTORY',
            data_source TEXT NOT NULL DEFAULT 'REAL',
            data_quality_status TEXT DEFAULT 'HIGH',
            evidence_status TEXT DEFAULT 'SUFFICIENT',
            risk_score REAL NOT NULL DEFAULT 0.0,
            risk_level TEXT NOT NULL DEFAULT 'LOW',
            investigation_priority TEXT NOT NULL DEFAULT 'LOW',
            human_review_required INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self._sqlite_conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns list of dictionary records."""
        if not self._pg_conn and not self._sqlite_conn:
            self.connect()

        if self.is_postgres and self._pg_conn:
            import psycopg2.extras
            with self._pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                if cur.description:
                    return [dict(row) for row in cur.fetchall()]
                return []
        else:
            assert self._sqlite_conn is not None
            cur = self._sqlite_conn.cursor()
            cur.execute(query, params)
            if cur.description:
                columns = [column[0] for column in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            self._sqlite_conn.commit()
            return []

    def close(self):
        if self._pg_conn:
            self._pg_conn.close()

db_manager = DatabaseManager()
