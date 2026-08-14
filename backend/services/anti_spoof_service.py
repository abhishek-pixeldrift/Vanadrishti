from typing import Dict, Any, List
import math
from datetime import datetime

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_spoof_risk(submission: Dict[str, Any], user_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a submission against user history and standard anti-spoofing heuristics.
    """
    flags = []
    
    # 1. Suspiciously perfect accuracy (<3m)
    accuracy = submission.get("gps_accuracy")
    if accuracy is not None and accuracy < 3:
        flags.append("suspiciously_perfect_accuracy")
        
    # 2. Timestamp drift (>60s)
    client_ts_str = submission.get("client_timestamp")
    server_ts_str = submission.get("server_timestamp")
    if client_ts_str and server_ts_str:
        try:
            # Handle ISO formats
            c_ts = datetime.fromisoformat(client_ts_str.replace("Z", "+00:00"))
            s_ts = datetime.fromisoformat(server_ts_str.replace("Z", "+00:00"))
            drift = abs((s_ts - c_ts).total_seconds())
            if drift > 60:
                flags.append("timestamp_drift_>60s")
        except ValueError:
            pass

    # Compare with history
    if user_history and len(user_history) > 0:
        last_visit = user_history[0] # assuming ordered by time descending
        
        last_lat = last_visit.get("gps_lat")
        last_lng = last_visit.get("gps_lng")
        curr_lat = submission.get("gps_lat")
        curr_lng = submission.get("gps_lng")
        
        # 3. Duplicate coordinates
        if last_lat == curr_lat and last_lng == curr_lng and curr_lat is not None:
            flags.append("duplicate_coordinates")
            
        # 4. Impossible Travel (>200 km/h)
        last_ts_str = last_visit.get("visit_timestamp")
        if last_lat and last_lng and curr_lat and curr_lng and last_ts_str and server_ts_str:
            try:
                l_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
                s_ts = datetime.fromisoformat(server_ts_str.replace("Z", "+00:00"))
                hours_diff = abs((s_ts - l_ts).total_seconds()) / 3600.0
                
                if hours_diff > 0:
                    dist_meters = _haversine(curr_lat, curr_lng, last_lat, last_lng)
                    km_h = (dist_meters / 1000.0) / hours_diff
                    if km_h > 200:
                        flags.append(f"impossible_travel_{int(km_h)}kmh")
            except ValueError:
                pass

    risk_level = "HIGH" if len(flags) >= 2 else "MEDIUM" if len(flags) == 1 else "LOW"
    
    return {
        "spoof_risk": risk_level,
        "flags": flags,
        "score": len(flags) * 10
    }
