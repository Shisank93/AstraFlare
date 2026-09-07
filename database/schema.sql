-- AstraFlare Core Database Schema (PostgreSQL + PostGIS Compatible)
-- Spatial Reference System: EPSG:4326 (WGS 84)

-- 1. HOTSPOTS TABLE (NASA FIRMS Observations & Thermal Anomalies)
CREATE TABLE IF NOT EXISTS hotspots (
    id VARCHAR(64) PRIMARY KEY,
    firms_id VARCHAR(64),
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    geom TEXT NOT NULL,
    acq_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    satellite VARCHAR(32) NOT NULL,
    instrument VARCHAR(32),
    brightness DOUBLE PRECISION CHECK (brightness IS NULL OR brightness >= 0),
    frp DOUBLE PRECISION NOT NULL CHECK (frp >= 0.0),
    confidence VARCHAR(16),
    daynight VARCHAR(4),
    data_source VARCHAR(32) NOT NULL DEFAULT 'REAL', -- Governance: 'REAL' vs 'SYNTHETIC_DEMO'
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hotspots_lat_lon ON hotspots (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_hotspots_timestamp ON hotspots (acq_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_hotspots_data_source ON hotspots (data_source);

-- 2. INDUSTRIAL SITES TABLE (OpenStreetMap Infrastructure Context)
CREATE TABLE IF NOT EXISTS industrial_sites (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR(64) UNIQUE,
    name VARCHAR(255),
    facility_type VARCHAR(64) NOT NULL,
    tags JSONB,
    geom TEXT NOT NULL,
    data_source VARCHAR(32) DEFAULT 'OSM',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industrial_sites_type ON industrial_sites (facility_type);

-- 3. LAND COVER TABLE (ESA WorldCover Reference Data)
CREATE TABLE IF NOT EXISTS land_cover (
    id SERIAL PRIMARY KEY,
    class_code INTEGER NOT NULL UNIQUE,
    class_name VARCHAR(64) NOT NULL,
    description TEXT,
    geom TEXT
);

INSERT INTO land_cover (class_code, class_name, description) VALUES
    (10, 'Tree cover', 'Tree cover / Forest area'),
    (20, 'Shrubland', 'Shrubland vegetation'),
    (30, 'Grassland', 'Natural grassland'),
    (40, 'Cropland', 'Agricultural farmland'),
    (50, 'Built-up', 'Urban, industrial, built-up infrastructure'),
    (60, 'Bare / sparse vegetation', 'Bare soil, sand, rocks'),
    (70, 'Snow and ice', 'Permanent snow or ice cover'),
    (80, 'Permanent water bodies', 'Lakes, rivers, reservoirs'),
    (90, 'Herbaceous wetland', 'Wetlands and marshes'),
    (95, 'Mangroves', 'Coastal mangrove forests'),
    (100, 'Moss and lichen', 'Tundra and high-altitude vegetation')
ON CONFLICT (class_code) DO NOTHING;

-- 4. WEATHER OBSERVATIONS TABLE (ERA5 / Environmental Data)
CREATE TABLE IF NOT EXISTS weather_observations (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    observation_time TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature_c DOUBLE PRECISION,
    wind_speed_kmh DOUBLE PRECISION CHECK (wind_speed_kmh IS NULL OR wind_speed_kmh >= 0),
    wind_direction_deg DOUBLE PRECISION CHECK (wind_direction_deg IS NULL OR (wind_direction_deg >= 0 AND wind_direction_deg <= 360)),
    relative_humidity_pct DOUBLE PRECISION CHECK (relative_humidity_pct IS NULL OR (relative_humidity_pct >= 0 AND relative_humidity_pct <= 100)),
    precipitation_mm DOUBLE PRECISION CHECK (precipitation_mm IS NULL OR precipitation_mm >= 0),
    source VARCHAR(64) DEFAULT 'ERA5',
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_observations (observation_time DESC);

-- 5. HISTORICAL FEATURES TABLE
CREATE TABLE IF NOT EXISTS historical_features (
    id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    historical_count_30d INTEGER DEFAULT 0,
    historical_count_365d INTEGER DEFAULT 0,
    historical_mean_frp DOUBLE PRECISION,
    historical_max_frp DOUBLE PRECISION,
    historical_std_frp DOUBLE PRECISION,
    frp_anomaly_score DOUBLE PRECISION,
    history_observation_count INTEGER DEFAULT 0,
    anomaly_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hist_features_hotspot ON historical_features (hotspot_id);

-- 6. PREDICTIONS TABLE
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    predicted_class VARCHAR(64) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    is_abstained BOOLEAN DEFAULT FALSE,
    risk_score DOUBLE PRECISION NOT NULL,
    prob_industrial_incident DOUBLE PRECISION,
    prob_persistent_heat DOUBLE PRECISION,
    prob_wildland_fire DOUBLE PRECISION,
    model_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_hotspot ON predictions (hotspot_id);
CREATE INDEX IF NOT EXISTS idx_predictions_class ON predictions (predicted_class);

-- 7. EVIDENCE TABLE
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id SERIAL PRIMARY KEY,
    hotspot_id VARCHAR(64) REFERENCES hotspots(id) ON DELETE CASCADE,
    evidence_type VARCHAR(32) NOT NULL,
    feature_name VARCHAR(64) NOT NULL,
    feature_value VARCHAR(128) NOT NULL,
    contribution DOUBLE PRECISION,
    human_readable_statement TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_hotspot ON evidence (hotspot_id);

-- 8. REVIEWS TABLE
CREATE TABLE IF NOT EXISTS reviews (
    review_id SERIAL PRIMARY KEY,
    event_id VARCHAR(64),
    hotspot_id VARCHAR(64),
    original_prediction VARCHAR(64) DEFAULT 'UNKNOWN',
    final_classification VARCHAR(64) NOT NULL,
    reviewer VARCHAR(128) DEFAULT 'analyst',
    decision VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    review_status VARCHAR(32) DEFAULT 'PENDING',
    notes TEXT,
    analyst_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE reviews ADD COLUMN IF NOT EXISTS event_id VARCHAR(64);
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS reviewer VARCHAR(128) DEFAULT 'analyst';
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS decision VARCHAR(64) DEFAULT 'PENDING';
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS analyst_note TEXT;

CREATE INDEX IF NOT EXISTS idx_reviews_event_id ON reviews (event_id);
CREATE INDEX IF NOT EXISTS idx_reviews_hotspot ON reviews (hotspot_id);

-- 9. PHYSICAL EVENTS TABLE (Physical Event Clusters & Phase 3 Intelligence)
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(64) PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    centroid_lat DOUBLE PRECISION NOT NULL CHECK (centroid_lat >= -90 AND centroid_lat <= 90),
    centroid_lon DOUBLE PRECISION NOT NULL CHECK (centroid_lon >= -180 AND centroid_lon <= 180),
    geom TEXT NOT NULL,
    duration_hours DOUBLE PRECISION DEFAULT 0.0,
    observation_count INTEGER NOT NULL DEFAULT 1,
    spatial_extent_m DOUBLE PRECISION DEFAULT 0.0,
    max_frp DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    mean_frp DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    std_frp DOUBLE PRECISION DEFAULT 0.0,
    max_brightness DOUBLE PRECISION DEFAULT 0.0,
    mean_brightness DOUBLE PRECISION DEFAULT 0.0,
    confidence_high_ratio DOUBLE PRECISION DEFAULT 0.0,
    satellite_count INTEGER DEFAULT 1,
    industrial_distance_m DOUBLE PRECISION,
    industrial_site_count_250m INTEGER DEFAULT 0,
    industrial_site_count_1km INTEGER DEFAULT 0,
    industrial_site_count_5km INTEGER DEFAULT 0,
    worldcover_class INTEGER,
    historical_count INTEGER DEFAULT 0,
    historical_mean_frp DOUBLE PRECISION,
    historical_max_frp DOUBLE PRECISION,
    historical_std_frp DOUBLE PRECISION,
    historical_anomaly_zscore DOUBLE PRECISION,
    historical_status VARCHAR(32) DEFAULT 'NO_PRIOR_HISTORY',
    data_source VARCHAR(32) NOT NULL DEFAULT 'REAL',
    data_quality_status VARCHAR(32) DEFAULT 'HIGH',
    evidence_status VARCHAR(32) DEFAULT 'SUFFICIENT',
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    risk_level VARCHAR(16) NOT NULL DEFAULT 'LOW',
    investigation_priority VARCHAR(16) NOT NULL DEFAULT 'LOW',
    human_review_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_lat_lon ON events (centroid_lat, centroid_lon);
CREATE INDEX IF NOT EXISTS idx_events_risk_score ON events (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_events_risk_level ON events (risk_level);
CREATE INDEX IF NOT EXISTS idx_events_priority ON events (investigation_priority);
CREATE INDEX IF NOT EXISTS idx_events_review ON events (human_review_required);
CREATE INDEX IF NOT EXISTS idx_events_data_source ON events (data_source);

