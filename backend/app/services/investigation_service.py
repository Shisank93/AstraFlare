"""
AstraFlare Human-in-the-Loop Investigation & Review Workflow Service.
Persists analyst decisions, notes, and corrected classifications in database.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from database.db import db_manager, DatabaseManager
from backend.app.services.hotspot_service import hotspot_service

logger = logging.getLogger("astraflare.backend.services.investigation")

class InvestigationService:
    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db = db_mgr or db_manager

    def submit_review(
        self,
        hotspot_id: str,
        decision: str,
        reviewer_id: str,
        notes: Optional[str] = None,
        corrected_classification: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Persists human analyst review into reviews table with input validation.
        Valid decisions: 'CONFIRMED', 'REJECTED', 'ESCALATED', 'CORRECTED'.
        """
        self.db.connect()

        # Check hotspot exists
        detail = hotspot_service.get_hotspot_detail(hotspot_id)
        if not detail:
            return None

        orig_class = detail.get("classification") or "UNCLASSIFIED"
        review_status = decision.upper()

        if corrected_classification:
            final_class = corrected_classification
        elif decision == "CONFIRMED":
            final_class = orig_class
        else:
            final_class = orig_class

        ph = "%s" if self.db.is_postgres else "?"
        now_iso = datetime.now(timezone.utc).isoformat()

        target_hotspot_fk = hotspot_id if not hotspot_id.startswith("evt_") else None

        # Insert or update review record
        if self.db.is_postgres:
            query = """
            INSERT INTO reviews (event_id, hotspot_id, original_prediction, final_classification, reviewer, decision, review_status, analyst_note, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING review_id, created_at, updated_at;
            """
            res = self.db.execute_query(query, (hotspot_id, target_hotspot_fk, orig_class, final_class, reviewer_id, review_status, review_status, notes or f"Reviewed by {reviewer_id}"))
            review_id = res[0]["review_id"] if res else 1
            created_at = str(res[0]["created_at"]) if res else now_iso
            updated_at = str(res[0]["updated_at"]) if res else now_iso
        else:
            query = """
            INSERT INTO reviews (event_id, hotspot_id, original_prediction, final_classification, reviewer, decision, review_status, analyst_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """
            self.db.execute_query(query, (hotspot_id, target_hotspot_fk, orig_class, final_class, reviewer_id, review_status, review_status, notes or f"Reviewed by {reviewer_id}"))
            rev_res = self.db.execute_query("SELECT MAX(review_id) as max_id FROM reviews;")
            review_id = rev_res[0]["max_id"] if rev_res else 1
            created_at = now_iso
            updated_at = now_iso

        return {
            "review_id": review_id,
            "hotspot_id": hotspot_id,
            "original_prediction": orig_class,
            "final_classification": final_class,
            "review_status": review_status,
            "analyst_note": notes or f"Reviewed by {reviewer_id}",
            "reviewer_id": reviewer_id,
            "created_at": created_at,
            "updated_at": updated_at
        }

    def get_investigation_queue(
        self,
        priority: Optional[str] = None,
        risk_level: Optional[str] = None,
        human_review_required: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        evidence_status: Optional[str] = None,
        data_quality_status: Optional[str] = None,
        data_source: str = "REAL",
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves the analyst's investigation queue.
        Prioritized by URGENT -> HIGH -> MEDIUM -> LOW, and within priority by risk_score DESC.
        """
        self.db.connect()

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

        if start_date:
            conditions.append(f"{ts_col} >= {ph}")
            params.append(start_date)
        if end_date:
            end_val = f"{end_date} 23:59:59" if len(end_date) == 10 else end_date
            conditions.append(f"{ts_col} <= {ph}")
            params.append(end_val)

        if table_name == "events":
            if priority:
                conditions.append(f"investigation_priority = {ph}")
                params.append(priority)
            if risk_level:
                conditions.append(f"risk_level = {ph}")
                params.append(risk_level)
            if human_review_required is not None:
                conditions.append(f"human_review_required = {ph}")
                params.append(bool(human_review_required) if self.db.is_postgres else (1 if human_review_required else 0))
            if evidence_status:
                conditions.append(f"evidence_status = {ph}")
                params.append(evidence_status)
            if data_quality_status:
                conditions.append(f"data_quality_status = {ph}")
                params.append(data_quality_status)

        where_clause = " WHERE " + " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) as cnt FROM {table_name}{where_clause};"
        count_res = self.db.execute_query(count_sql, tuple(params))
        total_records = count_res[0]["cnt"] if count_res else 0

        order_by_clause = """
        ORDER BY CASE investigation_priority
            WHEN 'URGENT' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
            ELSE 5 END ASC, risk_score DESC
        """ if table_name == "events" else "ORDER BY acq_timestamp DESC"

        offset = (max(1, page) - 1) * page_size
        query_sql = f"SELECT * FROM {table_name}{where_clause} {order_by_clause} LIMIT {page_size} OFFSET {offset};"
        records = self.db.execute_query(query_sql, tuple(params))

        items = []
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
                item["priority"] = item.get("investigation_priority") or "LOW"
                item["risk_level"] = item.get("risk_level") or "LOW"
                item["classification"] = "LIKELY_INDUSTRIAL_INCIDENT" if item.get("risk_level") == "HIGH" else "NATURAL_WILDLAND_FIRE"
            items.append(item)

        return items, total_records

    def list_investigations(
        self,
        review_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Lists persisted analyst investigation reviews with status filtering."""
        self.db.connect()

        conditions = []
        params: List[Any] = []
        ph = "%s" if self.db.is_postgres else "?"

        if review_status:
            conditions.append(f"review_status = {ph}")
            params.append(review_status)

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        count_sql = f"SELECT COUNT(*) as cnt FROM reviews{where_clause};"
        count_res = self.db.execute_query(count_sql, tuple(params))
        total_records = count_res[0]["cnt"] if count_res else 0

        offset = (max(1, page) - 1) * page_size
        query_sql = f"SELECT * FROM reviews{where_clause} ORDER BY updated_at DESC LIMIT {page_size} OFFSET {offset};"
        records = self.db.execute_query(query_sql, tuple(params))

        items = []
        for r in records:
            item = dict(r)
            item["created_at"] = str(item["created_at"])
            item["updated_at"] = str(item["updated_at"])
            items.append(item)

        return items, total_records

investigation_service = InvestigationService()
