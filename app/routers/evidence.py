from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import evidence_collection, incidents_collection
from app.deps import get_current_user
from app.models.incident import EvidenceOut
from app.services.cloudinary_service import generate_signed_upload_params

router = APIRouter(prefix="/evidence", tags=["Evidence Capture"])


class SignedUploadResponse(BaseModel):
    timestamp: int
    signature: str
    api_key: str
    cloud_name: str
    folder: str


class EvidenceRegister(BaseModel):
    incident_id: str
    type: str  # AUDIO | VIDEO | IMAGE
    cloudinary_url: str
    duration: float | None = None
    size_kb: float | None = None


@router.get("/upload-signature", response_model=SignedUploadResponse)
async def get_upload_signature(current_user: dict = Depends(get_current_user)):
    """
    Flutter calls this first, then uploads directly to Cloudinary using
    the returned signature (keeps the API secret off the client).
    """
    return generate_signed_upload_params(folder=f"raksha_evidence/{current_user['_id']}")


@router.post("", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def register_evidence(payload: EvidenceRegister, current_user: dict = Depends(get_current_user)):
    """After a successful direct Cloudinary upload, Flutter registers the
    resulting URL against the incident."""
    incident = await incidents_collection().find_one(
        {"_id": ObjectId(payload.incident_id), "user_id": current_user["_id"]}
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    doc = payload.model_dump()
    doc["incident_id"] = ObjectId(payload.incident_id)
    result = await evidence_collection().insert_one(doc)
    created = await evidence_collection().find_one({"_id": result.inserted_id})
    return created


@router.get("/{incident_id}", response_model=list[EvidenceOut])
async def list_evidence(incident_id: str, current_user: dict = Depends(get_current_user)):
    incident = await incidents_collection().find_one(
        {"_id": ObjectId(incident_id), "user_id": current_user["_id"]}
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    cursor = evidence_collection().find({"incident_id": ObjectId(incident_id)})
    return [doc async for doc in cursor]
