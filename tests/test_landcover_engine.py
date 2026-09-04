"""
Unit Tests for ESA WorldCover Land-Cover Engine & Classification Scheme.
"""
import pytest
from data_pipeline.landcover_engine import LandCoverEngine, WORLDCOVER_CLASS_MAP

def test_worldcover_class_mapping():
    assert 10 in WORLDCOVER_CLASS_MAP
    assert WORLDCOVER_CLASS_MAP[10]["name"] == "Tree cover"
    assert WORLDCOVER_CLASS_MAP[50]["name"] == "Built-up"
    assert WORLDCOVER_CLASS_MAP[40]["name"] == "Cropland"

def test_get_land_cover_class_sampling():
    engine = LandCoverEngine()
    
    # Test Gujarat Industrial Corridor Coordinate
    lc = engine.get_land_cover_class(22.3072, 73.1812)
    assert lc["class_code"] in (40, 50)
    assert lc["class_name"] in ("Built-up", "Cropland")
    assert lc["data_source"] in ("ESA_WORLDCOVER_POSTGIS", "ESA_WORLDCOVER_HEURISTIC")

    # Test Garhwal Himalayan Forest Coordinate
    lc_forest = engine.get_land_cover_class(30.4500, 78.8500)
    assert lc_forest["class_code"] == 10
    assert lc_forest["class_name"] == "Tree cover"

def test_invalid_coordinate_landcover():
    engine = LandCoverEngine()
    with pytest.raises(ValueError):
        engine.get_land_cover_class(95.0, 73.0)
