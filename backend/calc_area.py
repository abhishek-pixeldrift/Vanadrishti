import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database.connection import get_supabase

supabase = get_supabase()

res = supabase.rpc("execute_sql", {"sql_query": """
SELECT 
    p.id, 
    p.name, 
    p.area_hectares AS display_area,
    ST_SRID(pb.boundary) as srid,
    GeometryType(pb.boundary) as geom_type,
    ST_Area(pb.boundary::geography) as area_sqm,
    ST_Area(pb.boundary::geography) / 10000.0 as area_ha
FROM plantations p
JOIN plantation_boundaries pb ON p.id = pb.plantation_id
LIMIT 1;
"""}).execute()

print(res.data)
