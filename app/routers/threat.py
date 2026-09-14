from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.core.database import threat_events_collection
from app.deps import get_current_user
from app.models.incident import ThreatDetectionRequest, ThreatEventOut
from app.routers.sos import _create_sos_incident
from app.services.threat_detector import predict_threat

router = APIRouter(prefix="/threat", tags=["AI Threat Detection"])


@router.post("/detect", response_model=ThreatEventOut)
async def detect_threat(payload: ThreatDetectionRequest, current_user: dict = Depends(get_current_user)):
    confidence, auto_triggered, model_used = predict_threat(payload.features)

    auto_sos_incident_id: str | None = None
    if auto_triggered and payload.location is not None:
        incident = await _create_sos_incident(
            user=current_user,
            location=payload.location,
            trigger_type="auto_ai",
        )
        auto_sos_incident_id = str(incident["_id"])

    doc = {
        "user_id": current_user["_id"],
        "detected_at": datetime.now(timezone.utc),
        "model_used": model_used,
        "confidence": confidence,
        "auto_triggered": auto_triggered,
        "auto_sos_incident_id": auto_sos_incident_id,
    }
    result = await threat_events_collection().insert_one(doc)
    created = await threat_events_collection().find_one({"_id": result.inserted_id})
    return created

