from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from src.database.db import get_db
from src.schemas import Contact, ContactCreate, ContactUpdate
from src.database.models import User
from src.services.auth import auth_service
from src.repository.contacts import (
    get_contact,
    get_contacts,
    create_contact,
    update_contact,
    delete_contact,
    search_contacts,
    get_upcoming_birthdays
)

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_new_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return create_contact(db=db, contact=contact, owner_id=current_user.id)

@router.get("/", response_model=List[Contact])
def read_all_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return get_contacts(db, owner_id=current_user.id, skip=skip, limit=limit)

@router.get("/{contact_id}", response_model=Contact)
def read_single_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    db_contact = get_contact(db, contact_id=contact_id, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.put("/{contact_id}", response_model=Contact)
def update_existing_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    db_contact = update_contact(db=db, contact_id=contact_id, contact=contact, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}", response_model=Contact)
def delete_existing_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    db_contact = delete_contact(db=db, contact_id=contact_id, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search/", response_model=List[Contact])
def search_contacts_by_query(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return search_contacts(db, query=query, owner_id=current_user.id)

@router.get("/birthdays/", response_model=List[Contact])
def get_contacts_with_upcoming_birthdays(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    return get_upcoming_birthdays(db, owner_id=current_user.id)