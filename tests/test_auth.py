"""
Auth endpoint tests — covers the full authentication lifecycle.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import REGISTER_PAYLOAD, auth_headers, register_and_login

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert "password_hash" not in body  # never leak the hash


async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()


async def test_login_success_returns_token_pair(client: AsyncClient):
    tokens = await register_and_login(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "AnyPassword1"},
    )
    assert resp.status_code == 401


async def test_refresh_valid(client: AsyncClient):
    tokens = await register_and_login(client)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


async def test_refresh_with_access_token_rejected(client: AsyncClient):
    """Passing an access token to /refresh must be rejected."""
    tokens = await register_and_login(client)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert resp.status_code == 401


async def test_get_me_authenticated(client: AsyncClient):
    headers = await auth_headers(client)
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == REGISTER_PAYLOAD["email"]


async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # HTTPBearer raises 403 when header missing
