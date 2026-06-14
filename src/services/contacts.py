"""Contacts service module.

Coordinates high-level operations on contacts by interacting with repositories.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, ContactUpdate, User


class ContactService:
    """Service layer executing business rules for Contact records."""

    def __init__(self, db: AsyncSession):
        """Initializes the service with a database session.

        Args:
            db (AsyncSession): The active database session.
        """
        self.repository = ContactRepository(db)

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        first_name: str | None,
        last_name: str | None,
        email: str | None,
        user: User,
    ):
        """Fetches filtered contacts with pagination.

        Args:
            skip (int): Page offset.
            limit (int): Record limit.
            first_name (str | None): First name search parameter.
            last_name (str | None): Last name search parameter.
            email (str | None): Email search parameter.
            user (User): The authenticated owner of contacts.

        Returns:
            list[Contact]: Matched database records list.
        """
        return await self.repository.get_contacts(
            skip, limit, first_name, last_name, email, user
        )

    async def get_contact(self, contact_id: int, user: User):
        """Fetches a specific contact record by its ID.

        Args:
            contact_id (int): Contact unique identifier.
            user (User): Owner of the contact.

        Returns:
            Contact | None: The Contact database record, or None.
        """
        return await self.repository.get_contact_by_id(contact_id, user)

    async def get_upcoming_birthdays(self, user: User):
        """Retrieves birthdays scheduled within the next week.

        Args:
            user (User): Authenticated owner of the contacts.

        Returns:
            list[Contact]: List of Contact objects celebrating birthdays soon.
        """
        return await self.repository.get_upcoming_birthdays(user)

    async def create_contact(self, body: ContactModel, user: User):
        """Processes contact creation.

        Args:
            body (ContactModel): Validated input parameters.
            user (User): Owner of the new contact.

        Returns:
            Contact: Created Contact entity.
        """
        existing_contact = await self.repository.get_contact_by_email(body.email, user)

        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contact with this email already exists.",
            )

        return await self.repository.create_contact(body, user)

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User):
        """Processes contact updates.

        Args:
            contact_id (int): ID of the contact to update.
            body (ContactUpdate): Payload with parameters to update.
            user (User): Owner of the contact.

        Returns:
            Contact | None: Updated contact database model, or None.
        """
        existing_contact = await self.repository.get_contact_by_email(body.email, user)

        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A contact with this email already exists.",
            )

        return await self.repository.update_contact(contact_id, body, user)

    async def remove_contact(self, contact_id: int, user: User):
        """Processes contact deletion.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): Owner of the contact.

        Returns:
            Contact | None: Deleted contact database model, or None.
        """
        return await self.repository.remove_contact(contact_id, user)
