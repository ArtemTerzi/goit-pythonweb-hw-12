"""Authentication services module.

Provides utility classes and functions for hashing passwords, generating
various security tokens (access, refresh, and email confirmation tokens),
and validating active sessions.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Literal

import bcrypt
from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.database.models import User, UserRole
from src.conf.config import config
from src.conf import messages
from src.services.users import UserService
from src.services.cache import user_cache


class Hash:
    """Utility class for hashing and verifying passwords using Bcrypt."""

    def verify_password(self, plain_password, hashed_password):
        """Verifies a plain password against a hashed password.

        Args:
            plain_password (str): Cleartext password to check.
            hashed_password (str): Hashed password to compare against.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (UnicodeEncodeError, ValueError):
            return False

    def get_password_hash(self, password: str) -> str:
        """Generates a secure Bcrypt hash for a plain password.

        Args:
            password (str): The cleartext password to hash.

        Returns:
            str: The hashed password string.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")


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

    Acts as a FastAPI dependency for route authorization. To avoid querying the
    database on every authenticated request, the resolved user is cached in
    Redis keyed by username. Subsequent requests are served straight from the
    cache until the entry expires or is explicitly invalidated.

    Args:
        token (str): The extracted Bearer token string. Defaults to Dependency(oauth2_scheme).
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        User: The authorized User object (served from cache or the database).

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

    cached_user = await user_cache.get_user(username)
    if cached_user is not None:
        return cached_user

    user = await UserService(db).get_user_by_username(username)
    if user is None:
        raise credentials_exception

    await user_cache.set_user(user)
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

def create_reset_password_token(data: dict) -> str:
    """Generates a short-lived JWT used to authorize a password reset.

    The token carries a dedicated ``token_type`` of ``"reset"`` so it cannot be
    repurposed as an access, refresh, or email-confirmation token.

    Args:
        data (dict): Payload containing the subject (the user's email address).

    Returns:
        str: Encoded JWT password reset token.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=config.JWT_RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "token_type": "reset"})
    return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


async def get_email_from_reset_token(token: str) -> str:
    """Decodes a password reset token to retrieve the embedded email address.

    Args:
        token (str): The raw password reset token.

    Returns:
        str: The extracted email address.

    Raises:
        HTTPException: If the token is invalid, expired, or not a reset token (400 Bad Request).
    """
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        token_type = payload.get("token_type")
        if email is None or token_type != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=messages.INVALID_RESET_TOKEN,
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=messages.INVALID_RESET_TOKEN,
        )


class RoleAccess:
    """FastAPI dependency enforcing that the current user has an allowed role.

    Usage::

        require_admin = RoleAccess([UserRole.ADMIN])

        @router.patch("/avatar")
        async def update_avatar(user: User = Depends(require_admin)):
            ...

    Attributes:
        allowed_roles (list[UserRole]): Roles permitted to access the route.
    """

    def __init__(self, allowed_roles: list[UserRole]):
        """Initializes the dependency with the set of permitted roles.

        Args:
            allowed_roles (list[UserRole]): Roles allowed to pass the check.
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self, current_user: User = Depends(get_current_user)
    ) -> User:
        """Validates the current user's role against the allowed roles.

        Args:
            current_user (User): The authenticated user, injected by FastAPI.

        Returns:
            User: The current user, unchanged, if the role check passes.

        Raises:
            HTTPException: If the user's role is not permitted (403 Forbidden).
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=messages.INSUFFICIENT_PERMISSIONS,
            )
        return current_user


get_admin_user = RoleAccess([UserRole.ADMIN])
"""Dependency that allows only users with the ADMIN role."""
