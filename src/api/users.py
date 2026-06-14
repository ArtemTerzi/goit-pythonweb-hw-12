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
from src.services.auth import get_current_user, get_admin_user
from src.services.cache import user_cache
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
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploads a new avatar and updates the user's profile. Admins only.

    This endpoint is restricted to users with the ``admin`` role: only
    administrators may replace their default avatar. Integrates with the
    Cloudinary service to store the uploaded image, updates the user's database
    record with the new secure URL, and invalidates the cached user so the
    change is reflected immediately.

    Args:
        file (UploadFile): The raw image file uploaded by the user. Defaults to File().
        user (User): The currently authenticated admin user. Defaults to Depends(get_admin_user).
        db (AsyncSession): Asynchronous database session. Defaults to Depends(get_db).

    Returns:
        User: The updated user schema containing the new avatar URL.

    Raises:
        HTTPException: If the current user is not an administrator (403 Forbidden).
    """
    avatar_url = UploadFileService(
        config.CLOUDINARY_NAME, config.CLOUDINARY_API_KEY, config.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)
    await user_cache.invalidate_user(user.username)

    return user
