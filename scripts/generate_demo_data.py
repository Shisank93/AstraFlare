#!/usr/bin/env python3
"""
AstraFlare Synthetic Demo Data Generator.
Generates 4 distinct workflow demonstration scenarios clearly marked with data_source = 'SYNTHETIC_DEMO'.
DO NOT use synthetic demo observations as real NASA FIRMS observations or real ML accuracy evidence.
"""
import os
import sys

# Ensure repository root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
from database.db import db_manager
from data_pipeline.gis_engine import calculate_frp_anomaly_score
from backend.config import settings

def generate_demo_scenarios():
    print("=" * 70)
    print("ASTRAFLARE SYNTHETIC DEMO DATASET GENERATOR")
    print(f"Data Source Tag: {settings.DATA_SOURCE_DEMO}")
    print("=" * 70)

    db_manager.connect()

    # 1. Insert Reference Industrial Sites
    print("\n1. Seeding Industrial Reference Infrastructure...")
    industrial_sites = [
        {
            "osm_id": "way_101",
            "name": "Gujarat Refinery Complex",
            "facility_type": "refinery",
            "geom": "POINT(73.1812 22.3072)",
            "data_source": "OSM"
        },
        {
            "osm_id": "way_102",
            "name": "Jamnagar Flare Stack Cluster",
            "facility_type": "flare_stack",
            "geom": "POINT(70.0577 22.4707)",
            "data_source": "OSM"
        },
        {
            "osm_id": "way_103",
            "name": "Surat Chemical Processing Plant",
            "facility_type": "factory",
            "geom": "POINT(72.8311 21.1702)",
            "data_source": "OSM"
        }
    ]

    for site in industrial_sites:
        if db_manager.is_postgres:
            query = """
            INSERT INTO industrial_sites (osm_id, name, facility_type, geom, data_source)
            VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326), %s)
            ON CONFLICT (osm_id) DO UPDATE SET name = EXCLUDED.name;
            """
            db_manager.execute_query(query, (site["osm_id"], site["name"], site["facility_type"], site["geom"], site["data_source"]))
        else:
            query = """
            INSERT OR REPLACE INTO industrial_sites (osm_id, name, facility_type, geom, data_source)
            VALUES (?, ?, ?, ?, ?);
            """
            db_manager.execute_query(query, (site["osm_id"], site["name"], site["facility_type"], site["geom"], site["data_source"]))
    
    print("Industrial sites seeded.")

    # 2. Define Demo Scenarios
    scenarios = [
        # SCENARIO A: Likely Industrial Incident
        {
            "hotspot": {
                "id": "demo_hs_scenario_a",
                "firms_id": "firms_sim_01",
                "latitude": 22.3088,
                "longitude": 73.1825,  # 180m from Gujarat Refinery
                "geom": "POINT(73.1825 22.3088)",
                "acq_timestamp": "2026-09-04T14:15:00Z",
                "satellite": "VIIRS_SNPP",
                "instrument": "VIIRS",
                "brightness": 365.2,
                "frp": 155.0,  # High FRP surge
                "confidence": "high",
                "daynight": "N",
                "data_source": settings.DATA_SOURCE_DEMO
            },
            "history_stats": {"count": 2, "mean": 32.0, "max": 38.0, "std": 4.2},
            "prediction": {
                "predicted_class": "Likely Industrial Incident",
                "confidence": 0.92,
                "is_abstained": False,
                "risk_score": 0.95,
                "prob_industrial_incident": 0.92,
                "prob_persistent_heat": 0.05,
                "prob_wildland_fire": 0.03,
                "model_version": "v1.0.0-demo"
            },
            "evidence": [
                ("GIS_OPERATIONAL", "dist_industrial_m", "180m", 0.45, "Proximity (180m) to Gujarat Refinery Complex indicates industrial infrastructure setting."),
                ("GIS_OPERATIONAL", "frp_anomaly_score", "Z=29.28", 0.40, "FRP of 155.0 MW represents a 4.84x surge above the historical location mean (32.0 MW)."),
                ("GIS_OPERATIONAL", "land_cover", "Built-up / Industrial", 0.15, "Land cover confirmed as Industrial / Built-up area.")
            ]
        },

        # SCENARIO B: Persistent Industrial Heat
        {
            "hotspot": {
                "id": "demo_hs_scenario_b",
                "firms_id": "firms_sim_02",
                "latitude": 22.4715,
                "longitude": 70.0583,  # 120m from Jamnagar Flare Stack
                "geom": "POINT(70.0583 22.4715)",
                "acq_timestamp": "2026-09-04T12:30:00Z",
                "satellite": "VIIRS_NOAA20",
                "instrument": "VIIRS",
                "brightness": 332.0,
                "frp": 48.2,  # Routine FRP
                "confidence": "nominal",
                "daynight": "D",
                "data_source": settings.DATA_SOURCE_DEMO
            },
            "history_stats": {"count": 84, "mean": 46.5, "max": 58.0, "std": 5.1},
            "prediction": {
                "predicted_class": "Persistent Industrial Heat",
                "confidence": 0.94,
                "is_abstained": False,
                "risk_score": 0.35,  # Low operational risk (expected flare)
                "prob_industrial_incident": 0.04,
                "prob_persistent_heat": 0.94,
                "prob_wildland_fire": 0.02,
                "model_version": "v1.0.0-demo"
            },
            "evidence": [
                ("GIS_OPERATIONAL", "historical_count_365d", "84 events", 0.50, "High historical recurrence (84 detections in past 12 months) indicates persistent operational heat signature."),
                ("GIS_OPERATIONAL", "frp_anomaly_score", "Z=0.33", 0.35, "FRP is stable and matches historical routine industrial flare baseline (1.03x ratio)."),
                ("GIS_OPERATIONAL", "dist_industrial_m", "120m", 0.15, "Located within Jamnagar Petrochemical Flare Stack Cluster boundaries.")
            ]
        },

        # SCENARIO C: Natural / Wildland Fire
        {
            "hotspot": {
                "id": "demo_hs_scenario_c",
                "firms_id": "firms_sim_03",
                "latitude": 30.4500,
                "longitude": 78.8500,  # Garhwal Forest, Uttarakhand (Zero industry near)
                "geom": "POINT(78.8500 30.4500)",
                "acq_timestamp": "2026-09-04T09:10:00Z",
                "satellite": "MODIS_TERRA",
                "instrument": "MODIS",
                "brightness": 342.1,
                "frp": 88.5,
                "confidence": "high",
                "daynight": "D",
                "data_source": settings.DATA_SOURCE_DEMO
            },
            "history_stats": {"count": 1, "mean": 45.0, "max": 45.0, "std": 0.0},
            "prediction": {
                "predicted_class": "Natural/Wildland Fire",
                "confidence": 0.91,
                "is_abstained": False,
                "risk_score": 0.82,
                "prob_industrial_incident": 0.02,
                "prob_persistent_heat": 0.07,
                "prob_wildland_fire": 0.91,
                "model_version": "v1.0.0-demo"
            },
            "evidence": [
                ("GIS_OPERATIONAL", "dist_industrial_m", "14,200m", 0.55, "Zero industrial infrastructure within 14.2km radius."),
                ("GIS_OPERATIONAL", "land_cover", "Tree cover (Forest)", 0.35, "ESA WorldCover verifies high-density forest tree cover."),
                ("GIS_OPERATIONAL", "weather_humidity", "RH 22%", 0.10, "Low relative humidity (22%) favors forest fire propagation.")
            ]
        },

        # SCENARIO D: Human Review / Ambiguous Event
        {
            "hotspot": {
                "id": "demo_hs_scenario_d",
                "firms_id": "firms_sim_04",
                "latitude": 21.1702,
                "longitude": 72.8410,  # 1,100m on agricultural/industrial fringe
                "geom": "POINT(72.8410 21.1702)",
                "acq_timestamp": "2026-09-04T16:45:00Z",
                "satellite": "VIIRS_SNPP",
                "instrument": "VIIRS",
                "brightness": 324.5,
                "frp": 32.0,
                "confidence": "nominal",
                "daynight": "N",
                "data_source": settings.DATA_SOURCE_DEMO
            },
            "history_stats": {"count": 4, "mean": 24.0, "max": 30.0, "std": 4.5},
            "prediction": {
                "predicted_class": "Human Review Required",
                "confidence": 0.40,  # Below threshold 0.65 -> Abstain
                "is_abstained": True,
                "risk_score": 0.50,
                "prob_industrial_incident": 0.38,
                "prob_persistent_heat": 0.22,
                "prob_wildland_fire": 0.40,
                "model_version": "v1.0.0-demo"
            },
            "evidence": [
                ("GIS_OPERATIONAL", "confidence_gate", "Conflicted (0.40)", 0.60, f"Model confidence (0.40) is below initial operational threshold ({settings.HUMAN_REVIEW_THRESHOLD}). System abstained."),
                ("GIS_OPERATIONAL", "land_cover", "Cropland Fringe", 0.25, "Conflicting spatial signals: Farmland adjacent to chemical plant perimeter."),
                ("GIS_OPERATIONAL", "action_required", "Human Review", 0.15, "Routed to analyst review queue for visual satellite verification.")
            ]
        }
    ]

    print("\n2. Inserting Synthetic Demo Observations & Evidence...")
    for idx, scenario in enumerate(scenarios, 1):
        hs = scenario["hotspot"]
        print(f"Scenario {idx}: {hs['id']} -> {scenario['prediction']['predicted_class']}")

        # Insert Hotspot
        if db_manager.is_postgres:
            q_hs = """
            INSERT INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
            VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326), %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET frp = EXCLUDED.frp;
            """
            db_manager.execute_query(q_hs, (
                hs["id"], hs["firms_id"], hs["latitude"], hs["longitude"], hs["geom"],
                hs["acq_timestamp"], hs["satellite"], hs["instrument"], hs["brightness"],
                hs["frp"], hs["confidence"], hs["daynight"], hs["data_source"]
            ))
        else:
            q_hs = """
            INSERT OR REPLACE INTO hotspots (id, firms_id, latitude, longitude, geom, acq_timestamp, satellite, instrument, brightness, frp, confidence, daynight, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            db_manager.execute_query(q_hs, (
                hs["id"], hs["firms_id"], hs["latitude"], hs["longitude"], hs["geom"],
                hs["acq_timestamp"], hs["satellite"], hs["instrument"], hs["brightness"],
                hs["frp"], hs["confidence"], hs["daynight"], hs["data_source"]
            ))

        # Calculate Anomaly Score
        anomaly_res = calculate_frp_anomaly_score(hs["frp"], scenario["history_stats"])
        
        # Insert Historical Features
        if db_manager.is_postgres:
            q_hist = """
            INSERT INTO historical_features (hotspot_id, historical_count_30d, historical_count_365d, historical_mean_frp, historical_max_frp, historical_std_frp, frp_anomaly_score, history_observation_count, anomaly_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            db_manager.execute_query(q_hist, (
                hs["id"], scenario["history_stats"]["count"], scenario["history_stats"]["count"],
                scenario["history_stats"]["mean"], scenario["history_stats"]["max"], scenario["history_stats"]["std"],
                anomaly_res["anomaly_score"], scenario["history_stats"]["count"], anomaly_res["status"]
            ))
        else:
            q_hist = """
            INSERT INTO historical_features (hotspot_id, historical_count_30d, historical_count_365d, historical_mean_frp, historical_max_frp, historical_std_frp, frp_anomaly_score, history_observation_count, anomaly_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            db_manager.execute_query(q_hist, (
                hs["id"], scenario["history_stats"]["count"], scenario["history_stats"]["count"],
                scenario["history_stats"]["mean"], scenario["history_stats"]["max"], scenario["history_stats"]["std"],
                anomaly_res["anomaly_score"], scenario["history_stats"]["count"], anomaly_res["status"]
            ))

        # Insert Prediction Audit Log
        pred = scenario["prediction"]
        if db_manager.is_postgres:
            q_pred = """
            INSERT INTO predictions (hotspot_id, predicted_class, confidence, is_abstained, risk_score, prob_industrial_incident, prob_persistent_heat, prob_wildland_fire, model_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            db_manager.execute_query(q_pred, (
                hs["id"], pred["predicted_class"], pred["confidence"], pred["is_abstained"],
                pred["risk_score"], pred["prob_industrial_incident"], pred["prob_persistent_heat"],
                pred["prob_wildland_fire"], pred["model_version"]
            ))
        else:
            q_pred = """
            INSERT INTO predictions (hotspot_id, predicted_class, confidence, is_abstained, risk_score, prob_industrial_incident, prob_persistent_heat, prob_wildland_fire, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            db_manager.execute_query(q_pred, (
                hs["id"], pred["predicted_class"], pred["confidence"], 1 if pred["is_abstained"] else 0,
                pred["risk_score"], pred["prob_industrial_incident"], pred["prob_persistent_heat"],
                pred["prob_wildland_fire"], pred["model_version"]
            ))

        # Insert Evidence Items
        for ev_type, feat_name, feat_val, contrib, statement in scenario["evidence"]:
            if db_manager.is_postgres:
                q_ev = """
                INSERT INTO evidence (hotspot_id, evidence_type, feature_name, feature_value, contribution, human_readable_statement)
                VALUES (%s, %s, %s, %s, %s, %s);
                """
                db_manager.execute_query(q_ev, (hs["id"], ev_type, feat_name, feat_val, contrib, statement))
            else:
                q_ev = """
                INSERT INTO evidence (hotspot_id, evidence_type, feature_name, feature_value, contribution, human_readable_statement)
                VALUES (?, ?, ?, ?, ?, ?);
                """
                db_manager.execute_query(q_ev, (hs["id"], ev_type, feat_name, feat_val, contrib, statement))

    print("\nSynthetic demo data generation complete!")
    print(f"All records tagged with data_source = '{settings.DATA_SOURCE_DEMO}'.")
    print("=" * 70)

if __name__ == "__main__":
    generate_demo_scenarios()
