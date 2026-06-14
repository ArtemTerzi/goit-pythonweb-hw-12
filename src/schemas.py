"""Application schemas module.

Defines Pydantic models for data validation, serialization, and deserialization
used across authentication, user management, and contact operations.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.database.models import UserRole


class ContactModel(BaseModel):
    """Pydantic model representing input data for creating a contact.

    Attributes:
        first_name (str): First name of the contact. Min length 3, max length 50.
        last_name (str): Last name of the contact. Min length 3, max length 50.
        email (EmailStr): Validated unique email of the contact. Max length 50.
        phone_number (str): Phone number of the contact. Max length 20.
        birthday (date): Birthday of the contact.
        description (str, optional): Additional description. Max length 250.
    """

    first_name: str = Field(..., min_length=3, max_length=50)
    last_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=50)
    phone_number: str = Field(..., max_length=20)
    birthday: date
    description: str | None = Field(None, max_length=250)


class ContactResponse(ContactModel):
    """Pydantic model representing the output data for a contact.

    Inherits all fields from ContactModel and adds database-specific metadata.

    Attributes:
        id (int): Unique database identifier of the contact.
        created_at (datetime): The timestamp when the record was created.
        updated_at (datetime): The timestamp when the record was last modified.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactUpdate(BaseModel):
    """Pydantic model representing fields that can be updated for a contact.

    All fields are optional, enabling partial updates (PATCH requests).

    Attributes:
        first_name (str, optional): Updated first name. Min length 2, max length 50. Defaults to None.
        last_name (str, optional): Updated last name. Min length 2, max length 50. Defaults to None.
        email (EmailStr, optional): Updated validated email. Max length 50. Defaults to None.
        phone_number (str, optional): Updated phone number. Max length 20. Defaults to None.
        birthday (date, optional): Updated birthday. Defaults to None.
        description (str, optional): Updated description. Max length 250. Defaults to None.
    """

    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = Field(None, max_length=50)
    phone_number: str | None = Field(None, max_length=20)
    birthday: date | None = None
    description: str | None = Field(None, max_length=250)


class User(BaseModel):
    """Pydantic model representing user profile details returned in responses.

    Attributes:
        id (int): Unique database identifier of the user.
        username (str): The unique username of the user.
        email (EmailStr, optional): Validated email of the user. Max length 50. Defaults to None.
        avatar (str): URL path pointing to the user's avatar.
        role (UserRole): Access role of the user ("user" or "admin").
    """

    id: int
    username: str
    email: EmailStr | None = Field(None, max_length=50)
    avatar: str
    role: UserRole = UserRole.USER

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Pydantic model representing input data for user registration.

    Attributes:
        username (str): The requested unique username.
        email (EmailStr): Validated email address.
        password (str): Cleartext password.
    """

    username: str
    email: EmailStr
    password: str


class TokenModel(BaseModel):
    """Pydantic model representing authentication token details returned on successful login.

    Attributes:
        access_token (str): The encoded JWT access token.
        refresh_token (str): The encoded JWT refresh token.
        token_type (str): The token type (e.g., 'bearer').
    """

    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    """Pydantic model representing a token refresh payload.

    Attributes:
        refresh_token (str): The active refresh token used to request new tokens.
    """

    refresh_token: str


class RequestEmail(BaseModel):
    """Pydantic model representing a payload to request a verification email.

    Attributes:
        email (EmailStr): Validated email address of the target account.
    """

    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Pydantic model representing a request to start password recovery.

    Attributes:
        email (EmailStr): The email address of the account to recover.
    """

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Pydantic model representing a payload to set a new password.

    Attributes:
        new_password (str): The new cleartext password. Min length 6.
    """

    new_password: str = Field(..., min_length=6, max_length=128)
