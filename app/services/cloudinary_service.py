"""
Cloudinary integration for evidence media (M4 — Evidence Capture).
We never proxy raw media bytes through our own server for large files;
instead we hand the client a signed upload signature and let Flutter
upload directly to Cloudinary, then we save the returned URL.
"""

import time

import cloudinary
import cloudinary.utils

from app.core.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


def generate_signed_upload_params(folder: str = "raksha_evidence") -> dict:
    """
    Returns everything the Flutter app needs to perform a direct, signed
    upload to Cloudinary (keeps the API secret server-side only).
    """
    timestamp = int(time.time())
    params_to_sign = {"timestamp": timestamp, "folder": folder}
    signature = cloudinary.utils.api_sign_request(params_to_sign, settings.cloudinary_api_secret)

    return {
        "timestamp": timestamp,
        "signature": signature,
        "api_key": settings.cloudinary_api_key,
        "cloud_name": settings.cloudinary_cloud_name,
        "folder": folder,
    }
