from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.database import (
    contacts_collection,
    incidents_collection,
    location_logs_collection,
    users_collection,
)
from app.core.limiter import limiter
from app.deps import get_current_user
from app.models.incident import (
    GeoPoint,
    IncidentOut,
    LocationLogOut,
    LocationUpdate,
    SOSTriggerRequest,
)
from app.services.audit_service import log_event
from app.services.notification_service import dispatch_sos_alert

router = APIRouter(prefix="/sos", tags=["SOS Engine"])


class AudioPayload(BaseModel):
    audio_url: str
    duration_seconds: float | None = None


async def _create_sos_incident(
    user: dict,
    location: GeoPoint,
    trigger_type: Literal["manual", "auto_ai"] = "manual",
) -> dict:
    """
    Internal helper: create an SOS incident, notify contacts, return the
    saved document.  Called by both the HTTP endpoint and threat.py's
    auto-trigger path — no HTTP round-trip needed.
    """
    now = datetime.now(timezone.utc)
    incident_doc = {
        "user_id": user["_id"],
        "triggered_at": now,
        "status": "ACTIVE",
        "trigger_type": trigger_type,
        "location": location.model_dump(),
        "latest_audio_url": None,
    }
    result = await incidents_collection().insert_one(incident_doc)
    incident_id = result.inserted_id

    contacts_cursor = contacts_collection().find({"user_id": user["_id"]})
    contacts = [c async for c in contacts_cursor]

    live_map_url = f"/live/{incident_id}"
    await dispatch_sos_alert(contacts, str(incident_id), live_map_url)

    return await incidents_collection().find_one({"_id": incident_id})


@router.post("/trigger", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def trigger_sos(request: Request, payload: SOSTriggerRequest, current_user: dict = Depends(get_current_user)):
    geo_point = payload.get_geo_point()
    created = await _create_sos_incident(current_user, geo_point, payload.trigger_type)
    log_event("sos.trigger", user_id=current_user["_id"], detail={"incident_id": str(created["_id"]), "trigger_type": payload.trigger_type})
    return created


@router.get("/active", response_model=IncidentOut | None)
async def get_active_sos(current_user: dict = Depends(get_current_user)):
    """Return the user's currently active SOS incident if any."""
    incident = await incidents_collection().find_one(
        {"user_id": current_user["_id"], "status": "ACTIVE"}
    )
    return incident


@router.post("/{incident_id}/location", response_model=LocationLogOut, status_code=status.HTTP_201_CREATED)
async def push_location_update(
    incident_id: str, payload: LocationUpdate, current_user: dict = Depends(get_current_user)
):
    incident = await incidents_collection().find_one(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"]}
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if incident["status"] != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident is not active")

    geo_point = payload.get_geo_point()
    log_doc = {
        "incident_id": ObjectId(incident_id),
        "coordinates": geo_point.model_dump(),
        "accuracy": payload.accuracy,
        "timestamp": datetime.now(timezone.utc),
    }
    result = await location_logs_collection().insert_one(log_doc)
    created = await location_logs_collection().find_one({"_id": result.inserted_id})
    return created


@router.post("/{incident_id}/cancel", response_model=IncidentOut)
@router.post("/{incident_id}/stop", response_model=IncidentOut)
async def cancel_sos(incident_id: str, current_user: dict = Depends(get_current_user)):
    result = await incidents_collection().find_one_and_update(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"], "status": "ACTIVE"},
        {"$set": {"status": "RESOLVED"}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active incident not found")
    log_event("sos.cancel", user_id=current_user["_id"], detail={"incident_id": incident_id})
    return result


@router.post("/{incident_id}/audio")
async def attach_emergency_audio(
    incident_id: str,
    payload: AudioPayload,
    current_user: dict = Depends(get_current_user),
):
    """Save an emergency audio recording snippet or stream link to the incident."""
    incident = await incidents_collection().find_one_and_update(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"]},
        {"$set": {"latest_audio_url": payload.audio_url, "audio_updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return {"status": "ok", "latest_audio_url": payload.audio_url}


@router.get("/track/{target_id}")
async def track_target_user(target_id: str):
    """
    Guardian Tracking Endpoint:
    Invoked when a Guardian scans another user's Raksha+ QR code.
    target_id can be a user_id or active incident_id.
    Returns live GPS coordinates, alert status, and latest audio URL.
    """
    incident = None
    target_user = None

    if ObjectId.is_valid(target_id):
        obj_id = ObjectId(target_id)
        incident = await incidents_collection().find_one({"_id": obj_id})
        if incident:
            target_user = await users_collection().find_one({"_id": incident["user_id"]})
        else:
            target_user = await users_collection().find_one({"_id": obj_id})
            if target_user:
                incident = await incidents_collection().find_one(
                    {"user_id": target_user["_id"], "status": "ACTIVE"}
                )

    if not target_user and not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or incident not found")

    user_name = target_user.get("name", "Raksha+ User") if target_user else "Raksha+ User"
    user_phone = target_user.get("phone", "") if target_user else ""

    latest_location = None
    if incident:
        latest_log = await location_logs_collection().find_one(
            {"incident_id": incident["_id"]},
            sort=[("timestamp", -1)]
        )
        if latest_log:
            latest_location = latest_log.get("coordinates")
        else:
            latest_location = incident.get("location")

    return {
        "target_user_id": str(target_user["_id"]) if target_user else (str(incident["user_id"]) if incident else ""),
        "name": user_name,
        "phone": user_phone,
        "is_emergency": (incident.get("status") == "ACTIVE") if incident else False,
        "incident_id": str(incident["_id"]) if incident else None,
        "status": incident.get("status", "SAFE") if incident else "SAFE",
        "latest_location": latest_location or {"lat": 26.7271, "lng": 88.3953},
        "latest_audio_url": incident.get("latest_audio_url") if incident else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
