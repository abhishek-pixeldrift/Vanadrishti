"""
EcoTrack Phase 9 — Alerts & Risk Router.

Endpoints:
  GET  /alerts/              — active (unacknowledged) alerts
  POST /alerts/{id}/acknowledge — resolve an alert
  POST /alerts/scan          — run dynamic risk engine across all plantations
  GET  /risk/{plantation_id} — get current dynamic risk for a single plantation
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database.connection import get_supabase
from services.risk_engine import calculate_risk_score
from services.notify_service import send_telegram

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alerts"])

# ── Alerts CRUD ────────────────────────────────────────────────────────────────

@router.get("/alerts/")
def get_active_alerts():
    """Fetch active maintenance and risk alerts."""
    supabase = get_supabase()
    response = supabase.table("alerts") \
        .select("*, plantations!inner(site_class)") \
        .neq("plantations.site_class", "archived") \
        .eq("acknowledged", False) \
        .order("created_at", desc=True) \
        .execute()
    
    # Clean up the joined column so frontend gets the original shape
    for alert in response.data:
        if "plantations" in alert:
            del alert["plantations"]
    return response.data


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    """Mark an alert as resolved."""
    supabase = get_supabase()
    response = supabase.table("alerts") \
        .update({"acknowledged": True}) \
        .eq("id", alert_id) \
        .execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
    return {"status": "success", "alert": response.data[0]}


# ── Risk Engine ────────────────────────────────────────────────────────────────

@router.get("/risk/{plantation_id}")
def get_risk(plantation_id: str):
    """
    Get the current dynamically calculated risk for a plantation.
    This is the source of truth for risk scoring.
    """
    try:
        result = calculate_risk_score(plantation_id)
        return result
    except Exception as exc:
        logger.error("Risk calculation failed for %s: %s", plantation_id, exc)
        raise HTTPException(status_code=500, detail=f"Risk calculation failed: {exc}")


class ScanRequest(BaseModel):
    token: Optional[str] = None
    chat_id: Optional[str] = None


@router.post("/alerts/scan")
def run_risk_engine_scan(req: ScanRequest = None):
    """
    Compliance Audit: Calculate dynamic risk for ALL plantations.
    - Persists cached risk_score and status to plantations table.
    - Creates HIGH alert if risk_score >= 60 (no duplicates).
    - Sends Telegram notification for new critical alerts.
    """
    supabase = get_supabase()
    token = req.token if req else None
    chat_id = req.chat_id if req else None

    # Fetch all plantation IDs
    plantations_res = supabase.table("plantations").select("id, name").execute()
    plantations = plantations_res.data or []

    new_alerts_count = 0
    results = []

    for plant in plantations:
        pid = plant["id"]
        pname = plant["name"]

        try:
            risk = calculate_risk_score(pid)
        except Exception as exc:
            logger.error("Risk scan failed for %s: %s", pid, exc)
            results.append({"plantation_id": pid, "error": str(exc)})
            continue

        score = risk["risk_score"]
        level = risk["risk_level"]

        # Map risk level to plantation status
        status_map = {"HEALTHY": "healthy", "WARNING": "warning", "CRITICAL": "critical"}
        new_status = status_map.get(level, "warning")

        # Persist cached score and status
        try:
            supabase.table("plantations") \
                .update({"risk_score": score, "status": new_status}) \
                .eq("id", pid) \
                .execute()
        except Exception as exc:
            logger.warning("Failed to update cached risk for %s: %s", pid, exc)

        # Create alert for CRITICAL (score >= 60) if none exists
        if score >= 60:
            existing = supabase.table("alerts") \
                .select("id") \
                .eq("plantation_id", pid) \
                .eq("acknowledged", False) \
                .eq("alert_type", "dynamic_risk_critical") \
                .execute()

            if not existing.data:
                # Build descriptive message from top contributors
                top_factors = []
                for name, comp in risk["components"].items():
                    if comp["score"] > 0:
                        top_factors.append(f"{name}: {comp['score']}/{comp['max']}")
                factors_str = ", ".join(top_factors[:3])

                msg = (
                    f"Plantation '{pname}' risk score {score}/100 ({level}). "
                    f"Key factors: {factors_str}."
                )

                supabase.table("alerts").insert({
                    "plantation_id": pid,
                    "alert_type": "dynamic_risk_critical",
                    "severity": "high",
                    "message": msg,
                    "acknowledged": False,
                }).execute()
                new_alerts_count += 1

                # Telegram — failure must not crash the scan
                send_telegram(
                    f"🚨 EcoTrack Alert: {msg}",
                    override_token=token,
                    override_chat_id=chat_id,
                )

        results.append({
            "plantation_id": pid,
            "name": pname,
            "risk_score": score,
            "risk_level": level,
        })

    return {
        "status": "success",
        "message": f"Risk scan complete. Generated {new_alerts_count} new alerts.",
        "new_alerts": new_alerts_count,
        "results": results,
    }
