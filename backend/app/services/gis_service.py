"""
AstraFlare GIS & Industrial Site Context Service.
Provides industrial infrastructure queries, bounding box spatial filtering, and thermal detection association.
"""
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from database.db import db_manager, DatabaseManager
from data_pipeline.gis_engine import gis_engine, haversine_distance_m

logger = logging.getLogger("astraflare.backend.services.gis")

class GISService:
    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db = db_mgr or db_manager

    def get_industrial_sites(
        self,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        facility_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Queries industrial_sites table with spatial bounding box and facility type filters."""
        self.db.connect()

        conditions = []
        params: List[Any] = []
        ph = "%s" if self.db.is_postgres else "?"

        if min_lat is not None and max_lat is not None and min_lon is not None and max_lon is not None:
            if self.db.is_postgres and getattr(self.db, "has_postgis", False):
                conditions.append(f"ST_Within(geom::geometry, ST_MakeEnvelope({ph}, {ph}, {ph}, {ph}, 4326))")
                params.extend([min_lon, min_lat, max_lon, max_lat])
        if facility_type:
            conditions.append(f"facility_type = {ph}")
            params.append(facility_type)

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        # Total count
        count_sql = f"SELECT COUNT(*) as cnt FROM industrial_sites{where_clause};"
        count_res = self.db.execute_query(count_sql, tuple(params))
        total_records = count_res[0]["cnt"] if count_res else 0

        offset = (max(1, page) - 1) * page_size
        query_sql = f"SELECT id, osm_id, name, facility_type, geom, data_source FROM industrial_sites{where_clause} ORDER BY id ASC LIMIT {page_size} OFFSET {offset};"
        records = self.db.execute_query(query_sql, tuple(params))

        sites = []
        for r in records:
            site = dict(r)
            geom_str = str(site.get("geom") or "")
            if "POINT" in geom_str:
                coords = geom_str.replace("POINT(", "").replace(")", "").split()
                slon, slat = float(coords[0]), float(coords[1])
                site["longitude"] = slon
                site["latitude"] = slat

                # Query thermal detection count within 3000m
                det_count = self._count_nearby_hotspots(slat, slon, radius_m=3000.0)
                site["thermal_detection_count_3km"] = det_count
            else:
                site["latitude"] = 0.0
                site["longitude"] = 0.0
                site["thermal_detection_count_3km"] = 0

            sites.append(site)

        return sites, total_records

    def get_industrial_site_detail(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed record and nearby thermal hotspot detections for target industrial site."""
        self.db.connect()
        ph = "%s" if self.db.is_postgres else "?"
        res = self.db.execute_query(f"SELECT * FROM industrial_sites WHERE osm_id = {ph} OR CAST(id AS VARCHAR) = {ph};", (site_id, site_id))
        if not res:
            return None

        site = dict(res[0])
        geom_str = str(site.get("geom") or "")
        if "POINT" in geom_str:
            coords = geom_str.replace("POINT(", "").replace(")", "").split()
            slon, slat = float(coords[0]), float(coords[1])
            site["longitude"] = slon
            site["latitude"] = slat

            # Query nearby hotspot observations
            nearby_hs = self._get_nearby_hotspots(slat, slon, radius_m=3000.0)
            site["nearby_thermal_detections"] = nearby_hs
            site["thermal_detection_count_3km"] = len(nearby_hs)
        else:
            site["latitude"] = 0.0
            site["longitude"] = 0.0
            site["nearby_thermal_detections"] = []
            site["thermal_detection_count_3km"] = 0

        return site

    def _count_nearby_hotspots(self, lat: float, lon: float, radius_m: float = 3000.0) -> int:
        lat_delta = radius_m / 111000.0
        lon_delta = radius_m / (111000.0 * max(0.1, math.cos(math.radians(lat))))
        ph = "%s" if self.db.is_postgres else "?"
        query = f"SELECT id, latitude, longitude FROM hotspots WHERE latitude BETWEEN {ph} AND {ph} AND longitude BETWEEN {ph} AND {ph} AND data_source = 'REAL';"
        res = self.db.execute_query(query, (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta))
        
        cnt = 0
        for r in res:
            if haversine_distance_m(lat, lon, float(r["latitude"]), float(r["longitude"])) <= radius_m:
                cnt += 1
        return cnt

    def _get_nearby_hotspots(self, lat: float, lon: float, radius_m: float = 3000.0) -> List[Dict[str, Any]]:
        lat_delta = radius_m / 111000.0
        lon_delta = radius_m / (111000.0 * max(0.1, math.cos(math.radians(lat))))
        ph = "%s" if self.db.is_postgres else "?"
        query = f"SELECT id, acq_timestamp, frp, satellite, latitude, longitude FROM hotspots WHERE latitude BETWEEN {ph} AND {ph} AND longitude BETWEEN {ph} AND {ph} AND data_source = 'REAL' ORDER BY acq_timestamp DESC LIMIT 50;"
        res = self.db.execute_query(query, (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta))
        
        items = []
        for r in res:
            h_lat, h_lon = float(r["latitude"]), float(r["longitude"])
            dist = haversine_distance_m(lat, lon, h_lat, h_lon)
            if dist <= radius_m:
                items.append({
                    "id": r["id"],
                    "acq_timestamp": str(r["acq_timestamp"]),
                    "frp": float(r["frp"]),
                    "satellite": r["satellite"],
                    "distance_m": round(dist, 1)
                })
        return items

gis_service = GISService()
