from pydantic import BaseModel, EmailStr, Field

from app.models.common import PyObjectId


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    email: EmailStr | None = None
    relationship: str | None = Field(default=None, max_length=50)


class ContactUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    relationship: str | None = None


class ContactOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    name: str
    phone: str
    email: EmailStr | None = None
    relationship: str | None = None

    model_config = {"populate_by_name": True}
