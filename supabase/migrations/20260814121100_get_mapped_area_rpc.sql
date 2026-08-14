CREATE OR REPLACE FUNCTION get_mapped_area(p_plantation_id UUID)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    v_area DOUBLE PRECISION;
BEGIN
    SELECT ST_Area(boundary::geography) INTO v_area
    FROM plantation_boundaries
    WHERE plantation_id = p_plantation_id;
    
    RETURN v_area;
END;
$$ LANGUAGE plpgsql;
