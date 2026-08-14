import sys
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database.connection import get_supabase
from services.ndvi_service import fetch_sentinel2_ndvi

plantation_id = "a1000001-0000-0000-0000-000000000001"
supabase = get_supabase()

print("--- 1. Supabase NDVI Observations ---")
res = supabase.table("ndvi_observations").select("*").eq("plantation_id", plantation_id).order("observation_date").execute()
for obs in res.data:
    print(f"{obs['observation_date']} | {obs['data_source']} | NDVI: {obs['ndvi_value']}")

print("\n--- 2. EE Fetch diagnostics ---")
# March to August
now = datetime.now(timezone.utc)
for i in range(5, -1, -1):
    dt = now - timedelta(days=30 * i)
    first_day = dt.replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)
    last_day = next_month - timedelta(days=1)
    
    if first_day > now:
        continue
    if last_day > now:
        last_day = now
        
    start_str = first_day.strftime("%Y-%m-%d")
    end_str = last_day.strftime("%Y-%m-%d")
    
    print(f"\nMonth: {first_day.strftime('%Y-%m')} ({start_str} to {end_str})")
    
    res = fetch_sentinel2_ndvi(plantation_id, start_date=start_str, end_date=end_str)
    
    success = res.get("success")
    if success:
        print(f"  Success: True")
        print(f"  Scenes found (images_used): {res.get('images_used')}")
        print(f"  Valid pixels (pixel_count): {res.get('pixel_count')}")
        print(f"  NDVI Mean: {res.get('ndvi_mean')}")
        print(f"  Image Dates: {res.get('image_dates')}")
    else:
        print(f"  Success: False")
        print(f"  Error: {res.get('error')}")

