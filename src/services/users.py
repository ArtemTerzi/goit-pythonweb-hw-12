"""Users business logic service.

Provides user management operations, including lookup, creation with
Gravatar integration, email confirmation, and avatar URL updates.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import UserCreate


class UserService:
    """Business logic service for managing users.

    Serves as an intermediary between the API router layer and the UserRepository,
    implementing additional integration logic such as Gravatar profile image generation.

    Attributes:
        repository (UserRepository): The repository handling database operations for users.
    """

    def __init__(self, db: AsyncSession):
        """Initializes the service with a database session.

        Args:
            db (AsyncSession): The active asynchronous database session.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """Creates a new user and attempts to retrieve their default avatar from Gravatar.

        Args:
            body (UserCreate): The validated schema containing user registration details.

        Returns:
            User: The newly created database user record.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """Retrieves a user by their unique database ID.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str, refresh_token: str = None):
        """Retrieves a user by their unique username.

        Args:
            username (str): The unique username of the user.
            refresh_token (str, optional): The session refresh token. Defaults to None.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_username(username, refresh_token)

    async def get_user_by_email(self, email: str):
        """Retrieves a user by their unique email address.

        Args:
            email (str): The unique email address of the user.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """Marks the user's email address as confirmed.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """Updates the avatar image URL for a specified user.

        Args:
            email (str): The email address of the user.
            url (str): The new secure URL path to the avatar image (e.g., from Cloudinary).

        Returns:
            User: The updated User database record.
        """
        return await self.repository.update_avatar_url(email, url)
