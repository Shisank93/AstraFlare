"""
AstraFlare Database Connection & Execution Manager.
Provides PostgreSQL + PostGIS connectivity with safe SQLite fallback for sandboxed/isolated environments.
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger("astraflare.db")

class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.DATABASE_URL
        self.is_postgres = self.db_url.startswith("postgresql")
        self._pg_conn = None
        self._sqlite_conn = None

    def connect(self):
        """Establish connection to PostgreSQL or fallback SQLite."""
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self._pg_conn = psycopg2.connect(self.db_url)
                self._pg_conn.autocommit = True
                logger.info("Connected to PostgreSQL database successfully.")
                return True
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite database engine.")
                self.is_postgres = False

        # SQLite Fallback Engine
        self._sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._sqlite_conn.row_factory = sqlite3.Row
        self._init_sqlite_schema()
        logger.info("Connected to in-memory SQLite fallback engine.")
        return True

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
            hotspot_id TEXT REFERENCES hotspots(id),
            original_prediction TEXT NOT NULL,
            final_classification TEXT NOT NULL,
            review_status TEXT DEFAULT 'PENDING',
            analyst_note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
                cur.execute(query, params)
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
        if self._sqlite_conn:
            self._sqlite_conn.close()

db_manager = DatabaseManager()
