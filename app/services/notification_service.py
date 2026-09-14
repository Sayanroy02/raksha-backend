"""
Dispatches SOS alerts to emergency contacts.

Kept as a pluggable stub: at $0 budget, wire this to Firebase Cloud
Messaging (free, unlimited) for push notifications. Add a real SMS
gateway (Twilio, MSG91, etc.) later — it's called out as future work
in the synopsis rather than in-scope for the free-tier build.
"""

import logging

logger = logging.getLogger("raksha.notifications")


async def dispatch_sos_alert(contacts: list[dict], incident_id: str, live_map_url: str) -> None:
    for contact in contacts:
        # TODO: replace with an FCM push call once device tokens are collected
        logger.info(
            "SOS alert queued -> contact=%s phone=%s incident=%s link=%s",
            contact.get("name"),
            contact.get("phone"),
            incident_id,
            live_map_url,
        )
