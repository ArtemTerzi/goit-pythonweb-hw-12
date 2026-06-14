"""Database models module.

This module defines the SQLAlchemy Declarative models representing
the database schema for Users and Contacts.
"""

from datetime import datetime, date
from sqlalchemy import Integer, String, func, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from sqlalchemy.sql.sqltypes import DateTime, Date
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy Declarative models."""

    pass


class Contact(Base):
    """SQLAlchemy model representing a contact.

    Attributes:
        id (int): Unique identifier for the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        email (str): Unique email address of the contact.
        phone_number (str): Phone number of the contact.
        birthday (date): Birthday of the contact.
        description (str, optional): Additional details about the contact.
        created_at (datetime): Timestamp when the contact was created.
        updated_at (datetime): Timestamp when the contact was last updated.
        user_id (int): Foreign key linking to the owner's ID.
        user (User): Relationship pointing to the owner (User object).
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), default=None, nullable=True
    )
    user: Mapped["User"] = relationship("User", back_populates="contacts")


class User(Base):
    """SQLAlchemy model representing a user.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Unique username of the user.
        hashed_password (str): Hashed password of the user.
        email (str): Unique email address of the user.
        refresh_token (str, optional): Token used to issue new access tokens.
        created_at (datetime): Timestamp when the user registered.
        updated_at (datetime): Timestamp when the user profile was last updated.
        avatar (str, optional): URL path to the user's avatar image.
        contacts (list[Contact]): List of contacts owned by this user.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    avatar: Mapped[str] = mapped_column(String(200), nullable=True)
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="user")
