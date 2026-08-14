import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database.connection import get_supabase

supabase = get_supabase()

print("--- Plantation Boundaries ---")
res = supabase.table("plantation_boundaries").select("*").limit(1).execute()
print(res.data)

print("--- Field Visits ---")
res2 = supabase.table("field_visits").select("*").limit(2).execute()
print(res2.data)

print("--- Alerts ---")
res3 = supabase.table("alerts").select("*").limit(2).execute()
print(res3.data)
