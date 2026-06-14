"""Authentication services module.

Provides utility classes and functions for hashing passwords, generating
various security tokens (access, refresh, and email confirmation tokens),
and validating active sessions.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Literal

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.conf.config import config
from src.conf import messages
from src.services.users import UserService


class Hash:
    """Utility class for hashing and verifying passwords using Bcrypt."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """Verifies a plain password against a hashed password.

        Args:
            plain_password (str): Cleartext password to check.
            hashed_password (str): Hashed password to compare against.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """Generates a secure Bcrypt hash for a plain password.

        Args:
            password (str): The cleartext password to hash.

        Returns:
            str: The hashed password string.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
):
    """Creates an encoded JWT token based on the provided payload and lifetime.

    Args:
        data (dict): The payload data to encode inside the token.
        expires_delta (timedelta): Allowed lifespan for the token.
        token_type (Literal["access", "refresh"]): The category of token being created.

    Returns:
        str: Encoded JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM
    )
    return encoded_jwt


async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """Generates an access token with a configured expiration time.

    Args:
        data (dict): The payload data to encode.
        expires_delta (float, optional): Optional custom expiry in seconds. Defaults to None.

    Returns:
        str: Encoded JWT access token.
    """
    if expires_delta:
        access_token = create_token(data, expires_delta, "access")
    else:
        access_token = create_token(
            data, timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES), "access"
        )
    return access_token


async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """Generates a refresh token with a configured expiration time.

    Args:
        data (dict): The payload data to encode.
        expires_delta (float, optional): Optional custom expiry in seconds. Defaults to None.

    Returns:
        str: Encoded JWT refresh token.
    """
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data, timedelta(minutes=config.JWT_REFRESH_TOKEN_EXPIRE_MINUTES), "refresh"
        )
    return refresh_token


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Decodes and validates an incoming access token to retrieve the current user.

    Acts as a FastAPI dependency for route authorization.

    Args:
        token (str): The extracted Bearer token string. Defaults to Dependency(oauth2_scheme).
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        User: The authorized User object fetched from the database.

    Raises:
        HTTPException: If credentials validation fails, token has expired, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user = await UserService(db).get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


async def verify_refresh_token(refresh_token: str, db: AsyncSession):
    """Decodes a refresh token and validates it against database constraints.

    Args:
        refresh_token (str): The JWT refresh token string to verify.
        db (AsyncSession): Asynchronous database session.

    Returns:
        User: The verified User object.

    Raises:
        HTTPException: If verification fails, token has expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=messages.UNVERIFIED_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            refresh_token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        token_type = payload.get("token_type")
        if username is None or token_type != "refresh":
            raise credentials_exception
        user = await UserService(db).get_user_by_username(username, refresh_token)
        return user
    except JWTError as e:
        raise credentials_exception


def create_email_token(data: dict):
    """Generates a JWT token used specifically for email confirmation.

    Args:
        data (dict): Payload containing the subject (usually email address).

    Returns:
        str: Encoded JWT email token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=config.JWT_REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """Decodes an email token to retrieve the embedded email address.

    Args:
        token (str): The raw email verification token.

    Returns:
        str: The extracted email address.

    Raises:
        HTTPException: If the token is invalid, expired, or unprocessable.
    """
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=messages.UNEXISTING_TOKEN,
        )
