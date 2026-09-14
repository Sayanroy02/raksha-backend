from fastapi import APIRouter, Depends, Query

from app.core.database import incidents_collection, users_collection
from app.deps import require_admin
from app.models.incident import IncidentOut
from app.models.user import UserOut
from app.services.audit_service import log_event

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    cursor = users_collection().find({}).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.get("/incidents", response_model=list[IncidentOut])
async def list_all_incidents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    cursor = incidents_collection().find({}).sort("triggered_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, admin: dict = Depends(require_admin)):
    from bson import ObjectId

    await users_collection().update_one({"_id": ObjectId(user_id)}, {"$set": {"active": False}})
    log_event("admin.deactivate_user", user_id=admin["_id"], detail={"target_user_id": user_id})
    return {"detail": "User deactivated"}
