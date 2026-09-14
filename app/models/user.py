from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.common import PyObjectId


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    email: EmailStr
    phone: str
    role: Literal["user", "admin"] = "user"
    created_at: datetime

    model_config = {"populate_by_name": True}


class UserInDB(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password_hash: str
    role: Literal["user", "admin"] = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
