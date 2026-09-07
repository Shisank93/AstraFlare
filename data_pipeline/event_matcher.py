"""
AstraFlare Event Matching & Precedence Resolution Engine.
Clusters raw satellite hotspots into physical events (spatial <= 1.5km, temporal <= 24h),
matches independent external events to FIRMS physical clusters, enforces strict label precedence
(VERIFIED_EXTERNAL > MANUAL_VERIFIED > WEAK_RULE > UNLABELED), and handles conflicting evidence.
"""
import os
import sys
import math
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import db_manager
from data_pipeline.gis_engine import haversine_distance_m, parse_iso_timestamp
from data_pipeline.external_ground_truth import (
    STATUS_VERIFIED_EXTERNAL, STATUS_MANUAL_VERIFIED, STATUS_WEAK_RULE, STATUS_CONFLICTING_EVIDENCE
)

logger = logging.getLogger("astraflare.event_matcher")

# Label Precedence Weights
PRECEDENCE_WEIGHTS = {
    STATUS_VERIFIED_EXTERNAL: 100,
    STATUS_MANUAL_VERIFIED: 80,
    STATUS_WEAK_RULE: 40,
    "UNLABELED": 0
}

class EventMatcher:
    def __init__(self, db_mgr=None):
        self.db = db_mgr or db_manager

    def cluster_firms_hotspots(
        self, hotspots: List[Dict[str, Any]], radius_m: float = 1500.0, time_window_hours: float = 24.0
    ) -> List[Dict[str, Any]]:
        """
        Groups raw FIRMS observations into contiguous physical fire/heat event clusters
        using Union-Find spatial-temporal clustering (radius <= 1.5km, time <= 24h).
        Attaches 'physical_event_id' to each hotspot dictionary.
        """
        n = len(hotspots)
        if n == 0:
            return []

        parent = list(range(n))
        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i, root_j = find(i), find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        # Parse acquisition timestamps safely
        timestamps = []
        for h in hotspots:
            ts_val = h.get("acq_timestamp")
            if isinstance(ts_val, datetime):
                timestamps.append(ts_val)
            else:
                timestamps.append(parse_iso_timestamp(str(ts_val)))

        # Spatial grid indexing (cell size = 0.05 deg ~ 5.5km)
        grid = defaultdict(list)
        for idx, h in enumerate(hotspots):
            g_y = int(float(h["latitude"]) / 0.05)
            g_x = int(float(h["longitude"]) / 0.05)
            grid[(g_y, g_x)].append(idx)

        time_window_sec = time_window_hours * 3600.0

        for idx, h in enumerate(hotspots):
            lat_i, lon_i = float(h["latitude"]), float(h["longitude"])
            t_i = timestamps[idx]
            g_y, g_x = int(lat_i / 0.05), int(lon_i / 0.05)

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    for n_idx in grid.get((g_y + dy, g_x + dx), []):
                        if n_idx > idx:
                            t_j = timestamps[n_idx]
                            if abs((t_i - t_j).total_seconds()) <= time_window_sec:
                                dist = haversine_distance_m(lat_i, lon_i, float(hotspots[n_idx]["latitude"]), float(hotspots[n_idx]["longitude"]))
                                if dist <= radius_m:
                                    union(idx, n_idx)

        # Build physical event ID mapping
        cluster_map = defaultdict(list)
        for idx in range(n):
            cluster_map[find(idx)].append(idx)

        # Sort clusters by first timestamp for deterministic event ID naming
        sorted_roots = sorted(cluster_map.keys(), key=lambda r: min(timestamps[i] for i in cluster_map[r]))

        clustered_hotspots = [dict(h) for h in hotspots]
        for cluster_idx, root in enumerate(sorted_roots):
            evt_id = f"evt_cluster_{cluster_idx+1:04d}"
            for member_idx in cluster_map[root]:
                clustered_hotspots[member_idx]["physical_event_id"] = evt_id

        return clustered_hotspots

    def match_external_events_to_firms(
        self,
        firms_hotspots: List[Dict[str, Any]],
        ground_truth_events: List[Dict[str, Any]],
        dist_threshold_m: float = 2000.0,
        time_threshold_hours: float = 24.0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Matches independent external ground-truth events against physical FIRMS clusters.
        Enforces label precedence, records matching distance/time, and detects evidence conflicts.
        """
        self.db.connect()

        # 1. Cluster FIRMS hotspots first
        clustered_firms = self.cluster_firms_hotspots(firms_hotspots)
        
        # Group FIRMS hotspots by physical_event_id
        event_groups = defaultdict(list)
        for h in clustered_firms:
            event_groups[h["physical_event_id"]].append(h)

        matched_records = []
        conflicts = []
        match_stats = {
            "total_firms_hotspots": len(firms_hotspots),
            "total_firms_events": len(event_groups),
            "total_external_events": len(ground_truth_events),
            "matched_firms_events": 0,
            "matched_firms_hotspots": 0,
            "conflicting_events": 0
        }

        # Track external matches per FIRMS physical event
        firms_event_external_matches = defaultdict(list)

        for gt_evt in ground_truth_events:
            gt_lat = float(gt_evt["latitude"])
            gt_lon = float(gt_evt["longitude"])
            gt_ts_str = str(gt_evt["event_timestamp"])
            gt_ts = parse_iso_timestamp(gt_ts_str)

            for phys_evt_id, hs_list in event_groups.items():
                # Find min distance and min time difference to any hotspot in this cluster
                best_dist = float("inf")
                best_time_h = float("inf")
                best_hs = None

                for hs in hs_list:
                    h_lat, h_lon = float(hs["latitude"]), float(hs["longitude"])
                    h_ts = parse_iso_timestamp(str(hs["acq_timestamp"]))
                    
                    dist = haversine_distance_m(gt_lat, gt_lon, h_lat, h_lon)
                    time_h = abs((gt_ts - h_ts).total_seconds()) / 3600.0

                    if dist <= dist_threshold_m and time_h <= time_threshold_hours:
                        if dist < best_dist:
                            best_dist = dist
                            best_time_h = time_h
                            best_hs = hs

                if best_hs is not None:
                    firms_event_external_matches[phys_evt_id].append({
                        "ground_truth_event": gt_evt,
                        "best_hotspot": best_hs,
                        "match_distance_m": round(best_dist, 1),
                        "match_time_hours": round(best_time_h, 2)
                    })

        match_stats["matched_firms_events"] = len(firms_event_external_matches)

        # Apply precedence and conflict resolution per FIRMS observation
        for h in clustered_firms:
            phys_evt_id = h["physical_event_id"]
            ext_matches = firms_event_external_matches.get(phys_evt_id, [])

            if not ext_matches:
                # No independent external match -> Retain existing weak rule or unlabeled status
                h["label_precedence"] = STATUS_WEAK_RULE if h.get("label", "UNLABELED") != "UNLABELED" else "UNLABELED"
                matched_records.append(h)
                continue

            # Check for conflicting event types among external matches (e.g. Fire vs Industrial Incident)
            matched_types = set(m["ground_truth_event"]["event_type"] for m in ext_matches)
            
            if len(matched_types) > 1:
                # CONFLICTING EVIDENCE STATE
                h["label"] = "CONFLICTING_EVIDENCE"
                h["label_source"] = STATUS_CONFLICTING_EVIDENCE
                h["label_confidence"] = 0.0
                h["label_reason"] = f"Conflicting external evidence matches: {list(matched_types)}."
                h["verification_status"] = STATUS_CONFLICTING_EVIDENCE
                h["label_precedence"] = STATUS_CONFLICTING_EVIDENCE
                conflicts.append(h)
                matched_records.append(h)
                continue

            # Single unambiguous external match -> Apply VERIFIED_EXTERNAL label
            top_match = ext_matches[0]
            gt_evt = top_match["ground_truth_event"]

            h["label"] = gt_evt["event_type"]
            h["label_source"] = gt_evt["source_name"]
            h["label_confidence"] = gt_evt.get("source_confidence", 1.0)
            h["label_reason"] = f"Verified by external source {gt_evt['source_name']} ({gt_evt['source_record_id']}). Match dist={top_match['match_distance_m']}m, time={top_match['match_time_hours']}h."
            h["verification_status"] = gt_evt.get("verification_status", STATUS_VERIFIED_EXTERNAL)
            h["source_name"] = gt_evt["source_name"]
            h["source_record_id"] = gt_evt["source_record_id"]
            h["match_distance_m"] = top_match["match_distance_m"]
            h["match_time_hours"] = top_match["match_time_hours"]
            h["label_precedence"] = STATUS_VERIFIED_EXTERNAL

            matched_records.append(h)
            match_stats["matched_firms_hotspots"] += 1

            # Persist match link into event_hotspot_matches table
            hs_id = h.get("hotspot_id") or h.get("id") or "hs_unknown"
            try:
                if self.db.is_postgres:
                    query = """
                    INSERT INTO event_hotspot_matches (
                        event_id, hotspot_id, match_distance_m, match_time_hours, match_confidence
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (event_id, hotspot_id) DO NOTHING;
                    """
                    self.db.execute_query(query, (
                        gt_evt["event_id"], hs_id, top_match["match_distance_m"],
                        top_match["match_time_hours"], gt_evt.get("source_confidence", 1.0)
                    ))
                else:
                    query = """
                    INSERT OR IGNORE INTO event_hotspot_matches (
                        event_id, hotspot_id, match_distance_m, match_time_hours, match_confidence
                    ) VALUES (?, ?, ?, ?, ?);
                    """
                    self.db.execute_query(query, (
                        gt_evt["event_id"], hs_id, top_match["match_distance_m"],
                        top_match["match_time_hours"], gt_evt.get("source_confidence", 1.0)
                    ))
            except Exception as e:
                logger.warning(f"Failed to persist match link for {hs_id}: {e}")

        match_stats["conflicting_events"] = len(conflicts)
        return matched_records, match_stats

event_matcher = EventMatcher()

if __name__ == "__main__":
    print("Testing Event Matcher Engine...")
