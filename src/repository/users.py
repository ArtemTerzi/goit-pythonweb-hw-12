"""Users database repository.

Handles direct database operations on the User model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    """Repository handling read and write tasks on User models."""

    def __init__(self, session: AsyncSession):
        """Initializes the repository with a session.

        Args:
            session (AsyncSession): Active database session.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Finds user by database primary ID.

        Args:
            user_id (int): Primary key ID.

        Returns:
            User | None: Matched User entity, or None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(
        self, username: str, refresh_token: str | None
    ) -> User | None:
        """Finds user by username.

        Args:
            username (str): Target username.

        Returns:
            User | None: Matched User entity, or None.
        """
        stmt = select(User).filter_by(username=username)

        if refresh_token:
            stmt = stmt.filter_by(refresh_token=refresh_token)

        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Finds user by email.

        Args:
            email (str): Target email string.

        Returns:
            User | None: Matched User entity, or None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """Persists a new user record.

        Args:
            body (UserCreate): Schema payload with sign-up details.
            hashed_password (str): Prepared secure bcrypt hash.
            avatar (str, optional): Default avatar URL string. Defaults to None.

        Returns:
            User: Created User record.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_token(self, user: User, token: str | None) -> None:
        """Updates the refresh token for a specified user in the database.

        Args:
            user (User): The user object whose refresh token needs to be updated.
            token (str | None): The new refresh token string, or None to invalidate/clear the token.
        """
        user.refresh_token = token
        await self.db.commit()
        await self.db.refresh(user)

    async def confirmed_email(self, email: str) -> None:
        """Marks the user's email address as confirmed.

        Args:
            email (str): The email address of the user to confirm.
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Updates the avatar image URL for a user identified by their email.

        Args:
            email (str): The email address of the user.
            url (str): The new secure URL path to the avatar image (e.g. from Cloudinary).

        Returns:
            User: The updated User database object.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, email: str, hashed_password: str) -> User:
        """Updates the stored password hash for a user identified by email.

        Also clears any active refresh token so that previously issued sessions
        are invalidated after a password change.

        Args:
            email (str): The email address of the user.
            hashed_password (str): The new bcrypt password hash to store.

        Returns:
            User: The updated User database object.
        """
        user = await self.get_user_by_email(email)
        user.hashed_password = hashed_password
        user.refresh_token = None
        await self.db.commit()
        await self.db.refresh(user)
        return user
