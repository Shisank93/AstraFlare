#!/usr/bin/env python3
"""
AstraFlare Executable Database Migration & Initialization Script.
Safe, idempotent initialization of PostGIS database extensions, tables, and indexes.
"""
import os
import sys

# Ensure repository root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import db_manager
from backend.config import settings

def init_database():
    print("=" * 60)
    print("ASTRAFLARE DATABASE INITIALIZATION")
    print("=" * 60)
    
    schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_file):
        print(f"Error: Schema file not found at {schema_file}")
        sys.exit(1)

    with open(schema_file, "r", encoding="utf-8") as f:
        sql_script = f.read()

    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1]}")
    connected = db_manager.connect()
    
    if not connected:
        print("Error: Could not connect to database.")
        sys.exit(1)

    if db_manager.is_postgres:
        print("Executing PostGIS DDL schema initialization...")
        try:
            statements = [s.strip() for s in sql_script.split(";") if s.strip()]
            for stmt in statements:
                db_manager.execute_query(stmt)
            print("PostgreSQL + PostGIS database schema initialized successfully.")
        except Exception as e:
            print(f"PostgreSQL initialization failed: {e}")
            sys.exit(1)
    else:
        print("PostgreSQL unavailable; SQLite fallback schema initialized.")

    tables = db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table';" if not db_manager.is_postgres 
        else "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
    )
    table_names = [t.get("name") or t.get("table_name") for t in tables]
    print(f"Created Tables ({len(table_names)}): {', '.join(filter(None, table_names))}")
    print("=" * 60)

if __name__ == "__main__":
    init_database()
