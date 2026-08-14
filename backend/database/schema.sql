-- ============================================
-- EcoTrack Database Schema
-- Supabase / PostgreSQL + PostGIS
-- ============================================

-- Enable PostGIS extension for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================
-- 1. PLANTATIONS — Core plantation records
-- ============================================
CREATE TABLE plantations (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name            TEXT NOT NULL,
    district        TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'Maharashtra',
    area_hectares   DECIMAL(10, 2) NOT NULL,
    saplings_planted INTEGER NOT NULL,
    current_saplings INTEGER,
    planting_date   DATE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'healthy'
                    CHECK (status IN ('healthy', 'warning', 'critical')),
    risk_score      INTEGER DEFAULT 50
                    CHECK (risk_score >= 0 AND risk_score <= 100),
    latitude        DECIMAL(10, 7) NOT NULL,
    longitude       DECIMAL(10, 7) NOT NULL,
    geom            GEOMETRY(Point, 4326),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-populate geom from lat/lng
CREATE OR REPLACE FUNCTION update_plantation_geom()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_plantation_geom
    BEFORE INSERT OR UPDATE OF latitude, longitude ON plantations
    FOR EACH ROW
    EXECUTE FUNCTION update_plantation_geom();

-- ============================================
-- 2. PLANTATION BOUNDARIES (P1 — optional)
-- ============================================
CREATE TABLE plantation_boundaries (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plantation_id   UUID REFERENCES plantations(id) ON DELETE CASCADE,
    boundary        GEOMETRY(Polygon, 4326),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. FIELD VISITS — Field worker submissions
-- ============================================
CREATE TABLE field_visits (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plantation_id   UUID REFERENCES plantations(id) ON DELETE CASCADE,
    worker_name     TEXT NOT NULL,
    gps_lat         DECIMAL(10, 7),
    gps_lng         DECIMAL(10, 7),
    gps_accuracy    DECIMAL(6, 2),
    photo_url       TEXT,
    visit_timestamp TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT,
    verification_status TEXT DEFAULT 'pending'
                    CHECK (verification_status IN ('pending', 'verified', 'flagged', 'rejected')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 4. AI VERIFICATIONS — Gemini + YOLO results
-- ============================================
CREATE TABLE ai_verifications (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    field_visit_id  UUID REFERENCES field_visits(id) ON DELETE CASCADE,
    tree_detected   BOOLEAN,
    health_assessment TEXT,
    condition_notes TEXT,
    confidence      DECIMAL(4, 2),
    gemini_response JSONB,
    yolo_count      INTEGER,
    yolo_response   JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 5. NDVI OBSERVATIONS — Vegetation health data
-- ============================================
CREATE TABLE ndvi_observations (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plantation_id   UUID REFERENCES plantations(id) ON DELETE CASCADE,
    observation_date DATE NOT NULL,
    ndvi_value      DECIMAL(5, 4) NOT NULL
                    CHECK (ndvi_value >= -1 AND ndvi_value <= 1),
    health_status   TEXT NOT NULL DEFAULT 'moderate'
                    CHECK (health_status IN ('poor', 'moderate', 'good', 'excellent')),
    data_source     TEXT NOT NULL DEFAULT 'seed'
                    CHECK (data_source IN ('seed', 'sentinel2', 'manual')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 6. ALERTS — System-generated warnings
-- ============================================
CREATE TABLE alerts (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plantation_id   UUID REFERENCES plantations(id) ON DELETE CASCADE,
    alert_type      TEXT NOT NULL
                    CHECK (alert_type IN ('ndvi_decline', 'maintenance_overdue', 'verification_failed', 'high_risk', 'low_survival')),
    severity        TEXT NOT NULL DEFAULT 'medium'
                    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message         TEXT NOT NULL,
    acknowledged    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 7. MAINTENANCE TASKS — Action items
-- ============================================
CREATE TABLE maintenance_tasks (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plantation_id   UUID REFERENCES plantations(id) ON DELETE CASCADE,
    alert_id        UUID REFERENCES alerts(id) ON DELETE SET NULL,
    problem         TEXT NOT NULL,
    risk_level      TEXT NOT NULL DEFAULT 'medium'
                    CHECK (risk_level IN ('low', 'medium', 'high')),
    recommended_action TEXT NOT NULL,
    assigned_to     TEXT,
    due_date        DATE,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed')),
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES for query performance
-- ============================================
CREATE INDEX idx_plantations_status ON plantations(status);
CREATE INDEX idx_plantations_geom ON plantations USING GIST(geom);
CREATE INDEX idx_field_visits_plantation ON field_visits(plantation_id);
CREATE INDEX idx_ndvi_plantation_date ON ndvi_observations(plantation_id, observation_date);
CREATE INDEX idx_alerts_plantation ON alerts(plantation_id);
CREATE INDEX idx_maintenance_status ON maintenance_tasks(status);
