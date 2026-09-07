"""
NASA FIRMS Historical Archive Ingestion & Authentication Inspector.
Inspects Earthdata credentials / MAP_KEY requirements, target date range (2023-01-01 to 2025-12-31),
and manages local raw storage registration in data/raw/firms_archive/.
"""
import os
import sys
from typing import Dict, Any
from data_pipeline.sources.data_manifest import manifest_manager

class FIRMSArchiveIngestor:
    """Handles verification and preparation of historical NASA FIRMS archive downloads."""
    def __init__(self):
        self.archive_dir = "data/raw/firms_archive"
        os.makedirs(self.archive_dir, exist_ok=True)

    def check_authentication_status(self) -> Dict[str, Any]:
        """Checks for presence of Earthdata authentication or FIRMS MAP_KEY."""
        map_key = os.environ.get("FIRMS_MAP_KEY")
        earthdata_user = os.environ.get("EARTHDATA_USER")
        netrc_exists = os.path.exists(os.path.expanduser("~/.netrc"))
        
        has_auth = bool(map_key or earthdata_user or netrc_exists)
        
        return {
            "has_auth": has_auth,
            "map_key_present": bool(map_key),
            "earthdata_user_present": bool(earthdata_user),
            "netrc_present": netrc_exists,
            "manual_action_required": not has_auth,
            "instructions": (
                "To download historical FIRMS archive data (>7 days old):\n"
                "1. Register at urs.earthdata.nasa.gov\n"
                "2. Request a MAP_KEY at firms.modaps.eosdis.nasa.gov/api/map_key/\n"
                "3. Set export FIRMS_MAP_KEY='<your_map_key>' in your environment."
                if not has_auth else "Authentication available."
            )
        }

    def inspect_historical_capabilities(self) -> Dict[str, Any]:
        auth_status = self.check_authentication_status()
        
        return {
            "source_name": "NASA_FIRMS_HISTORICAL_ARCHIVE",
            "target_region": "India (6.0N-37.5N, 68.0E-97.5E)",
            "target_date_range": "2023-01-01 to 2025-12-31",
            "sensors": ["VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP", "MODIS_TERRA_AQUA"],
            "estimated_size_mb": 127.0,
            "provenance_status": "SATELLITE_DERIVED_CORROBORATION",
            "authentication_status": auth_status
        }

firms_archive_ingestor = FIRMSArchiveIngestor()

if __name__ == "__main__":
    caps = firms_archive_ingestor.inspect_historical_capabilities()
    print("FIRMS Archive Capabilities:")
    import json
    print(json.dumps(caps, indent=2))
