"""
EcoTrack Phase 9 — Telegram Notification Service.

Sends alert notifications via the Telegram Bot API.
Never crashes the caller. Never exposes credentials.
"""

import os
import logging

import httpx

logger = logging.getLogger(__name__)


def send_telegram(
    message: str,
    override_token: str = None,
    override_chat_id: str = None,
) -> dict:
    """
    Send a message via Telegram Bot API.

    Parameters
    ----------
    message : str
        Text to send.
    override_token : str, optional
        Bot token. Falls back to TELEGRAM_TOKEN env var.
    override_chat_id : str, optional
        Chat ID. Falls back to TELEGRAM_CHAT_ID env var.

    Returns
    -------
    dict  {"success": bool, "error": str | None}
    """
    token = override_token or os.getenv("TELEGRAM_TOKEN")
    chat_id = override_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.info(
            "[Telegram] No credentials configured. Message: %s",
            message[:120],
        )
        return {"success": False, "error": "No Telegram token or chat_id configured"}

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = httpx.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        if resp.status_code == 200:
            logger.info("[Telegram] Sent to %s", chat_id)
            return {"success": True, "error": None}
        else:
            err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            logger.warning("[Telegram] Failed: %s", err)
            return {"success": False, "error": err}
    except Exception as exc:
        logger.warning("[Telegram] Exception: %s", exc)
        return {"success": False, "error": str(exc)}
