from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from database.connection import get_supabase
from models.schemas import Plantation, DashboardStats

router = APIRouter(prefix="/plantations", tags=["plantations"])

@router.get("/", response_model=List[Plantation])
def get_plantations():
    """Get all plantations."""
    supabase = get_supabase()
    response = supabase.table("plantations").select("*").neq("site_class", "archived").execute()
    return response.data

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """Get aggregate statistics for the dashboard."""
    supabase = get_supabase()
    
    # In a real app we might do this with a custom SQL function via RPC, 
    # but for MVP we fetch and aggregate or do simple counts.
    # Supabase Python client v2 `count()` method:
    plantations_res = supabase.table("plantations").select("id, status, saplings_planted, current_saplings").neq("site_class", "archived").execute()
    plantations = plantations_res.data
    
    total = len(plantations)
    healthy = sum(1 for p in plantations if p.get("status") == "healthy")
    at_risk = sum(1 for p in plantations if p.get("status") in ("warning", "critical"))

    alerts_res = supabase.table("alerts") \
        .select("id, plantations!inner(site_class)", count="exact") \
        .neq("plantations.site_class", "archived") \
        .eq("acknowledged", False) \
        .execute()
    active_alerts = len(alerts_res.data) if alerts_res.data else 0

    return DashboardStats(
        total_plantations=total,
        healthy_count=healthy,
        at_risk_count=at_risk,
        active_alerts=active_alerts
    )

@router.get("/{plantation_id}", response_model=Plantation)
def get_plantation(plantation_id: str):
    """Get a single plantation by ID."""
    supabase = get_supabase()
    response = supabase.table("plantations").select("*").eq("id", plantation_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Plantation not found")
        
    return response.data[0]

@router.get("/{plantation_id}/last-verified-visit")
def get_last_verified_visit(plantation_id: str):
    """Get the latest verified field visit for a plantation."""
    supabase = get_supabase()
    # We want verification_status = 'verified' and we order by server_timestamp (which is captured during creation)
    # If server_timestamp is null for older seed data, we can fallback to created_at
    response = supabase.table("field_visits").select("*").eq("plantation_id", plantation_id).eq("verification_status", "verified").order("server_timestamp", desc=True).limit(1).execute()
    
    if not response.data:
        # Fallback order by created_at if server_timestamp is missing
        response = supabase.table("field_visits").select("*").eq("plantation_id", plantation_id).eq("verification_status", "verified").order("created_at", desc=True).limit(1).execute()
        
    if not response.data:
        return None
        
    return response.data[0]

@router.get("/{plantation_id}/active-alerts")
def get_active_alerts(plantation_id: str):
    """Get active (unacknowledged) alerts for a plantation."""
    supabase = get_supabase()
    response = supabase.table("alerts").select("*").eq("plantation_id", plantation_id).eq("acknowledged", False).order("created_at", desc=True).execute()
    return response.data

@router.get("/{plantation_id}/boundary")
def get_plantation_boundary(plantation_id: str):
    """Get boundary GeoJSON and status for a plantation."""
    supabase = get_supabase()
    
    status_res = supabase.table("plantation_boundaries").select("boundary_status").eq("plantation_id", plantation_id).execute()
    boundary_status = status_res.data[0].get("boundary_status", "unknown") if status_res.data else "unknown"
    
    geom_res = supabase.rpc("get_boundary_geojson", {"p_id": plantation_id}).execute()
    
    return {
        "boundary_status": boundary_status,
        "boundary": geom_res.data
    }
