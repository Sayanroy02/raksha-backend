from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Any

from app.models.common import PyObjectId


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    email: EmailStr | None = None
    relationship: str | None = Field(default=None, max_length=50)
    relation: str | None = None

    @model_validator(mode="before")
    @classmethod
    def unify_relation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            rel = data.get("relationship") or data.get("relation") or "Family"
            data["relationship"] = rel
            data["relation"] = rel
        return data


class ContactUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    relationship: str | None = None
    relation: str | None = None

    @model_validator(mode="before")
    @classmethod
    def unify_relation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            rel = data.get("relationship") or data.get("relation")
            if rel:
                data["relationship"] = rel
                data["relation"] = rel
        return data


class ContactOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    name: str
    phone: str
    email: EmailStr | None = None
    relationship: str | None = "Family"
    relation: str | None = "Family"

    @model_validator(mode="before")
    @classmethod
    def populate_relation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            rel = data.get("relationship") or data.get("relation") or "Family"
            data["relationship"] = rel
            data["relation"] = rel
        return data

    model_config = {"populate_by_name": True}
