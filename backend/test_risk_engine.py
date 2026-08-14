"""
EcoTrack Phase 9 — Risk Engine Tests.

Tests:
  A: HEALTHY scenario
  B: WARNING scenario
  C: CRITICAL scenario
  D: Missing data policies
  E: Alert deduplication
  F: Telegram failure resilience
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from services.risk_engine import (
    calculate_risk_score,
    _calculate_ndvi_component,
    _calculate_ai_health_component,
    _calculate_visit_recency_component,
    _calculate_location_trust_component,
    _calculate_maintenance_component,
)
from services.notify_service import send_telegram
from database.connection import get_supabase

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def test_a_healthy():
    """Test A: HEALTHY scenario — Nashik Hills Block A.
    Has real Sentinel-2 NDVI, a verified visit, no maintenance issues.
    Expected: low/moderate risk score."""
    print("\n═══ Test A: HEALTHY Scenario ═══")
    pid = "a1000001-0000-0000-0000-000000000001"
    result = calculate_risk_score(pid)

    check("Result has risk_score", "risk_score" in result, str(result.keys()))
    check("Result has risk_level", "risk_level" in result)
    check("Result has components", "components" in result)
    check("Result has missing_inputs", "missing_inputs" in result)
    check("Result has generated_at", "generated_at" in result)
    check("risk_score is int", isinstance(result["risk_score"], int), type(result["risk_score"]))

    # This plantation has sentinel2 NDVI, 1 verified visit (old), no AI, no location_confidence on visit
    # Expected: NDVI exists but low values, no AI result, old visit, no location trust
    print(f"  Score: {result['risk_score']}/100 ({result['risk_level']})")
    for name, comp in result["components"].items():
        print(f"    {name}: {comp['score']}/{comp['max']} (source: {comp.get('source', '?')})")

    check("NDVI source is sentinel2", result["components"]["ndvi"]["source"] == "sentinel2")
    check("NDVI source is NOT seed", result["components"]["ndvi"]["source"] != "seed")
    check("Total is sum of components",
          result["risk_score"] == sum(c["score"] for c in result["components"].values()),
          f"total={result['risk_score']} vs sum={sum(c['score'] for c in result['components'].values())}")


def test_b_warning():
    """Test B: WARNING scenario — Pune Western Ghats B.
    Has seed NDVI only (no sentinel2), so risk engine should report no_sentinel2_ndvi."""
    print("\n═══ Test B: WARNING Scenario ═══")
    pid = "a1000001-0000-0000-0000-000000000002"
    result = calculate_risk_score(pid)

    print(f"  Score: {result['risk_score']}/100 ({result['risk_level']})")
    for name, comp in result["components"].items():
        print(f"    {name}: {comp['score']}/{comp['max']} (source: {comp.get('source', '?')})")

    # This plantation has only seed NDVI, which the risk engine must NOT use
    check("NDVI does not use seed data",
          result["components"]["ndvi"]["source"] in ("none", "sentinel2"),
          f"source={result['components']['ndvi']['source']}")
    check("Missing inputs includes NDVI if no sentinel2",
          "no_sentinel2_ndvi" in result["missing_inputs"] or result["components"]["ndvi"]["source"] == "sentinel2",
          str(result["missing_inputs"]))
    check("Total is sum of components",
          result["risk_score"] == sum(c["score"] for c in result["components"].values()))


def test_c_critical():
    """Test C: CRITICAL scenario — Ratnagiri Coastal C.
    Plantation marked critical with no verified visits, no AI, etc."""
    print("\n═══ Test C: CRITICAL Scenario ═══")
    pid = "a1000001-0000-0000-0000-000000000003"
    result = calculate_risk_score(pid)

    print(f"  Score: {result['risk_score']}/100 ({result['risk_level']})")
    for name, comp in result["components"].items():
        print(f"    {name}: {comp['score']}/{comp['max']} (source: {comp.get('source', '?')})")
    print(f"  Missing: {result['missing_inputs']}")

    # Should have high risk from multiple missing components
    check("Risk level is WARNING or CRITICAL",
          result["risk_level"] in ("WARNING", "CRITICAL"),
          result["risk_level"])
    check("Multiple missing inputs",
          len(result["missing_inputs"]) >= 2,
          f"missing={result['missing_inputs']}")


def test_d_missing_data():
    """Test D: Missing data policies."""
    print("\n═══ Test D: Missing Data Policies ═══")

    # Test NDVI component with a plantation that has no sentinel2 data
    ndvi = _calculate_ndvi_component("a1000001-0000-0000-0000-000000000004")
    print(f"  NDVI (Satara Ridge D): score={ndvi['score']}/{ndvi['max']}, source={ndvi['source']}")

    # If no sentinel2 data, should get uncertainty score of 20, not catastrophic 35
    if ndvi["source"] == "none":
        check("No NDVI → score 20 (not catastrophic)", ndvi["score"] == 20, f"score={ndvi['score']}")
    else:
        check("Has sentinel2 NDVI", ndvi["source"] == "sentinel2")

    # Test AI health with plantation that has no AI verifications
    ai = _calculate_ai_health_component("a1000001-0000-0000-0000-000000000004")
    print(f"  AI (Satara Ridge D): score={ai['score']}/{ai['max']}, source={ai['source']}")
    if ai["source"] == "none":
        check("No AI → score 15 (not maximum 25)", ai["score"] == 15, f"score={ai['score']}")

    # Test visit recency with plantation with no visits
    visit = _calculate_visit_recency_component("a1000001-0000-0000-0000-000000000004")
    print(f"  Visit (Satara Ridge D): score={visit['score']}/{visit['max']}, source={visit['source']}")
    if visit["source"] == "none":
        check("No visit → score 20 (full penalty)", visit["score"] == 20, f"score={visit['score']}")

    # Test maintenance with no tasks
    maint = _calculate_maintenance_component("a1000001-0000-0000-0000-000000000004")
    print(f"  Maintenance (Satara Ridge D): score={maint['score']}/{maint['max']}")
    check("No maintenance → score 0 (no penalty)", maint["score"] == 0, f"score={maint['score']}")

    # Test location trust with no trust data
    trust = _calculate_location_trust_component("a1000001-0000-0000-0000-000000000004")
    print(f"  Trust (Satara Ridge D): score={trust['score']}/{trust['max']}, source={trust['source']}")
    if trust["source"] == "none":
        check("No trust → score 8 (moderate penalty)", trust["score"] == 8, f"score={trust['score']}")


def test_e_alert_dedup():
    """Test E: Alert deduplication — scan twice, verify no duplicate HIGH alerts."""
    print("\n═══ Test E: Alert Deduplication ═══")
    from routers.alerts import run_risk_engine_scan, ScanRequest

    # First scan
    req = ScanRequest(token=None, chat_id=None)
    res1 = run_risk_engine_scan(req)
    print(f"  Scan 1: {res1['new_alerts']} new alerts")

    # Second scan
    res2 = run_risk_engine_scan(req)
    print(f"  Scan 2: {res2['new_alerts']} new alerts")
    check("Second scan creates 0 new alerts (dedup works)", res2["new_alerts"] == 0, f"new_alerts={res2['new_alerts']}")

    # Verify no duplicate unacknowledged dynamic_risk_critical alerts per plantation
    supabase = get_supabase()
    for pid_suffix in range(1, 6):
        pid = f"a1000001-0000-0000-0000-00000000000{pid_suffix}"
        alerts_res = supabase.table("alerts") \
            .select("id") \
            .eq("plantation_id", pid) \
            .eq("acknowledged", False) \
            .eq("alert_type", "dynamic_risk_critical") \
            .execute()
        count = len(alerts_res.data or [])
        check(f"  Plantation {pid_suffix}: ≤1 unacknowledged critical alert", count <= 1, f"count={count}")


def test_f_telegram_failure():
    """Test F: Telegram failure resilience."""
    print("\n═══ Test F: Telegram Failure ═══")

    # Test with invalid credentials
    result = send_telegram(
        "Test message",
        override_token="INVALID_TOKEN_12345",
        override_chat_id="INVALID_CHAT",
    )
    check("Telegram returns failure without crashing", result["success"] == False)
    check("Error message provided", result["error"] is not None, str(result))

    # Test with no credentials
    result2 = send_telegram("Test message")
    check("No credentials returns failure gracefully",
          result2["success"] == False,
          str(result2))


def test_risk_levels():
    """Verify risk level boundaries."""
    print("\n═══ Test: Risk Level Boundaries ═══")

    # Run risk for all plantations and verify level assignment
    for i in range(1, 6):
        pid = f"a1000001-0000-0000-0000-00000000000{i}"
        result = calculate_risk_score(pid)
        score = result["risk_score"]
        level = result["risk_level"]

        if score <= 39:
            expected = "HEALTHY"
        elif score <= 59:
            expected = "WARNING"
        else:
            expected = "CRITICAL"

        check(f"  Plantation {i}: score={score} → {level}",
              level == expected,
              f"expected={expected}, got={level}")


if __name__ == "__main__":
    print("=" * 60)
    print("EcoTrack Phase 9 — Risk Engine Tests")
    print("=" * 60)

    test_a_healthy()
    test_b_warning()
    test_c_critical()
    test_d_missing_data()
    test_e_alert_dedup()
    test_f_telegram_failure()
    test_risk_levels()

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
