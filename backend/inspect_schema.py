import sys, os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database.connection import get_supabase
supabase = get_supabase()

print("="*60)
print("1. field_visits columns:")
res = supabase.table('field_visits').select('*').limit(1).execute()
print('field_visits columns:', list(res.data[0].keys()) if res.data else 'EMPTY TABLE')

print("\n" + "="*60)
print("2. ai_verifications columns:")
res = supabase.table('ai_verifications').select('*').limit(1).execute()
print('ai_verifications columns:', list(res.data[0].keys()) if res.data else 'EMPTY TABLE')

print("\n" + "="*60)
print("3. alerts columns:")
res = supabase.table('alerts').select('*').limit(1).execute()
print('alerts columns:', list(res.data[0].keys()) if res.data else 'EMPTY TABLE')

print("\n" + "="*60)
print("4. maintenance_tasks table check:")
try:
    res = supabase.table('maintenance_tasks').select('*').limit(1).execute()
    print('maintenance_tasks columns:', list(res.data[0].keys()) if res.data else 'TABLE EXISTS BUT EMPTY')
except Exception as e:
    print('maintenance_tasks ERROR:', str(e))

print("\n" + "="*60)
print("5. plantations columns:")
res = supabase.table('plantations').select('*').limit(1).execute()
print('plantations columns:', list(res.data[0].keys()) if res.data else 'EMPTY TABLE')

print("\n" + "="*60)
print("6. ndvi_observations columns:")
res = supabase.table('ndvi_observations').select('*').limit(1).execute()
print('ndvi_observations columns:', list(res.data[0].keys()) if res.data else 'EMPTY TABLE')

print("\n" + "="*60)
print("7. Distinct verification_status values:")
res = supabase.table('field_visits').select('verification_status').execute()
statuses = set(d['verification_status'] for d in res.data)
print('verification_status values:', statuses)

print("\n" + "="*60)
print("8. ai_verifications ALL records:")
res = supabase.table('ai_verifications').select('*').execute()
print('ai_verifications count:', len(res.data))
for r in res.data:
    print(r)

print("\n" + "="*60)
print("9. alerts ALL records:")
res = supabase.table('alerts').select('*').execute()
print('alerts count:', len(res.data))
for r in res.data:
    print(r)

print("\n" + "="*60)
print("10. plantations with risk_score and status:")
res = supabase.table('plantations').select('id, name, risk_score, status').execute()
for r in res.data:
    print(r)

print("\n" + "="*60)
print("11. field_visits for plantation a1000001:")
res = supabase.table('field_visits').select('id, verification_status, server_timestamp, created_at, location_confidence, worker_name').eq('plantation_id', 'a1000001-0000-0000-0000-000000000001').execute()
for r in res.data:
    print(r)

print("\n" + "="*60)
print("12. ndvi_observations for plantation a1000001:")
res = supabase.table('ndvi_observations').select('observation_date, ndvi_value, data_source, health_status').eq('plantation_id', 'a1000001-0000-0000-0000-000000000001').order('observation_date').execute()
for r in res.data:
    print(r)
print("="*60)
