"""Contacts API router.

Defines the FastAPI routes for handling CRUD operations on contact records,
including retrieving lists, filtering, updating, and deleting contacts.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import ContactModel, ContactResponse, ContactUpdate, User
from src.services.contacts import ContactService
from src.api.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    first_name: str | None = Query(None, description="Search by name"),
    last_name: str | None = Query(None, description="Search by last name"),
    email: str | None = Query(None, description="Search by email"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieves a list of contacts owned by the current authenticated user.

    Supports pagination limits and optional substring filtering by first name,
    last name, or email address.

    Args:
        skip (int): The number of records to skip (offset) for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 100.
        first_name (str | None): Optional search keyword for the first name field. Defaults to None.
        last_name (str | None): Optional search keyword for the last name field. Defaults to None.
        email (str | None): Optional search keyword for the email field. Defaults to None.
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        list[ContactResponse]: A list of contact schemas representing the matched records.
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts(
        skip, limit, first_name, last_name, email, user
    )
    return contacts


@router.get("/birthdays", response_model=list[ContactResponse])
async def read_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieves contacts celebrating birthdays within the next 7 days.

    Args:
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        list[ContactResponse]: A list of contact schemas with upcoming birthdays.
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_upcoming_birthdays(user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieves detailed information of a specific contact by its ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        ContactResponse: The matching contact schema.

    Raises:
        HTTPException: If the contact does not exist or does not belong to the user (404 Not Found).
    """
    contact_service = ContactService(db)
    contact = await contact_service.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Creates a new contact record linked to the authenticated user.

    Args:
        body (ContactModel): The schema payload containing contact details.
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        ContactResponse: The newly created contact schema.
    """
    contact_service = ContactService(db)
    return await contact_service.create_contact(body, user)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdate,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Partially updates an existing contact record.

    Args:
        body (ContactUpdate): The payload containing fields to update.
        contact_id (int): The ID of the contact to update.
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        ContactResponse: The updated contact schema.

    Raises:
        HTTPException: If the contact is not found or does not belong to the user (404 Not Found).
    """
    contact_service = ContactService(db)
    contact = await contact_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Deletes a specific contact from the database.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        ContactResponse: The deleted contact schema.

    Raises:
        HTTPException: If the contact is not found or does not belong to the user (404 Not Found).
    """
    contact_service = ContactService(db)
    contact = await contact_service.remove_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact
