"""
Phase 3.11.1 Real India Population Risk Validation Script.
Applies EvidenceRiskEngine to the complete 4,310,499 physical event population (DATASET_C_ALL_EVENTS.csv)
and exports metrics, distributions, cross-checks, edge case audits, and charts to docs/ai/phase_3_11_1/.
"""
import os
import sys
import time
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from typing import Dict, Any, List
from backend.risk_engine.engine import EvidenceRiskEngine
from backend.risk_engine.models import RiskInput

DATASET_DIR = "data/processed/event_dataset"
ALL_EVENTS_PATH = os.path.join(DATASET_DIR, "DATASET_C_ALL_EVENTS.csv")
VERIFIED_EXT_PATH = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")
PERSISTENT_REF_PATH = os.path.join(DATASET_DIR, "DATASET_C_PERSISTENT_REFERENCE.csv")
WILDFIRE_REF_PATH = os.path.join(DATASET_DIR, "DATASET_C_WILDFIRE_REFERENCE.csv")

OUTPUT_DIR = "docs/ai/phase_3_11_1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_val(val, default, cast_type):
    if pd.isna(val) or val is None:
        return default
    try:
        return cast_type(val)
    except:
        return default

def main():
    print("=== AstraFlare Phase 3.11.1 Real Population Risk Validation ===", flush=True)
    t_start = time.time()

    if not os.path.exists(ALL_EVENTS_PATH):
        raise FileNotFoundError(f"Dataset not found at {ALL_EVENTS_PATH}")

    engine = EvidenceRiskEngine()

    print(f"Reading dataset: {ALL_EVENTS_PATH}", flush=True)
    chunksize = 200000
    total_rows = 0
    
    risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    priorities = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "URGENT": 0}
    review_req = {"TRUE": 0, "FALSE": 0}
    evidence_statuses = {}
    likely_contexts = {}
    history_statuses = {}
    data_quality_statuses = {}

    arr_risk = []
    arr_thermal = []
    arr_historical = []
    arr_industrial = []
    arr_natural = []
    arr_recurrence = []
    arr_persistence = []
    arr_quality = []

    frp_buckets = {
        "<10": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        "10-25": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        "25-50": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        "50-100": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        "100-250": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        "250-500": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
        ">500": {"count": 0, "risk_sum": 0.0, "high_cnt": 0},
    }

    dist_bands = {
        "<=250m": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "250-500m": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "500-1000m": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "1-2km": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "2-5km": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        ">5km": {"count": 0, "ind_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
    }

    hist_bands = {
        "NO_HISTORY": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "INSUFFICIENT_DATA": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "Z < 1": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "1 <= Z < 2": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "2 <= Z < 3": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
        "Z >= 3": {"count": 0, "hist_sum": 0.0, "risk_sum": 0.0, "high_cnt": 0, "review_cnt": 0},
    }

    land_cover_stats = {}

    priority_vs_risk = {
        p: {r: 0 for r in ["LOW", "MEDIUM", "HIGH"]}
        for p in ["LOW", "MEDIUM", "HIGH", "URGENT"]
    }

    review_by_risk = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    review_by_evidence = {}
    review_by_context = {}
    review_by_quality = {}
    review_reasons_counter = {}

    top_100_candidates = []

    case_study_candidates = {
        "HIGH_RISK_INDUSTRIAL": None,
        "HIGH_RISK_NATURAL": None,
        "PERSISTENT_INDUSTRIAL": None,
        "CONFLICTING_EVIDENCE": None,
        "LOW_RISK_ROUTINE": None,
        "HIGH_FRP": None,
        "HIGH_HISTORICAL_ANOMALY": None,
        "NO_HISTORY": None
    }

    total_obs_sum = 0
    date_min = None
    date_max = None
    lat_min, lat_max = 999.0, -999.0
    lon_min, lon_max = 999.0, -999.0

    print("Beginning fast chunked risk engine execution over 4.31M events...", flush=True)

    cols_needed = [
        'event_id', 'event_start', 'event_end', 'duration_hours', 'observation_count',
        'centroid_lat', 'centroid_lon', 'max_frp', 'mean_frp', 'std_frp',
        'max_brightness', 'mean_brightness', 'confidence_high_ratio', 'satellite_count',
        'industrial_distance_m', 'industrial_site_count_250m', 'industrial_site_count_1km',
        'industrial_site_count_5km', 'worldcover_class'
    ]
    
    for chunk_idx, chunk in enumerate(pd.read_csv(ALL_EVENTS_PATH, chunksize=chunksize, usecols=cols_needed)):
        t_chunk = time.time()
        chunk_len = len(chunk)
        total_rows += chunk_len
        total_obs_sum += int(chunk["observation_count"].sum())

        c_lat = chunk["centroid_lat"]
        c_lon = chunk["centroid_lon"]
        lat_min = min(lat_min, float(c_lat.min()))
        lat_max = max(lat_max, float(c_lat.max()))
        lon_min = min(lon_min, float(c_lon.min()))
        lon_max = max(lon_max, float(c_lon.max()))

        s_min = str(chunk["event_start"].min())
        s_max = str(chunk["event_start"].max())
        if date_min is None or s_min < date_min: date_min = s_min
        if date_max is None or s_max > date_max: date_max = s_max

        records = chunk.to_dict('records')
        for r in records:
            event_id = str(r['event_id'])
            max_frp = clean_val(r.get('max_frp'), 0.0, float)
            mean_frp = clean_val(r.get('mean_frp'), None, float)
            std_frp = clean_val(r.get('std_frp'), None, float)
            max_bright = clean_val(r.get('max_brightness'), None, float)
            mean_bright = clean_val(r.get('mean_brightness'), None, float)
            obs_cnt = clean_val(r.get('observation_count'), 1, int)
            dur_hrs = clean_val(r.get('duration_hours'), 0.0, float)
            conf_hi = clean_val(r.get('confidence_high_ratio'), 0.0, float)
            sat_cnt = clean_val(r.get('satellite_count'), 1, int)
            ind_dist = clean_val(r.get('industrial_distance_m'), 10000.0, float)
            ind_250m = clean_val(r.get('industrial_site_count_250m'), 0, int)
            ind_1km = clean_val(r.get('industrial_site_count_1km'), 0, int)
            ind_5km = clean_val(r.get('industrial_site_count_5km'), 0, int)
            wc_cls = str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown"
            c_lat_v = clean_val(r.get('centroid_lat'), 0.0, float)
            c_lon_v = clean_val(r.get('centroid_lon'), 0.0, float)
            ev_start = str(r['event_start']) if pd.notna(r.get('event_start')) else None
            ev_end = str(r['event_end']) if pd.notna(r.get('event_end')) else None

            inp = RiskInput(
                event_id=event_id,
                max_frp=max_frp,
                mean_frp=mean_frp,
                std_frp=std_frp,
                max_brightness=max_bright,
                mean_brightness=mean_bright,
                observation_count=obs_cnt,
                duration_hours=dur_hrs,
                confidence_high_ratio=conf_hi,
                satellite_count=sat_cnt,
                industrial_distance_m=ind_dist,
                industrial_site_count_250m=ind_250m,
                industrial_site_count_1km=ind_1km,
                industrial_site_count_5km=ind_5km,
                worldcover_class=wc_cls,
                centroid_lat=c_lat_v,
                centroid_lon=c_lon_v,
                event_start=ev_start,
                event_end=ev_end
            )

            res = engine.assess_event(inp)

            r_score = res.overall_risk_score
            r_level = res.risk_level
            p_level = res.investigation_priority
            e_status = res.evidence_status
            l_context = res.likely_context
            h_status = res.history_status
            q_status = res.data_quality_status
            rev_req = res.human_review_required

            arr_risk.append(r_score)
            arr_thermal.append(res.thermal_anomaly_score)
            arr_historical.append(res.historical_anomaly_score)
            arr_industrial.append(res.industrial_context_score)
            arr_natural.append(res.natural_fire_context_score)
            arr_recurrence.append(res.recurrence_score)
            arr_persistence.append(res.persistence_score)
            arr_quality.append(res.data_quality_score)

            risk_levels[r_level] += 1
            priorities[p_level] += 1
            priority_vs_risk[p_level][r_level] += 1

            evidence_statuses[e_status] = evidence_statuses.get(e_status, 0) + 1
            likely_contexts[l_context] = likely_contexts.get(l_context, 0) + 1
            history_statuses[h_status] = history_statuses.get(h_status, 0) + 1
            data_quality_statuses[q_status] = data_quality_statuses.get(q_status, 0) + 1

            if rev_req:
                review_req["TRUE"] += 1
                review_by_risk[r_level] += 1
                review_by_evidence[e_status] = review_by_evidence.get(e_status, 0) + 1
                review_by_context[l_context] = review_by_context.get(l_context, 0) + 1
                review_by_quality[q_status] = review_by_quality.get(q_status, 0) + 1
                for reason in res.human_review_reasons:
                    review_reasons_counter[reason] = review_reasons_counter.get(reason, 0) + 1
            else:
                review_req["FALSE"] += 1

            # FRP bucketing
            if max_frp < 10: b_key = "<10"
            elif max_frp < 25: b_key = "10-25"
            elif max_frp < 50: b_key = "25-50"
            elif max_frp < 100: b_key = "50-100"
            elif max_frp < 250: b_key = "100-250"
            elif max_frp < 500: b_key = "250-500"
            else: b_key = ">500"

            frp_buckets[b_key]["count"] += 1
            frp_buckets[b_key]["risk_sum"] += r_score
            if r_level == "HIGH": frp_buckets[b_key]["high_cnt"] += 1

            # Distance bucketing
            if ind_dist <= 250: d_key = "<=250m"
            elif ind_dist <= 500: d_key = "250-500m"
            elif ind_dist <= 1000: d_key = "500-1000m"
            elif ind_dist <= 2000: d_key = "1-2km"
            elif ind_dist <= 5000: d_key = "2-5km"
            else: d_key = ">5km"

            dist_bands[d_key]["count"] += 1
            dist_bands[d_key]["ind_sum"] += res.industrial_context_score
            dist_bands[d_key]["risk_sum"] += r_score
            if r_level == "HIGH": dist_bands[d_key]["high_cnt"] += 1
            if rev_req: dist_bands[d_key]["review_cnt"] += 1

            # Historical anomaly bucketing
            if h_status == "NO_PRIOR_HISTORY": h_key = "NO_HISTORY"
            elif h_status == "LIMITED_HISTORY": h_key = "INSUFFICIENT_DATA"
            else:
                z_val = inp.frp_anomaly_z if inp.frp_anomaly_z is not None else 0.0
                if z_val < 1.0: h_key = "Z < 1"
                elif z_val < 2.0: h_key = "1 <= Z < 2"
                elif z_val < 3.0: h_key = "2 <= Z < 3"
                else: h_key = "Z >= 3"

            hist_bands[h_key]["count"] += 1
            hist_bands[h_key]["hist_sum"] += res.historical_anomaly_score
            hist_bands[h_key]["risk_sum"] += r_score
            if r_level == "HIGH": hist_bands[h_key]["high_cnt"] += 1
            if rev_req: hist_bands[h_key]["review_cnt"] += 1

            # Land cover stats
            if wc_cls not in land_cover_stats:
                land_cover_stats[wc_cls] = {"count": 0, "risk_sum": 0.0, "nat_sum": 0.0, "ind_sum": 0.0, "high_cnt": 0}
            land_cover_stats[wc_cls]["count"] += 1
            land_cover_stats[wc_cls]["risk_sum"] += r_score
            land_cover_stats[wc_cls]["nat_sum"] += res.natural_fire_context_score
            land_cover_stats[wc_cls]["ind_sum"] += res.industrial_context_score
            if r_level == "HIGH": land_cover_stats[wc_cls]["high_cnt"] += 1

            # Top 100 track
            if len(top_100_candidates) < 100 or r_score > top_100_candidates[-1]["overall_risk_score"]:
                top_100_candidates.append({
                    "event_id": inp.event_id,
                    "event_start": inp.event_start,
                    "lat": inp.centroid_lat,
                    "lon": inp.centroid_lon,
                    "max_frp": inp.max_frp,
                    "industrial_distance_m": inp.industrial_distance_m,
                    "industrial_site_count_250m": inp.industrial_site_count_250m,
                    "historical_anomaly_z": inp.frp_anomaly_z,
                    "recurrence_score": res.recurrence_score,
                    "worldcover_class": inp.worldcover_class,
                    "overall_risk_score": r_score,
                    "risk_level": r_level,
                    "investigation_priority": p_level,
                    "evidence_status": e_status,
                    "likely_context": l_context,
                    "human_review_required": rev_req,
                    "data_quality_status": q_status
                })
                top_100_candidates.sort(key=lambda x: x["overall_risk_score"], reverse=True)
                top_100_candidates = top_100_candidates[:100]

            # Case studies capture
            if case_study_candidates["HIGH_RISK_INDUSTRIAL"] is None and l_context == "INDUSTRIAL_CONTEXT" and r_level == "HIGH" and not rev_req:
                case_study_candidates["HIGH_RISK_INDUSTRIAL"] = (inp.dict(), res.dict())
            if case_study_candidates["HIGH_RISK_NATURAL"] is None and l_context == "NATURAL_FIRE_CONTEXT" and r_level == "HIGH":
                case_study_candidates["HIGH_RISK_NATURAL"] = (inp.dict(), res.dict())
            if case_study_candidates["PERSISTENT_INDUSTRIAL"] is None and e_status == "PERSISTENT_INDUSTRIAL_CONTEXT":
                case_study_candidates["PERSISTENT_INDUSTRIAL"] = (inp.dict(), res.dict())
            if case_study_candidates["CONFLICTING_EVIDENCE"] is None and e_status == "CONFLICTING_EVIDENCE":
                case_study_candidates["CONFLICTING_EVIDENCE"] = (inp.dict(), res.dict())
            if case_study_candidates["LOW_RISK_ROUTINE"] is None and r_level == "LOW" and e_status == "UNUSUAL_THERMAL_ACTIVITY":
                case_study_candidates["LOW_RISK_ROUTINE"] = (inp.dict(), res.dict())
            if case_study_candidates["HIGH_FRP"] is None and inp.max_frp > 300.0:
                case_study_candidates["HIGH_FRP"] = (inp.dict(), res.dict())
            if case_study_candidates["HIGH_HISTORICAL_ANOMALY"] is None and inp.frp_anomaly_z is not None and inp.frp_anomaly_z > 3.0:
                case_study_candidates["HIGH_HISTORICAL_ANOMALY"] = (inp.dict(), res.dict())
            if case_study_candidates["NO_HISTORY"] is None and h_status == "NO_PRIOR_HISTORY":
                case_study_candidates["NO_HISTORY"] = (inp.dict(), res.dict())

        dt_chunk = time.time() - t_chunk
        print(f"Chunk {chunk_idx+1}: processed {chunk_len} rows in {dt_chunk:.2f}s (Total: {total_rows}/{4310499})", flush=True)

    t_eval = time.time() - t_start
    print(f"\nCompleted risk engine assessment on all {total_rows} events in {t_eval:.2f}s ({total_rows/t_eval:.1f} ev/s)", flush=True)

    arr_risk = np.array(arr_risk, dtype=np.float32)
    arr_thermal = np.array(arr_thermal, dtype=np.float32)
    arr_historical = np.array(arr_historical, dtype=np.float32)
    arr_industrial = np.array(arr_industrial, dtype=np.float32)
    arr_natural = np.array(arr_natural, dtype=np.float32)
    arr_recurrence = np.array(arr_recurrence, dtype=np.float32)
    arr_persistence = np.array(arr_persistence, dtype=np.float32)
    arr_quality = np.array(arr_quality, dtype=np.float32)

    def calc_stats(arr):
        return {
            "min": round(float(np.min(arr)), 4),
            "max": round(float(np.max(arr)), 4),
            "mean": round(float(np.mean(arr)), 4),
            "median": round(float(np.median(arr)), 4),
            "std": round(float(np.std(arr)), 4),
            "P5": round(float(np.percentile(arr, 5)), 4),
            "P10": round(float(np.percentile(arr, 10)), 4),
            "P25": round(float(np.percentile(arr, 25)), 4),
            "P50": round(float(np.percentile(arr, 50)), 4),
            "P75": round(float(np.percentile(arr, 75)), 4),
            "P90": round(float(np.percentile(arr, 90)), 4),
            "P95": round(float(np.percentile(arr, 95)), 4),
            "P99": round(float(np.percentile(arr, 99)), 4),
            "P99.9": round(float(np.percentile(arr, 99.9)), 4)
        }

    risk_stats = calc_stats(arr_risk)
    thermal_stats = calc_stats(arr_thermal)
    hist_stats = calc_stats(arr_historical)
    ind_stats = calc_stats(arr_industrial)
    nat_stats = calc_stats(arr_natural)
    rec_stats = calc_stats(arr_recurrence)
    qual_stats = calc_stats(arr_quality)

    contrib_stats = [
        {"component": "Thermal Intensity", "weight": 0.30, "mean_score": thermal_stats["mean"], "mean_contribution": round(thermal_stats["mean"] * 0.30, 4), "P95_contrib": round(thermal_stats["P95"] * 0.30, 4), "P99_contrib": round(thermal_stats["P99"] * 0.30, 4)},
        {"component": "Historical Anomaly", "weight": 0.25, "mean_score": hist_stats["mean"], "mean_contribution": round(hist_stats["mean"] * 0.25, 4), "P95_contrib": round(hist_stats["P95"] * 0.25, 4), "P99_contrib": round(hist_stats["P99"] * 0.25, 4)},
        {"component": "Industrial Context", "weight": 0.20, "mean_score": ind_stats["mean"], "mean_contribution": round(ind_stats["mean"] * 0.20, 4), "P95_contrib": round(ind_stats["P95"] * 0.20, 4), "P99_contrib": round(ind_stats["P99"] * 0.20, 4)},
        {"component": "Recurrence / Persistence", "weight": 0.10, "mean_score": rec_stats["mean"], "mean_contribution": round(rec_stats["mean"] * 0.10, 4), "P95_contrib": round(rec_stats["P95"] * 0.10, 4), "P99_contrib": round(rec_stats["P99"] * 0.10, 4)},
        {"component": "Natural Context (Adj)", "weight": 0.10, "mean_score": nat_stats["mean"], "mean_contribution": round(nat_stats["mean"] * 0.10, 4), "P95_contrib": round(nat_stats["P95"] * 0.10, 4), "P99_contrib": round(nat_stats["P99"] * 0.10, 4)},
        {"component": "Data Quality", "weight": 0.05, "mean_score": qual_stats["mean"], "mean_contribution": round(qual_stats["mean"] * 0.05, 4), "P95_contrib": round(qual_stats["P95"] * 0.05, 4), "P99_contrib": round(qual_stats["P99"] * 0.05, 4)},
    ]

    print("\n--- GROUND-TRUTH CROSS-CHECKS ---", flush=True)
    verified_ext_results = []
    if os.path.exists(VERIFIED_EXT_PATH):
        df_ext = pd.read_csv(VERIFIED_EXT_PATH)
        for r in df_ext.to_dict('records'):
            inp = RiskInput(
                event_id=str(r['event_id']),
                max_frp=clean_val(r.get('max_frp'), 0.0, float),
                observation_count=clean_val(r.get('observation_count'), 1, int),
                industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
                industrial_site_count_250m=clean_val(r.get('industrial_site_count_250m'), 0, int),
                industrial_site_count_1km=clean_val(r.get('industrial_site_count_1km'), 0, int),
                industrial_site_count_5km=clean_val(r.get('industrial_site_count_5km'), 0, int),
                worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown",
                centroid_lat=clean_val(r.get('centroid_lat'), 0.0, float),
                centroid_lon=clean_val(r.get('centroid_lon'), 0.0, float),
                event_start=str(r['event_start']) if pd.notna(r.get('event_start')) else None
            )
            res = engine.assess_event(inp)
            verified_ext_results.append({
                "event_id": inp.event_id,
                "label": str(r.get("label", "LIKELY_INDUSTRIAL_INCIDENT")),
                "overall_risk_score": res.overall_risk_score,
                "risk_level": res.risk_level,
                "investigation_priority": res.investigation_priority,
                "industrial_context_score": res.industrial_context_score,
                "evidence_status": res.evidence_status,
                "human_review_required": res.human_review_required
            })

    persistent_ref_results = []
    if os.path.exists(PERSISTENT_REF_PATH):
        df_p = pd.read_csv(PERSISTENT_REF_PATH)
        for r in df_p.to_dict('records'):
            inp = RiskInput(
                event_id=str(r['event_id']),
                max_frp=clean_val(r.get('max_frp'), 0.0, float),
                observation_count=clean_val(r.get('observation_count'), 1, int),
                industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
                industrial_site_count_250m=clean_val(r.get('industrial_site_count_250m'), 0, int),
                industrial_site_count_1km=clean_val(r.get('industrial_site_count_1km'), 0, int),
                industrial_site_count_5km=clean_val(r.get('industrial_site_count_5km'), 0, int),
                worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown",
                centroid_lat=clean_val(r.get('centroid_lat'), 0.0, float),
                centroid_lon=clean_val(r.get('centroid_lon'), 0.0, float),
                event_start=str(r['event_start']) if pd.notna(r.get('event_start')) else None
            )
            res = engine.assess_event(inp)
            persistent_ref_results.append({
                "event_id": inp.event_id,
                "overall_risk_score": res.overall_risk_score,
                "risk_level": res.risk_level,
                "investigation_priority": res.investigation_priority,
                "industrial_context_score": res.industrial_context_score,
                "evidence_status": res.evidence_status,
                "likely_context": res.likely_context
            })

    wildfire_ref_results = {"total": 0, "risk_sum": 0.0, "nat_sum": 0.0, "ind_sum": 0.0, "high_cnt": 0, "natural_cnt": 0}
    if os.path.exists(WILDFIRE_REF_PATH):
        df_w = pd.read_csv(WILDFIRE_REF_PATH)
        wildfire_ref_results["total"] = len(df_w)
        for r in df_w.to_dict('records'):
            inp = RiskInput(
                event_id=str(r['event_id']),
                max_frp=clean_val(r.get('max_frp'), 0.0, float),
                observation_count=clean_val(r.get('observation_count'), 1, int),
                industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
                worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown",
                centroid_lat=clean_val(r.get('centroid_lat'), 0.0, float),
                centroid_lon=clean_val(r.get('centroid_lon'), 0.0, float),
                event_start=str(r['event_start']) if pd.notna(r.get('event_start')) else None
            )
            res = engine.assess_event(inp)
            wildfire_ref_results["risk_sum"] += res.overall_risk_score
            wildfire_ref_results["nat_sum"] += res.natural_fire_context_score
            wildfire_ref_results["ind_sum"] += res.industrial_context_score
            if res.risk_level == "HIGH": wildfire_ref_results["high_cnt"] += 1
            if res.likely_context == "NATURAL_FIRE_CONTEXT": wildfire_ref_results["natural_cnt"] += 1

    print("\n--- FORMULA RECOMPUTATION VALIDATION ---", flush=True)
    df_sample = pd.read_csv(ALL_EVENTS_PATH, nrows=100)
    formula_matches = 0
    for r in df_sample.to_dict('records'):
        inp = RiskInput(
            event_id=str(r['event_id']),
            max_frp=clean_val(r.get('max_frp'), 0.0, float),
            observation_count=clean_val(r.get('observation_count'), 1, int),
            industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
            worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown",
            centroid_lat=clean_val(r.get('centroid_lat'), 0.0, float),
            centroid_lon=clean_val(r.get('centroid_lon'), 0.0, float)
        )
        res = engine.assess_event(inp)
        manual_score = sum(ev.contribution for ev in res.evidence)
        if abs(manual_score - res.overall_risk_score) < 1e-4:
            formula_matches += 1
    print(f"Formula recomputation match rate: {formula_matches}/100", flush=True)

    print("\nGenerating visualization charts...", flush=True)
    
    plt.figure(figsize=(8, 4.5))
    plt.hist(arr_risk, bins=50, color='#1E88E5', edgecolor='black', alpha=0.8)
    plt.title("AstraFlare Risk Score Distribution (Real India Population N=4,310,499)")
    plt.xlabel("Overall Risk Score")
    plt.ylabel("Event Count")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "risk_score_distribution.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    r_keys = ["LOW", "MEDIUM", "HIGH"]
    r_vals = [risk_levels[k] for k in r_keys]
    plt.bar(r_keys, r_vals, color=['#4CAF50', '#FF9800', '#F44336'])
    plt.title("Risk Level Classification")
    plt.xlabel("Risk Level")
    plt.ylabel("Event Count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "risk_level_distribution.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.bar(["No Review Required", "Human Review Required"], [review_req["FALSE"], review_req["TRUE"]], color=['#2196F3', '#E91E63'])
    plt.title("Human Review Gate Decisions")
    plt.ylabel("Event Count")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "human_review_distribution.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(9, 4.5))
    c_names = [c["component"] for c in contrib_stats]
    c_contribs = [c["mean_contribution"] for c in contrib_stats]
    plt.barh(c_names, c_contribs, color='#3F51B5')
    plt.title("Average Score Contribution by Evidence Component")
    plt.xlabel("Mean Score Contribution")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "component_contribution_distribution.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    f_keys = list(frp_buckets.keys())
    f_means = [frp_buckets[k]["risk_sum"]/max(1, frp_buckets[k]["count"]) for k in f_keys]
    plt.plot(f_keys, f_means, marker='o', color='#FF5722', linewidth=2)
    plt.title("Mean Overall Risk Score by FRP Magnitude Band")
    plt.xlabel("FRP Band (MW)")
    plt.ylabel("Mean Risk Score")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "frp_vs_risk.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    d_keys = list(dist_bands.keys())
    d_ind_means = [dist_bands[k]["ind_sum"]/max(1, dist_bands[k]["count"]) for k in d_keys]
    d_risk_means = [dist_bands[k]["risk_sum"]/max(1, dist_bands[k]["count"]) for k in d_keys]
    plt.plot(d_keys, d_ind_means, marker='s', label='Industrial Context Score', color='#9C27B0', linewidth=2)
    plt.plot(d_keys, d_risk_means, marker='o', label='Overall Risk Score', color='#00BCD4', linewidth=2)
    plt.title("Industrial Context & Risk Score by Proximity Band")
    plt.xlabel("Distance to Nearest Industrial Site")
    plt.ylabel("Score")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "industrial_distance_vs_risk.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    h_keys = list(hist_bands.keys())
    h_means = [hist_bands[k]["risk_sum"]/max(1, hist_bands[k]["count"]) for k in h_keys]
    plt.plot(h_keys, h_means, marker='^', color='#4CAF50', linewidth=2)
    plt.title("Mean Risk Score by Historical FRP Anomaly Band")
    plt.xlabel("Historical Anomaly Z-Score Band")
    plt.ylabel("Mean Risk Score")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "historical_anomaly_vs_risk.png"), dpi=200)
    plt.close()

    summary_report = {
        "dataset": {
            "total_events": total_rows,
            "total_observations": int(total_obs_sum),
            "obs_per_event_ratio": round(total_obs_sum / total_rows, 4),
            "date_range": [date_min, date_max],
            "geographic_bounds": {
                "lat_min": round(float(lat_min), 4),
                "lat_max": round(float(lat_max), 4),
                "lon_min": round(float(lon_min), 4),
                "lon_max": round(float(lon_max), 4)
            }
        },
        "performance": {
            "total_processing_time_sec": round(t_eval, 2),
            "events_per_second": round(total_rows / t_eval, 1)
        },
        "risk_score_stats": risk_stats,
        "risk_levels": {k: {"count": v, "pct": round(v/total_rows*100, 2)} for k, v in risk_levels.items()},
        "priorities": {k: {"count": v, "pct": round(v/total_rows*100, 2)} for k, v in priorities.items()},
        "priority_vs_risk": priority_vs_risk,
        "human_review": {
            "TRUE": {"count": review_req["TRUE"], "pct": round(review_req["TRUE"]/total_rows*100, 2)},
            "FALSE": {"count": review_req["FALSE"], "pct": round(review_req["FALSE"]/total_rows*100, 2)},
            "by_risk": review_by_risk,
            "by_evidence": review_by_evidence,
            "by_context": review_by_context,
            "by_quality": review_by_quality,
            "top_reasons": review_reasons_counter
        },
        "evidence_statuses": {k: {"count": v, "pct": round(v/total_rows*100, 2)} for k, v in evidence_statuses.items()},
        "likely_contexts": {k: {"count": v, "pct": round(v/total_rows*100, 2)} for k, v in likely_contexts.items()},
        "component_stats": {
            "thermal": thermal_stats,
            "historical": hist_stats,
            "industrial": ind_stats,
            "natural": nat_stats,
            "recurrence": rec_stats,
            "quality": qual_stats
        },
        "contribution_stats": contrib_stats,
        "frp_buckets": {
            k: {
                "count": v["count"],
                "pct": round(v["count"]/total_rows*100, 2),
                "mean_risk": round(v["risk_sum"]/max(1, v["count"]), 4),
                "high_risk_pct": round(v["high_cnt"]/max(1, v["count"])*100, 2)
            } for k, v in frp_buckets.items()
        },
        "dist_bands": {
            k: {
                "count": v["count"],
                "pct": round(v["count"]/total_rows*100, 2),
                "mean_ind_score": round(v["ind_sum"]/max(1, v["count"]), 4),
                "mean_overall_risk": round(v["risk_sum"]/max(1, v["count"]), 4),
                "high_risk_pct": round(v["high_cnt"]/max(1, v["count"])*100, 2),
                "review_pct": round(v["review_cnt"]/max(1, v["count"])*100, 2)
            } for k, v in dist_bands.items()
        },
        "hist_bands": {
            k: {
                "count": v["count"],
                "pct": round(v["count"]/total_rows*100, 2),
                "mean_hist_score": round(v["hist_sum"]/max(1, v["count"]), 4),
                "mean_overall_risk": round(v["risk_sum"]/max(1, v["count"]), 4),
                "high_risk_pct": round(v["high_cnt"]/max(1, v["count"])*100, 2),
                "review_pct": round(v["review_cnt"]/max(1, v["count"])*100, 2)
            } for k, v in hist_bands.items()
        },
        "land_cover_stats": {
            k: {
                "count": v["count"],
                "pct": round(v["count"]/total_rows*100, 2),
                "mean_risk": round(v["risk_sum"]/max(1, v["count"]), 4),
                "mean_nat_score": round(v["nat_sum"]/max(1, v["count"]), 4),
                "mean_ind_score": round(v["ind_sum"]/max(1, v["count"]), 4),
                "high_risk_pct": round(v["high_cnt"]/max(1, v["count"])*100, 2)
            } for k, v in land_cover_stats.items()
        },
        "case_studies": case_study_candidates,
        "top_100_summary": {
            "max_risk": top_100_candidates[0]["overall_risk_score"] if top_100_candidates else 0.0,
            "min_risk_in_top100": top_100_candidates[-1]["overall_risk_score"] if top_100_candidates else 0.0,
            "count": len(top_100_candidates)
        },
        "verified_ext_results": verified_ext_results,
        "persistent_ref_results": persistent_ref_results,
        "wildfire_ref_results": wildfire_ref_results,
        "formula_matches": formula_matches
    }

    with open(os.path.join(OUTPUT_DIR, "validation_metrics_summary.json"), "w") as f:
        json.dump(summary_report, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "top_100_events.json"), "w") as f:
        json.dump(top_100_candidates, f, indent=2)

    print("\nSummary metrics and visualizations exported successfully to docs/ai/phase_3_11_1/", flush=True)

if __name__ == "__main__":
    main()
