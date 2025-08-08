from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
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
async def create_new_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    """
    Create a new contact for the current user.

    :param contact: The contact data to create.
    :type contact: ContactCreate
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The newly created contact.
    :rtype: Contact
    """
    return await create_contact(db=db, contact=contact, owner_id=current_user.id)

@router.get("/", response_model=List[Contact])
async def read_all_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> List[Contact]:
    """
    Retrieve a list of contacts for the current user.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A list of contacts for the current user.
    :rtype: List[Contact]
    """
    return await get_contacts(db, owner_id=current_user.id, skip=skip, limit=limit)

@router.get("/{contact_id}", response_model=Contact)
async def read_single_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    """
    Retrieve a single contact by its ID for the current user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The contact with the specified ID.
    :rtype: Contact
    """
    db_contact = await get_contact(db, contact_id=contact_id, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.put("/{contact_id}", response_model=Contact)
async def update_existing_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    """
    Update an existing contact for the current user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param contact: The updated contact data.
    :type contact: ContactUpdate
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The updated contact.
    :rtype: Contact
    """
    db_contact = await update_contact(db=db, contact_id=contact_id, contact=contact, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}", response_model=Contact)
async def delete_existing_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    """
    Delete a contact by its ID for the current user.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The deleted contact.
    :rtype: Contact
    """
    db_contact = await delete_contact(db=db, contact_id=contact_id, owner_id=current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search/", response_model=List[Contact])
async def search_contacts_by_query(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> List[Contact]:
    """ 
    Search for contacts by a query string for the current user.

    :param query: The search query string.
    :type query: str
    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A list of contacts matching the search query.
    :rtype: List[Contact]
    """
    return await search_contacts(db, query=query, owner_id=current_user.id)

@router.get("/birthdays/", response_model=List[Contact])
async def get_contacts_with_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> List[Contact]:
    """
    Retrieve contacts with upcoming birthdays for the current user.

    :param db: The database session.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[Contact]
    """
    return await get_upcoming_birthdays(db, owner_id=current_user.id)