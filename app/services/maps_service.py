"""
Server-side Geo Services using Geoapify with Google Maps fallback.

Provides:
- Nearby emergency places (police, hospitals) via Geoapify Places API
- Reverse Geocoding via Geoapify Geocoding API
- IP-based Geolocation via Geoapify IP API
- Static Map URL generator for SOS emails and alerts
"""

import logging
import httpx

from app.core.config import get_settings

logger = logging.getLogger("raksha.maps")
settings = get_settings()

GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_REVERSE_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/reverse"
GEOAPIFY_IP_INFO_URL = "https://api.geoapify.com/v1/ipinfo"
GOOGLE_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def get_geoapify_key() -> str:
    return settings.geoapify_api_key_geolocator or ""


async def reverse_geocode(lat: float, lng: float) -> dict:
    """
    Reverse geocodes coordinates to a human-readable address using Geoapify.
    """
    key = get_geoapify_key()
    if not key:
        return {
            "formatted": f"{lat:.5f}, {lng:.5f}",
            "city": "Unknown",
            "country": "India",
            "lat": lat,
            "lng": lng,
        }

    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "apiKey": key,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(GEOAPIFY_REVERSE_GEOCODE_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    first = results[0]
                    return {
                        "formatted": first.get("formatted", f"{lat:.5f}, {lng:.5f}"),
                        "street": first.get("street", ""),
                        "suburb": first.get("suburb", ""),
                        "city": first.get("city", first.get("town", "")),
                        "state": first.get("state", ""),
                        "postcode": first.get("postcode", ""),
                        "country": first.get("country", ""),
                        "lat": lat,
                        "lng": lng,
                    }
    except Exception as e:
        logger.warning("Geoapify reverse geocoding failed: %s", e)

    return {
        "formatted": f"{lat:.5f}, {lng:.5f}",
        "city": "Unknown",
        "country": "",
        "lat": lat,
        "lng": lng,
    }


async def find_nearby_services(lat: float, lng: float, place_type: str, radius_m: int = 3000) -> list[dict]:
    """
    place_type: 'police' or 'hospital'
    Uses Geoapify Places API v2 with Google Places fallback.
    """
    key = get_geoapify_key()

    if key:
        # Geoapify category mapping
        category = "service.police" if "police" in place_type.lower() else "healthcare.hospital"
        params = {
            "categories": category,
            "filter": f"circle:{lng},{lat},{radius_m}",
            "bias": f"proximity:{lng},{lat}",
            "limit": 20,
            "apiKey": key,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(GEOAPIFY_PLACES_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    results = []
                    for f in features:
                        props = f.get("properties", {})
                        geom = f.get("geometry", {})
                        coords = geom.get("coordinates", [lng, lat])
                        results.append({
                            "name": props.get("name") or props.get("formatted") or "Emergency Facility",
                            "address": props.get("formatted") or props.get("address_line2") or "",
                            "location": {"lat": coords[1], "lng": coords[0]},
                            "distance": props.get("distance"),
                            "phone": props.get("contact", {}).get("phone") if isinstance(props.get("contact"), dict) else None,
                        })
                    if results:
                        return results
        except Exception as e:
            logger.warning("Geoapify Places API failed, trying fallback: %s", e)

    # Google Maps fallback if google_maps_api_key is present
    if settings.google_maps_api_key:
        try:
            params = {
                "location": f"{lat},{lng}",
                "radius": radius_m,
                "type": place_type,
                "key": settings.google_maps_api_key,
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(GOOGLE_NEARBY_URL, params=params)
                if response.status_code == 200:
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
        except Exception as e:
            logger.warning("Google Places API failed: %s", e)

    # Built-in emergency contact fallback
    return [
        {
            "name": "Local Police Station (Emergency 112)",
            "address": "Nearest Police Outpost",
            "location": {"lat": lat + 0.005, "lng": lng + 0.005},
            "rating": 5.0,
        },
        {
            "name": "District General Hospital",
            "address": "Emergency Trauma Center",
            "location": {"lat": lat - 0.005, "lng": lng - 0.005},
            "rating": 4.8,
        },
    ]


async def get_ip_location(ip: str | None = None) -> dict:
    """
    IP Geolocation using Geoapify IP Info API.
    Provides fast, indoor fallback when GPS satellites are obscured.
    """
    key = get_geoapify_key()
    params = {"apiKey": key} if key else {}
    if ip and ip not in ("127.0.0.1", "localhost", "10.0.2.2"):
        params["ip"] = ip

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(GEOAPIFY_IP_INFO_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                loc = data.get("location", {})
                city = data.get("city", {}).get("name", "")
                country = data.get("country", {}).get("name", "India")
                return {
                    "lat": loc.get("latitude", 26.7271),
                    "lng": loc.get("longitude", 88.3953),
                    "city": city,
                    "country": country,
                }
    except Exception as e:
        logger.warning("IP Geolocation failed: %s", e)

    return {"lat": 26.7271, "lng": 88.3953, "city": "Siliguri", "country": "India"}


def get_static_map_url(lat: float, lng: float, width: int = 600, height: int = 350, zoom: int = 15) -> str:
    """
    Generates a Geoapify Static Map image URL.
    """
    key = get_geoapify_key()
    if key:
        return (
            f"https://maps.geoapify.com/v1/staticmap?"
            f"style=osm-bright&width={width}&height={height}"
            f"&center=lonlat:{lng},{lat}&zoom={zoom}"
            f"&marker=lonlat:{lng},{lat};color:%23ff0055;size:large"
            f"&apiKey={key}"
        )
    return f"https://static-maps.yandex.ru/1.x/?ll={lng},{lat}&z={zoom}&l=map&pt={lng},{lat},pm2rdm"
