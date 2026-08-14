import os
import sys
from dotenv import load_dotenv
load_dotenv('../.env')
from datetime import datetime, timezone, timedelta

# Add current dir to path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.geo_service import validate_point_in_boundary, calculate_location_confidence
from services.anti_spoof_service import calculate_spoof_risk

PLANTATION_ID = "a1000001-0000-0000-0000-000000000001"
CENTER_LAT = 20.0063
CENTER_LNG = 73.791

def run_tests():
    print("Running M6B Tests...")
    
    # 1. Test Inside Boundary (Using center point)
    res_inside = validate_point_in_boundary(CENTER_LAT, CENTER_LNG, PLANTATION_ID)
    print(f"Inside Test: {res_inside}")
    assert res_inside.get("inside") == True, "Center point should be inside"
    
    # 2. Test Just Outside Boundary (+0.01 deg lat is ~1.1km, so +0.005 is ~500m)
    res_outside = validate_point_in_boundary(CENTER_LAT + 0.005, CENTER_LNG, PLANTATION_ID)
    print(f"Outside <=1000m Test: {res_outside}")
    assert res_outside.get("inside") == False, "Point should be outside"
    assert 100 < res_outside.get("distance_meters", 0) < 1000, "Should be between 100m and 1000m"
    
    # 3. Test >1000m Outside (+0.05 deg lat is ~5.5km)
    res_far = validate_point_in_boundary(CENTER_LAT + 0.05, CENTER_LNG, PLANTATION_ID)
    print(f"Outside >1000m Test: {res_far}")
    assert res_far.get("inside") == False
    assert res_far.get("distance_meters", 0) > 1000
    
    # 4. Impossible Travel Test
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    
    curr_coords = {
        "gps_lat": CENTER_LAT,
        "gps_lng": CENTER_LNG,
        "gps_accuracy": 10,
        "server_timestamp": now.isoformat(),
        "client_timestamp": now.isoformat()
    }
    
    # User was 500km away 1 hour ago
    user_history = [{
        "gps_lat": CENTER_LAT + 4.5, # ~500km away
        "gps_lng": CENTER_LNG,
        "visit_timestamp": one_hour_ago.isoformat()
    }]
    
    spoof_res = calculate_spoof_risk(curr_coords, user_history)
    print(f"Spoof Risk Test (Impossible Travel): {spoof_res}")
    assert spoof_res["spoof_risk"] in ["HIGH", "MEDIUM"]
    assert any("impossible_travel" in f for f in spoof_res["flags"])
    
    # 5. Suspiciously Perfect Accuracy Test
    curr_coords["gps_accuracy"] = 1.5
    spoof_res_acc = calculate_spoof_risk(curr_coords, [])
    print(f"Spoof Risk Test (Perfect Accuracy): {spoof_res_acc}")
    assert "suspiciously_perfect_accuracy" in spoof_res_acc["flags"]
    
    # 6. Confidence Scoring Test
    conf = calculate_location_confidence(
        gps_data={"gps_accuracy": 10, "gps_altitude": 100},
        boundary_result={"inside": True, "distance_meters": 0},
        spoof_result={"spoof_risk": "LOW", "flags": []}
    )
    print(f"Confidence Test (Perfect): {conf}")
    assert conf["score"] == 100
    assert conf["confidence_level"] == "HIGH"

    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
