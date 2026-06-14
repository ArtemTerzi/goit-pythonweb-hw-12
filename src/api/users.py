"""Users API router.

Defines the FastAPI routes for retrieving current user profile information and
updating user avatars using the Cloudinary cloud storage service.
"""

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database.db import get_db
from src.schemas import User
from src.services.auth import get_current_user
from src.services.upload_file import UploadFileService
from src.services.users import UserService
from src.conf.config import config

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=User)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user.

    This endpoint has an active rate-limiting configuration of maximum 5 requests
    per minute per remote IP address.

    Args:
        request (Request): The incoming HTTP request (required by the rate limiter).
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).

    Returns:
        User: The schema containing the user's profile details.
    """
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploads a new avatar file and updates the user's profile in the database.

    Integrates with the Cloudinary service to store the uploaded image file,
    then updates the user's database record with the newly generated secure image URL.

    Args:
        file (UploadFile): The raw image file uploaded by the user. Defaults to File().
        user (User): The currently authenticated user. Defaults to Depends(get_current_user).
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).

    Returns:
        User: The updated user schema containing the new avatar URL.
    """
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
