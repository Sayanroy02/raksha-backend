"""
SOS lifecycle tests — trigger, location push, cancel, and error cases.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio

SOS_PAYLOAD = {
    "location": {"lat": 12.9716, "lng": 77.5946},
    "trigger_type": "manual",
}


def unique_register_payload() -> dict:
    """Generate a unique user payload per test to avoid login rate-limit sharing."""
    return {
        "name": "SOS Test User",
        "email": f"sosuser_{uuid.uuid4().hex[:8]}@example.com",
        "phone": "9876543210",
        "password": "SecurePass123",
    }


async def _register_login_sos(client: AsyncClient) -> tuple[dict, dict]:
    """Register a fresh unique user, log in, trigger SOS. Returns (headers, incident)."""
    payload = unique_register_payload()
    await client.post("/api/v1/auth/register", json=payload)
    token_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert token_resp.status_code == 200, token_resp.text
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}
    sos_resp = await client.post("/api/v1/sos/trigger", json=SOS_PAYLOAD, headers=headers)
    assert sos_resp.status_code == 201, sos_resp.text
    return headers, sos_resp.json()


async def test_trigger_sos_creates_incident(client: AsyncClient):
    headers, incident = await _register_login_sos(client)
    assert incident["status"] == "ACTIVE"
    assert incident["trigger_type"] == "manual"
    assert incident["location"]["lat"] == pytest.approx(12.9716)
    assert "_id" in incident  # raw key from mongomock (not serialized via pydantic alias)


async def test_push_location_update(client: AsyncClient):
    headers, incident = await _register_login_sos(client)
    incident_id = incident["_id"]

    resp = await client.post(
        f"/api/v1/sos/{incident_id}/location",
        json={"coordinates": {"lat": 12.9720, "lng": 77.5950}, "accuracy": 5.0},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["coordinates"]["lat"] == pytest.approx(12.9720)
    assert body["accuracy"] == pytest.approx(5.0)


async def test_push_location_to_unknown_incident_404(client: AsyncClient):
    payload = unique_register_payload()
    await client.post("/api/v1/auth/register", json=payload)
    token_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}
    fake_id = "000000000000000000000001"
    resp = await client.post(
        f"/api/v1/sos/{fake_id}/location",
        json={"coordinates": {"lat": 0.0, "lng": 0.0}},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_cancel_sos(client: AsyncClient):
    headers, incident = await _register_login_sos(client)
    incident_id = incident["_id"]

    resp = await client.post(f"/api/v1/sos/{incident_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


async def test_cancel_already_resolved_404(client: AsyncClient):
    """Cancelling an already-resolved incident must return 404."""
    headers, incident = await _register_login_sos(client)
    incident_id = incident["_id"]

    await client.post(f"/api/v1/sos/{incident_id}/cancel", headers=headers)
    resp = await client.post(f"/api/v1/sos/{incident_id}/cancel", headers=headers)
    assert resp.status_code == 404


async def test_geopoint_lat_out_of_range_rejected(client: AsyncClient):
    """lat > 90 must be rejected at the model validation layer (422)."""
    payload = unique_register_payload()
    await client.post("/api/v1/auth/register", json=payload)
    token_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    headers = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}
    resp = await client.post(
        "/api/v1/sos/trigger",
        json={"location": {"lat": 200.0, "lng": 77.5946}, "trigger_type": "manual"},
        headers=headers,
    )
    assert resp.status_code == 422

