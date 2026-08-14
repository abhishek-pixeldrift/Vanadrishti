with open('services/ndvi_service.py', 'r') as f:
    content = f.read()

new_code = '''
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
    today_str = now.strftime("%Y-%m-%d")

    # 1. Fetch all existing observations for this plantation
    existing_res = supabase.table("ndvi_observations").select("*").eq("plantation_id", plantation_id).order("observation_date").execute()
    existing_data = existing_res.data or []
    
    # Check if we already have a sentinel2 observation for today (cache)
    has_today_s2 = any(
        obs.get("observation_date") == today_str and obs.get("data_source") == "sentinel2"
        for obs in existing_data
    )

    if source == 'seed':
        return {
            "data": [obs for obs in existing_data if obs.get("data_source") == "seed"],
            "metadata": {"data_source": "seed", "fallback_used": False, "failure_reason": None}
        }

    if source == 'sentinel2':
        if not has_today_s2:
            s2_result = fetch_sentinel2_ndvi(plantation_id)
            if s2_result.get("success"):
                # Determine health status based on NDVI mean
                ndvi_val = s2_result.get("ndvi_mean", 0)
                health = "healthy" if ndvi_val >= 0.6 else ("moderate" if ndvi_val >= 0.3 else "poor")
                
                # Insert new observation
                new_obs = {
                    "plantation_id": plantation_id,
                    "observation_date": today_str,
                    "ndvi_value": ndvi_val,
                    "health_status": health,
                    "data_source": "sentinel2"
                }
                insert_res = supabase.table("ndvi_observations").insert(new_obs).execute()
                if insert_res.data:
                    existing_data.append(insert_res.data[0])
            else:
                return {
                    "data": [obs for obs in existing_data if obs.get("data_source") == "sentinel2"],
                    "metadata": {"data_source": "sentinel2", "fallback_used": False, "failure_reason": s2_result.get("error")}
                }
        
        # In sentinel2 mode, we only return sentinel2 data
        s2_data = [obs for obs in existing_data if obs.get("data_source") == "sentinel2"]
        return {
            "data": s2_data,
            "metadata": {"data_source": "sentinel2", "fallback_used": False, "failure_reason": None}
        }

    # source == 'auto'
    metadata = {"data_source": "sentinel2", "fallback_used": False, "failure_reason": None}
    
    if not has_today_s2:
        s2_result = fetch_sentinel2_ndvi(plantation_id)
        if s2_result.get("success"):
            ndvi_val = s2_result.get("ndvi_mean", 0)
            health = "healthy" if ndvi_val >= 0.6 else ("moderate" if ndvi_val >= 0.3 else "poor")
            new_obs = {
                "plantation_id": plantation_id,
                "observation_date": today_str,
                "ndvi_value": ndvi_val,
                "health_status": health,
                "data_source": "sentinel2"
            }
            insert_res = supabase.table("ndvi_observations").insert(new_obs).execute()
            if insert_res.data:
                existing_data.append(insert_res.data[0])
        else:
            # Fallback to seed
            metadata = {"data_source": "seed", "fallback_used": True, "failure_reason": s2_result.get("error")}
    
    # In auto mode, we return all data (seed + sentinel2)
    # Sort data by observation_date
    existing_data.sort(key=lambda x: x.get("observation_date"))
    
    return {
        "data": existing_data,
        "metadata": metadata
    }
'''

with open('services/ndvi_service.py', 'w') as f:
    f.write(content + '\n' + new_code)
