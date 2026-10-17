from fastapi import APIRouter, Depends, Query, Request

from app.deps import get_current_user
from app.services.maps_service import (
    find_nearby_services,
    get_ip_location,
    reverse_geocode,
)

router = APIRouter(prefix="/places", tags=["Location & Map Services"])


@router.get("/nearby")
async def nearby_services(
    lat: float = Query(...),
    lng: float = Query(...),
    type: str = Query("police", pattern="^(police|hospital)$"),
    radius_m: int = Query(3000, ge=100, le=50000),
    current_user: dict = Depends(get_current_user),
):
    """Find nearby police stations or hospitals using Geoapify."""
    return await find_nearby_services(lat, lng, type, radius_m)


@router.get("/reverse-geocode")
async def get_address_from_coords(
    lat: float = Query(...),
    lng: float = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Reverse geocode coordinates into a formatted address."""
    return await reverse_geocode(lat, lng)


@router.get("/ip-location")
async def get_client_ip_location(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get location estimated from client IP when GPS is unavailable."""
    client_ip = request.client.host if request.client else None
    return await get_ip_location(client_ip)
