from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import evidence_collection, incidents_collection, location_logs_collection
from app.deps import get_current_user
from app.models.incident import EvidenceOut, IncidentOut, LocationLogOut

router = APIRouter(prefix="/incidents", tags=["Incident History"])


@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    cursor = incidents_collection().find({"user_id": current_user["_id"]}).sort("triggered_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: str, current_user: dict = Depends(get_current_user)):
    incident = await incidents_collection().find_one(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"]}
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str, current_user: dict = Depends(get_current_user)):
    incident = await incidents_collection().find_one(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"]}
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    locations_cursor = location_logs_collection().find({"incident_id": ObjectId(incident_id)}).sort("timestamp", 1)
    evidence_cursor = evidence_collection().find({"incident_id": ObjectId(incident_id)})

    locations = [LocationLogOut.model_validate(doc).model_dump() async for doc in locations_cursor]
    evidence = [EvidenceOut.model_validate(doc).model_dump() async for doc in evidence_cursor]

    return {
        "incident": IncidentOut.model_validate(incident).model_dump(),
        "location_trail": locations,
        "evidence": evidence,
    }
