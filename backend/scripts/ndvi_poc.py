"""
Phase 8 Proof-of-Concept: Real Sentinel-2 NDVI for one EcoTrack plantation.

This script:
1. Retrieves a real plantation polygon from Supabase.
2. Queries Google Earth Engine for Sentinel-2 Level-2A Surface Reflectance.
3. Applies cloud/quality filtering using the SCL band.
4. Calculates NDVI from Red (B4) and NIR (B8).
5. Computes plantation-level mean and median NDVI.
6. Returns structured results proving real satellite data.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Setup path so we can use the project's database module
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

import ee
from database.connection import get_supabase

# ─── Configuration ───────────────────────────────────────────────────────────
PROJECT_ID = "ecotrack-ndvi"
COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

# Plantation 1: Nashik Hills Block A  (largest, healthy, best chance of imagery)
PLANTATION_ID = "a1000001-0000-0000-0000-000000000001"

# Date range: last 90 days (to find recent cloud-free imagery)
END_DATE = datetime.utcnow()
START_DATE = END_DATE - timedelta(days=90)


def get_plantation_boundary(plantation_id: str) -> dict:
    """Retrieve the plantation boundary polygon from Supabase via the existing RPC."""
    supabase = get_supabase()
    
    # Use the existing get_boundary_geojson RPC
    result = supabase.rpc("get_boundary_geojson", {"p_id": plantation_id}).execute()
    
    if result.data:
        return result.data
    
    # Fallback: get lat/lng from plantation and create a buffer
    plantation = supabase.table("plantations").select("latitude, longitude, name, area_hectares").eq("id", plantation_id).execute()
    if not plantation.data:
        raise ValueError(f"Plantation {plantation_id} not found")
    
    p = plantation.data[0]
    print(f"[FALLBACK] No boundary polygon found. Using center point buffer.")
    print(f"  Plantation: {p['name']}")
    print(f"  Center: ({p['latitude']}, {p['longitude']})")
    
    # Create a simple square buffer (~600m radius)
    import math
    lat, lng = float(p["latitude"]), float(p["longitude"])
    offset_lat = 600 / 111320
    offset_lng = 600 / (111320 * math.cos(math.radians(lat)))
    
    return {
        "type": "Polygon",
        "coordinates": [[
            [lng - offset_lng, lat - offset_lat],
            [lng + offset_lng, lat - offset_lat],
            [lng + offset_lng, lat + offset_lat],
            [lng - offset_lng, lat + offset_lat],
            [lng - offset_lng, lat - offset_lat]
        ]]
    }


def compute_ndvi_for_plantation(geojson: dict, start_date: str, end_date: str) -> dict:
    """
    Query Earth Engine for Sentinel-2 NDVI over a plantation polygon.
    
    Uses COPERNICUS/S2_SR_HARMONIZED Level-2A Surface Reflectance.
    Applies SCL-based cloud masking (keeps vegetation, bare soil, water).
    Calculates NDVI = (B8 - B4) / (B8 + B4).
    """
    
    # Initialize Earth Engine
    ee.Initialize(project=PROJECT_ID)
    print("[OK] Earth Engine initialized")
    
    # Create EE geometry from GeoJSON
    aoi = ee.Geometry(geojson)
    
    # Load Sentinel-2 SR Harmonized collection
    s2 = (
        ee.ImageCollection(COLLECTION)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    )
    
    # Get image count before processing
    count = s2.size().getInfo()
    print(f"[OK] Found {count} Sentinel-2 images in date range")
    
    if count == 0:
        return {
            "success": False,
            "error": "No Sentinel-2 images found for this date range and location",
            "plantation_id": PLANTATION_ID,
            "date_range": f"{start_date} to {end_date}",
            "images_found": 0
        }
    
    # Cloud masking using Scene Classification Layer (SCL band)
    # SCL values to KEEP:
    #   4 = Vegetation
    #   5 = Bare soil
    #   6 = Water
    #   7 = Unclassified (can contain useful data)
    def mask_clouds_scl(image):
        scl = image.select("SCL")
        clear_mask = (
            scl.eq(4)       # Vegetation
            .Or(scl.eq(5))  # Bare soil
            .Or(scl.eq(6))  # Water
            .Or(scl.eq(7))  # Unclassified
        )
        return image.updateMask(clear_mask)
    
    # Apply cloud mask and compute NDVI
    def add_ndvi(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return image.addBands(ndvi)
    
    s2_clean = s2.map(mask_clouds_scl).map(add_ndvi)
    
    # Compute the composite (median across all clean images)
    composite = s2_clean.select("NDVI").median()
    
    # Reduce over the plantation AOI
    stats = composite.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.median(),
            sharedInputs=True
        ).combine(
            reducer2=ee.Reducer.stdDev(),
            sharedInputs=True
        ).combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True
        ),
        geometry=aoi,
        scale=10,  # Sentinel-2 native resolution
        maxPixels=1e8
    )
    
    stats_info = stats.getInfo()
    print(f"[OK] NDVI statistics computed: {stats_info}")
    
    # Get metadata from the most recent image
    latest_image = s2.sort("system:time_start", False).first()
    latest_info = latest_image.getInfo()
    latest_props = latest_info.get("properties", {})
    
    # Get individual image dates for provenance
    dates = s2.aggregate_array("system:time_start").getInfo()
    image_dates = [datetime.utcfromtimestamp(d / 1000).strftime("%Y-%m-%d") for d in sorted(dates)]
    
    return {
        "success": True,
        "plantation_id": PLANTATION_ID,
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "date_range": f"{start_date} to {end_date}",
        "ndvi_mean": stats_info.get("NDVI_mean"),
        "ndvi_median": stats_info.get("NDVI_median"),
        "ndvi_stddev": stats_info.get("NDVI_stdDev"),
        "ndvi_min": stats_info.get("NDVI_min"),
        "ndvi_max": stats_info.get("NDVI_max"),
        "images_used": count,
        "image_dates": image_dates,
        "source": "COPERNICUS/S2_SR_HARMONIZED",
        "source_identifier": latest_props.get("PRODUCT_ID", "unknown"),
        "cloud_coverage_assessment": latest_props.get("CLOUDY_PIXEL_PERCENTAGE"),
        "processing_baseline": latest_props.get("PROCESSING_BASELINE"),
        "spacecraft": latest_props.get("SPACECRAFT_NAME"),
        "data_source": "sentinel2",
        "scale_meters": 10
    }


def main():
    print("=" * 70)
    print("ECOTRACK PHASE 8 - SENTINEL-2 NDVI PROOF OF CONCEPT")
    print("=" * 70)
    
    # Step 1: Get plantation polygon from Supabase
    print(f"\n[1] Retrieving boundary for plantation {PLANTATION_ID}...")
    geojson = get_plantation_boundary(PLANTATION_ID)
    print(f"[OK] Got boundary polygon: type={geojson.get('type')}")
    
    if geojson.get("coordinates"):
        coords = geojson["coordinates"][0]
        print(f"     Vertices: {len(coords) - 1} points")
        # Print bounding box
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        print(f"     Bounding box: ({min(lats):.5f}, {min(lngs):.5f}) to ({max(lats):.5f}, {max(lngs):.5f})")
    
    # Step 2: Query Earth Engine
    start_str = START_DATE.strftime("%Y-%m-%d")
    end_str = END_DATE.strftime("%Y-%m-%d")
    print(f"\n[2] Querying Earth Engine...")
    print(f"    Collection: {COLLECTION}")
    print(f"    Date range: {start_str} to {end_str}")
    print(f"    Cloud filter: < 30%")
    
    result = compute_ndvi_for_plantation(geojson, start_str, end_str)
    
    # Step 3: Report results
    print("\n" + "=" * 70)
    if result["success"]:
        print("RESULT: SUCCESS - Real Sentinel-2 NDVI retrieved")
        print("=" * 70)
        print(f"  Plantation ID:     {result['plantation_id']}")
        print(f"  Observation Date:  {result['observation_date']}")
        print(f"  Date Range:        {result['date_range']}")
        print(f"  Images Used:       {result['images_used']}")
        print(f"  Image Dates:       {', '.join(result['image_dates'][:5])}{'...' if len(result['image_dates']) > 5 else ''}")
        print(f"  ---")
        print(f"  NDVI Mean:         {result['ndvi_mean']:.4f}" if result['ndvi_mean'] else "  NDVI Mean:         N/A")
        print(f"  NDVI Median:       {result['ndvi_median']:.4f}" if result['ndvi_median'] else "  NDVI Median:       N/A")
        print(f"  NDVI StdDev:       {result['ndvi_stddev']:.4f}" if result['ndvi_stddev'] else "  NDVI StdDev:       N/A")
        print(f"  NDVI Min:          {result['ndvi_min']:.4f}" if result['ndvi_min'] else "  NDVI Min:          N/A")
        print(f"  NDVI Max:          {result['ndvi_max']:.4f}" if result['ndvi_max'] else "  NDVI Max:          N/A")
        print(f"  ---")
        print(f"  Source:            {result['source']}")
        print(f"  Product ID:        {result['source_identifier']}")
        print(f"  Spacecraft:        {result['spacecraft']}")
        print(f"  Cloud Coverage:    {result['cloud_coverage_assessment']}%")
        print(f"  Resolution:        {result['scale_meters']}m")
        print(f"  Data Source Label: {result['data_source']}")
        print(f"\n  ** This is NOT seed/mock data. This is real satellite imagery **")
    else:
        print("RESULT: FAILED - No satellite data available")
        print("=" * 70)
        print(f"  Error: {result['error']}")
        print(f"  Images found: {result['images_found']}")
    
    # Output as JSON for programmatic consumption
    print(f"\n--- RAW JSON ---")
    print(json.dumps(result, indent=2, default=str))
    
    return result


if __name__ == "__main__":
    main()
