"""
Unit Tests for FRP Anomaly Score Calculation & Edge Cases.
Tests safeguards for zero standard deviation, missing history, and insufficient observations.
"""
import pytest
from data_pipeline.gis_engine import calculate_frp_anomaly_score

def test_normal_frp_anomaly():
    # Normal case: 5 events, mean 50, std 10, current FRP 80 -> z = (80 - 50) / 10 = 3.0
    stats = {"count": 5, "mean": 50.0, "max": 65.0, "std": 10.0}
    res = calculate_frp_anomaly_score(80.0, stats)
    assert res["status"] == "VALID"
    assert res["anomaly_score"] == 3.0

def test_insufficient_history():
    # Insufficient history: count < 3 -> return INSUFFICIENT_DATA
    stats = {"count": 2, "mean": 45.0, "max": 50.0, "std": 7.07}
    res = calculate_frp_anomaly_score(150.0, stats)
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["anomaly_score"] is None
    assert "Insufficient historical observations" in res["message"]

def test_no_history():
    # Missing history: count 0 -> return NO_HISTORY
    stats = {"count": 0, "mean": None, "max": None, "std": None}
    res = calculate_frp_anomaly_score(100.0, stats)
    assert res["status"] == "NO_HISTORY"
    assert res["anomaly_score"] is None

def test_zero_std_equal():
    # Zero std dev safeguard: current FRP equals historical mean -> score 0.0
    stats = {"count": 10, "mean": 45.0, "max": 45.0, "std": 0.0}
    res = calculate_frp_anomaly_score(45.0, stats)
    assert res["status"] == "ZERO_STD"
    assert res["anomaly_score"] == 0.0

def test_zero_std_positive_anomaly():
    # Zero std dev safeguard: current FRP surge above zero-variance baseline -> capped score 10.0
    stats = {"count": 10, "mean": 45.0, "max": 45.0, "std": 0.0}
    res = calculate_frp_anomaly_score(120.0, stats)
    assert res["status"] == "ZERO_STD"
    assert res["anomaly_score"] == 10.0

def test_negative_frp_rejection():
    stats = {"count": 5, "mean": 50.0, "std": 10.0}
    with pytest.raises(ValueError):
        calculate_frp_anomaly_score(-10.0, stats)
