from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.common import PyObjectId


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lng: float = Field(ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class SOSTriggerRequest(BaseModel):
    location: Optional[GeoPoint] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    trigger_type: Literal["manual", "auto_ai"] = "manual"

    def get_geo_point(self) -> GeoPoint:
        if self.location is not None:
            return self.location
        lt = self.lat if self.lat is not None else self.latitude
        ln = self.lng if self.lng is not None else self.longitude
        if lt is not None and ln is not None:
            return GeoPoint(lat=lt, lng=ln)
        return GeoPoint(lat=0.0, lng=0.0)


class IncidentOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    incident_id: Optional[str] = None
    user_id: PyObjectId
    triggered_at: datetime
    status: Literal["ACTIVE", "RESOLVED", "CANCELLED"]
    trigger_type: str
    location: GeoPoint
    latest_audio_url: Optional[str] = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def set_incident_id(self):
        if not self.incident_id and self.id:
            self.incident_id = str(self.id)
        return self


class LocationUpdate(BaseModel):
    coordinates: Optional[GeoPoint] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    accuracy: float | None = None

    def get_geo_point(self) -> GeoPoint:
        if self.coordinates is not None:
            return self.coordinates
        lt = self.latitude if self.latitude is not None else self.lat
        ln = self.longitude if self.longitude is not None else self.lng
        if lt is not None and ln is not None:
            return GeoPoint(lat=lt, lng=ln)
        return GeoPoint(lat=0.0, lng=0.0)


class LocationLogOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    incident_id: PyObjectId
    coordinates: GeoPoint
    accuracy: float | None = None
    timestamp: datetime

    model_config = {"populate_by_name": True}


class EvidenceOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    incident_id: PyObjectId
    type: Literal["AUDIO", "VIDEO", "IMAGE"]
    cloudinary_url: str
    duration: float | None = None
    size_kb: float | None = None

    model_config = {"populate_by_name": True}


class ThreatDetectionRequest(BaseModel):
    """Feature vector the client (or an edge model) has already extracted."""
    features: list[float]
    location: Optional[GeoPoint] = None  # required for auto-SOS to fire

    @field_validator("features")
    @classmethod
    def validate_feature_length(cls, v: list[float]) -> list[float]:
        if not (1 <= len(v) <= 50):
            raise ValueError("features must contain between 1 and 50 values")
        return v


class ThreatEventOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    detected_at: datetime
    model_used: str
    confidence: float
    auto_triggered: bool
    auto_sos_incident_id: Optional[str] = None

    model_config = {"populate_by_name": True}
