from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import users_collection
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps import get_current_user
from app.core.limiter import limiter
from app.models.user import RefreshRequest, TokenPair, UserLogin, UserOut, UserRegister
from app.services.audit_service import log_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    existing = await users_collection().find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password),
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection().insert_one(user_doc)
    created = await users_collection().find_one({"_id": result.inserted_id})
    log_event("auth.register", user_id=created["_id"], detail={"email": payload.email})
    return created


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
async def login(request: Request, payload: UserLogin):
    user = await users_collection().find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        log_event("auth.login.failed", user_id=None, detail={"email": payload.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user_id = str(user["_id"])
    log_event("auth.login", user_id=user["_id"], detail={"email": payload.email})
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshRequest):
    try:
        decoded = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user_id = decoded["sub"]
    user = await users_collection().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    log_event("auth.refresh", user_id=user["_id"], detail={})
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
