import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from services.ndvi_service import get_ndvi_observations

plantation_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

print("Fetching NDVI for plantation:", plantation_id)
res = get_ndvi_observations(plantation_id, source="auto")
print("Metadata:", res["metadata"])
for obs in res["data"]:
    print(f"Date: {obs.get('observation_date')} | NDVI: {obs.get('ndvi_value')} | Source: {obs.get('data_source')}")
