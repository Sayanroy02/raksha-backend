from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import contacts_collection
from app.deps import get_current_user
from app.models.contact import ContactCreate, ContactOut, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts"])


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def add_contact(payload: ContactCreate, current_user: dict = Depends(get_current_user)):
    doc = payload.model_dump()
    doc["user_id"] = current_user["_id"]
    result = await contacts_collection().insert_one(doc)
    created = await contacts_collection().find_one({"_id": result.inserted_id})
    return created


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    cursor = contacts_collection().find({"user_id": current_user["_id"]}).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(contact_id: str, payload: ContactUpdate, current_user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await contacts_collection().find_one_and_update(
        {"_id": ObjectId(contact_id), "user_id": current_user["_id"]},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return result


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(contact_id: str, current_user: dict = Depends(get_current_user)):
    result = await contacts_collection().delete_one(
        {"_id": ObjectId(contact_id), "user_id": current_user["_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
