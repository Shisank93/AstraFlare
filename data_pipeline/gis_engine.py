"""
AstraFlare Reusable GIS & Spatial Feature Engineering Engine.
Provides spatial query functions, coordinate validation, distance calculations, 
historical recurrence aggregation, and robust FRP anomaly score evaluation.
"""
import math
import logging
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger("astraflare.gis")

# --- 1. DATA VALIDATION ---

def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
    """Validates geographic latitude and longitude ranges (WGS84 EPSG:4326)."""
    if not isinstance(latitude, (int, float)) or math.isnan(latitude):
        return False, "Latitude must be a valid number."
    if not isinstance(longitude, (int, float)) or math.isnan(longitude):
        return False, "Longitude must be a valid number."
    if not (-90.0 <= latitude <= 90.0):
        return False, f"Latitude {latitude} out of valid bounds [-90, 90]."
    if not (-180.0 <= longitude <= 180.0):
        return False, f"Longitude {longitude} out of valid bounds [-180, 180]."
    return True, None

def validate_frp(frp: float) -> Tuple[bool, Optional[str]]:
    """Validates Fire Radiative Power (FRP in Megawatts)."""
    if not isinstance(frp, (int, float)) or math.isnan(frp):
        return False, "FRP must be a valid number."
    if frp < 0.0:
        return False, f"FRP cannot be negative ({frp})."
    return True, None

def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """Parses and validates ISO timestamp handling timezone consistently."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        raise ValueError(f"Invalid timestamp format '{timestamp_str}': {e}")


# --- 2. GEODESIC MATH UTILITIES ---

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes exact geodesic distance in meters between two lat/lon points on Earth."""
    R = 6371000.0  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


# --- 3. ROBUST FRP ANOMALY CALCULATION ---

def calculate_frp_anomaly_score(current_frp: float, historical_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates FRP Anomaly Z-Score with full operational safeguards.
    
    Formula: Z = (current_FRP - historical_mean) / historical_std
    
    Safeguards:
    - Insufficient historical observations (< 3): returns status='INSUFFICIENT_DATA'
    - Zero standard deviation (std == 0.0): handles flat historical baseline safely
    - Missing historical data: returns status='NO_HISTORY'
    """
    valid_frp, err = validate_frp(current_frp)
    if not valid_frp:
        raise ValueError(err)

    count = historical_stats.get("count", 0)
    mean = historical_stats.get("mean")
    std = historical_stats.get("std")

    if count == 0 or mean is None:
        return {
            "anomaly_score": None,
            "status": "NO_HISTORY",
            "message": "No historical observations found within search buffer."
        }

    if count < 3:
        return {
            "anomaly_score": None,
            "status": "INSUFFICIENT_DATA",
            "message": f"Insufficient historical observations ({count} < 3 required for robust z-score)."
        }

    # Zero standard deviation safeguard
    if std is None or std == 0.0:
        if current_frp == mean:
            score = 0.0
        elif current_frp > mean:
            score = 10.0  # Capped upper limit for positive anomaly with zero historical variance
        else:
            score = -10.0
        return {
            "anomaly_score": score,
            "status": "ZERO_STD",
            "message": f"Historical standard deviation is zero (baseline mean={mean:.1f} MW)."
        }

    # Normal Z-score calculation
    z_score = (current_frp - mean) / std
    return {
        "anomaly_score": round(z_score, 2),
        "status": "VALID",
        "message": f"Valid FRP anomaly score (Z={z_score:.2f}, baseline mean={mean:.1f} MW, std={std:.1f})."
    }


# --- 4. GIS SPATIAL ENGINE LAYER ---

class GISEngine:
    def __init__(self, db_mgr=None):
        from database.db import db_manager
        self.db = db_mgr or db_manager

    def get_nearest_industrial_site(
        self, latitude: float, longitude: float, max_distance_m: float = 10000.0
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Finds nearest industrial facility and distance in meters using spatial indexing.
        """
        valid, err = validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(err)

        if self.db.is_postgres and getattr(self.db, "has_postgis", False):
            query = """
            SELECT 
                id, osm_id, name, facility_type, tags,
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 
                    geom::geography
                ) AS dist_meters
            FROM industrial_sites
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 
                geom::geography, 
                %s
            )
            ORDER BY ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography <-> geom::geography
            LIMIT 1;
            """
            res = self.db.execute_query(query, (longitude, latitude, longitude, latitude, max_distance_m, longitude, latitude))
            if res:
                site = res[0]
                dist = site.pop("dist_meters")
                return site, round(dist, 1)
            return None, max_distance_m
        else:
            # Fallback Python spatial search over SQLite storage
            sites = self.db.execute_query("SELECT id, osm_id, name, facility_type, geom FROM industrial_sites;")
            nearest_site = None
            min_dist = max_distance_m

            for site in sites:
                # Parse geometry point string e.g. "POINT(lon lat)"
                geom_str = site["geom"]
                if "POINT" in geom_str:
                    coords = geom_str.replace("POINT(", "").replace(")", "").split()
                    slon, slat = float(coords[0]), float(coords[1])
                    dist = haversine_distance_m(latitude, longitude, slat, slon)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_site = site

            if nearest_site:
                return nearest_site, round(min_dist, 1)
            return None, max_distance_m

    def count_industrial_sites_in_radius(
        self, latitude: float, longitude: float, radius_m: float = 1000.0
    ) -> int:
        """Counts industrial facilities within configurable radius (meters)."""
        valid, err = validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(err)

        if self.db.is_postgres and getattr(self.db, "has_postgis", False):
            query = """
            SELECT COUNT(*) AS count
            FROM industrial_sites
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 
                geom::geography, 
                %s
            );
            """
            res = self.db.execute_query(query, (longitude, latitude, radius_m))
            return res[0]["count"] if res else 0
        else:
            sites = self.db.execute_query("SELECT geom FROM industrial_sites;")
            count = 0
            for site in sites:
                geom_str = site["geom"]
                if "POINT" in geom_str:
                    coords = geom_str.replace("POINT(", "").replace(")", "").split()
                    slon, slat = float(coords[0]), float(coords[1])
                    if haversine_distance_m(latitude, longitude, slat, slon) <= radius_m:
                        count += 1
            return count

    def get_historical_hotspot_recurrence(
        self, latitude: float, longitude: float, time_window_days: int = 365, radius_m: float = 1000.0
    ) -> int:
        """Returns count of historical hotspots within radius_m in past time_window_days."""
        stats = self.get_historical_frp_stats(latitude, longitude, time_window_days, radius_m)
        return stats["count"]

    def get_historical_frp_stats(
        self, latitude: float, longitude: float, time_window_days: int = 365, radius_m: float = 1000.0, exclude_hotspot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates count, mean, max, and standard deviation of historical FRP.
        Crucial Rule: Excludes target observation (exclude_hotspot_id) from statistics.
        """
        valid, err = validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(err)

        if self.db.is_postgres and getattr(self.db, "has_postgis", False):
            query = """
            SELECT frp
            FROM hotspots
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 
                geom::geography, 
                %s
            )
            """
            params: List[Any] = [longitude, latitude, radius_m]
            if exclude_hotspot_id:
                query += " AND id != %s"
                params.append(exclude_hotspot_id)

            res = self.db.execute_query(query, tuple(params))
            frp_list = [r["frp"] for r in res]
        else:
            lat_delta = radius_m / 111000.0
            lon_delta = radius_m / (111000.0 * max(0.1, math.cos(math.radians(latitude))))
            min_lat, max_lat = latitude - lat_delta, latitude + lat_delta
            min_lon, max_lon = longitude - lon_delta, longitude + lon_delta

            if self.db.is_postgres:
                hotspots = self.db.execute_query(
                    "SELECT id, latitude, longitude, frp FROM hotspots WHERE latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s;",
                    (min_lat, max_lat, min_lon, max_lon)
                )
            else:
                hotspots = self.db.execute_query(
                    "SELECT id, latitude, longitude, frp FROM hotspots WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?;",
                    (min_lat, max_lat, min_lon, max_lon)
                )

            frp_list = []
            for h in hotspots:
                if exclude_hotspot_id and h["id"] == exclude_hotspot_id:
                    continue
                dist = haversine_distance_m(latitude, longitude, h["latitude"], h["longitude"])
                if dist <= radius_m:
                    frp_list.append(h["frp"])

        count = len(frp_list)
        if count == 0:
            return {"count": 0, "mean": None, "max": None, "std": None}

        mean = sum(frp_list) / count
        max_frp = max(frp_list)
        
        if count > 1:
            variance = sum((x - mean) ** 2 for x in frp_list) / (count - 1)
            std = math.sqrt(variance)
        else:
            std = 0.0

        return {
            "count": count,
            "mean": round(mean, 2),
            "max": round(max_frp, 2),
            "std": round(std, 2)
        }

gis_engine = GISEngine()
