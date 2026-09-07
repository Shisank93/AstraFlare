"""
Global pytest configuration and fixtures for AstraFlare.
Ensures test runner uses DEMO mode with SQLite fallback unless testing REAL mode explicitly.
"""
import os
import sys

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import pytest
from backend.app.config import settings

@pytest.fixture(autouse=True, scope="session")
def set_test_mode():
    if "ASTRAFLARE_MODE" not in os.environ:
        os.environ["ASTRAFLARE_MODE"] = "DEMO"
        settings.ASTRAFLARE_MODE = "DEMO"
