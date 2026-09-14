"""
Central app configuration.

Everything here is read from environment variables (via a local .env file
in development, or real environment variables in production/hosting).
Never hardcode secrets in this file — .env is git-ignored on purpose.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Raksha+"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Database
    mongodb_uri: str
    mongodb_db_name: str = "rakshaplus"

    # Cloudinary
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    # Google Maps
    google_maps_api_key: str

    # CORS — comma-separated origins in .env, parsed into a list here
    cors_origins: str = "http://localhost"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so .env is only parsed once per process."""
    return Settings()
