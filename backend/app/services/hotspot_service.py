"""
AstraFlare Hotspot Query & Data Service.
Handles database filtering, pagination, detail assembly, historical context, and GeoJSON formatting.
"""
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from database.db import db_manager, DatabaseManager
from backend.app.config import settings
from data_pipeline.gis_engine import gis_engine, haversine_distance_m
from data_pipeline.landcover_engine import landcover_engine
from data_pipeline.feature_pipeline import feature_pipeline
from ml.labeling import construct_weak_label

logger = logging.getLogger("astraflare.backend.services.hotspot")

class HotspotService:
    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db = db_mgr or db_manager

    def get_hotspots(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        bbox: Optional[str] = None,
        min_frp: Optional[float] = None,
        max_frp: Optional[float] = None,
        confidence: Optional[str] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        priority: Optional[str] = None,
        review_required: Optional[bool] = None,
        data_quality_status: Optional[str] = None,
        evidence_status: Optional[str] = None,
        worldcover_class: Optional[int] = None,
        near_industry: Optional[bool] = None,
        satellite: Optional[str] = None,
        data_source: str = "REAL",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Queries events/hotspots table with dynamic SQL filtering, PostGIS spatial indexing, and pagination."""
        self.db.connect()

        # Parse bbox if provided (minLon,minLat,maxLon,maxLat)
        if bbox:
            try:
                parts = [float(p.strip()) for p in bbox.split(",")]
                if len(parts) == 4:
                    min_lon, min_lat, max_lon, max_lat = parts[0], parts[1], parts[2], parts[3]
            except ValueError:
                logger.warning(f"Invalid bbox parameter format: '{bbox}'")

        # Determine target table: 'events' table if populated, otherwise 'hotspots'
        table_name = "events"
        try:
            check_res = self.db.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name};")
            if not check_res or check_res[0]["cnt"] == 0:
                table_name = "hotspots"
        except Exception:
            table_name = "hotspots"

        ph = "%s" if self.db.is_postgres else "?"
        conditions = [f"data_source = {ph}"]
        params: List[Any] = [data_source]

        ts_col = "event_timestamp" if table_name == "events" else "acq_timestamp"
        lat_col = "centroid_lat" if table_name == "events" else "latitude"
        lon_col = "centroid_lon" if table_name == "events" else "longitude"
        frp_col = "max_frp" if table_name == "events" else "frp"

        if start_date:
            conditions.append(f"{ts_col} >= {ph}")
            params.append(start_date)
        if end_date:
            end_val = f"{end_date} 23:59:59" if len(end_date) == 10 else end_date
            conditions.append(f"{ts_col} <= {ph}")
            params.append(end_val)

        if self.db.is_postgres and self.db.has_postgis and min_lon is not None and min_lat is not None and max_lon is not None and max_lat is not None:
            conditions.append("ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))")
            params.extend([min_lon, min_lat, max_lon, max_lat])
        else:
            if min_lat is not None:
                conditions.append(f"{lat_col} >= {ph}")
                params.append(min_lat)
            if max_lat is not None:
                conditions.append(f"{lat_col} <= {ph}")
                params.append(max_lat)
            if min_lon is not None:
                conditions.append(f"{lon_col} >= {ph}")
                params.append(min_lon)
            if max_lon is not None:
                conditions.append(f"{lon_col} <= {ph}")
                params.append(max_lon)

        if min_frp is not None:
            conditions.append(f"{frp_col} >= {ph}")
            params.append(min_frp)
        if max_frp is not None:
            conditions.append(f"{frp_col} <= {ph}")
            params.append(max_frp)

        if table_name == "events":
            if risk_level:
                conditions.append(f"risk_level = {ph}")
                params.append(risk_level)
            if priority:
                conditions.append(f"investigation_priority = {ph}")
                params.append(priority)
            if review_required is not None:
                conditions.append(f"human_review_required = {ph}")
                params.append(bool(review_required) if self.db.is_postgres else (1 if review_required else 0))
            if data_quality_status:
                conditions.append(f"data_quality_status = {ph}")
                params.append(data_quality_status)
            if evidence_status:
                conditions.append(f"evidence_status = {ph}")
                params.append(evidence_status)
            if worldcover_class is not None:
                conditions.append(f"worldcover_class = {ph}")
                params.append(worldcover_class)
            if near_industry:
                conditions.append(f"industrial_distance_m <= {ph}")
                params.append(1000.0)
        else:
            if confidence:
                conditions.append(f"confidence = {ph}")
                params.append(confidence)
            if satellite:
                conditions.append(f"satellite = {ph}")
                params.append(satellite)

        where_clause = " WHERE " + " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) as cnt FROM {table_name}{where_clause};"
        count_res = self.db.execute_query(count_sql, tuple(params))
        total_records = count_res[0]["cnt"] if count_res else 0

        offset = (max(1, page) - 1) * page_size
        query_sql = f"SELECT * FROM {table_name}{where_clause} ORDER BY {ts_col} DESC LIMIT {page_size} OFFSET {offset};"
        records = self.db.execute_query(query_sql, tuple(params))

        enriched_items = []
        for r in records:
            item = dict(r)
            if "event_id" in item:
                item["id"] = item["event_id"]
                item["latitude"] = float(item.get("centroid_lat") or 0.0)
                item["longitude"] = float(item.get("centroid_lon") or 0.0)
                item["acq_timestamp"] = str(item.get("event_timestamp", ""))
                item["satellite"] = item.get("satellite") or "VIIRS"
                item["frp"] = float(item.get("max_frp") or 0.0)
                item["data_source"] = item.get("data_source") or "REAL"
                item["review_required"] = bool(item.get("human_review_required"))
                item["risk_level"] = item.get("risk_level") or "LOW"
                item["priority"] = item.get("investigation_priority") or "LOW"
                item["classification"] = "LIKELY_INDUSTRIAL_INCIDENT" if item.get("risk_level") == "HIGH" else "NATURAL_WILDLAND_FIRE"
            else:
                item["acq_timestamp"] = str(item["acq_timestamp"])
                lat, lon = float(item["latitude"]), float(item["longitude"])
                near_site, dist_m = gis_engine.get_nearest_industrial_site(lat, lon, max_distance_m=5000.0)
                feat_dict = {
                    "industrial_distance_m": dist_m,
                    "frp": float(item.get("frp", 0.0)),
                    "daynight_is_day": 1 if item.get("daynight") == "D" else 0
                }
                lbl_meta = construct_weak_label(feat_dict)
                item["classification"] = lbl_meta["label"]
                item["prediction_confidence"] = lbl_meta["label_confidence"]
                item["review_required"] = lbl_meta["label_confidence"] < settings.HUMAN_REVIEW_THRESHOLD
                frp = float(item.get("frp", 0.0))
                if dist_m <= 1000.0 or frp > 100.0:
                    item["risk_level"] = "HIGH"
                    item["priority"] = "HIGH"
                elif dist_m <= 3000.0 or frp > 30.0:
                    item["risk_level"] = "MEDIUM"
                    item["priority"] = "MEDIUM"
                else:
                    item["risk_level"] = "LOW"
                    item["priority"] = "LOW"

            enriched_items.append(item)

        if table_name == "hotspots":
            if classification:
                enriched_items = [x for x in enriched_items if x["classification"] == classification]
            if risk_level:
                enriched_items = [x for x in enriched_items if x["risk_level"] == risk_level]
            if review_required is not None:
                enriched_items = [x for x in enriched_items if x["review_required"] == review_required]

        return enriched_items, total_records

    def get_hotspot_detail(self, hotspot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full investigation-oriented detail object for a single hotspot."""
        self.db.connect()
        ph = "%s" if self.db.is_postgres else "?"
        res = self.db.execute_query(f"SELECT * FROM hotspots WHERE id = {ph};", (hotspot_id,))
        if not res:
            try:
                evt_res = self.db.execute_query(f"SELECT * FROM events WHERE event_id = {ph};", (hotspot_id,))
                if evt_res:
                    evt = dict(evt_res[0])
                    evt["id"] = evt["event_id"]
                    evt["latitude"] = float(evt.get("centroid_lat") or 0.0)
                    evt["longitude"] = float(evt.get("centroid_lon") or 0.0)
                    evt["acq_timestamp"] = str(evt.get("event_timestamp", ""))
                    evt["satellite"] = "VIIRS"
                    evt["frp"] = float(evt.get("max_frp") or 0.0)
                    evt["brightness"] = float(evt.get("max_brightness") or 300.0)
                    return evt
            except Exception as e:
                logger.warning(f"Events table query error: {e}")
            return None

        hs = dict(res[0])
        hs["acq_timestamp"] = str(hs["acq_timestamp"])

        # Run feature pipeline enrichment
        enriched = feature_pipeline.enrich_hotspot(hs, mock_fallback=False, skip_network=True)
        
        # Merge enriched fields
        hs["nearest_industrial_name"] = enriched.get("nearest_industrial_name")
        hs["industrial_distance_m"] = float(enriched.get("industrial_distance_m") or enriched.get("industrial_distance") or 10000.0)
        hs["industrial_count_1km"] = int(enriched.get("industrial_count_1km") or enriched.get("industrial_site_count_1000m") or 0)
        hs["industrial_count_5km"] = int(enriched.get("industrial_count_5km") or 0)
        hs["land_cover_code"] = int(enriched.get("land_cover_code") or 40)
        hs["land_cover_name"] = str(enriched.get("land_cover_name") or "Cropland")
        hs["historical_count_30d"] = int(enriched.get("historical_count_30d") or 0)
        hs["historical_mean_frp"] = enriched.get("historical_mean_frp")
        hs["frp_anomaly_zscore"] = enriched.get("frp_anomaly_score")
        hs["anomaly_status"] = str(enriched.get("anomaly_status") or "VALID")

        # Weak label construction
        feat_dict = {
            "industrial_distance_m": hs["industrial_distance_m"],
            "industrial_count_1km": hs["industrial_count_1km"],
            "frp": float(hs.get("frp", 0.0)),
            "historical_count_30d": hs["historical_count_30d"],
            "daynight_is_day": 1 if hs.get("daynight") == "D" else 0
        }
        lbl_meta = construct_weak_label(feat_dict)
        hs["classification"] = lbl_meta["label"]
        hs["prediction_confidence"] = lbl_meta["label_confidence"]
        hs["review_required"] = lbl_meta["label_confidence"] < settings.HUMAN_REVIEW_THRESHOLD
        hs["verification_status"] = lbl_meta.get("verification_status", "WEAK_RULE")

        # Risk score calculation
        dist_m = hs["industrial_distance_m"]
        frp = float(hs.get("frp", 0.0))
        if dist_m <= 1000.0 or frp > 100.0:
            hs["risk_level"] = "HIGH"
        elif dist_m <= 3000.0 or frp > 30.0:
            hs["risk_level"] = "MEDIUM"
        else:
            hs["risk_level"] = "LOW"

        # Query reviews table for persisted analyst review status
        rev_res = self.db.execute_query(f"SELECT final_classification, review_status FROM reviews WHERE hotspot_id = {ph} ORDER BY updated_at DESC LIMIT 1;", (hotspot_id,))
        if rev_res:
            hs["review_status"] = rev_res[0]["review_status"]
            if rev_res[0].get("final_classification"):
                hs["classification"] = rev_res[0]["final_classification"]
        else:
            hs["review_status"] = "PENDING"

        return hs

    def get_hotspots_geojson(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        bbox: Optional[str] = None,
        min_frp: Optional[float] = None,
        max_frp: Optional[float] = None,
        risk_level: Optional[str] = None,
        priority: Optional[str] = None,
        review_required: Optional[bool] = None,
        data_source: str = "REAL",
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Generates RFC 7946 compliant GeoJSON FeatureCollection.
        CRITICAL RULE: GeoJSON coordinates MUST BE [longitude, latitude].
        Supports PostGIS spatial bounding box (bbox) filtering.
        """
        items, _ = self.get_hotspots(
            start_date=start_date, end_date=end_date,
            min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
            bbox=bbox, min_frp=min_frp, max_frp=max_frp,
            risk_level=risk_level, priority=priority, review_required=review_required,
            data_source=data_source, page=1, page_size=limit
        )
        
        features = []
        for item in items:
            lat = float(item["latitude"])
            lon = float(item["longitude"])

            # RFC 7946 strictly requires coordinates: [longitude, latitude]
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": item
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }

    def get_hotspot_history(self, hotspot_id: str) -> Dict[str, Any]:
        """Returns historical context and recurrence telemetry around target hotspot."""
        self.db.connect()
        hs_detail = self.get_hotspot_detail(hotspot_id)
        if not hs_detail:
            return {"hotspot_id": hotspot_id, "found": False, "history": []}

        lat, lon = float(hs_detail["latitude"]), float(hs_detail["longitude"])
        stats = gis_engine.get_historical_frp_stats(lat, lon, time_window_days=365, radius_m=1000.0, exclude_hotspot_id=hotspot_id)

        # Query past nearby hotspots
        ph = "%s" if self.db.is_postgres else "?"
        nearby = self.db.execute_query(
            f"SELECT id, acq_timestamp, frp, satellite FROM hotspots WHERE id != {ph} AND data_source = 'REAL' ORDER BY acq_timestamp DESC LIMIT 20;",
            (hotspot_id,)
        )

        history_items = []
        for n in nearby:
            n_lat, n_lon = float(n.get("latitude") or lat), float(n.get("longitude") or lon)
            dist = haversine_distance_m(lat, lon, n_lat, n_lon)
            if dist <= 1000.0:
                history_items.append({
                    "id": n["id"],
                    "acq_timestamp": str(n["acq_timestamp"]),
                    "frp": float(n["frp"]),
                    "satellite": n["satellite"],
                    "distance_m": round(dist, 1)
                })

        return {
            "hotspot_id": hotspot_id,
            "target_timestamp": hs_detail["acq_timestamp"],
            "recurrence_count_30d": hs_detail.get("historical_count_30d", 0),
            "historical_mean_frp": stats.get("mean"),
            "historical_max_frp": stats.get("max"),
            "historical_std_frp": stats.get("std"),
            "frp_anomaly_zscore": hs_detail.get("frp_anomaly_zscore"),
            "anomaly_status": hs_detail.get("anomaly_status", "VALID"),
            "nearby_historical_detections": history_items
        }

hotspot_service = HotspotService()
