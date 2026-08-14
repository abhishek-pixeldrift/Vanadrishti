from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from database.connection import get_supabase

router = APIRouter(prefix="/plantations", tags=["boundaries"])

@router.get("/{plantation_id}/boundary")
def get_plantation_boundary(plantation_id: str) -> Dict[str, Any]:
    """Get the boundary polygon for a specific plantation as GeoJSON."""
    supabase = get_supabase()
    
    # We use the RPC function we created in the migration to safely return GeoJSON
    try:
        response = supabase.rpc("get_boundary_geojson", {"p_id": plantation_id}).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Boundary not found for this plantation")
            
        # The RPC returns a JSON object directly
        return response.data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
