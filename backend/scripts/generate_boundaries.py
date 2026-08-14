import os
import math
import random
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from the root .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY")
    return create_client(url, key)

def generate_polygon(lat: float, lng: float, radius_m: float = 600, points: int = 12) -> str:
    # 1 degree of latitude is approx 111,320 meters
    lat_degree_m = 111320
    # 1 degree of longitude is approx 111,320 * cos(lat) meters
    lng_degree_m = 111320 * math.cos(math.radians(lat))
    
    coordinates = []
    angle_step = 2 * math.pi / points
    
    for i in range(points):
        angle = i * angle_step
        # Randomize radius between 400m and 800m to make irregular polygons
        r = radius_m + random.uniform(-200, 200)
        
        # Calculate coordinate offsets
        d_lat = (r * math.sin(angle)) / lat_degree_m
        d_lng = (r * math.cos(angle)) / lng_degree_m
        
        point_lat = lat + d_lat
        point_lng = lng + d_lng
        coordinates.append((point_lng, point_lat)) # PostGIS expects Longitude, Latitude
        
    # Close the polygon by repeating the first point
    coordinates.append(coordinates[0])
    
    # Create WKT (Well-Known Text) string
    coords_str = ", ".join([f"{lon} {lat}" for lon, lat in coordinates])
    wkt = f"POLYGON(({coords_str}))"
    return wkt

def main():
    supabase = get_supabase()
    print("Fetching plantations...")
    response = supabase.table("plantations").select("id, latitude, longitude").execute()
    plantations = response.data
    
    if not plantations:
        print("No plantations found!")
        return
        
    print(f"Found {len(plantations)} plantations. Generating boundaries...")
    
    for p in plantations:
        p_id = p["id"]
        lat = p["latitude"]
        lng = p["longitude"]
        
        wkt = generate_polygon(lat, lng)
        
        # PostgREST auto-casts WKT strings to Geography types
        try:
            res = supabase.table("plantation_boundaries").insert({
                "plantation_id": p_id,
                "boundary": wkt
            }).execute()
            print(f"Inserted boundary for plantation {p_id}")
        except Exception as e:
            print(f"Failed to insert boundary for {p_id}: {e}")

if __name__ == "__main__":
    main()
