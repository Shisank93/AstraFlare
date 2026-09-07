"""
AstraFlare Data Storage & Immutable Raw Data Manifest Manager.
Manages metadata registration, checksum calculation, storage paths (raw/staging/processed),
provenance tagging, and spatial India boundary filtering for acquired datasets.
"""
import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

INDIA_BBOX = {
    "min_lat": 6.0,
    "max_lat": 37.5,
    "min_lon": 68.0,
    "max_lon": 97.5
}

class DataManifestManager:
    """Manages immutable raw file registration, checksum verification, and catalog indexing."""
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.staging_dir = os.path.join(base_dir, "staging")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.manifest_file = os.path.join(base_dir, "manifest.json")
        
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if os.path.exists(self.manifest_file):
            try:
                with open(self.manifest_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"datasets": {}, "updated_at": datetime.utcnow().isoformat()}

    def _save_manifest(self):
        self.manifest["updated_at"] = datetime.utcnow().isoformat()
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def calculate_sha256(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return "FILE_NOT_FOUND"
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def register_dataset(
        self,
        dataset_id: str,
        source_name: str,
        file_path: str,
        provenance_status: str,
        total_records: int,
        india_records: int,
        date_range: str,
        source_url: str,
        license_type: str,
        dataset_version: str = "v1.0"
    ) -> Dict[str, Any]:
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        checksum = self.calculate_sha256(file_path) if os.path.exists(file_path) else "N/A"

        meta = {
            "dataset_id": dataset_id,
            "source_name": source_name,
            "file_path": file_path,
            "file_size_bytes": file_size,
            "checksum_sha256": checksum,
            "provenance_status": provenance_status,
            "total_records": total_records,
            "india_records": india_records,
            "date_range": date_range,
            "source_url": source_url,
            "license": license_type,
            "dataset_version": dataset_version,
            "registered_at": datetime.utcnow().isoformat()
        }
        self.manifest["datasets"][dataset_id] = meta
        self._save_manifest()
        return meta

    @staticmethod
    def is_inside_india(lat: float, lon: float) -> bool:
        """Spatial boundary check for India coordinates."""
        return (
            INDIA_BBOX["min_lat"] <= lat <= INDIA_BBOX["max_lat"] and
            INDIA_BBOX["min_lon"] <= lon <= INDIA_BBOX["max_lon"]
        )

manifest_manager = DataManifestManager()
