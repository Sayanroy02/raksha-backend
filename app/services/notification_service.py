"""
Dispatches SOS alerts to emergency contacts via Resend email API.

Features:
- Automatic reverse geocoding via Geoapify to provide exact street address
- Embedded Geoapify static map snapshot in the email
- Direct Google Maps / OpenStreetMap navigation links
- Delivery to all contacts with registered email addresses
- Confirmation copy to the user's registered email
"""

import logging
from datetime import datetime, timezone
import httpx

from app.core.config import get_settings
from app.services.maps_service import get_static_map_url, reverse_geocode

logger = logging.getLogger("raksha.notifications")
settings = get_settings()

RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_resend_email(to_email: str, subject: str, html_body: str) -> bool:
    """Sends an email using Resend API."""
    api_key = settings.resend_api_key
    if not api_key:
        logger.warning("RESEND_API_KEY not configured. Skipping email to %s", to_email)
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(RESEND_ENDPOINT, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                logger.info("Resend email sent successfully to %s: %s", to_email, resp.json())
                return True
            else:
                logger.error("Resend API error (%s): %s", resp.status_code, resp.text)
                return False
    except Exception as e:
        logger.error("Failed to send Resend email to %s: %s", to_email, e)
        return False


def _build_sos_email_html(
    user_name: str,
    user_phone: str,
    incident_id: str,
    lat: float,
    lng: float,
    address_str: str,
    static_map_url: str,
    nav_url: str,
    triggered_at_str: str,
    home_address: str = "",
) -> str:
    home_address_block = (
        f'<p style="margin: 4px 0; font-size: 14px;"><strong>🏠 Registered Address:</strong> {home_address}</p>'
        if home_address else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Emergency SOS Alert</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0c16; color: #ffffff; padding: 20px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #161828; border-radius: 16px; overflow: hidden; border: 1px solid #ff0055;">
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #ff0055, #ff5370); padding: 24px; text-align: center;">
      <h1 style="margin: 0; color: #ffffff; font-size: 24px; letter-spacing: 1px;">🚨 EMERGENCY SOS ALERT</h1>
      <p style="margin: 6px 0 0 0; color: #ffe6ee; font-size: 14px; font-weight: 600;">Raksha+ Women Safety Network</p>
    </div>

    <!-- Body -->
    <div style="padding: 24px;">
      <p style="font-size: 16px; line-height: 1.5; color: #f1f1f5; margin-top: 0;">
        <strong>{user_name}</strong> has triggered an <span style="color: #ff3366; font-weight: bold;">EMERGENCY SOS ALERT</span> and needs your immediate help!
      </p>

      <!-- Info Box -->
      <div style="background-color: #1e2238; border-radius: 12px; padding: 16px; margin: 20px 0; border-left: 4px solid #ff0055;">
        <p style="margin: 4px 0; font-size: 14px;"><strong>👤 Sender:</strong> {user_name}</p>
        <p style="margin: 4px 0; font-size: 14px;"><strong>📞 Phone:</strong> <a href="tel:{user_phone}" style="color: #ff5370; text-decoration: none;">{user_phone or 'Not provided'}</a></p>
        <p style="margin: 4px 0; font-size: 14px;"><strong>⏰ Time:</strong> {triggered_at_str}</p>
        <p style="margin: 4px 0; font-size: 14px;"><strong>📍 GPS:</strong> {lat:.5f}, {lng:.5f}</p>
        {home_address_block}
        <p style="margin: 4px 0; font-size: 14px;"><strong>🗺️ GPS Landmark / Area:</strong> {address_str}</p>
        <p style="margin: 4px 0; font-size: 12px; color: #a0a5ba;"><strong>Incident ID:</strong> {incident_id}</p>
      </div>

      <!-- Static Map Image -->
      <div style="text-align: center; margin: 20px 0;">
        <a href="{nav_url}" target="_blank">
          <img src="{static_map_url}" alt="Incident Location Map" style="width: 100%; max-width: 550px; height: auto; border-radius: 12px; border: 1px solid #2a2e45;" />
        </a>
      </div>

      <!-- Action Button -->
      <div style="text-align: center; margin: 28px 0 16px 0;">
        <a href="{nav_url}" target="_blank" style="background-color: #ff0055; color: #ffffff; padding: 14px 28px; text-decoration: none; font-size: 15px; font-weight: bold; border-radius: 30px; display: inline-block; box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4);">
          📍 Open Live GPS in Google Maps
        </a>
      </div>

      <p style="font-size: 12px; color: #8e95ad; text-align: center; margin-top: 24px;">
        If you believe the sender is in imminent danger, please notify local emergency authorities (call 112) immediately.
      </p>
    </div>

    <!-- Footer -->
    <div style="background-color: #0f101d; padding: 16px; text-align: center; font-size: 11px; color: #626982;">
      Raksha+ Automated Emergency Notification System • Protecting Every Step
    </div>
  </div>
</body>
</html>"""


async def dispatch_sos_alert(
    contacts: list[dict],
    incident_id: str,
    live_map_url: str,
    user: dict | None = None,
    location: dict | None = None,
) -> int:
    """
    Sends emergency notifications to trusted contacts.
    For all contacts with an email (and the user), sends rich Resend email with live map.
    Returns the number of emails successfully dispatched.
    """
    user_name = user.get("name", "Raksha+ User") if user else "Raksha+ User"
    user_phone = user.get("phone", "") if user else ""
    user_email = user.get("email", "") if user else ""

    lat = 26.7271
    lng = 88.3953
    if location:
        lat = location.get("lat", location.get("latitude", lat))
        lng = location.get("lng", location.get("longitude", lng))

    # Reverse geocode to exact address with Geoapify
    geo_data = await reverse_geocode(lat, lng)
    address_str = geo_data.get("formatted", f"{lat:.5f}, {lng:.5f}")

    static_map = get_static_map_url(lat, lng, width=600, height=320)
    nav_url = f"https://www.google.com/maps?q={lat},{lng}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    subject = f"🚨 EMERGENCY SOS ALERT: {user_name} needs help!"
    user_home_address = user.get("home_address", "") if user else ""
    html_content = _build_sos_email_html(
        user_name=user_name,
        user_phone=user_phone,
        incident_id=incident_id,
        lat=lat,
        lng=lng,
        address_str=address_str,
        static_map_url=static_map,
        nav_url=nav_url,
        triggered_at_str=now_str,
        home_address=user_home_address,
    )

    emails_to_notify: set[str] = set()

    for contact in contacts:
        c_name = contact.get("name", "Contact")
        c_phone = contact.get("phone", "")
        c_email = contact.get("email")

        logger.info(
            "SOS alert queued -> contact=%s phone=%s email=%s incident=%s link=%s",
            c_name,
            c_phone,
            c_email,
            incident_id,
            live_map_url,
        )

        if c_email and "@" in c_email:
            emails_to_notify.add(c_email.strip())

    # Also notify the user's registered email so they have immediate email confirmation of the SOS alert
    if user_email and "@" in user_email:
        emails_to_notify.add(user_email.strip())

    sent_count = 0
    for email_addr in emails_to_notify:
        success = await send_resend_email(email_addr, subject, html_content)
        if success:
            sent_count += 1

    return sent_count
