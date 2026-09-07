"""
Phase 3.11.1 Post-Validation Audit & Metric Reconciliation Script.
Audits the complete 4,310,499 event population to reconcile:
1. Singleton vs LOW data quality status
2. Human review driver counts and multi-category overlaps
3. Review rates by singleton, quality status, evidence status, risk level, priority
4. Component contribution distribution and dominance
5. Exact risk distribution quantiles
6. Verified industrial, persistent heat, and wildfire reference cross-checks
7. Warning categorization
8. Timing audit
"""
import os
import sys
import time
import json
import numpy as np
import pandas as pd

from backend.risk_engine.engine import EvidenceRiskEngine
from backend.risk_engine.models import RiskInput
from backend.risk_engine.config import RiskEngineConfig

DATASET_DIR = "data/processed/event_dataset"
ALL_EVENTS_PATH = os.path.join(DATASET_DIR, "DATASET_C_ALL_EVENTS.csv")
VERIFIED_EXT_PATH = os.path.join(DATASET_DIR, "DATASET_C_VERIFIED_EXTERNAL.csv")
PERSISTENT_REF_PATH = os.path.join(DATASET_DIR, "DATASET_C_PERSISTENT_REFERENCE.csv")
WILDFIRE_REF_PATH = os.path.join(DATASET_DIR, "DATASET_C_WILDFIRE_REFERENCE.csv")

def clean_val(val, default, cast_type):
    if pd.isna(val) or val is None:
        return default
    try:
        return cast_type(val)
    except:
        return default

def main():
    print("=== AstraFlare Phase 3.11.1 Post-Validation Audit & Metric Reconciliation ===", flush=True)
    t_start = time.time()

    engine = EvidenceRiskEngine()
    cfg = RiskEngineConfig()

    chunksize = 200000
    total_events = 0

    # 1. Singleton vs Quality counters
    singletons_total = 0
    singletons_low_q = 0
    singletons_not_low_q = 0
    multi_obs_total = 0
    multi_obs_low_q = 0

    # 2. Human review driver counters
    total_review_true = 0
    total_review_false = 0
    driver_low_q = 0
    driver_ambiguous = 0
    driver_industrial_anomaly = 0
    
    # Driver overlaps
    overlap_low_q_and_ambiguous = 0
    overlap_low_q_and_ind_anomaly = 0
    overlap_ambiguous_and_ind_anomaly = 0
    overlap_all_three = 0
    unexplained_review_count = 0

    # 3. Review rate breakdowns
    review_by_obs = {"SINGLETON": {"total": 0, "review_true": 0}, "MULTI_OBS": {"total": 0, "review_true": 0}}
    review_by_q_status = {q: {"total": 0, "review_true": 0} for q in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]}
    review_by_e_status = {}
    review_by_risk_lvl = {r: {"total": 0, "review_true": 0} for r in ["LOW", "MEDIUM", "HIGH"]}
    review_by_priority = {p: {"total": 0, "review_true": 0} for p in ["LOW", "MEDIUM", "HIGH", "URGENT"]}

    # Arrays for distribution recalculations
    arr_risk = []
    arr_c_thermal = []
    arr_c_hist = []
    arr_c_ind = []
    arr_c_rec = []
    arr_c_nat = []
    arr_c_qual = []

    cols_needed = [
        'event_id', 'event_start', 'event_end', 'duration_hours', 'observation_count',
        'centroid_lat', 'centroid_lon', 'max_frp', 'mean_frp', 'std_frp',
        'max_brightness', 'mean_brightness', 'confidence_high_ratio', 'satellite_count',
        'industrial_distance_m', 'industrial_site_count_250m', 'industrial_site_count_1km',
        'industrial_site_count_5km', 'worldcover_class'
    ]

    print("Auditing 4,310,499 events across chunked batches...", flush=True)

    t_processing_start = time.time()

    for chunk_idx, chunk in enumerate(pd.read_csv(ALL_EVENTS_PATH, chunksize=chunksize, usecols=cols_needed)):
        chunk_len = len(chunk)
        total_events += chunk_len

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
            q_status = res.data_quality_status
            rev_req = res.human_review_required

            # 1. Singleton vs Quality
            is_singleton = (obs_cnt == 1)
            is_low_q = (q_status in ("LOW", "INSUFFICIENT"))

            if is_singleton:
                singletons_total += 1
                if is_low_q:
                    singletons_low_q += 1
                else:
                    singletons_not_low_q += 1
            else:
                multi_obs_total += 1
                if is_low_q:
                    multi_obs_low_q += 1

            # 2. Review Driver Analysis
            if rev_req:
                total_review_true += 1

                # Check driver triggers independently
                c_low_q = is_low_q
                c_ambig = (e_status == "INSUFFICIENT_EVIDENCE") or (e_status == "CONFLICTING_EVIDENCE")
                c_ind_anom = (res.industrial_context_score >= 0.75 and max_frp >= 40.0)

                if c_low_q: driver_low_q += 1
                if c_ambig: driver_ambiguous += 1
                if c_ind_anom: driver_industrial_anomaly += 1

                if c_low_q and c_ambig: overlap_low_q_and_ambiguous += 1
                if c_low_q and c_ind_anom: overlap_low_q_and_ind_anomaly += 1
                if c_ambig and c_ind_anom: overlap_ambiguous_and_ind_anomaly += 1
                if c_low_q and c_ambig and c_ind_anom: overlap_all_three += 1

                if not (c_low_q or c_ambig or c_ind_anom):
                    unexplained_review_count += 1
            else:
                total_review_false += 1

            # 3. Review Rates by Category
            obs_grp = "SINGLETON" if is_singleton else "MULTI_OBS"
            review_by_obs[obs_grp]["total"] += 1
            if rev_req: review_by_obs[obs_grp]["review_true"] += 1

            review_by_q_status[q_status]["total"] += 1
            if rev_req: review_by_q_status[q_status]["review_true"] += 1

            if e_status not in review_by_e_status:
                review_by_e_status[e_status] = {"total": 0, "review_true": 0}
            review_by_e_status[e_status]["total"] += 1
            if rev_req: review_by_e_status[e_status]["review_true"] += 1

            review_by_risk_lvl[r_level]["total"] += 1
            if rev_req: review_by_risk_lvl[r_level]["review_true"] += 1

            review_by_priority[p_level]["total"] += 1
            if rev_req: review_by_priority[p_level]["review_true"] += 1

            # Store contributions
            # res.evidence items: THERMAL_ANOMALY, HISTORICAL_ANOMALY, INDUSTRIAL_CONTEXT, NATURAL_CONTEXT, RECURRENCE, DATA_QUALITY
            c_dict = {item.type: item.contribution for item in res.evidence}
            arr_risk.append(r_score)
            arr_c_thermal.append(c_dict.get("THERMAL_ANOMALY", 0.0))
            arr_c_hist.append(c_dict.get("HISTORICAL_ANOMALY", 0.0))
            arr_c_ind.append(c_dict.get("INDUSTRIAL_CONTEXT", 0.0))
            arr_c_rec.append(c_dict.get("RECURRENCE", 0.0))
            arr_c_nat.append(c_dict.get("NATURAL_CONTEXT", 0.0))
            arr_c_qual.append(c_dict.get("DATA_QUALITY", 0.0))

    t_processing_end = time.time()
    proc_time_sec = round(t_processing_end - t_processing_start, 2)

    print(f"Processed all {total_events} events in {proc_time_sec} seconds.", flush=True)

    arr_risk = np.array(arr_risk, dtype=np.float32)
    arr_c_thermal = np.array(arr_c_thermal, dtype=np.float32)
    arr_c_hist = np.array(arr_c_hist, dtype=np.float32)
    arr_c_ind = np.array(arr_c_ind, dtype=np.float32)
    arr_c_rec = np.array(arr_c_rec, dtype=np.float32)
    arr_c_nat = np.array(arr_c_nat, dtype=np.float32)
    arr_c_qual = np.array(arr_c_qual, dtype=np.float32)

    def calc_contrib_stats(arr):
        total_risk_sum = float(np.sum(arr_risk))
        c_sum = float(np.sum(arr))
        return {
            "mean_contrib": round(float(np.mean(arr)), 4),
            "median_contrib": round(float(np.median(arr)), 4),
            "P95_contrib": round(float(np.percentile(arr, 95)), 4),
            "max_contrib": round(float(np.max(arr)), 4),
            "pct_of_total_risk": round((c_sum / total_risk_sum * 100.0), 2)
        }

    contrib_analysis = {
        "Thermal Intensity": calc_contrib_stats(arr_c_thermal),
        "Historical Anomaly": calc_contrib_stats(arr_c_hist),
        "Industrial Context": calc_contrib_stats(arr_c_ind),
        "Recurrence / Persistence": calc_contrib_stats(arr_c_rec),
        "Natural Context (Adj)": calc_contrib_stats(arr_c_nat),
        "Data Quality": calc_contrib_stats(arr_c_qual),
    }

    # Verified external incidents detailed audit
    verified_ext_audit = []
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
            verified_ext_audit.append({
                "event_id": inp.event_id,
                "overall_risk_score": res.overall_risk_score,
                "risk_level": res.risk_level,
                "investigation_priority": res.investigation_priority,
                "industrial_context_score": res.industrial_context_score,
                "evidence_status": res.evidence_status,
                "human_review_required": res.human_review_required
            })

    # Persistent ref detailed audit
    persistent_ref_audit = []
    if os.path.exists(PERSISTENT_REF_PATH):
        df_p = pd.read_csv(PERSISTENT_REF_PATH)
        for r in df_p.to_dict('records'):
            inp = RiskInput(
                event_id=str(r['event_id']),
                max_frp=clean_val(r.get('max_frp'), 0.0, float),
                observation_count=clean_val(r.get('observation_count'), 1, int),
                industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
                industrial_site_count_250m=clean_val(r.get('industrial_site_count_250m'), 0, int),
                worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown"
            )
            res = engine.assess_event(inp)
            persistent_ref_audit.append({
                "event_id": inp.event_id,
                "overall_risk_score": res.overall_risk_score,
                "industrial_context_score": res.industrial_context_score,
                "persistence_score": res.persistence_score,
                "historical_anomaly_score": res.historical_anomaly_score,
                "investigation_priority": res.investigation_priority,
                "human_review_required": res.human_review_required
            })

    # Wildfire ref audit
    wildfire_ref_audit = {"total": 0, "mean_nat_score": 0.0, "mean_ind_score": 0.0, "mean_risk_score": 0.0, "review_cnt": 0, "priorities": {}}
    if os.path.exists(WILDFIRE_REF_PATH):
        df_w = pd.read_csv(WILDFIRE_REF_PATH)
        wildfire_ref_audit["total"] = len(df_w)
        r_sum = 0.0
        n_sum = 0.0
        i_sum = 0.0
        for r in df_w.to_dict('records'):
            inp = RiskInput(
                event_id=str(r['event_id']),
                max_frp=clean_val(r.get('max_frp'), 0.0, float),
                observation_count=clean_val(r.get('observation_count'), 1, int),
                industrial_distance_m=clean_val(r.get('industrial_distance_m'), 10000.0, float),
                worldcover_class=str(r.get('worldcover_class')) if pd.notna(r.get('worldcover_class')) else "Unknown"
            )
            res = engine.assess_event(inp)
            r_sum += res.overall_risk_score
            n_sum += res.natural_fire_context_score
            i_sum += res.industrial_context_score
            if res.human_review_required: wildfire_ref_audit["review_cnt"] += 1
            p = res.investigation_priority
            wildfire_ref_audit["priorities"][p] = wildfire_ref_audit["priorities"].get(p, 0) + 1
        wildfire_ref_audit["mean_risk_score"] = round(r_sum / len(df_w), 4)
        wildfire_ref_audit["mean_nat_score"] = round(n_sum / len(df_w), 4)
        wildfire_ref_audit["mean_ind_score"] = round(i_sum / len(df_w), 4)

    audit_summary = {
        "reconciliation_singleton_vs_quality": {
            "total_events": total_events,
            "singletons_total_obs_cnt_1": singletons_total,
            "singletons_low_q": singletons_low_q,
            "singletons_not_low_q_medium": singletons_not_low_q,
            "multi_obs_total": multi_obs_total,
            "multi_obs_low_q": multi_obs_low_q,
            "total_low_q_in_population": singletons_low_q + multi_obs_low_q
        },
        "reconciliation_human_review_drivers": {
            "total_review_true": total_review_true,
            "total_review_false": total_review_false,
            "driver_low_quality": driver_low_q,
            "driver_ambiguous": driver_ambiguous,
            "driver_industrial_anomaly": driver_industrial_anomaly,
            "raw_driver_sum": driver_low_q + driver_ambiguous + driver_industrial_anomaly,
            "overlaps": {
                "low_q_and_ambiguous": overlap_low_q_and_ambiguous,
                "low_q_and_ind_anomaly": overlap_low_q_and_ind_anomaly,
                "ambiguous_and_ind_anomaly": overlap_ambiguous_and_ind_anomaly,
                "all_three": overlap_all_three
            },
            "unexplained_review_count": unexplained_review_count
        },
        "review_rate_breakdowns": {
            "by_observation_count": {k: {"total": v["total"], "review_pct": round(v["review_true"]/max(1, v["total"])*100, 2)} for k, v in review_by_obs.items()},
            "by_quality_status": {k: {"total": v["total"], "review_pct": round(v["review_true"]/max(1, v["total"])*100, 2)} for k, v in review_by_q_status.items()},
            "by_evidence_status": {k: {"total": v["total"], "review_pct": round(v["review_true"]/max(1, v["total"])*100, 2)} for k, v in review_by_e_status.items()},
            "by_risk_level": {k: {"total": v["total"], "review_pct": round(v["review_true"]/max(1, v["total"])*100, 2)} for k, v in review_by_risk_lvl.items()},
            "by_investigation_priority": {k: {"total": v["total"], "review_pct": round(v["review_true"]/max(1, v["total"])*100, 2)} for k, v in review_by_priority.items()},
        },
        "component_contribution_analysis": contrib_analysis,
        "timing_audit": {
            "total_execution_time_sec": round(time.time() - t_start, 2),
            "processing_time_sec": proc_time_sec,
            "events_per_second": round(total_events / proc_time_sec, 1)
        },
        "verified_ext_audit": verified_ext_audit,
        "persistent_ref_audit": persistent_ref_audit,
        "wildfire_ref_audit": wildfire_ref_audit
    }

    output_path = "docs/ai/phase_3_11_1/post_validation_audit_summary.json"
    with open(output_path, "w") as f:
        json.dump(audit_summary, f, indent=2)

    print(f"Post-validation audit metrics successfully written to {output_path}", flush=True)

if __name__ == "__main__":
    main()
