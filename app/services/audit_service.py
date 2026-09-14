"""
Audit logging service.

Every auth event, SOS trigger/cancel, and admin action should call
log_event() so the audit_logs collection stays populated, as required
by the synopsis ER design and compliance requirements.

Design: fire-and-forget via asyncio.create_task so a DB hiccup never
blocks the request that triggered the event.  If the task itself fails,
the exception is logged but not re-raised.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.database import audit_logs_collection

logger = logging.getLogger("raksha.audit")


async def _write_event(event_type: str, user_id: Any, detail: dict) -> None:
    try:
        await audit_logs_collection().insert_one(
            {
                "event_type": event_type,
                "user_id": user_id,
                "detail": detail,
                "timestamp": datetime.now(timezone.utc),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Audit log write failed [%s]: %s", event_type, exc)


def log_event(event_type: str, user_id: Any = None, detail: dict | None = None) -> None:
    """
    Schedule an audit log write as a background task.
    Safe to call from any async context — never awaited by the caller.

    Args:
        event_type: e.g. "auth.login", "sos.trigger", "admin.deactivate_user"
        user_id:    MongoDB ObjectId (or None for pre-auth events like failed login)
        detail:     arbitrary dict with event-specific fields (email, incident_id, etc.)
    """
    asyncio.create_task(_write_event(event_type, user_id, detail or {}))
