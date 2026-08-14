-- Add advanced GPS metadata and anti-spoofing columns to field_visits table
ALTER TABLE field_visits
ADD COLUMN IF NOT EXISTS gps_altitude FLOAT,
ADD COLUMN IF NOT EXISTS gps_heading FLOAT,
ADD COLUMN IF NOT EXISTS gps_speed FLOAT,
ADD COLUMN IF NOT EXISTS client_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS server_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS user_agent TEXT,
ADD COLUMN IF NOT EXISTS location_confidence JSONB;
