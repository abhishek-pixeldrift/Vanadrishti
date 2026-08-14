from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Optional
from database.connection import get_supabase
from models.schemas import NDVIObservation
from services.ndvi_service import get_ndvi_observations

router = APIRouter(prefix="/ndvi", tags=["ndvi"])

@router.get("/{plantation_id}", response_model=List[NDVIObservation])
def get_ndvi_history(plantation_id: str, response: Response, source: str = Query("auto", description="Data source: auto, sentinel2, or seed")):
    """Get historical NDVI observations for a plantation."""
    try:
        result = get_ndvi_observations(plantation_id, source=source)
        
        # Attach fallback metadata to response headers
        metadata = result["metadata"]
        response.headers["X-Data-Source"] = metadata["data_source"]
        response.headers["X-Fallback-Used"] = str(metadata["fallback_used"]).lower()
        if metadata["failure_reason"]:
            response.headers["X-Failure-Reason"] = metadata["failure_reason"]
            
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plantation_id}/latest")
def get_latest_ndvi(plantation_id: str, source: str = Query("auto", description="Data source: auto, sentinel2, or seed")):
    """Get the latest NDVI observation and explicit fallback metadata."""
    try:
        result = get_ndvi_observations(plantation_id, source=source)
        data = result["data"]
        latest = data[-1] if data else None
        
        return {
            "latest_observation": latest,
            "metadata": result["metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
