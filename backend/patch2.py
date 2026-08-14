import re

def update_ndvi_service():
    with open('services/ndvi_service.py', 'r') as f:
        content = f.read()

    # We want to replace get_ndvi_observations completely
    # Let's find where it starts
    start_idx = content.find("def get_ndvi_observations")
    
    new_func = """def get_ndvi_observations(plantation_id: str, source: str = 'auto') -> dict:
    \"\"\"
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
    \"\"\"
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
"""
    
    final_content = content[:start_idx] + new_func
    with open('services/ndvi_service.py', 'w') as f:
        f.write(final_content)

if __name__ == "__main__":
    update_ndvi_service()
    print("Done")
