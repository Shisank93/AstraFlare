"""
Unit and Integration Tests for Phase 3.7 Data Acquisition & Profiling Infrastructure.
"""
import os
import pytest
from data_pipeline.sources.data_manifest import DataManifestManager, manifest_manager
from data_pipeline.sources.firms_archive_ingest import firms_archive_ingestor

def test_india_spatial_bbox_filter():
    """Verify spatial bounding box filtering for India coordinates."""
    # Delhi (inside)
    assert DataManifestManager.is_inside_india(28.6139, 77.2090) is True
    # Mumbai (inside)
    assert DataManifestManager.is_inside_india(19.0760, 72.8777) is True
    # London (outside)
    assert DataManifestManager.is_inside_india(51.5074, -0.1278) is False
    # Tokyo (outside)
    assert DataManifestManager.is_inside_india(35.6762, 139.6503) is False

def test_dataset_registration_manifest(tmp_path):
    """Verify raw dataset registration and checksum calculation."""
    manager = DataManifestManager(base_dir=str(tmp_path))
    dummy_file = tmp_path / "raw" / "dummy_data.csv"
    dummy_file.parent.mkdir(parents=True, exist_ok=True)
    dummy_file.write_text("event_id,lat,lon\n1,22.5,73.2\n2,19.1,72.8\n")

    meta = manager.register_dataset(
        dataset_id="test_ds_01",
        source_name="Zenodo_GIHS",
        file_path=str(dummy_file),
        provenance_status="INDUSTRIAL_HEAT_REFERENCE",
        total_records=2,
        india_records=2,
        date_range="2012-2023",
        source_url="https://zenodo.org/records/20960492",
        license_type="CC BY 4.0"
    )

    assert meta["dataset_id"] == "test_ds_01"
    assert meta["provenance_status"] == "INDUSTRIAL_HEAT_REFERENCE"
    assert meta["total_records"] == 2
    assert meta["checksum_sha256"] != "N/A"
    assert os.path.exists(manager.manifest_file)

def test_firms_auth_inspection():
    """Verify that FIRMS archive authentication requirements are correctly evaluated."""
    auth_status = firms_archive_ingestor.check_authentication_status()
    assert "has_auth" in auth_status
    assert "manual_action_required" in auth_status
    assert isinstance(auth_status["instructions"], str)
