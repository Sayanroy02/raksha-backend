from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import contacts_collection, incidents_collection, location_logs_collection
from app.core.limiter import limiter
from app.deps import get_current_user
from app.models.incident import GeoPoint, IncidentOut, LocationLogOut, LocationUpdate, SOSTriggerRequest
from app.services.audit_service import log_event
from app.services.notification_service import dispatch_sos_alert

router = APIRouter(prefix="/sos", tags=["SOS Engine"])


async def _create_sos_incident(
    user: dict,
    location: GeoPoint,
    trigger_type: Literal["manual", "auto_ai"] = "manual",
) -> dict:
    """
    Internal helper: create an SOS incident, notify contacts, return the
    saved document.  Called by both the HTTP endpoint and threat.py's
    auto-trigger path \u2014 no HTTP round-trip needed.
    """
    now = datetime.now(timezone.utc)
    incident_doc = {
        "user_id": user["_id"],
        "triggered_at": now,
        "status": "ACTIVE",
        "trigger_type": trigger_type,
        "location": location.model_dump(),
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
    created = await _create_sos_incident(current_user, payload.location, payload.trigger_type)
    log_event("sos.trigger", user_id=current_user["_id"], detail={"incident_id": str(created["_id"]), "trigger_type": payload.trigger_type})
    return created


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

    log_doc = {
        "incident_id": ObjectId(incident_id),
        "coordinates": payload.coordinates.model_dump(),
        "accuracy": payload.accuracy,
        "timestamp": datetime.now(timezone.utc),
    }
    result = await location_logs_collection().insert_one(log_doc)
    created = await location_logs_collection().find_one({"_id": result.inserted_id})
    return created


@router.post("/{incident_id}/cancel", response_model=IncidentOut)
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

