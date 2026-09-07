"""
Logging configuration for AstraFlare Backend.
"""
import logging
import sys
from backend.app.config import settings

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger("astraflare.backend")