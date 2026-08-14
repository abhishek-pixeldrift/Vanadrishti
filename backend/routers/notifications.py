import os
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/status")
def get_notification_status():
    """Check if Telegram notifications are configured backend-side."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    configured = bool(token and chat_id)
    return {"configured": configured}
