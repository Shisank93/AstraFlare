"""
AstraFlare Enriched Feature Pipeline.
Unifies NASA FIRMS hotspots, OpenStreetMap industrial context, PostGIS spatial queries,
historical FRP statistics, and ESA WorldCover land-cover into standardized feature records.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import db_manager
from data_pipeline.gis_engine import gis_engine, calculate_frp_anomaly_score
from data_pipeline.osm_ingestion import osm_client
from data_pipeline.landcover_engine import landcover_engine

logger = logging.getLogger("astraflare.feature_pipeline")

class FeaturePipeline:
    def __init__(self):
        self.gis = gis_engine
        self.osm = osm_client
        self.landcover = landcover_engine

    def enrich_hotspot(self, hotspot: Dict[str, Any], mock_fallback: bool = True, skip_network: bool = False) -> Dict[str, Any]:
        """
        Enriches a raw or persisted hotspot dictionary with spatial, industrial, historical, and land-cover context.
        Conforms strictly to the AstraFlare Feature Output Contract.
        """
        hotspot_id = hotspot.get("id") or "hs_temp"
        lat = float(hotspot["latitude"])
        lon = float(hotspot["longitude"])
        frp = float(hotspot["frp"])
        data_source = hotspot.get("data_source", "REAL")

        context_issues = []

        # 1. Industrial Proximity & Site Ingestion Cache Check
        try:
            # Ensure contextual OSM features exist in local PostGIS cache if network enabled
            if not skip_network:
                self.osm.ingest_contextual_osm(lat, lon, radius_m=5000.0, mock_fallback=mock_fallback)
            nearest_site, dist_ind_m = self.gis.get_nearest_industrial_site(lat, lon, max_distance_m=10000.0)
            nearest_name = nearest_site.get("name") if nearest_site else None
        except Exception as e:
            logger.warning(f"OSM Context enrichment error for {hotspot_id}: {e}")
            nearest_site, dist_ind_m, nearest_name = None, 10000.0, None
            context_issues.append("OSM_UNAVAILABLE")

        # 2. Multi-Radius Industrial Counts
        try:
            count_250m = self.gis.count_industrial_sites_in_radius(lat, lon, radius_m=250.0)
            count_500m = self.gis.count_industrial_sites_in_radius(lat, lon, radius_m=500.0)
            count_1000m = self.gis.count_industrial_sites_in_radius(lat, lon, radius_m=1000.0)
        except Exception as e:
            logger.warning(f"Industrial radius count error for {hotspot_id}: {e}")
            count_250m, count_500m, count_1000m = 0, 0, 0
            context_issues.append("RADIUS_COUNT_ERROR")

        # 3. Historical Recurrence & FRP Baseline Statistics (Excluding current hotspot)
        try:
            hist_30d = self.gis.get_historical_hotspot_recurrence(lat, lon, time_window_days=30, radius_m=1000.0)
            hist_stats = self.gis.get_historical_frp_stats(
                lat, lon, time_window_days=365, radius_m=1000.0, exclude_hotspot_id=hotspot_id
            )
            hist_365d = hist_stats["count"]
            hist_mean = hist_stats["mean"]
            hist_max = hist_stats["max"]
            hist_std = hist_stats["std"]
            
            # Anomaly Z-Score Calculation with Safeguards
            anomaly_res = calculate_frp_anomaly_score(frp, hist_stats)
            anomaly_score = anomaly_res["anomaly_score"]
            anomaly_status = anomaly_res["status"]
        except Exception as e:
            logger.warning(f"Historical feature extraction error for {hotspot_id}: {e}")
            hist_30d, hist_365d, hist_mean, hist_max, hist_std = 0, 0, None, None, None
            anomaly_score, anomaly_status = None, "ERROR"
            context_issues.append("HISTORICAL_STATS_ERROR")

        # 4. ESA WorldCover Land-Cover Context
        try:
            lc_res = self.landcover.get_land_cover_class(lat, lon)
            land_cover_class = lc_res["class_name"]
            land_cover_code = lc_res["class_code"]
            land_cover_category = lc_res["category"]
        except Exception as e:
            logger.warning(f"Land cover sampling error for {hotspot_id}: {e}")
            land_cover_class = "Unknown / Unmapped"
            land_cover_code = 40
            land_cover_category = "unknown"
            context_issues.append("LANDCOVER_UNAVAILABLE")

        # Determine Data Quality Tag
        if not context_issues:
            data_quality = "COMPLETE"
        elif len(context_issues) < 3:
            data_quality = "PARTIAL_CONTEXT"
        else:
            data_quality = "RAW_OBSERVATION"

        # Construct Final Standardized Feature Record
        return {
            "hotspot_id": hotspot_id,
            "firms_id": hotspot.get("firms_id") or hotspot_id,
            "latitude": lat,
            "longitude": lon,
            "frp": frp,
            "brightness": float(hotspot.get("brightness") or 0.0),
            "confidence": hotspot.get("confidence", "nominal"),
            "satellite": hotspot.get("satellite", "VIIRS"),
            "acq_timestamp": hotspot.get("acq_timestamp"),
            "industrial_distance": dist_ind_m,
            "industrial_distance_m": dist_ind_m,
            "nearest_industrial_name": nearest_name,
            "industrial_site_count_250m": count_250m,
            "industrial_site_count_500m": count_500m,
            "industrial_site_count_1000m": count_1000m,
            "industrial_count_1km": count_1000m,
            "historical_count_30d": hist_30d,
            "historical_count_365d": hist_365d,
            "historical_mean_frp": hist_mean,
            "historical_max_frp": hist_max,
            "historical_std_frp": hist_std,
            "frp_anomaly_score": anomaly_score,
            "frp_anomaly_status": anomaly_status,
            "land_cover_class": land_cover_class,
            "land_cover_code": land_cover_code,
            "land_cover_category": land_cover_category,
            "data_source": data_source,
            "data_quality": data_quality
        }

feature_pipeline = FeaturePipeline()

if __name__ == "__main__":
    print("Testing Enriched Feature Pipeline...")
    sample_hs = {
        "id": "hs_test_feature_01",
        "latitude": 22.3088,
        "longitude": 73.1825,
        "frp": 145.0,
        "brightness": 365.2,
        "satellite": "VIIRS_SNPP",
        "acq_timestamp": "2026-09-04T14:15:00Z",
        "data_source": "MOCK"
    }
    feature_record = feature_pipeline.enrich_hotspot(sample_hs, mock_fallback=True)
    print("Enriched Feature Record Output:")
    for k, v in feature_record.items():
        print(f"  {k}: {v}")
