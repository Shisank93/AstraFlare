"""
FastAPI Dependency Injection Module.
Provides shared database manager instances and common query parameter dependencies.
"""
from typing import Generator
from database.db import db_manager, DatabaseManager

def get_db() -> Generator[DatabaseManager, None, None]:
    """Dependency that yields connected DatabaseManager instance."""
    db_manager.connect()
    try:
        yield db_manager
    finally:
        pass
