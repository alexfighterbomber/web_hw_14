from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from sqlalchemy.engine import Result
from datetime import date, timedelta
from typing import List

from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdate

async def get_contact(db: AsyncSession, contact_id: int, owner_id: int) -> Contact | None:
    """
    Retrieves a single contact with the contact_id for a specific owner_id.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param owner_id: The owner_id to retrieve the contact for.
    :type owner_id: int
    :param db: The database session.
    :type db: AsyncSession
    :return: The contact with the specified contact_id, or None if it does not exist.
    :rtype: contact | None
    """
    req = select(Contact).where(
        Contact.id == contact_id,
        Contact.owner_id == owner_id
    )
    result: Result = await db.execute(req)
    return result.scalar_one_or_none()

    # return db.query(Contact).filter(
    #     Contact.id == contact_id,
    #     Contact.owner_id == owner_id
    # ).first()

async def get_contacts(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
    """
    Retrieves a list of contacts for a specific owner_id with specified pagination parameters.

    :param db: The database session.
    :type db: AsyncSession
    :param owner_id: The ID of the owner of the contacts.
    :type owner_id: int
    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :return: A list of contacts.
    :rtype: List[ContactModel]
    """
    req = select(Contact).where(
        Contact.owner_id == owner_id
    ).offset(skip).limit(limit)
    result: Result = await db.execute(req)
    return result.scalars().all()

    # return db.query(Contact).filter(
    #     Contact.owner_id == owner_id
    # ).offset(skip).limit(limit).all()


async def create_contact(db: AsyncSession, contact: ContactCreate, owner_id: int) -> Contact:
    """
    Creates a new contact for a specific owner_id.

    :param db: The database session.
    :type db: AsyncSession
    :param contact: The data for the contact to create.
    :type contact: ContactCreate
    :param owner_id: The ID of the owner of the contacts.
    :type owner_id: int
    :return: The newly created note.
    :rtype: Contact
    """
    db_contact = Contact(**contact.dict(), owner_id=owner_id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact



async def update_contact(db: AsyncSession, contact_id: int, contact: ContactUpdate, owner_id: int) -> Contact | None:
    """
    Updates a contact for a specific owner_id.

    :param db: The database session.
    :type db: AsyncSession
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param contact: The data for the contact to create.
    :type contact: ContactUpdate
    :param owner_id: The ID of the owner of the contacts.
    :type owner_id: int
    :return: Updated contact or  or None if it does not exist.
    :rtype: Contact|None
    """
    db_contact = await get_contact(db, contact_id=contact_id, owner_id=owner_id)
    if not db_contact:
        return None
    
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def delete_contact(db: AsyncSession, contact_id: int, owner_id: int) -> Contact | None:
    """
    Removes a single contact for a specific owner_id.

    :param db: The database session.
    :type db: AsyncSession
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param owner_id: The ID of the owner of the contacts.
    :type owner_id: int
    :return: Deleted contact or  or None if it does not exist.
    :rtype: Contact|None
    """    
    db_contact = await get_contact(db, contact_id=contact_id, owner_id=owner_id)
    if not db_contact:
        return None
    
    await db.delete(db_contact)
    await db.commit()
    return db_contact


async def search_contacts(db: AsyncSession, query: str, owner_id: int) -> list[Contact]:
    """
    Search a contact by query for a specific owner_id.

    :param db: The database session.
    :type db: AsyncSession
    :param query: The search query to filter contacts.
    :type query: str
    :param owner_id: The owner_id to retrieve the contact for.
    :type owner_id: int
    :return: A list of contacts that match the search query.
    :rtype: List[Contact]
    """    
    req = select(Contact).where(
        Contact.owner_id == owner_id, or_ (
            Contact.first_name.ilike(f"%{query}%"),
            Contact.last_name.ilike(f"%{query}%"),
            Contact.email.ilike(f"%{query}%")
        )
    )
    result: Result = await db.execute(req)
    return result.scalars().all()


async def get_upcoming_birthdays(db: AsyncSession, owner_id: int) -> list[Contact]:
    """
    Retrieves a list of contacts with upcoming birthdays within the next week for a specific owner_id.

    :param db: The database session.
    :type db: AsyncSession
    :param owner_id: The ID of the owner of the contacts.
    :type owner_id: int
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[Contact]
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    
    req = select(Contact).where(Contact.owner_id == owner_id)
    result: Result = await db.execute(req)
    contacts = result.scalars().all()

    upcoming_contacts = []
    
    for contact in contacts:
        if contact.birthday:
            bday_this_year = contact.birthday.replace(year=today.year)
            
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
            
            if today <= bday_this_year <= next_week:
                upcoming_contacts.append(contact)
    
    return upcoming_contacts
