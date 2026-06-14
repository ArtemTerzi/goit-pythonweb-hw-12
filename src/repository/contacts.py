"""Contacts database repository.

Provides direct database queries for Contact records using SQLAlchemy.
"""

from typing import List
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact
from src.schemas import ContactModel, ContactUpdate, User


class ContactRepository:
    """Repository class for handling database queries for Contacts."""

    def __init__(self, session: AsyncSession):
        """Initializes the repository with a database session.

        Args:
            session (AsyncSession): The active asynchronous database session.
        """
        self.db = session

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        first_name: str | None,
        last_name: str | None,
        email: str | None,
        user: User,
    ) -> List[Contact]:
        """Retrieves a list of contacts with pagination and optional filters.

        Args:
            skip (int): The number of contacts to skip (offset).
            limit (int): The maximum number of contacts to return.
            first_name (str | None): Filter by first name substring.
            last_name (str | None): Filter by last name substring.
            email (str | None): Filter by email substring.
            user (User): The authenticated owner of the contacts.

        Returns:
            List[Contact]: List of Contacts matching the criteria.
        """
        stmt = select(Contact).filter_by(user=user)

        if first_name:
            stmt = stmt.filter(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.filter(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.filter(Contact.email.ilike(f"%{email}%"))

        stmt = stmt.offset(skip).limit(limit)

        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(
        self,
        contact_id: int,
        user: User,
    ) -> Contact | None:
        """Retrieves a single contact by its ID.

        Args:
            contact_id (int): The ID of the contact to find.
            user (User): The owner of the contact.

        Returns:
            Contact | None: The Contact object if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def get_upcoming_birthdays(
        self,
        user: User,
    ) -> List[Contact]:
        """Finds contacts with birthdays within the next 7 days.

        Args:
            user (User): The owner of the contacts.

        Returns:
            List[Contact]: List of contacts celebrating their birthday soon.
        """
        today = date.today()
        upcoming_dates = [today + timedelta(days=i) for i in range(8)]
        target_days = [d.strftime("%m-%d") for d in upcoming_dates]

        stmt = (
            select(Contact)
            .filter_by(user=user)
            .filter(func.to_char(Contact.birthday, "MM-DD").in_(target_days))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_contact(
        self,
        body: ContactModel,
        user: User,
    ) -> Contact:
        """Creates a new contact record in the database.

        Args:
            body (ContactModel): Validated schema containing contact details.
            user (User): Owner of the new contact.

        Returns:
            Contact: The newly created database record.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self,
        contact_id: int,
        body: ContactUpdate,
        user: User,
    ) -> Contact | None:
        """Updates fields of a specified contact.

        Args:
            contact_id (int): ID of the contact to update.
            body (ContactUpdate): Payload containing update parameters.
            user (User): Owner of the contact.

        Returns:
            Contact | None: The updated Contact object, or None if not found.
        """
        query = select(Contact).filter_by(id=contact_id, user=user)
        result = await self.db.execute(query)
        contact = result.scalar_one_or_none()

        if not contact:
            return None

        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def remove_contact(
        self,
        contact_id: int,
        user: User,
    ) -> Contact | None:
        """Deletes a contact from the database.

        Args:
            contact_id (int): ID of the target contact.
            user (User): Owner of the contact.

        Returns:
            Contact | None: The deleted Contact object, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def get_contact_by_email(
        self,
        email: str,
        user: User,
    ) -> Contact | None:
        """Finds a contact by its unique email address.

        Args:
            email (str): Target email string.
            user (User): Owner of the contact.

        Returns:
            Contact | None: Contact record if matched, otherwise None.
        """
        stmt = select(Contact).filter_by(email=email, user=user)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
