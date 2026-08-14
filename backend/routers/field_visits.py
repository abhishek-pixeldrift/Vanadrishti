import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
from database.connection import get_supabase
import math
from datetime import datetime, timezone
from services.ai_service import verify_image_with_gemini
from models.schemas import FieldVisit, AIVerification
from services.geo_service import validate_gps_metadata, validate_point_in_boundary, calculate_location_confidence
from services.anti_spoof_service import calculate_spoof_risk

router = APIRouter(prefix="/field-visits", tags=["field_visits"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=FieldVisit)
async def create_field_visit(
    plantation_id: str = Form(...),
    worker_name: str = Form(...),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    gps_accuracy: Optional[float] = Form(None),
    gps_altitude: Optional[float] = Form(None),
    gps_heading: Optional[float] = Form(None),
    gps_speed: Optional[float] = Form(None),
    client_timestamp: Optional[str] = Form(None),
    user_agent: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    photo: UploadFile = File(...)
):
    """Submit a field visit with an image upload."""
    # 1. Save Image
    file_extension = os.path.splitext(photo.filename)[1]
    filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
        
    photo_url = f"/uploads/{filename}"
    

    # 2. Base Validation
    server_timestamp = datetime.now(timezone.utc).isoformat()
    coords_dict = {
        "gps_lat": gps_lat,
        "gps_lng": gps_lng,
        "gps_accuracy": gps_accuracy,
        "gps_altitude": gps_altitude,
        "gps_heading": gps_heading,
        "gps_speed": gps_speed,
        "client_timestamp": client_timestamp,
        "user_agent": user_agent,
        "server_timestamp": server_timestamp
    }
    
    validation = validate_gps_metadata(coords_dict)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=f"Invalid GPS Data: {validation['reason']}")

    supabase = get_supabase()
    status = "pending"
    location_confidence = {}
    
    if gps_lat is not None and gps_lng is not None:
        # 3. Geofence Check (PostGIS)
        boundary_result = validate_point_in_boundary(gps_lat, gps_lng, plantation_id)
        dist = boundary_result.get("distance_meters", float('inf'))
        
        # Immediate rejection for > 1000m
        if not boundary_result.get("inside") and dist > 1000:
            status = "rejected"
            note_str = f"[FRAUD FLAG: Location {int(dist)}m outside boundary. Rejected.]"
            notes = f"{notes} {note_str}" if notes else note_str
            
            # Save rejection immediately
            visit_data = {
                "plantation_id": plantation_id,
                "worker_name": worker_name,
                "gps_lat": gps_lat,
                "gps_lng": gps_lng,
                "gps_accuracy": gps_accuracy,
                "gps_altitude": gps_altitude,
                "gps_heading": gps_heading,
                "gps_speed": gps_speed,
                "client_timestamp": client_timestamp,
                "server_timestamp": server_timestamp,
                "user_agent": user_agent,
                "notes": notes,
                "photo_url": photo_url,
                "verification_status": status,
                "location_confidence": boundary_result
            }
            res = supabase.table("field_visits").insert(visit_data).execute()
            if not res.data:
                raise HTTPException(status_code=500, detail="Failed to save rejected visit")
            return res.data[0]

        # 4. Anti-Spoofing Analysis
        # Get user history (last 5 visits)
        history_res = supabase.table("field_visits").select("*").eq("worker_name", worker_name).order("visit_timestamp", desc=True).limit(5).execute()
        user_history = history_res.data if history_res.data else []
        
        spoof_result = calculate_spoof_risk(coords_dict, user_history)
        
        # 5. Location Confidence Calculation
        confidence_result = calculate_location_confidence(coords_dict, boundary_result, spoof_result)
        
        location_confidence = {
            "boundary": boundary_result,
            "spoof": spoof_result,
            "confidence": confidence_result
        }
        
        # Safe location decisions
        if confidence_result["confidence_level"] == "LOW" or spoof_result["spoof_risk"] == "HIGH":
            status = "flagged_location"
            note_str = f"[WARNING: Suspicious Location. Confidence: {confidence_result['score']}/100]"
            notes = f"{notes} {note_str}" if notes else note_str
        elif not boundary_result.get("inside"):
            # Distance is <= 1000m (handled above), but still outside
            note_str = f"[WARNING: Location {int(dist)}m outside boundary]"
            notes = f"{notes} {note_str}" if notes else note_str

    # 6. Save to Database
    visit_data = {
        "plantation_id": plantation_id,
        "worker_name": worker_name,
        "gps_lat": gps_lat,
        "gps_lng": gps_lng,
        "gps_accuracy": gps_accuracy,
        "gps_altitude": gps_altitude,
        "gps_heading": gps_heading,
        "gps_speed": gps_speed,
        "client_timestamp": client_timestamp,
        "server_timestamp": server_timestamp,
        "user_agent": user_agent,
        "notes": notes,
        "photo_url": photo_url,
        "verification_status": status,
        "location_confidence": location_confidence
    }
    
    response = supabase.table("field_visits").insert(visit_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save field visit")
        
    return response.data[0]


@router.post("/{visit_id}/verify", response_model=AIVerification)
async def verify_field_visit(visit_id: str):
    """Trigger AI verification for a specific field visit."""
    supabase = get_supabase()
    
    # 1. Get the field visit
    visit_res = supabase.table("field_visits").select("*").eq("id", visit_id).execute()
    if not visit_res.data:
        raise HTTPException(status_code=404, detail="Field visit not found")
        
    visit = visit_res.data[0]
    if not visit.get("photo_url"):
        raise HTTPException(status_code=400, detail="Field visit has no photo")
        
    # Extract filename from photo_url (e.g. /uploads/uuid.jpg -> uuid.jpg)
    filename = visit["photo_url"].split("/")[-1]
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")
        
    # Ensure rejected submissions can't reach Gemini
    if visit.get("verification_status") == "rejected":
        raise HTTPException(status_code=400, detail="Cannot verify a rejected field visit")
        
    # Phase 7 Gating: check location confidence
    loc_conf = visit.get("location_confidence", {})
    conf_level = loc_conf.get("confidence", {}).get("confidence_level", "LOW") if loc_conf else "LOW"
    
    if conf_level == "LOW":
        # Skip Gemini entirely, return early
        supabase.table("field_visits").update({"verification_status": "pending_location_review"}).eq("id", visit_id).execute()
        return {
            "status": "pending_location_review",
            "message": "Location confidence too low \u2014 flagged for officer review",
            "location_confidence": loc_conf,
            "tree_detected": False,
            "health_assessment": "poor",
            "condition_notes": "",
            "confidence": 0.0
        }
        
    # 2. Call Gemini AI Service for MEDIUM/HIGH confidence
    ai_result = await verify_image_with_gemini(file_path)
    
    # 3. Save AI Verification Result
    verification_data = {
        "field_visit_id": visit_id,
        "tree_detected": ai_result.get("tree_detected", False),
        "health_assessment": ai_result.get("health_assessment", "poor"),
        "condition_notes": ai_result.get("condition_notes", ""),
        "confidence": ai_result.get("confidence", 0.0)
    }
    
    verification_res = supabase.table("ai_verifications").insert(verification_data).execute()
    
    # 4. Update Field Visit Status
    status = "verified" if ai_result.get("tree_detected") else "flagged"
    supabase.table("field_visits").update({"verification_status": status}).eq("id", visit_id).execute()
    
    if not verification_res.data:
        raise HTTPException(status_code=500, detail="Failed to save AI verification")
        
    return verification_res.data[0]
