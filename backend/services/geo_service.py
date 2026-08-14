from typing import Dict, Any

def validate_gps_metadata(coords: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the structural integrity and plausibility of raw GPS metadata.
    """
    is_valid = True
    reason = None
    
    accuracy = coords.get("gps_accuracy")
    if accuracy is not None and accuracy > 500:
        is_valid = False
        reason = "Accuracy > 500m"
        
    return {
        "valid": is_valid,
        "reason": reason
    }

from database.connection import get_supabase

def validate_point_in_boundary(lat: float, lng: float, plantation_id: str) -> Dict[str, Any]:
    """
    Validates if a given GPS point falls inside the PostGIS boundary for a plantation.
    Uses the check_point_in_plantation RPC.
    """
    try:
        supabase = get_supabase()
        res = supabase.rpc("check_point_in_plantation", {
            "p_lat": lat,
            "p_lng": lng,
            "p_plantation_id": plantation_id
        }).execute()
        
        if res.data:
            return res.data
            
        return {
            "inside": False,
            "distance_meters": float('inf'),
            "error": "No response from RPC"
        }
    except Exception as e:
        return {
            "inside": False,
            "distance_meters": float('inf'),
            "error": str(e)
        }

def calculate_location_confidence(gps_data: Dict[str, Any], boundary_result: Dict[str, Any], spoof_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates GPS metadata, geofence status, and anti-spoof heuristics into a final location confidence score.
    Max Score: 100
    - accuracy <= 50m: 30
    - inside geofence: 40
    - no spoof flags: 20
    - reasonable altitude: 10
    """
    score = 0
    
    # 1. Accuracy
    accuracy = gps_data.get("gps_accuracy")
    if accuracy is not None and accuracy <= 50:
        score += 30
    elif accuracy is not None and accuracy <= 100:
        score += 15
        
    # 2. Geofence
    if boundary_result.get("inside", False):
        score += 40
    elif boundary_result.get("distance_meters", float('inf')) <= 500:
        score += 20 # Partial score if slightly outside
        
    # 3. Spoofing
    if spoof_result.get("spoof_risk") == "LOW":
        score += 20
        
    # 4. Altitude (reasonable is non-zero, < 8000m)
    alt = gps_data.get("gps_altitude")
    if alt is not None and -100 < alt < 8000:
        score += 10
        
    if score >= 80:
        confidence_level = "HIGH"
    elif score >= 50:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
        
    return {
        "score": score,
        "confidence_level": confidence_level
    }
