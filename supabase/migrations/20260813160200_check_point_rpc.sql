-- Migration to add check_point_in_plantation RPC function
CREATE OR REPLACE FUNCTION check_point_in_plantation(
    p_lat DOUBLE PRECISION,
    p_lng DOUBLE PRECISION,
    p_plantation_id UUID
) RETURNS JSONB AS $$
DECLARE
    v_boundary GEOMETRY;
    v_point GEOMETRY;
    v_inside BOOLEAN;
    v_distance_meters DOUBLE PRECISION;
BEGIN
    -- Get the boundary geometry
    SELECT boundary INTO v_boundary
    FROM plantation_boundaries
    WHERE plantation_id = p_plantation_id
    LIMIT 1;

    IF v_boundary IS NULL THEN
        -- No boundary found, fallback to center point of plantation
        DECLARE
            v_center_geom GEOMETRY;
        BEGIN
            SELECT geom INTO v_center_geom
            FROM plantations
            WHERE id = p_plantation_id;
            
            IF v_center_geom IS NULL THEN
                RETURN jsonb_build_object(
                    'error', 'Plantation not found or no boundary/center available'
                );
            END IF;

            v_point := ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326);
            v_distance_meters := ST_Distance(v_center_geom::geography, v_point::geography);
            
            RETURN jsonb_build_object(
                'inside', (v_distance_meters <= 500), -- fallback radius 500m
                'distance_meters', v_distance_meters,
                'fallback_used', true
            );
        END;
    END IF;

    -- Create point geometry from lat/lng
    v_point := ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326);

    -- Check if point is inside boundary
    v_inside := ST_Contains(v_boundary, v_point);

    IF v_inside THEN
        v_distance_meters := 0;
    ELSE
        -- Calculate distance to boundary edge in meters using geography type for accuracy
        v_distance_meters := ST_Distance(v_boundary::geography, v_point::geography);
    END IF;

    RETURN jsonb_build_object(
        'inside', v_inside,
        'distance_meters', v_distance_meters,
        'fallback_used', false
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
