import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ndvi_service import get_ndvi_observations

# Nashik Hills Block A
plantation_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

print("Fetching NDVI for plantation:", plantation_id)
res = get_ndvi_observations(plantation_id, source="auto")
print("Metadata:", res["metadata"])
for obs in res["data"]:
    print(f"Date: {obs.get('observation_date')} | NDVI: {obs.get('ndvi_value')} | Source: {obs.get('data_source')}")

