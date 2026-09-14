"""
Thin server-side proxy for Google Places 'nearby search' (M6 — Map &
Places). Keeping this on the backend means the Maps API key used for
Places never has to be embedded in the Flutter app.
"""

import httpx

from app.core.config import get_settings

settings = get_settings()

NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


async def find_nearby_services(lat: float, lng: float, place_type: str, radius_m: int = 3000) -> list[dict]:
    """place_type: 'police' or 'hospital'"""
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "type": place_type,
        "key": settings.google_maps_api_key,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(NEARBY_SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()

    return [
        {
            "name": result.get("name"),
            "address": result.get("vicinity"),
            "location": result.get("geometry", {}).get("location"),
            "rating": result.get("rating"),
        }
        for result in data.get("results", [])
    ]
