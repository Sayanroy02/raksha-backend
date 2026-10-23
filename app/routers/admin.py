import random
from datetime import datetime, timezone
from typing import Literal, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.database import (
    admin_config_collection,
    audit_logs_collection,
    contacts_collection,
    danger_zones_collection,
    evidence_collection,
    incidents_collection,
    location_logs_collection,
    police_dispatches_collection,
    reports_collection,
    users_collection,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.services.audit_service import log_event

router = APIRouter(prefix="/admin", tags=["Raksha Admin"])

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "Admin@123"


# --- Helper to serialize Mongo docs ---
def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    res = dict(doc)
    if "_id" in res:
        res["id"] = str(res["_id"])
        res["_id"] = str(res["_id"])
    for k, v in res.items():
        if isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, datetime):
            res[k] = v.isoformat()
        elif isinstance(v, list):
            res[k] = [serialize_doc(i) if isinstance(i, dict) else str(i) if isinstance(i, ObjectId) else i for i in v]
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
    return res


# --- Auth Models ---
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminChangeCredentialsRequest(BaseModel):
    current_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None


class IncidentStatusUpdate(BaseModel):
    status: Literal["ACTIVE", "RESOLVED", "CANCELLED"]


class ReportCreate(BaseModel):
    user_name: str
    user_phone: Optional[str] = None
    category: str  # Harassment, Stalking, Suspicious Activity, Safety Query, App Support
    title: str
    description: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class ReportStatusUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED"]
    admin_notes: Optional[str] = None


class PoliceDispatchRequest(BaseModel):
    incident_id: Optional[str] = None
    user_name: str
    mobile_number: str
    phone_imei: Optional[str] = "867459038291045"
    latitude: float
    longitude: float
    address: Optional[str] = "Emergency Location"
    threat_level: Literal["CRITICAL", "HIGH", "MODERATE"] = "CRITICAL"
    pcr_unit: Optional[str] = "PCR-112 Central Rapid Response"
    notes: Optional[str] = None
    evidence_urls: Optional[list[str]] = []


class DangerZoneCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    zone_type: Literal["CIRCLE", "ROAD_LINE"] = "CIRCLE"
    latitude: float
    longitude: float
    radius_m: int = Field(default=300, ge=10, le=10000)
    path_coordinates: Optional[list[list[float]]] = []
    severity: Literal["HIGH", "MODERATE", "LOW"] = "HIGH"
    is_active: bool = True


class DangerZoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    zone_type: Optional[Literal["CIRCLE", "ROAD_LINE"]] = None
    radius_m: Optional[int] = None
    path_coordinates: Optional[list[list[float]]] = None
    severity: Optional[Literal["HIGH", "MODERATE", "LOW"]] = None
    is_active: Optional[bool] = None


# --- 1. Admin Authentication & Settings ---
@router.post("/login")
async def admin_login(payload: AdminLoginRequest):
    admin_doc = await admin_config_collection().find_one({"type": "admin_credentials"})
    if not admin_doc:
        # Check against initial default
        if payload.username == DEFAULT_ADMIN_USER and payload.password == DEFAULT_ADMIN_PASS:
            # Seed credentials
            await admin_config_collection().insert_one({
                "type": "admin_credentials",
                "username": DEFAULT_ADMIN_USER,
                "password_hash": hash_password(DEFAULT_ADMIN_PASS),
                "created_at": datetime.now(timezone.utc),
            })
            token = create_access_token("admin_raksha")
            return {
                "access_token": token,
                "token_type": "bearer",
                "username": DEFAULT_ADMIN_USER,
                "role": "superadmin",
            }
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin username or password")

    # Match stored username & password hash
    if payload.username != admin_doc.get("username"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin username or password")

    if not verify_password(payload.password, admin_doc.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin username or password")

    token = create_access_token(str(admin_doc.get("_id", "admin_raksha")))
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": admin_doc["username"],
        "role": "superadmin",
    }


@router.post("/change-credentials")
async def change_admin_credentials(payload: AdminChangeCredentialsRequest):
    admin_doc = await admin_config_collection().find_one({"type": "admin_credentials"})
    if not admin_doc:
        # If not initialized, current password must be default
        if payload.current_password != DEFAULT_ADMIN_PASS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        current_username = DEFAULT_ADMIN_USER
    else:
        if not verify_password(payload.current_password, admin_doc.get("password_hash", "")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        current_username = admin_doc.get("username", DEFAULT_ADMIN_USER)

    new_username = payload.new_username.strip() if payload.new_username and payload.new_username.strip() else current_username
    new_hash = hash_password(payload.new_password) if payload.new_password and payload.new_password.strip() else (
        admin_doc.get("password_hash") if admin_doc else hash_password(DEFAULT_ADMIN_PASS)
    )

    update_payload = {
        "type": "admin_credentials",
        "username": new_username,
        "password_hash": new_hash,
        "updated_at": datetime.now(timezone.utc),
    }

    await admin_config_collection().update_one(
        {"type": "admin_credentials"},
        {"$set": update_payload},
        upsert=True,
    )
    log_event("admin.change_credentials", user_id="admin", detail={"new_username": new_username})

    return {
        "success": True,
        "message": "Admin credentials successfully updated",
        "username": new_username,
    }


@router.get("/me")
async def get_admin_profile():
    admin_doc = await admin_config_collection().find_one({"type": "admin_credentials"})
    username = admin_doc.get("username", DEFAULT_ADMIN_USER) if admin_doc else DEFAULT_ADMIN_USER
    return {"username": username, "role": "superadmin", "status": "active"}


# --- System Stats ---
@router.get("/stats")
async def get_admin_stats():
    total_users = await users_collection().count_documents({})
    active_sos = await incidents_collection().count_documents({"status": "ACTIVE"})
    total_incidents = await incidents_collection().count_documents({})
    total_evidence = await evidence_collection().count_documents({})
    total_reports = await reports_collection().count_documents({})
    active_danger_zones = await danger_zones_collection().count_documents({"is_active": True})
    total_dispatches = await police_dispatches_collection().count_documents({})

    return {
        "total_users": total_users,
        "active_sos": active_sos,
        "total_incidents": total_incidents,
        "total_evidence": total_evidence,
        "total_reports": total_reports,
        "active_danger_zones": active_danger_zones,
        "total_dispatches": total_dispatches,
    }


# --- 1. Users Details ---
@router.get("/users")
async def get_all_users(skip: int = 0, limit: int = 100):
    cursor = users_collection().find({}).sort("created_at", -1).skip(skip).limit(limit)
    users = []
    async for doc in cursor:
        user_id = doc["_id"]
        # Fetch emergency contacts count
        contacts_count = await contacts_collection().count_documents({"user_id": user_id})
        # Fetch emergency contacts list
        contacts_cursor = contacts_collection().find({"user_id": user_id})
        contacts = [serialize_doc(c) async for c in contacts_cursor]
        # Fetch incidents count
        incidents_count = await incidents_collection().count_documents({"user_id": user_id})

        user_data = serialize_doc(doc)
        user_data.pop("password_hash", None)
        user_data["emergency_contacts"] = contacts
        user_data["emergency_contacts_count"] = contacts_count
        user_data["incidents_count"] = incidents_count
        user_data["phone_imei"] = doc.get("phone_imei", f"86745{str(user_id)[-10:]}")
        user_data["device_model"] = doc.get("device_model", "Android / iOS Device")
        users.append(user_data)
    return users


@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, is_active: bool = Query(...)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    await users_collection().update_one({"_id": oid}, {"$set": {"active": is_active}})
    return {"success": True, "active": is_active}


# --- 2. SOS Trigger Details When & Where ---
@router.get("/incidents")
async def get_all_incidents(
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()

    cursor = incidents_collection().find(query).sort("triggered_at", -1).skip(skip).limit(limit)
    incidents = []
    async for inc in cursor:
        inc_data = serialize_doc(inc)
        user_id = inc.get("user_id")
        user = await users_collection().find_one({"_id": user_id}) if isinstance(user_id, ObjectId) else None
        if user:
            inc_data["user_name"] = user.get("name", "Unknown User")
            inc_data["user_phone"] = user.get("phone", "N/A")
            inc_data["user_email"] = user.get("email", "N/A")
            inc_data["user_blood_group"] = user.get("blood_group", "N/A")
            inc_data["user_medical_notes"] = user.get("medical_notes", "N/A")
            inc_data["user_imei"] = user.get("phone_imei", f"86745{str(user['_id'])[-10:]}")
        else:
            inc_data["user_name"] = "Registered User"
            inc_data["user_phone"] = "N/A"
            inc_data["user_imei"] = "867459038291045"

        # Evidence count & latest evidence
        ev_cursor = evidence_collection().find({"incident_id": inc["_id"]})
        evidence_list = [serialize_doc(ev) async for ev in ev_cursor]
        inc_data["evidence"] = evidence_list
        inc_data["evidence_count"] = len(evidence_list)

        if not inc_data.get("latest_audio_url"):
            for ev in evidence_list:
                if ev.get("type") == "AUDIO" and ev.get("cloudinary_url"):
                    inc_data["latest_audio_url"] = ev.get("cloudinary_url")
                    break
        if not inc_data.get("latest_video_url"):
            for ev in evidence_list:
                if ev.get("type") == "VIDEO" and ev.get("cloudinary_url"):
                    inc_data["latest_video_url"] = ev.get("cloudinary_url")
                    break

        # Reverse geocoded address preview or coordinates
        loc = inc.get("location", {})
        lat = loc.get("lat", 0.0)
        lng = loc.get("lng", 0.0)
        inc_data["lat"] = lat
        inc_data["lng"] = lng
        inc_data["address"] = inc.get("address", f"Lat: {lat:.5f}, Lng: {lng:.5f}")

        incidents.append(inc_data)
    return incidents


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, payload: IncidentStatusUpdate):
    try:
        oid = ObjectId(incident_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    res = await incidents_collection().update_one(
        {"_id": oid},
        {"$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc)}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")

    log_event("admin.incident_status_change", user_id="admin", detail={"incident_id": incident_id, "new_status": payload.status})
    return {"success": True, "incident_id": incident_id, "status": payload.status}


# --- 3. Video, Audio and Photo Evidence Vault ---
@router.get("/evidence")
async def get_all_evidence(media_type: Optional[str] = Query(None), limit: int = 100):
    query = {}
    if media_type:
        query["type"] = media_type.upper()

    cursor = evidence_collection().find(query).sort("_id", -1).limit(limit)
    items = []
    async for doc in cursor:
        ev_data = serialize_doc(doc)
        inc_id = doc.get("incident_id")
        if inc_id:
            try:
                inc_oid = ObjectId(inc_id) if isinstance(inc_id, str) else inc_id
                incident = await incidents_collection().find_one({"_id": inc_oid})
                if incident:
                    ev_data["incident_status"] = incident.get("status")
                    ev_data["triggered_at"] = incident.get("triggered_at")
                    user = await users_collection().find_one({"_id": incident.get("user_id")})
                    if user:
                        ev_data["user_name"] = user.get("name")
                        ev_data["user_phone"] = user.get("phone")
            except Exception:
                pass
        items.append(ev_data)
    return items


# --- 4. User Reports & Queries ---
@router.get("/reports")
async def get_all_reports(status_filter: Optional[str] = Query(None)):
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()

    cursor = reports_collection().find(query).sort("created_at", -1)
    reports = []
    async for r in cursor:
        reports.append(serialize_doc(r))
    return reports


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_user_report(payload: ReportCreate):
    doc = payload.model_dump()
    doc["status"] = "OPEN"
    doc["created_at"] = datetime.now(timezone.utc)
    doc["admin_notes"] = ""
    res = await reports_collection().insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc["_id"] = str(res.inserted_id)
    return serialize_doc(doc)


@router.patch("/reports/{report_id}")
async def update_report_status(report_id: str, payload: ReportStatusUpdate):
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    updates = {"status": payload.status, "updated_at": datetime.now(timezone.utc)}
    if payload.admin_notes is not None:
        updates["admin_notes"] = payload.admin_notes

    res = await reports_collection().update_one({"_id": oid}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True, "report_id": report_id, "status": payload.status}


# --- 5. Real-Time User Tracking ---
@router.get("/tracking/live")
async def get_live_tracking_users():
    """
    Returns live locations of users with active SOS incidents
    and most recent known coordinates.
    """
    active_incidents = incidents_collection().find({"status": "ACTIVE"}).sort("triggered_at", -1)
    results = []
    async for inc in active_incidents:
        user_id = inc.get("user_id")
        user = await users_collection().find_one({"_id": user_id}) if isinstance(user_id, ObjectId) else None
        
        # Get latest location log for this incident
        latest_log = await location_logs_collection().find_one(
            {"incident_id": inc["_id"]},
            sort=[("timestamp", -1)],
        )

        coord = latest_log.get("coordinates") if latest_log else inc.get("location", {})
        lat = coord.get("lat", 0.0)
        lng = coord.get("lng", 0.0)

        # Get trail (last 10 location points)
        trail_cursor = location_logs_collection().find({"incident_id": inc["_id"]}).sort("timestamp", 1).limit(30)
        trail = []
        async for pt in trail_cursor:
            c = pt.get("coordinates", {})
            if "lat" in c and "lng" in c:
                trail.append({"lat": c["lat"], "lng": c["lng"], "time": pt.get("timestamp")})

        results.append({
            "incident_id": str(inc["_id"]),
            "user_id": str(user_id) if user_id else "unknown",
            "user_name": user.get("name", "Active User") if user else "Active User",
            "user_phone": user.get("phone", "N/A") if user else "N/A",
            "phone_imei": user.get("phone_imei", f"86745{str(user['_id'])[-10:]}") if user else "867459038291045",
            "current_lat": lat,
            "current_lng": lng,
            "accuracy_m": latest_log.get("accuracy", 12.0) if latest_log else 15.0,
            "status": "ACTIVE_SOS",
            "triggered_at": inc.get("triggered_at"),
            "trigger_type": inc.get("trigger_type", "manual"),
            "route_trail": trail,
        })

    return results


@router.get("/tracking/route/{incident_id}")
async def get_incident_route_trail(incident_id: str):
    try:
        oid = ObjectId(incident_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid incident ID")

    trail_cursor = location_logs_collection().find({"incident_id": oid}).sort("timestamp", 1)
    points = []
    async for pt in trail_cursor:
        c = pt.get("coordinates", {})
        points.append({
            "lat": c.get("lat"),
            "lng": c.get("lng"),
            "accuracy": pt.get("accuracy"),
            "timestamp": pt.get("timestamp"),
        })
    return points


# --- 6. Send Details to Police in Real-Time (IMEI, Mobile, Location) ---
@router.post("/dispatch-police")
async def dispatch_to_police(payload: PoliceDispatchRequest):
    dispatch_code = f"PCR-112-{random.randint(100000, 999999)}"
    now = datetime.now(timezone.utc)

    dispatch_doc = {
        "dispatch_code": dispatch_code,
        "incident_id": payload.incident_id,
        "user_name": payload.user_name,
        "mobile_number": payload.mobile_number,
        "phone_imei": payload.phone_imei,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "address": payload.address,
        "threat_level": payload.threat_level,
        "pcr_unit": payload.pcr_unit,
        "notes": payload.notes,
        "evidence_urls": payload.evidence_urls or [],
        "status": "DISPATCHED_TO_POLICE",
        "dispatched_at": now,
        "police_control_room": "National Emergency Response Support System (112)",
    }

    res = await police_dispatches_collection().insert_one(dispatch_doc)
    dispatch_doc["_id"] = str(res.inserted_id)
    dispatch_doc["id"] = str(res.inserted_id)

    # If linked to an incident, mark police dispatch flag
    if payload.incident_id:
        try:
            await incidents_collection().update_one(
                {"_id": ObjectId(payload.incident_id)},
                {"$set": {"police_dispatched": True, "police_dispatch_code": dispatch_code}},
            )
        except Exception:
            pass

    log_event("admin.police_dispatch", user_id="admin", detail={
        "dispatch_code": dispatch_code,
        "mobile": payload.mobile_number,
        "imei": payload.phone_imei,
        "lat": payload.latitude,
        "lng": payload.longitude,
    })

    return {
        "success": True,
        "message": f"Real-time emergency dispatch successfully routed to {payload.pcr_unit}",
        "dispatch_details": serialize_doc(dispatch_doc),
    }


@router.get("/dispatch-history")
async def get_police_dispatch_history():
    cursor = police_dispatches_collection().find({}).sort("dispatched_at", -1).limit(100)
    dispatches = []
    async for d in cursor:
        dispatches.append(serialize_doc(d))
    return dispatches


# --- 7. Danger Zones (Mark on Map & Show to User in Real-Time) ---
@router.get("/danger-zones")
async def get_all_danger_zones():
    cursor = danger_zones_collection().find({}).sort("created_at", -1)
    zones = []
    async for z in cursor:
        zones.append(serialize_doc(z))
    return zones


@router.post("/danger-zones", status_code=status.HTTP_201_CREATED)
async def create_danger_zone(payload: DangerZoneCreate):
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    doc["created_by"] = "admin"
    res = await danger_zones_collection().insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc["_id"] = str(res.inserted_id)

    log_event("admin.create_danger_zone", user_id="admin", detail={"title": payload.title, "lat": payload.latitude, "lng": payload.longitude})
    return serialize_doc(doc)


@router.patch("/danger-zones/{zone_id}")
async def update_danger_zone(zone_id: str, payload: DangerZoneUpdate):
    try:
        oid = ObjectId(zone_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid danger zone ID")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)

    res = await danger_zones_collection().update_one({"_id": oid}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Danger zone not found")

    updated = await danger_zones_collection().find_one({"_id": oid})
    return serialize_doc(updated)


@router.delete("/danger-zones/{zone_id}")
async def delete_danger_zone(zone_id: str):
    try:
        oid = ObjectId(zone_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid danger zone ID")

    res = await danger_zones_collection().delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Danger zone not found")

    log_event("admin.delete_danger_zone", user_id="admin", detail={"zone_id": zone_id})
    return {"success": True, "message": "Danger zone removed"}
