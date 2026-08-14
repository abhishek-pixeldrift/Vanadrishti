"""
EcoTrack Phase 9 — Maintenance Tasks Router.

Endpoints:
  GET   /maintenance/{plantation_id}  — list tasks for a plantation
  POST  /maintenance/                 — create a new task
  PATCH /maintenance/{task_id}/status — update task status
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from database.connection import get_supabase

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


class MaintenanceCreate(BaseModel):
    plantation_id: str
    alert_id: Optional[str] = None
    problem: str
    risk_level: Optional[str] = "medium"
    recommended_action: str
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str  # "pending", "assigned", "in_progress", "completed"


@router.get("/{plantation_id}")
def get_maintenance_tasks(plantation_id: str):
    """List all maintenance tasks for a plantation."""
    supabase = get_supabase()
    res = supabase.table("maintenance_tasks") \
        .select("*") \
        .eq("plantation_id", plantation_id) \
        .order("created_at", desc=True) \
        .execute()
    return res.data


@router.post("/")
def create_maintenance_task(task: MaintenanceCreate):
    """Create a new maintenance task."""
    supabase = get_supabase()

    data = {
        "plantation_id": task.plantation_id,
        "problem": task.problem,
        "risk_level": task.risk_level,
        "recommended_action": task.recommended_action,
        "status": "pending",
    }
    if task.alert_id:
        data["alert_id"] = task.alert_id
    if task.assigned_to:
        data["assigned_to"] = task.assigned_to
    if task.due_date:
        data["due_date"] = task.due_date

    res = supabase.table("maintenance_tasks").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create maintenance task")
    return res.data[0]


@router.patch("/{task_id}/status")
def update_task_status(task_id: str, update: StatusUpdate):
    """Update a maintenance task's status."""
    supabase = get_supabase()

    valid_statuses = {"pending", "assigned", "in_progress", "completed"}
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    patch = {"status": update.status}
    if update.status == "completed":
        patch["completed_at"] = datetime.now(timezone.utc).isoformat()

    res = supabase.table("maintenance_tasks") \
        .update(patch) \
        .eq("id", task_id) \
        .execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Maintenance task not found")
    return res.data[0]
