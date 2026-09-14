from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.database import close_mongo_connection, connect_to_mongo, create_indexes
from app.core.limiter import limiter
from app.routers import admin, auth, contacts, evidence, incidents, places, sos, threat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await create_indexes()
    yield
    close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Powered Women Safety and Emergency Response System — REST API",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(contacts.router, prefix=settings.api_v1_prefix)
app.include_router(sos.router, prefix=settings.api_v1_prefix)
app.include_router(evidence.router, prefix=settings.api_v1_prefix)
app.include_router(threat.router, prefix=settings.api_v1_prefix)
app.include_router(places.router, prefix=settings.api_v1_prefix)
app.include_router(incidents.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.app_name}
