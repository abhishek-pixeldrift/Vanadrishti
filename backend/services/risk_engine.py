"""
EcoTrack Phase 9 — Dynamic Risk Engine.

Calculates an explainable, multi-factor risk score (0–100) for a plantation.
Higher score = higher risk.

Components (100 total):
  NDVI Trend:       35 pts  (sentinel2 only)
  AI Health:        25 pts  (latest Gemini verification)
  Visit Recency:    20 pts  (server-side timestamp)
  Maintenance:      10 pts  (open/overdue tasks)
  Location Trust:   10 pts  (latest verified visit confidence)

Risk levels:
  0–39   → HEALTHY
  40–59  → WARNING
  60–100 → CRITICAL
"""

import logging
from datetime import datetime, timezone
from database.connection import get_supabase

logger = logging.getLogger(__name__)


def _calculate_ndvi_component(plantation_id: str) -> dict:
    """
    NDVI Trend contribution (max 35 points).

    Uses ONLY data_source='sentinel2' observations with non-null ndvi_value.
    Never uses seed/mock data.

    Trend logic (latest 3 valid observations):
      avg_delta > +0.03  → improving    →  0 pts
      |avg_delta| ≤ 0.03 → stable       → 10 pts
      avg_delta < -0.03  → declining    → 25 pts
      < 2 observations   → insufficient → 20 pts

    Vegetation-stress modifier:
      latest NDVI < 0.3 → +10 pts (capped at 35 total)
    """
    supabase = get_supabase()

    res = supabase.table("ndvi_observations") \
        .select("observation_date, ndvi_value, data_source") \
        .eq("plantation_id", plantation_id) \
        .eq("data_source", "sentinel2") \
        .not_.is_("ndvi_value", "null") \
        .order("observation_date", desc=True) \
        .limit(3) \
        .execute()

    valid_obs = [o for o in (res.data or []) if o.get("ndvi_value") is not None]
    # Re-sort chronologically (oldest first) for delta calculation
    valid_obs.sort(key=lambda x: x["observation_date"])

    component = {
        "score": 0,
        "max": 35,
        "source": "sentinel2",
        "trend": None,
        "latest_ndvi": None,
        "observation_count": len(valid_obs),
        "observation_dates": [o["observation_date"] for o in valid_obs],
    }

    if len(valid_obs) < 2:
        component["score"] = 20
        component["trend"] = "insufficient_data"
        component["source"] = "none" if len(valid_obs) == 0 else "sentinel2"
        if valid_obs:
            component["latest_ndvi"] = valid_obs[-1]["ndvi_value"]
            # Apply stress modifier even with insufficient trend data
            if valid_obs[-1]["ndvi_value"] < 0.3:
                component["score"] = min(35, component["score"] + 10)
        return component

    # Calculate average delta between consecutive observations
    deltas = []
    for i in range(1, len(valid_obs)):
        deltas.append(valid_obs[i]["ndvi_value"] - valid_obs[i - 1]["ndvi_value"])
    avg_delta = sum(deltas) / len(deltas)

    if avg_delta > 0.03:
        component["trend"] = "improving"
        component["score"] = 0
    elif avg_delta < -0.03:
        component["trend"] = "declining"
        component["score"] = 25
    else:
        component["trend"] = "stable"
        component["score"] = 10

    latest_ndvi = valid_obs[-1]["ndvi_value"]
    component["latest_ndvi"] = latest_ndvi

    # Vegetation-stress modifier
    if latest_ndvi < 0.3:
        component["score"] = min(35, component["score"] + 10)

    return component


def _calculate_ai_health_component(plantation_id: str) -> dict:
    """
    AI Health contribution (max 25 points).

    Uses the latest ai_verification linked to a verified/flagged field visit.

    Mapping:
      excellent → 0, good → 5, moderate → 12, poor → 20,
      no tree detected → 25, no AI result → 15
    """
    supabase = get_supabase()

    HEALTH_SCORES = {
        "excellent": 0,
        "good": 5,
        "moderate": 12,
        "poor": 20,
    }

    # Get field visits that went through AI verification
    visits_res = supabase.table("field_visits") \
        .select("id") \
        .eq("plantation_id", plantation_id) \
        .in_("verification_status", ["verified", "flagged"]) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    visit_ids = [v["id"] for v in (visits_res.data or [])]

    component = {
        "score": 15,
        "max": 25,
        "source": "none",
        "health_assessment": None,
        "tree_detected": None,
        "confidence": None,
    }

    if not visit_ids:
        return component

    # Find the latest AI verification for any of these visits
    for vid in visit_ids:
        ai_res = supabase.table("ai_verifications") \
            .select("*") \
            .eq("field_visit_id", vid) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if ai_res.data:
            ai = ai_res.data[0]
            component["source"] = "gemini"
            component["health_assessment"] = ai.get("health_assessment")
            component["tree_detected"] = ai.get("tree_detected")
            component["confidence"] = ai.get("confidence")

            if not ai.get("tree_detected"):
                component["score"] = 25
            else:
                assessment = (ai.get("health_assessment") or "poor").lower()
                component["score"] = HEALTH_SCORES.get(assessment, 20)
            return component

    # No AI verifications found for any visit
    return component


def _calculate_visit_recency_component(plantation_id: str) -> dict:
    """
    Visit Recency contribution (max 20 points).

    Uses the latest verified field visit's server_timestamp (falls back to
    created_at for legacy seed records where server_timestamp is null).

    Scoring:
      ≤7 days   →  0
      ≤30 days  →  5
      ≤90 days  → 10
      ≤180 days → 15
      >180 days → 20
      no visit  → 20
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    component = {
        "score": 20,
        "max": 20,
        "source": "none",
        "last_visit_id": None,
        "last_visit_timestamp": None,
        "timestamp_source": None,
        "days_since_visit": None,
    }

    # Try server_timestamp first
    res = supabase.table("field_visits") \
        .select("id, server_timestamp, created_at, worker_name") \
        .eq("plantation_id", plantation_id) \
        .eq("verification_status", "verified") \
        .order("server_timestamp", desc=True) \
        .limit(1) \
        .execute()

    visit = None
    ts_source = None

    if res.data:
        v = res.data[0]
        if v.get("server_timestamp"):
            visit = v
            ts_source = "server_timestamp"
        else:
            # Legacy record: server_timestamp is null, fall back to created_at
            if v.get("created_at"):
                visit = v
                ts_source = "created_at"

    if not visit:
        # Try ordering by created_at as a final fallback
        res2 = supabase.table("field_visits") \
            .select("id, server_timestamp, created_at, worker_name") \
            .eq("plantation_id", plantation_id) \
            .eq("verification_status", "verified") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        if res2.data:
            visit = res2.data[0]
            ts_source = "created_at"

    if not visit:
        return component

    ts_str = visit.get(ts_source)
    if not ts_str:
        return component

    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        days = (now - ts).days

        component["source"] = "field_visits"
        component["last_visit_id"] = visit["id"]
        component["last_visit_timestamp"] = ts_str
        component["timestamp_source"] = ts_source
        component["days_since_visit"] = days

        if days <= 7:
            component["score"] = 0
        elif days <= 30:
            component["score"] = 5
        elif days <= 90:
            component["score"] = 10
        elif days <= 180:
            component["score"] = 15
        else:
            component["score"] = 20
    except (ValueError, TypeError) as exc:
        logger.warning("Failed to parse visit timestamp for %s: %s", plantation_id, exc)

    return component


def _calculate_location_trust_component(plantation_id: str) -> dict:
    """
    Location Trust contribution (max 10 points).

    Uses location_confidence.confidence.score from the latest verified visit.

    Scoring:
      ≥80 → 0, ≥50 → 3, ≥30 → 6, <30 → 8, none → 8
    """
    supabase = get_supabase()

    component = {
        "score": 8,
        "max": 10,
        "source": "none",
        "trust_score": None,
        "confidence_level": None,
    }

    res = supabase.table("field_visits") \
        .select("location_confidence") \
        .eq("plantation_id", plantation_id) \
        .eq("verification_status", "verified") \
        .not_.is_("location_confidence", "null") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not res.data:
        return component

    loc_conf = res.data[0].get("location_confidence")
    if not loc_conf or not isinstance(loc_conf, dict):
        return component

    # Navigate nested structure: {confidence: {score: N, confidence_level: "..."}}
    confidence = loc_conf.get("confidence", {})
    if not isinstance(confidence, dict):
        return component

    trust_score = confidence.get("score")
    if trust_score is None:
        return component

    component["source"] = "field_visits"
    component["trust_score"] = trust_score
    component["confidence_level"] = confidence.get("confidence_level")

    if trust_score >= 80:
        component["score"] = 0
    elif trust_score >= 50:
        component["score"] = 3
    elif trust_score >= 30:
        component["score"] = 6
    else:
        component["score"] = 8

    return component


def _calculate_maintenance_component(plantation_id: str) -> dict:
    """
    Maintenance contribution (max 10 points).

    Uses actual maintenance_tasks records.

    Scoring:
      Each open task:    +3 (cap 10)
      Each overdue task: +5 (cap 10)
      Overdue supersedes open (no double-counting).
      No tasks / all completed: 0
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    component = {
        "score": 0,
        "max": 10,
        "source": "maintenance_tasks",
        "open_count": 0,
        "overdue_count": 0,
        "total_tasks": 0,
    }

    try:
        res = supabase.table("maintenance_tasks") \
            .select("id, status, due_date") \
            .eq("plantation_id", plantation_id) \
            .in_("status", ["pending", "assigned", "in_progress"]) \
            .execute()

        tasks = res.data or []
    except Exception as exc:
        logger.warning("Failed to query maintenance_tasks for %s: %s", plantation_id, exc)
        return component

    component["total_tasks"] = len(tasks)

    open_count = 0
    overdue_count = 0

    for task in tasks:
        due_str = task.get("due_date")
        is_overdue = False
        if due_str:
            try:
                due = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                if due.tzinfo is None:
                    # Treat as UTC if no timezone
                    due = due.replace(tzinfo=timezone.utc)
                if now > due:
                    is_overdue = True
            except (ValueError, TypeError):
                pass

        if is_overdue:
            overdue_count += 1
        else:
            open_count += 1

    component["open_count"] = open_count
    component["overdue_count"] = overdue_count

    # Overdue tasks are more severe; open tasks are moderate
    # Each task counts once (no double-counting)
    score = (overdue_count * 5) + (open_count * 3)
    component["score"] = min(10, score)

    return component


def calculate_risk_score(plantation_id: str) -> dict:
    """
    Calculate the dynamic, explainable risk score for a plantation.

    Returns a dict with:
      plantation_id, risk_score, risk_level, components, missing_inputs,
      generated_at
    """
    now = datetime.now(timezone.utc)

    ndvi = _calculate_ndvi_component(plantation_id)
    ai_health = _calculate_ai_health_component(plantation_id)
    visit_recency = _calculate_visit_recency_component(plantation_id)
    location_trust = _calculate_location_trust_component(plantation_id)
    maintenance = _calculate_maintenance_component(plantation_id)

    total = (
        ndvi["score"]
        + ai_health["score"]
        + visit_recency["score"]
        + location_trust["score"]
        + maintenance["score"]
    )

    if total <= 39:
        level = "HEALTHY"
    elif total <= 59:
        level = "WARNING"
    else:
        level = "CRITICAL"

    # Collect missing inputs
    missing = []
    if ndvi["source"] == "none":
        missing.append("no_sentinel2_ndvi")
    if ai_health["source"] == "none":
        missing.append("no_ai_verification")
    if visit_recency["source"] == "none":
        missing.append("no_verified_visit")
    if location_trust["source"] == "none":
        missing.append("no_location_trust")

    return {
        "plantation_id": plantation_id,
        "risk_score": total,
        "risk_level": level,
        "components": {
            "ndvi": ndvi,
            "ai_health": ai_health,
            "visit_recency": visit_recency,
            "maintenance": maintenance,
            "location_trust": location_trust,
        },
        "missing_inputs": missing,
        "generated_at": now.isoformat(),
    }
