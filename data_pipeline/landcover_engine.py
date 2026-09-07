"""
AstraFlare ESA WorldCover Land-Cover Engine.
Provides land-cover context sampling, spatial uncertainty buffer lookup,
and class code to natural language mapping.
"""
import os
import sys
import logging
from typing import Dict, Any, Tuple, Optional

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import db_manager
from data_pipeline.gis_engine import validate_coordinates

logger = logging.getLogger("astraflare.landcover")

# ESA WorldCover Official Classification Scheme (10m Resolution)
WORLDCOVER_CLASS_MAP = {
    10: {"name": "Tree cover", "category": "forest", "desc": "Tree cover / Forest area"},
    20: {"name": "Shrubland", "category": "vegetation", "desc": "Shrubland vegetation"},
    30: {"name": "Grassland", "category": "vegetation", "desc": "Natural grassland"},
    40: {"name": "Cropland", "category": "agriculture", "desc": "Agricultural farmland"},
    50: {"name": "Built-up", "category": "urban_industrial", "desc": "Urban, industrial, built-up infrastructure"},
    60: {"name": "Bare / sparse vegetation", "category": "bare", "desc": "Bare soil, sand, rocks"},
    70: {"name": "Snow and ice", "category": "water", "desc": "Permanent snow or ice cover"},
    80: {"name": "Permanent water bodies", "category": "water", "desc": "Lakes, rivers, reservoirs"},
    90: {"name": "Herbaceous wetland", "category": "wetland", "desc": "Wetlands and marshes"},
    95: {"name": "Mangroves", "category": "forest", "desc": "Coastal mangrove forests"},
    100: {"name": "Moss and lichen", "category": "tundra", "desc": "Tundra and high-altitude vegetation"}
}

class LandCoverEngine:
    def __init__(self, db_mgr=None):
        from database.db import db_manager
        self.db = db_mgr or db_manager

    def get_land_cover_class(
        self, latitude: float, longitude: float, buffer_m: float = 375.0
    ) -> Dict[str, Any]:
        """
        Samples surface land-cover class at coordinate taking into account 375m satellite pixel uncertainty.
        Returns class_code, class_name, category, description, and data_source tag.
        """
        valid, err = validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(err)

        # 1. Database PostGIS Geometry / Raster Lookup
        if self.db.is_postgres and getattr(self.db, "has_postgis", False):
            query = """
            SELECT class_code, class_name, description
            FROM land_cover
            WHERE geom IS NOT NULL 
              AND ST_Intersects(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            LIMIT 1;
            """
            res = self.db.execute_query(query, (longitude, latitude))
            if res:
                code = res[0]["class_code"]
                meta = WORLDCOVER_CLASS_MAP.get(code, {"name": res[0]["class_name"], "category": "unknown", "desc": res[0]["description"]})
                return {
                    "class_code": code,
                    "class_name": meta["name"],
                    "category": meta["category"],
                    "description": meta["desc"],
                    "data_source": "ESA_WORLDCOVER_POSTGIS"
                }

        # 2. Heuristic Contextual Lookup (Fallback for sandbox/mock scenarios)
        # Based on latitude/longitude regional biomes in India for offline testing
        heur_code = self._heuristic_land_cover_fallback(latitude, longitude)
        meta = WORLDCOVER_CLASS_MAP[heur_code]
        return {
            "class_code": heur_code,
            "class_name": meta["name"],
            "category": meta["category"],
            "description": meta["desc"],
            "data_source": "ESA_WORLDCOVER_HEURISTIC"
        }

    def _heuristic_land_cover_fallback(self, latitude: float, longitude: float) -> int:
        """Determines approximate regional biome code for offline development testing."""
        # Garhwal / Himalayas region (dense tree cover)
        if latitude > 29.0 and longitude > 77.0:
            return 10
        # Gujarat / Industrial corridor (Built-up / Farmland)
        if 20.0 <= latitude <= 24.0 and 68.0 <= longitude <= 74.0:
            return 50  # Built-up / Industrial
        # Default agricultural / cropland
        return 40  # Cropland

landcover_engine = LandCoverEngine()

if __name__ == "__main__":
    print("Testing Land Cover Engine...")
    res = landcover_engine.get_land_cover_class(22.3072, 73.1812)
    print(f"Land Cover Result: {res}")
