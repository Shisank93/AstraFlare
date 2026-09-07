"""
Unit tests for Zenodo Fire Dataset Inspector & Data Governance.
"""
import pytest
from data_pipeline.sources.inspect_zenodo_fires import zenodo_inspector, ZenodoFireDatasetInspector

def test_zenodo_inspector_metadata():
    """Verify Zenodo metadata and data governance properties."""
    meta = ZenodoFireDatasetInspector.ZENODO_METADATA
    assert meta["source_name"] == "ZENODO_GLOBAL_INDIVIDUAL_FIRE_EVENTS"
    assert meta["source_record"] == "20302344"
    assert meta["doi"] == "10.5281/zenodo.20302344"
    assert meta["provenance_status"] == "SATELLITE_DERIVED_EXTERNAL"
    assert meta["ground_truth"] is False
    assert meta["license"] == "Creative Commons Attribution 4.0 International (CC BY 4.0)"

def test_zenodo_inspector_file_check():
    """Verify file status check handles local absence without crashing."""
    status = zenodo_inspector.check_file_status()
    assert "file_present" in status
    assert "accessibility_status" in status
    assert "zenodo_metadata" in status
