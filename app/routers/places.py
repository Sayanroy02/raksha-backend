from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user
from app.services.maps_service import find_nearby_services

router = APIRouter(prefix="/places", tags=["Location & Map Services"])


@router.get("/nearby")
async def nearby_services(
    lat: float = Query(...),
    lng: float = Query(...),
    type: str = Query("police", pattern="^(police|hospital)$"),
    radius_m: int = Query(3000, ge=100, le=50000),
    current_user: dict = Depends(get_current_user),
):
    return await find_nearby_services(lat, lng, type, radius_m)
