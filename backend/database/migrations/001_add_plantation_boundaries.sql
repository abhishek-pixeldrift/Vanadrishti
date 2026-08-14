-- Enable PostGIS if not already enabled (might require superuser, but often enabled on Supabase)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create the plantation boundaries table
CREATE TABLE IF NOT EXISTS plantation_boundaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plantation_id UUID REFERENCES plantations(id) ON DELETE CASCADE,
    boundary GEOGRAPHY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create spatial index for performance
CREATE INDEX IF NOT EXISTS plantation_boundaries_geom_idx 
    ON plantation_boundaries 
    USING GIST (boundary);

-- Create an RPC function to retrieve the boundary as GeoJSON easily via the REST API
CREATE OR REPLACE FUNCTION get_boundary_geojson(p_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT ST_AsGeoJSON(boundary)::JSON INTO result
    FROM plantation_boundaries
    WHERE plantation_id = p_id
    LIMIT 1;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
