"""
AstraFlare Backend Configuration Module (Pydantic Settings).
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_FILE = os.path.join(_ROOT_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=_ENV_FILE)

    # System Environment & Version
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ASTRAFLARE_MODE: str = os.getenv("ASTRAFLARE_MODE", "REAL").upper()
    VERSION: str = "0.4.0"
    APP_NAME: str = "AstraFlare Backend API"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")

    # Security & CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "astraflare_dev_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "astraflare")

    @property
    def DATABASE_URL(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Operational Thresholds
    HUMAN_REVIEW_THRESHOLD: float = float(os.getenv("HUMAN_REVIEW_THRESHOLD", "0.65"))
    RISK_HIGH_THRESHOLD: float = float(os.getenv("RISK_HIGH_THRESHOLD", "0.75"))

    # ML Model Artifact
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "ml/models/astraflare_gbdt.json")
    ML_MODEL_STATUS: str = "RESEARCH BASELINE"

    # Data Source Governance Tags
    DATA_SOURCE_REAL: str = "REAL"
    DATA_SOURCE_DEMO: str = "SYNTHETIC_DEMO"

    # NASA FIRMS API Credentials & Options
    NASA_FIRMS_MAP_KEY: str = os.getenv("NASA_FIRMS_MAP_KEY", "")
    NASA_FIRMS_DEFAULT_SOURCE: str = os.getenv("NASA_FIRMS_DEFAULT_SOURCE", "VIIRS_SNPP_NRT")
    NASA_FIRMS_DEFAULT_AREA: str = os.getenv("NASA_FIRMS_DEFAULT_AREA", "South_Asia")

    # GIS Configuration
    OSM_SEARCH_RADIUS_KM: float = float(os.getenv("OSM_SEARCH_RADIUS_KM", "5.0"))
    DEFAULT_CRS: str = "EPSG:4326"

settings = Settings()
