"""
Phase 8B Verification: Test get_ndvi_observations caching, fallback, and API logic.
"""

import os
import sys
import json
from unittest.mock import patch
from datetime import datetime, timezone

# Setup paths
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from services.ndvi_service import get_ndvi_observations
from database.connection import get_supabase

# Test plantation
PLANTATION_ID = "a1000001-0000-0000-0000-000000000001"

def clean_sentinel2_data():
    """Remove any sentinel2 data inserted today to start fresh"""
    supabase = get_supabase()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    supabase.table("ndvi_observations").delete().eq("plantation_id", PLANTATION_ID).eq("data_source", "sentinel2").eq("observation_date", now).execute()

def print_result(name, res):
    print(f"\n--- {name} ---")
    print(f"Metadata: {json.dumps(res['metadata'])}")
    print(f"Data records: {len(res['data'])}")
    if res['data']:
        latest = res['data'][-1]
        print(f"Latest obs: {latest.get('observation_date')} | source: {latest.get('data_source')} | ndvi: {latest.get('ndvi_value')}")

def run_tests():
    print("=" * 70)
    print("PHASE 8B VERIFICATION: get_ndvi_observations")
    print("=" * 70)

    clean_sentinel2_data()

    checks = []

    # 1. Seed mode
    res_seed = get_ndvi_observations(PLANTATION_ID, source='seed')
    print_result("1. Seed Mode", res_seed)
    passed_seed = res_seed['metadata']['data_source'] == 'seed' and not res_seed['metadata']['fallback_used'] and all(d['data_source'] == 'seed' for d in res_seed['data'])
    checks.append(("Seed mode returns only seed data", passed_seed))

    # 2. Auto mode (Fresh EE call)
    print("\nFetching Auto Mode (Will call EE)...")
    res_auto1 = get_ndvi_observations(PLANTATION_ID, source='auto')
    print_result("2. Auto Mode (Fresh)", res_auto1)
    passed_auto1 = res_auto1['metadata']['data_source'] == 'sentinel2' and not res_auto1['metadata']['fallback_used'] and any(d['data_source'] == 'sentinel2' for d in res_auto1['data'])
    checks.append(("Auto mode calls EE and persists sentinel2 data", passed_auto1))

    # 3. Cached Auto mode
    print("\nFetching Auto Mode again (Should use Cache)...")
    with patch('services.ndvi_service.fetch_sentinel2_ndvi') as mock_fetch:
        mock_fetch.return_value = {"success": False, "error": "Should not be called"}
        res_auto2 = get_ndvi_observations(PLANTATION_ID, source='auto')
        print_result("3. Auto Mode (Cached)", res_auto2)
        passed_cache = res_auto2['metadata']['data_source'] == 'sentinel2' and mock_fetch.call_count == 0
        checks.append(("Auto mode uses cached data, no EE call", passed_cache))

    # 4. Sentinel2 mode
    print("\nFetching Sentinel2 Mode (Should use Cache)...")
    res_s2 = get_ndvi_observations(PLANTATION_ID, source='sentinel2')
    print_result("4. Sentinel2 Mode", res_s2)
    passed_s2 = res_s2['metadata']['data_source'] == 'sentinel2' and all(d['data_source'] == 'sentinel2' for d in res_s2['data'])
    checks.append(("Sentinel2 mode returns ONLY sentinel2 data", passed_s2))

    # 5. Simulated EE failure -> Fallback to seed
    print("\nSimulating EE Failure in Auto mode...")
    clean_sentinel2_data() # clear cache
    with patch('services.ndvi_service.fetch_sentinel2_ndvi') as mock_fetch_fail:
        mock_fetch_fail.return_value = {"success": False, "error": "Simulated Earth Engine Error", "boundary_fallback_used": False}
        res_fallback = get_ndvi_observations(PLANTATION_ID, source='auto')
        print_result("5. Auto Mode (EE Failure)", res_fallback)
        passed_fallback = res_fallback['metadata']['fallback_used'] is True and res_fallback['metadata']['data_source'] == 'seed' and "Simulated Earth Engine Error" in res_fallback['metadata']['failure_reason']
        checks.append(("Auto mode falls back to seed on EE failure", passed_fallback))

    print(f"\n{'=' * 70}")
    total = len(checks)
    passed_count = sum(1 for _, p in checks if p)
    print(f"RESULT: {passed_count}/{total} checks passed")
    for name, p in checks:
        print(f"[{'PASS' if p else 'FAIL'}] {name}")
    print("=" * 70)

    return passed_count == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
