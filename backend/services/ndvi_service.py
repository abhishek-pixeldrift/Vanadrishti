"""
NDVI Service — Real Sentinel-2 NDVI via Google Earth Engine.

Phase 8A: Provides fetch_sentinel2_ndvi() which queries COPERNICUS/S2_SR_HARMONIZED
Level-2A Surface Reflectance, applies SCL-based quality masking, computes NDVI
from Red (B4) and NIR (B8), and aggregates over the authorized plantation polygon
at 10m native resolution.

Earth Engine project: ecotrack-ndvi
"""

import os
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import ee
from database.connection import get_supabase

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
EE_PROJECT = "ecotrack-ndvi"
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
SCALE_METERS = 10  # Sentinel-2 B4/B8 native resolution
MAX_CLOUD_PERCENT = 30  # Scene-level cloud filter
DEFAULT_LOOKBACK_DAYS = 90

# SCL (Scene Classification Layer) values to KEEP for vegetation NDVI.
# We explicitly include only land-surface classes and exclude everything else.
#   4 = Vegetation
#   5 = Bare Soil / Not Vegetated
# Excluded:
#   0 = No Data, 1 = Saturated/Defective, 2 = Cast Shadow (Topographic),
#   3 = Cloud Shadow, 6 = Water, 7 = Unclassified,
#   8 = Cloud Medium Probability, 9 = Cloud High Probability,
#   10 = Thin Cirrus, 11 = Snow/Ice
SCL_KEEP = [4, 5]

# Track whether ee.Initialize() has been called in this process
_ee_initialized = False


def _ensure_ee_initialized():
    """Initialize Earth Engine once per process. Raises on failure."""
    global _ee_initialized
    if _ee_initialized:
        return

    try:
        ee.Initialize(project=EE_PROJECT)
        _ee_initialized = True
        logger.info("Earth Engine initialized (project=%s)", EE_PROJECT)
    except Exception as exc:
        logger.error("Earth Engine initialization failed: %s", exc)
        raise RuntimeError(
            f"Cannot initialize Google Earth Engine (project={EE_PROJECT}): {exc}"
        ) from exc


def _get_plantation_boundary(plantation_id: str) -> dict:
    """
    Retrieve the authorized plantation boundary polygon from Supabase.

    Uses the existing get_boundary_geojson RPC (returns GeoJSON Polygon).
    Falls back to a center-point buffer (~600m radius square) only if the
    plantation_boundaries table has no row for this plantation — this mirrors
    the documented fallback already present in check_point_in_plantation RPC.
    """
    supabase = get_supabase()

    # Primary path: real polygon from plantation_boundaries table
    rpc_result = supabase.rpc("get_boundary_geojson", {"p_id": plantation_id}).execute()

    if rpc_result.data:
        geojson = rpc_result.data
        if isinstance(geojson, dict) and geojson.get("type") == "Polygon":
            logger.info("Retrieved authorized boundary polygon for %s", plantation_id)
            return geojson, False  # geojson, used_fallback

    # Documented fallback: center-point buffer
    plantation_res = (
        supabase.table("plantations")
        .select("latitude, longitude, name, area_hectares")
        .eq("id", plantation_id)
        .execute()
    )
    if not plantation_res.data:
        raise ValueError(f"Plantation {plantation_id} not found in database")

    p = plantation_res.data[0]
    lat, lng = float(p["latitude"]), float(p["longitude"])

    logger.warning(
        "No boundary polygon for %s (%s). Using center-point buffer fallback.",
        plantation_id, p["name"],
    )

    # Create a square buffer approximating 600m radius
    offset_lat = 600 / 111320
    offset_lng = 600 / (111320 * math.cos(math.radians(lat)))

    geojson = {
        "type": "Polygon",
        "coordinates": [[
            [lng - offset_lng, lat - offset_lat],
            [lng + offset_lng, lat - offset_lat],
            [lng + offset_lng, lat + offset_lat],
            [lng - offset_lng, lat + offset_lat],
            [lng - offset_lng, lat - offset_lat],
        ]],
    }
    return geojson, True


def fetch_sentinel2_ndvi(
    plantation_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    Fetch real Sentinel-2 NDVI for a plantation polygon via Google Earth Engine.

    Parameters
    ----------
    plantation_id : str
        UUID of the plantation (must exist in Supabase).
    start_date : str, optional
        ISO date string (YYYY-MM-DD). Defaults to 90 days before end_date.
    end_date : str, optional
        ISO date string (YYYY-MM-DD). Defaults to today (UTC).

    Returns
    -------
    dict with keys:
        success : bool
        plantation_id : str
        observation_date : str          — date of computation
        date_range : str                — start to end
        ndvi_mean : float | None
        ndvi_median : float | None
        ndvi_stddev : float | None
        ndvi_min : float | None
        ndvi_max : float | None
        pixel_count : int | None        — valid pixels after masking
        images_used : int               — Sentinel-2 scenes matched
        image_dates : list[str]         — acquisition dates
        source : str                    — collection ID
        source_identifier : str         — Sentinel-2 product ID (latest scene)
        spacecraft : str | None
        cloud_coverage_assessment : float | None
        processing_baseline : str | None
        data_source : str               — always "sentinel2"
        scale_meters : int              — 10
        boundary_fallback_used : bool
        error : str | None              — populated only on failure
    """

    # ── Resolve date range ─────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    if end_date is None:
        end_date = now.strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = now - timedelta(days=DEFAULT_LOOKBACK_DAYS)
        start_date = start_dt.strftime("%Y-%m-%d")

    base = {
        "plantation_id": plantation_id,
        "observation_date": now.strftime("%Y-%m-%d"),
        "date_range": f"{start_date} to {end_date}",
        "data_source": "sentinel2",
        "scale_meters": SCALE_METERS,
    }

    # ── Step 1: Retrieve plantation boundary ───────────────────────────────
    try:
        geojson, fallback_used = _get_plantation_boundary(plantation_id)
        base["boundary_fallback_used"] = fallback_used
    except ValueError as exc:
        return {**base, "success": False, "error": str(exc),
                "boundary_fallback_used": True, "images_used": 0}

    # ── Step 2: Initialize Earth Engine ────────────────────────────────────
    try:
        _ensure_ee_initialized()
    except RuntimeError as exc:
        return {**base, "success": False, "error": str(exc),
                "boundary_fallback_used": fallback_used, "images_used": 0}

    # ── Step 3: Query Sentinel-2 collection ────────────────────────────────
    try:
        aoi = ee.Geometry(geojson)

        s2 = (
            ee.ImageCollection(S2_COLLECTION)
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        )

        count = s2.size().getInfo()
        logger.info("Sentinel-2 images found: %d (range %s to %s)", count, start_date, end_date)

        if count == 0:
            return {
                **base,
                "success": False,
                "error": (
                    f"No Sentinel-2 imagery with <{MAX_CLOUD_PERCENT}% cloud cover "
                    f"found for date range {start_date} to {end_date}"
                ),
                "images_used": 0,
                "boundary_fallback_used": fallback_used,
            }

        # ── Step 4: SCL cloud/quality masking ──────────────────────────────
        def mask_scl(image):
            """Keep only Vegetation (4) and Bare Soil (5) SCL pixels."""
            scl = image.select("SCL")
            mask = scl.eq(SCL_KEEP[0])
            for val in SCL_KEEP[1:]:
                mask = mask.Or(scl.eq(val))
            return image.updateMask(mask)

        # ── Step 5: NDVI band math ─────────────────────────────────────────
        def add_ndvi(image):
            """NDVI = (B8 - B4) / (B8 + B4)"""
            ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
            return image.addBands(ndvi)

        s2_processed = s2.map(mask_scl).map(add_ndvi)

        # ── Step 6: Temporal composite (median) ────────────────────────────
        composite = s2_processed.select("NDVI").median()

        # ── Step 7: Spatial aggregation over plantation polygon ────────────
        stats = composite.reduceRegion(
            reducer=(
                ee.Reducer.mean()
                .combine(reducer2=ee.Reducer.median(), sharedInputs=True)
                .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
                .combine(reducer2=ee.Reducer.minMax(), sharedInputs=True)
                .combine(reducer2=ee.Reducer.count(), sharedInputs=True)
            ),
            geometry=aoi,
            scale=SCALE_METERS,
            maxPixels=1e8,
        )

        stats_info = stats.getInfo()
        logger.info("NDVI stats for %s: %s", plantation_id, stats_info)

        # Check for empty result (all pixels masked)
        ndvi_mean = stats_info.get("NDVI_mean")
        pixel_count = stats_info.get("NDVI_count")

        if ndvi_mean is None or pixel_count in (None, 0):
            return {
                **base,
                "success": False,
                "error": (
                    "All pixels masked by quality filter. "
                    "Cloud/shadow/snow coverage is too high over this plantation."
                ),
                "images_used": count,
                "boundary_fallback_used": fallback_used,
            }

        # ── Step 8: Provenance metadata from latest image ──────────────────
        latest = s2.sort("system:time_start", False).first()
        latest_props = latest.getInfo().get("properties", {})

        # Image acquisition dates for the composite
        timestamps = s2.aggregate_array("system:time_start").getInfo()
        image_dates = sorted(set(
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            for ts in timestamps
        ))

        return {
            **base,
            "success": True,
            "ndvi_mean": stats_info.get("NDVI_mean"),
            "ndvi_median": stats_info.get("NDVI_median"),
            "ndvi_stddev": stats_info.get("NDVI_stdDev"),
            "ndvi_min": stats_info.get("NDVI_min"),
            "ndvi_max": stats_info.get("NDVI_max"),
            "pixel_count": int(pixel_count) if pixel_count else 0,
            "images_used": count,
            "image_dates": image_dates,
            "source": S2_COLLECTION,
            "source_identifier": latest_props.get("PRODUCT_ID", "unknown"),
            "spacecraft": latest_props.get("SPACECRAFT_NAME"),
            "cloud_coverage_assessment": latest_props.get("CLOUDY_PIXEL_PERCENTAGE"),
            "processing_baseline": latest_props.get("PROCESSING_BASELINE"),
            "boundary_fallback_used": fallback_used,
            "error": None,
        }

    except ee.EEException as exc:
        logger.error("Earth Engine computation failed for %s: %s", plantation_id, exc)
        return {
            **base,
            "success": False,
            "error": f"Earth Engine error: {exc}",
            "images_used": 0,
            "boundary_fallback_used": fallback_used,
        }
    except Exception as exc:
        logger.error("Unexpected error in fetch_sentinel2_ndvi for %s: %s", plantation_id, exc)
        return {
            **base,
            "success": False,
            "error": f"Unexpected error: {exc}",
            "images_used": 0,
            "boundary_fallback_used": fallback_used,
        }


def fetch_seed_ndvi(plantation_id: str) -> list:
    """Fetch existing seed NDVI data for the plantation."""
    try:
        supabase = get_supabase()
        res = supabase.table("ndvi_observations").select("*").eq("plantation_id", plantation_id).eq("data_source", "seed").order("observation_date").execute()
        return res.data or []
    except Exception as exc:
        logger.error("Error fetching seed NDVI for %s: %s", plantation_id, exc)
        return []

def get_ndvi_observations(plantation_id: str, source: str = 'auto') -> dict:
    """
    Get NDVI observations for a plantation with caching and fallback.
    Maintains a historical monthly time series of Sentinel-2 data.
    Returns:
        {
            "data": [list of observations],
            "metadata": {
                "data_source": "sentinel2" or "seed",
                "fallback_used": bool,
                "failure_reason": str or None
            }
        }
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    
    # 1. Fetch all existing observations for this plantation
    existing_res = supabase.table("ndvi_observations").select("*").eq("plantation_id", plantation_id).order("observation_date").execute()
    existing_data = existing_res.data or []
    
    if source == 'seed':
        return {
            "data": [obs for obs in existing_data if obs.get("data_source") == "seed"],
            "metadata": {"data_source": "seed", "fallback_used": False, "failure_reason": None}
        }

    metadata = {"data_source": "sentinel2", "fallback_used": False, "failure_reason": None}
    
    # We want to maintain a 6-month historical time series
    # For each of the last 6 months, check if we have a sentinel2 observation.
    # If not, fetch it from EE and store it.
    
    months_to_check = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=30 * i)
        # First and last day of that month
        first_day = dt.replace(day=1)
        # Next month first day minus 1 day
        next_month = (first_day + timedelta(days=32)).replace(day=1)
        last_day = next_month - timedelta(days=1)
        
        # Don't query future dates
        if first_day > now:
            continue
        if last_day > now:
            last_day = now
            
        months_to_check.append({
            "year_month": first_day.strftime("%Y-%m"),
            "start": first_day.strftime("%Y-%m-%d"),
            "end": last_day.strftime("%Y-%m-%d")
        })

    s2_data = [obs for obs in existing_data if obs.get("data_source") == "sentinel2"]
    
    ee_failed = False
    ee_error = None
    
    # Check what months we already have
    existing_s2_months = set()
    for obs in s2_data:
        obs_date = obs.get("observation_date")
        if obs_date:
            existing_s2_months.add(obs_date[:7]) # YYYY-MM
            
    # Fetch missing months
    new_insertions = []
    for m in months_to_check:
        if m["year_month"] not in existing_s2_months and not ee_failed:
            logger.info("Fetching Sentinel-2 NDVI for %s (Missing month %s)", plantation_id, m["year_month"])
            s2_result = fetch_sentinel2_ndvi(plantation_id, start_date=m["start"], end_date=m["end"])
            
            if s2_result.get("success"):
                ndvi_val = s2_result.get("ndvi_mean", 0)
                health = "healthy" if ndvi_val >= 0.6 else ("moderate" if ndvi_val >= 0.3 else "poor")
                
                # Use actual observation date from the latest image in that month, or fallback to end of period
                image_dates = s2_result.get("image_dates", [])
                actual_obs_date = image_dates[-1] if image_dates else m["end"]
                
                new_obs = {
                    "plantation_id": plantation_id,
                    "observation_date": actual_obs_date,
                    "ndvi_value": ndvi_val,
                    "health_status": health,
                    "data_source": "sentinel2"
                }
                insert_res = supabase.table("ndvi_observations").insert(new_obs).execute()
                if insert_res.data:
                    s2_data.append(insert_res.data[0])
                    new_insertions.append(insert_res.data[0])
                    existing_s2_months.add(actual_obs_date[:7])
            else:
                # If error is just "No imagery", we don't treat it as a hard failure that triggers seed fallback.
                # We just leave that month missing as requested: "If no usable imagery exists for a month, leave that month missing rather than inventing a value."
                err = s2_result.get("error", "")
                if "No Sentinel-2 imagery" in err or "All pixels masked" in err:
                    logger.info("No usable imagery for %s in %s. Leaving missing.", plantation_id, m["year_month"])
                    import uuid
                    missing_obs = {
                        "id": str(uuid.uuid4()),
                        "plantation_id": plantation_id,
                        "observation_date": m["end"],
                        "ndvi_value": None,
                        "health_status": "missing",
                        "data_source": "sentinel2",
                        "created_at": now.isoformat()
                    }
                    s2_data.append(missing_obs)
                else:
                    # Hard EE error (e.g. quota, network) -> trigger fallback if auto
                    logger.error("EE Failure: %s", err)
                    ee_failed = True
                    ee_error = err

    if source == 'sentinel2':
        s2_data.sort(key=lambda x: x.get("observation_date"))
        return {
            "data": s2_data,
            "metadata": {"data_source": "sentinel2", "fallback_used": False, "failure_reason": ee_error}
        }
        
    # auto mode
    if ee_failed and len(s2_data) == 0:
        # If EE failed completely and we have NO s2 data, fallback to seed
        metadata = {"data_source": "seed", "fallback_used": True, "failure_reason": ee_error}
        seed_data = [obs for obs in existing_data if obs.get("data_source") == "seed"]
        seed_data.sort(key=lambda x: x.get("observation_date"))
        return {
            "data": seed_data,
            "metadata": metadata
        }
    
    # If we have some S2 data, return it
    if len(s2_data) > 0:
        s2_data.sort(key=lambda x: x.get("observation_date"))
        return {
            "data": s2_data,
            "metadata": metadata
        }
        
    # If we reach here, it means we didn't fail but we found NO imagery for any month.
    # Fallback to seed as well.
    metadata = {"data_source": "seed", "fallback_used": True, "failure_reason": "No valid imagery found in the last 6 months"}
    seed_data = [obs for obs in existing_data if obs.get("data_source") == "seed"]
    seed_data.sort(key=lambda x: x.get("observation_date"))
    return {
        "data": seed_data,
        "metadata": metadata
    }
