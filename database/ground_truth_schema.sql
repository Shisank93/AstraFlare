-- AstraFlare Ground-Truth Evidence Schema (PostgreSQL + PostGIS Compatible)
-- Spatial Reference System: EPSG:4326 (WGS 84)

-- 1. GROUND TRUTH EVENTS TABLE (Independent Real-World Verified Events)
CREATE TABLE IF NOT EXISTS ground_truth_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    event_type VARCHAR(64) NOT NULL, -- 'NATURAL_WILDLAND_FIRE', 'LIKELY_INDUSTRIAL_INCIDENT', 'PERSISTENT_INDUSTRIAL_HEAT', 'CONFLICTING_EVIDENCE'
    source_name VARCHAR(128) NOT NULL, -- e.g. 'NASA_FIRMS_NRT_EVENT_CATALOG', 'GLOBAL_FOREST_WATCH', 'PESO_NDMA_INCIDENT_REGISTRY', 'MANUAL_VERIFIED'
    source_url VARCHAR(512),
    source_record_id VARCHAR(128),
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    geometry TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    matching_distance_m DOUBLE PRECISION,
    matching_time_hours DOUBLE PRECISION,
    source_confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED_EXTERNAL', -- 'VERIFIED_EXTERNAL', 'MANUAL_VERIFIED', 'WEAK_RULE', 'CONFLICTING_EVIDENCE'
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_gt_events_id ON ground_truth_events (event_id);
CREATE INDEX IF NOT EXISTS idx_gt_events_type ON ground_truth_events (event_type);
CREATE INDEX IF NOT EXISTS idx_gt_events_lat_lon ON ground_truth_events (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_gt_events_status ON ground_truth_events (verification_status);

-- 2. EVENT HOTSPOT MATCHES TABLE (Links Ground-Truth Events to FIRMS Observations)
CREATE TABLE IF NOT EXISTS event_hotspot_matches (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL REFERENCES ground_truth_events(event_id) ON DELETE CASCADE,
    hotspot_id VARCHAR(64) NOT NULL REFERENCES hotspots(id) ON DELETE CASCADE,
    match_distance_m DOUBLE PRECISION NOT NULL,
    match_time_hours DOUBLE PRECISION NOT NULL,
    match_confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, hotspot_id)
);

CREATE INDEX IF NOT EXISTS idx_event_matches_event ON event_hotspot_matches (event_id);
CREATE INDEX IF NOT EXISTS idx_event_matches_hotspot ON event_hotspot_matches (hotspot_id);
