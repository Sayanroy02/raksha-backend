"""
Test fixtures for Raksha+ backend.

Uses mongomock-motor for an in-memory MongoDB so tests run offline,
with no Atlas connection required.  The app's database module is
monkey-patched before the FastAPI app is imported.
"""

import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def mock_db():
    """Fresh in-memory Mongo database per test function."""
    client = AsyncMongoMockClient()
    db = client["rakshaplus_test"]
    yield db
    # Drop all collections after each test for isolation
    for name in await db.list_collection_names():
        await db.drop_collection(name)


@pytest_asyncio.fixture(scope="function")
async def client(mock_db):
    """
    AsyncClient wired to the FastAPI app with the real database swapped
    out for mongomock-motor.  create_indexes is also patched out since
    mongomock doesn't support all index types (2dsphere).  The rate
    limiter is disabled so tests never hit 429 due to accumulated counts.
    """
    import app.core.database as db_module
    from app.core.limiter import limiter

    db_module._db = mock_db
    db_module._client = mock_db.client

    async def noop_indexes():
        pass

    original_enabled = limiter.enabled
    limiter.enabled = False  # disable rate limiting during tests
    try:
        with patch.object(db_module, "create_indexes", noop_indexes):
            from app.main import app as fastapi_app

            async with AsyncClient(
                transport=ASGITransport(app=fastapi_app), base_url="http://test"
            ) as ac:
                yield ac
    finally:
        limiter.enabled = original_enabled


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

REGISTER_PAYLOAD = {
    "name": "Test User",
    "email": "testuser@example.com",
    "phone": "9876543210",
    "password": "SecurePass123",
}


async def register_and_login(client: AsyncClient) -> dict:
    """Register a user and return the TokenPair dict."""
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    return resp.json()


async def auth_headers(client: AsyncClient) -> dict:
    tokens = await register_and_login(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
