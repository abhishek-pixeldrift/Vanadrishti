import os
import sys
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv('../.env')

from main import app
from database.connection import get_supabase

client = TestClient(app)
PLANTATION_ID = "a1000001-0000-0000-0000-000000000001"
CENTER_LAT = 20.0063
CENTER_LNG = 73.791

def get_test_photo():
    # create a dummy image file
    with open("dummy.jpg", "wb") as f:
        f.write(b"test image")
    return open("dummy.jpg", "rb")

def test_hard_rejection_blocks_gemini():
    """Test that a >1000m outside submission is rejected and blocks Gemini"""
    photo = get_test_photo()
    res = client.post("/field-visits/", data={
        "plantation_id": PLANTATION_ID,
        "worker_name": "Test Worker",
        "gps_lat": CENTER_LAT + 0.5, # Very far
        "gps_lng": CENTER_LNG,
        "gps_accuracy": 10.0
    }, files={"photo": ("dummy.jpg", photo, "image/jpeg")})
    
    assert res.status_code == 200
    visit = res.json()
    assert visit["verification_status"] == "rejected"
    visit_id = visit["id"]
    
    # Now try to verify
    verify_res = client.post(f"/field-visits/{visit_id}/verify")
    assert verify_res.status_code == 400
    assert "Cannot verify a rejected field visit" in verify_res.json()["detail"]
    print("[PASS] Hard rejection blocks Gemini")

def test_low_confidence_skips_gemini():
    """Test that LOW confidence (e.g. outside <=1000m) skips Gemini"""
    photo = get_test_photo()
    res = client.post("/field-visits/", data={
        "plantation_id": PLANTATION_ID,
        "worker_name": "Test Worker",
        "gps_lat": CENTER_LAT + 0.005, # Outside but <1000m
        "gps_lng": CENTER_LNG,
        "gps_accuracy": 100.0 # Bad accuracy
    }, files={"photo": ("dummy.jpg", photo, "image/jpeg")})
    
    visit = res.json()
    assert visit["verification_status"] == "flagged_location"
    
    # verify
    verify_res = client.post(f"/field-visits/{visit['id']}/verify")
    assert verify_res.status_code == 200
    ai_data = verify_res.json()
    assert ai_data["status"] == "pending_location_review"
    assert ai_data["confidence"] == 0.0 # Proves Gemini wasn't called
    print("[PASS] LOW confidence skips Gemini")

def test_high_confidence_calls_gemini():
    """Test that HIGH confidence continues to Gemini"""
    photo = get_test_photo()
    res = client.post("/field-visits/", data={
        "plantation_id": PLANTATION_ID,
        "worker_name": "Test Worker",
        "gps_lat": CENTER_LAT,
        "gps_lng": CENTER_LNG,
        "gps_accuracy": 10.0
    }, files={"photo": ("dummy.jpg", photo, "image/jpeg")})
    
    visit = res.json()
    assert visit["verification_status"] == "pending"
    
    # verify
    verify_res = client.post(f"/field-visits/{visit['id']}/verify")
    assert verify_res.status_code == 200
    ai_data = verify_res.json()
    
    # Since we use a dummy image, Gemini will either return a mock response (if key missing)
    # or fail to parse (if key present but image is bad), but it WON'T be pending_location_review.
    assert ai_data.get("status", "verified") == "verified"
    print("[PASS] High confidence calls Gemini")

if __name__ == "__main__":
    print("Running Phase 7 Gating Tests...")
    test_hard_rejection_blocks_gemini()
    test_low_confidence_skips_gemini()
    test_high_confidence_calls_gemini()
    
    # cleanup
    if os.path.exists("dummy.jpg"):
        os.remove("dummy.jpg")
    print("All Phase 7 tests passed!")
