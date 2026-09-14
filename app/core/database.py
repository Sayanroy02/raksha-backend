"""
MongoDB connection using Motor (async driver), as specified in the synopsis
(Tier 3 — Data Layer, MongoDB Atlas).
"""

import logging
import ssl

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, GEOSPHERE

logger = logging.getLogger("raksha.database")

from app.core.config import get_settings

settings = get_settings()


def _make_ssl_context() -> ssl.SSLContext:
    """
    Build an SSLContext compatible with MongoDB Atlas and Python 3.14+.
    Uses certifi's CA bundle and allows TLS 1.2 / 1.3 negotiation.
    """
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Some Python/OpenSSL builds need this to avoid INTERNAL_ERROR on handshake
    ctx.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
    return ctx

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        tls=True,
        tlsCAFile=certifi.where(),  # Use certifi CA bundle — fixes TLS handshake on Python 3.14+
    )
    _db = _client[settings.mongodb_db_name]
    try:
        # Ping the deployment to verify the connection is alive
        await _client.admin.command("ping")
        print("✅ Database connected successfully!")
        logger.info("Database connected successfully.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database ping failed at startup: %s", exc)


def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Did startup run?")
    return _db


# Convenience collection accessors — mirrors the collections in the synopsis'
# database design section (users, emergency_contacts, incidents, etc.)
def users_collection():
    return get_db()["users"]


def contacts_collection():
    return get_db()["emergency_contacts"]


def incidents_collection():
    return get_db()["incidents"]


def location_logs_collection():
    return get_db()["location_logs"]


def evidence_collection():
    return get_db()["evidence"]


def threat_events_collection():
    return get_db()["threat_events"]


def audit_logs_collection():
    return get_db()["audit_logs"]


async def create_indexes() -> None:
    """
    Create all MongoDB indexes specified in the synopsis ER / indexing strategy.
    Uses create_index with background=False (safe at startup, idempotent).
    Non-fatal: if MongoDB is unreachable at startup a warning is logged and
    the server still starts — indexes will be created on the next restart once
    a real connection is available.
    """
    try:
        db = get_db()

        # users — unique email for fast lookup + duplicate prevention
        await db["users"].create_index([("email", ASCENDING)], unique=True, name="users_email_unique")

        # emergency_contacts — scoped lookups per user, unique phone per user
        await db["emergency_contacts"].create_index(
            [("user_id", ASCENDING), ("phone", ASCENDING)],
            unique=True,
            name="contacts_user_phone_unique",
        )

        # incidents — history sorted by time per user (most common query)
        await db["incidents"].create_index(
            [("user_id", ASCENDING), ("triggered_at", DESCENDING)],
            name="incidents_user_time",
        )

        # location_logs — by incident for timeline queries + 2dsphere for geo queries
        await db["location_logs"].create_index(
            [("incident_id", ASCENDING), ("timestamp", ASCENDING)],
            name="location_logs_incident_time",
        )
        # 2dsphere index requires coordinates stored as GeoJSON; kept as a named
        # index so it can be added without crashing if coordinates are plain dicts.
        try:
            await db["location_logs"].create_index(
                [("coordinates", GEOSPHERE)], name="location_logs_2dsphere"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("2dsphere index skipped (coordinates not GeoJSON?): %s", exc)

        # evidence — lookups by incident
        await db["evidence"].create_index([("incident_id", ASCENDING)], name="evidence_incident")

        # threat_events — per-user history
        await db["threat_events"].create_index(
            [("user_id", ASCENDING), ("detected_at", DESCENDING)],
            name="threat_events_user_time",
        )

        # audit_logs — by event type and time for compliance queries
        await db["audit_logs"].create_index(
            [("event_type", ASCENDING), ("timestamp", DESCENDING)],
            name="audit_logs_event_time",
        )
        await db["audit_logs"].create_index([("user_id", ASCENDING)], name="audit_logs_user")

        logger.info("MongoDB indexes created / verified.")

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "MongoDB indexes could not be created at startup (DB unreachable?): %s. "
            "Indexes will be created automatically on the next restart once the DB is reachable.",
            exc,
        )

