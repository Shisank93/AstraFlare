"""
Unit Tests for Data & Coordinate Validation Rules.
"""
import math
import pytest
from data_pipeline.gis_engine import validate_coordinates, validate_frp, parse_iso_timestamp

def test_valid_coordinates():
    ok, err = validate_coordinates(22.3072, 73.1812)
    assert ok is True
    assert err is None

def test_invalid_latitude():
    ok, err = validate_coordinates(95.0, 73.1812)
    assert ok is False
    assert "Latitude 95.0 out of valid bounds" in err

    ok2, err2 = validate_coordinates(-90.5, 0.0)
    assert ok2 is False

def test_invalid_longitude():
    ok, err = validate_coordinates(20.0, 185.0)
    assert ok is False
    assert "Longitude 185.0 out of valid bounds" in err

    ok2, err2 = validate_coordinates(0.0, -180.1)
    assert ok2 is False

def test_nan_coordinates():
    ok, err = validate_coordinates(float('nan'), 75.0)
    assert ok is False
    assert "valid number" in err

def test_valid_frp():
    ok, err = validate_frp(120.5)
    assert ok is True
    assert err is None

    ok_zero, err_zero = validate_frp(0.0)
    assert ok_zero is True

def test_negative_frp():
    ok, err = validate_frp(-10.0)
    assert ok is False
    assert "FRP cannot be negative" in err

def test_iso_timestamp_parsing():
    dt = parse_iso_timestamp("2026-09-04T14:15:00Z")
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 4
    assert dt.tzinfo is not None

def test_invalid_timestamp():
    with pytest.raises(ValueError):
        parse_iso_timestamp("invalid-date-string")
