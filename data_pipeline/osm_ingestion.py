"""
AstraFlare OpenStreetMap Industrial Infrastructure Ingestion Service.
Queries Overpass API for contextual industrial infrastructure around thermal coordinates,
normalizes point/polygon geometries, and caches sites in PostGIS.
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from database.db import db_manager
from data_pipeline.gis_engine import validate_coordinates

logger = logging.getLogger("astraflare.osm")

class OSMIngestionClient:
    def __init__(self, overpass_url: Optional[str] = None):
        self.overpass_url = overpass_url or getattr(settings, "OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")

    def build_overpass_query(self, latitude: float, longitude: float, radius_m: float = 5000.0) -> str:
        """Constructs Overpass QL query searching industrial infrastructure within radius_m buffer."""
        return f"""
        [out:json][timeout:25];
        (
          node["landuse"="industrial"](around:{radius_m}, {latitude}, {longitude});
          way["landuse"="industrial"](around:{radius_m}, {latitude}, {longitude});
          relation["landuse"="industrial"](around:{radius_m}, {latitude}, {longitude});
          node["man_made"="flare_stack"](around:{radius_m}, {latitude}, {longitude});
          way["refinery"](around:{radius_m}, {latitude}, {longitude});
          node["power"="plant"](around:{radius_m}, {latitude}, {longitude});
          way["power"="plant"](around:{radius_m}, {latitude}, {longitude});
        );
        out center;
        """

    def fetch_osm_industrial_sites(
        self, latitude: float, longitude: float, radius_m: float = 5000.0
    ) -> List[Dict[str, Any]]:
        """Queries Overpass API for industrial facilities near coordinates."""
        valid, err = validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(err)

        query_str = self.build_overpass_query(latitude, longitude, radius_m)
        logger.info(f"Querying Overpass API for coordinates ({latitude}, {longitude}) buffer {radius_m}m...")

        retries = 3
        headers = {"User-Agent": "AstraFlare/1.0 (contact@astraflare.org)"}
        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=25.0, headers=headers) as client:
                    resp = client.post(self.overpass_url, data={"data": query_str})
                    resp.raise_for_status()
                    data = resp.json()
                    elements = data.get("elements", [])
                    return self.normalize_osm_elements(elements)
            except Exception as e:
                logger.warning(f"Overpass API request failed (attempt {attempt}/{retries}): {e}")
                if attempt == retries:
                    logger.error("Overpass API unavailable after max retries.")
                    return []

        return []

    def normalize_osm_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizes OSM Node/Way/Relation elements into standardized industrial_sites records."""
        normalized = []
        for elem in elements:
            try:
                osm_type = elem.get("type", "node")
                osm_id = f"{osm_type}_{elem.get('id')}"
                tags = elem.get("tags", {})
                
                facility_type = (
                    tags.get("industrial") or 
                    tags.get("man_made") or 
                    tags.get("refinery") or 
                    tags.get("power") or 
                    tags.get("landuse") or 
                    "industrial"
                )
                
                name = tags.get("name") or f"Industrial Site ({osm_id})"

                lat = elem.get("lat") or elem.get("center", {}).get("lat")
                lon = elem.get("lon") or elem.get("center", {}).get("lon")

                if lat is None or lon is None:
                    continue

                geom_wkt = f"POINT({lon} {lat})"

                normalized.append({
                    "osm_id": osm_id,
                    "name": name,
                    "facility_type": str(facility_type).lower(),
                    "tags": tags,
                    "geom": geom_wkt,
                    "data_source": "OSM"
                })
            except Exception as e:
                logger.warning(f"Failed to normalize OSM element: {e}")
                continue

        return normalized

    def ingest_contextual_osm(
        self, latitude: float, longitude: float, radius_m: float = 5000.0, mock_fallback: bool = False
    ) -> int:
        """
        Checks local database cache first. If no sites found within radius_m, fetches from Overpass API
        and persists normalized sites into industrial_sites table.
        """
        db_manager.connect()

        cached_count = self._count_cached_sites(latitude, longitude, radius_m)
        if cached_count > 0:
            logger.info(f"OSM Cache Hit: Found {cached_count} industrial sites in PostGIS cache. Skipping Overpass API network call.")
            return cached_count

        sites = []
        if not mock_fallback:
            try:
                sites = self.fetch_osm_industrial_sites(latitude, longitude, radius_m)
            except Exception as e:
                logger.warning(f"Overpass fetch failed: {e}")

        if not sites and mock_fallback:
            logger.info("Generating mock contextual OSM industrial sites.")
            sites = [
                {
                    "osm_id": f"way_mock_{int(latitude*100)}_{int(longitude*100)}",
                    "name": "Contextual Industrial Zone",
                    "facility_type": "factory",
                    "tags": {"landuse": "industrial"},
                    "geom": f"POINT({longitude + 0.002} {latitude + 0.002})",
                    "data_source": "OSM"
                }
            ]

        inserted = 0
        for site in sites:
            if db_manager.is_postgres:
                query = """
                INSERT INTO industrial_sites (osm_id, name, facility_type, geom, data_source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (osm_id) DO NOTHING;
                """
                db_manager.execute_query(query, (site["osm_id"], site["name"], site["facility_type"], site["geom"], site["data_source"]))
            else:
                query = """
                INSERT OR IGNORE INTO industrial_sites (osm_id, name, facility_type, geom, data_source)
                VALUES (?, ?, ?, ?, ?);
                """
                db_manager.execute_query(query, (site["osm_id"], site["name"], site["facility_type"], site["geom"], site["data_source"]))
            inserted += 1

        logger.info(f"Persisted {inserted} new OSM industrial sites to database.")
        return inserted

    def _count_cached_sites(self, latitude: float, longitude: float, radius_m: float) -> int:
        """Queries database for existing industrial sites within radius."""
        from data_pipeline.gis_engine import gis_engine
        return gis_engine.count_industrial_sites_in_radius(latitude, longitude, radius_m)

osm_client = OSMIngestionClient()

if __name__ == "__main__":
    print("Executing OSM Ingestion Client Test...")
    count = osm_client.ingest_contextual_osm(22.3072, 73.1812, radius_m=5000.0, mock_fallback=True)
    print(f"OSM Context Ingestion Result: {count} sites available.")
