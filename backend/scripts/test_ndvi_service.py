"""
Phase 8A Verification: Test fetch_sentinel2_ndvi against a real plantation.

Tests:
1. Earth Engine query succeeds.
2. Real Sentinel-2 imagery is used (provenance check).
3. NDVI is calculated (non-null mean/median).
4. Returned result contains real provenance metadata.
5. No seed/mock data is involved (data_source == 'sentinel2').
"""

import os
import sys
import json

# Setup paths
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from services.ndvi_service import fetch_sentinel2_ndvi

# Test plantation: Nashik Hills Block A (known to have boundary + imagery)
PLANTATION_ID = "a1000001-0000-0000-0000-000000000001"


def test_real_sentinel2_ndvi():
    print("=" * 70)
    print("PHASE 8A VERIFICATION: fetch_sentinel2_ndvi()")
    print("=" * 70)

    print(f"\nPlantation: {PLANTATION_ID}")
    print("Calling fetch_sentinel2_ndvi()...\n")

    result = fetch_sentinel2_ndvi(PLANTATION_ID)

    # Print full result
    print("--- Full Result ---")
    print(json.dumps(result, indent=2, default=str))
    print()

    # Run verification checks
    checks = []

    # Check 1: Earth Engine query succeeds
    passed = result.get("success") is True
    checks.append(("Earth Engine query succeeds", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 1. Earth Engine query succeeds")

    # Check 2: Real Sentinel-2 imagery is used
    passed = (
        result.get("source") == "COPERNICUS/S2_SR_HARMONIZED"
        and result.get("images_used", 0) > 0
        and result.get("source_identifier", "unknown") != "unknown"
    )
    checks.append(("Real Sentinel-2 imagery used", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 2. Real Sentinel-2 imagery used")
    if passed:
        print(f"       Product: {result.get('source_identifier')}")
        print(f"       Spacecraft: {result.get('spacecraft')}")
        print(f"       Images: {result.get('images_used')}")

    # Check 3: NDVI calculated successfully
    ndvi_mean = result.get("ndvi_mean")
    ndvi_median = result.get("ndvi_median")
    passed = (
        ndvi_mean is not None
        and ndvi_median is not None
        and -1.0 <= ndvi_mean <= 1.0
        and -1.0 <= ndvi_median <= 1.0
    )
    checks.append(("NDVI calculated successfully", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 3. NDVI calculated successfully")
    if ndvi_mean is not None:
        print(f"       Mean:   {ndvi_mean:.4f}")
        print(f"       Median: {ndvi_median:.4f}")
        print(f"       StdDev: {result.get('ndvi_stddev', 'N/A')}")
        print(f"       Min:    {result.get('ndvi_min', 'N/A')}")
        print(f"       Max:    {result.get('ndvi_max', 'N/A')}")
        print(f"       Pixels: {result.get('pixel_count', 'N/A')}")

    # Check 4: Real provenance metadata present
    passed = (
        result.get("source_identifier") is not None
        and result.get("spacecraft") is not None
        and result.get("cloud_coverage_assessment") is not None
        and result.get("image_dates") is not None
        and len(result.get("image_dates", [])) > 0
    )
    checks.append(("Real provenance metadata present", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 4. Real provenance metadata present")
    if passed:
        dates = result.get("image_dates", [])
        print(f"       Dates: {', '.join(dates[:5])}{'...' if len(dates) > 5 else ''}")
        print(f"       Cloud: {result.get('cloud_coverage_assessment')}%")
        print(f"       Baseline: {result.get('processing_baseline')}")

    # Check 5: No seed/mock data involved
    passed = result.get("data_source") == "sentinel2"
    checks.append(("data_source is sentinel2 (not seed/mock)", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 5. data_source is 'sentinel2' (not seed/mock)")

    # Check 6: Used actual boundary polygon (not fallback)
    passed = result.get("boundary_fallback_used") is False
    checks.append(("Used authorized plantation polygon", passed))
    print(f"[{'PASS' if passed else 'FAIL'}] 6. Used authorized plantation polygon (not fallback)")

    # Summary
    total = len(checks)
    passed_count = sum(1 for _, p in checks if p)
    print(f"\n{'=' * 70}")
    print(f"RESULT: {passed_count}/{total} checks passed")
    if passed_count == total:
        print("PHASE 8A VERIFICATION: ALL PASSED")
    else:
        failed = [name for name, p in checks if not p]
        print(f"FAILED: {', '.join(failed)}")
    print("=" * 70)

    return passed_count == total


if __name__ == "__main__":
    success = test_real_sentinel2_ndvi()
    sys.exit(0 if success else 1)
