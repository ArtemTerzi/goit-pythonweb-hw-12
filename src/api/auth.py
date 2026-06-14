"""Authentication API router.

Defines API endpoints for user signup, email verification, login, token refresh,
and requesting confirmation emails.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas import (
    UserCreate,
    TokenModel,
    TokenRefreshRequest,
    User,
    RequestEmail,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    Hash,
    get_email_from_token,
    get_email_from_reset_token,
)
from src.services.users import UserService
from src.services.cache import user_cache
from src.database.db import get_db
from src.conf import messages
from src.services.email import send_email, send_reset_password_email

router = APIRouter(prefix="/auth", tags=["auth"])
hash_handler = Hash()


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup(
    body: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new user in the system.

    Checks the database to ensure the username and email are unique. If unique,
    hashes the provided password, persists the user record, and schedules a
    verification email to be sent asynchronously in the background.

    Args:
        body (UserCreate): The registration details for the new user.
        request (Request): The incoming HTTP request, used to construct the base URL.
        background_tasks (BackgroundTasks): FastAPI manager to execute async tasks.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        User: The newly created User database record.

    Raises:
        HTTPException: If the username or email is already registered (409 Conflict).
    """
    user_servive = UserService(db)

    exist_user = await user_servive.get_user_by_username(body.username)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=messages.USER_EMAIL_OR_NAME_ALREADY_EXISTS,
        )

    exist_email = await user_servive.get_user_by_email(body.email)
    if exist_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=messages.USER_EMAIL_OR_NAME_ALREADY_EXISTS,
        )

    hashed_password = hash_handler.get_password_hash(body.password)
    body.password = hashed_password
    new_user = await user_servive.create_user(body)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verifies a user's email address using a security token.

    Args:
        token (str): The email verification token sent to the user.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A success message indicating whether the user's email was confirmed
            or if it was already confirmed.

    Raises:
        HTTPException: If the token is invalid, expired, or the user cannot be found (400 Bad Request).
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=messages.UNVERIFIED_CREDENTIALS,
        )
    if user.confirmed:
        return {"message": messages.USER_ALREADY_CONFIRMED}
    await user_service.confirmed_email(email)
    return {"message": messages.USER_CONFIRMED}


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_201_CREATED)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Authenticates a user and generates OAuth2 access and refresh tokens.

    Verifies the username, password, and confirmation status of the user before
    generating tokens and saving the new refresh token to the database.

    Args:
        form_data (OAuth2PasswordRequestForm): Standard OAuth2 password form containing
            the username and password. Defaults to Depends().
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A dictionary containing the access token, refresh token, and token type.

    Raises:
        HTTPException: If credentials are invalid (401 Unauthorized) or
            if the email address has not been confirmed yet (401 Unauthorized).
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)

    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.USER_NOT_CONFIRMED,
        )

    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = refresh_token
    await db.commit()
    await db.refresh(user)
    await user_cache.invalidate_user(user.username)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh-token", response_model=TokenModel, status_code=status.HTTP_201_CREATED
)
async def refresh_token(
    request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
):
    """Validates a refresh token and generates a new pair of access and refresh tokens.

    Args:
        request (TokenRefreshRequest): Schema containing the raw refresh token.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A dictionary containing the new access token, refresh token, and token type.

    Raises:
        HTTPException: If the refresh token is invalid, expired, or revoked (401 Unauthorized).
    """
    user = await verify_refresh_token(request.refresh_token, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.INVALID_REFRESH_TOKEN,
        )

    new_access_token = await create_access_token(data={"sub": user.username})
    new_refresh_token = await create_refresh_token(data={"sub": user.username})

    user.refresh_token = new_refresh_token
    await db.commit()
    await db.refresh(user)
    await user_cache.invalidate_user(user.username)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/secret")
async def read_item(current_user: User = Depends(get_current_user)):
    """A protected endpoint for testing authentication status.

    Args:
        current_user (User): The authenticated user fetched from the access token.
            Defaults to Depends(get_current_user).

    Returns:
        dict: A success message and the username of the verified owner.
    """
    return {"message": "secret router", "owner": current_user.username}


@router.post("/request_email", status_code=status.HTTP_201_CREATED)
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Resends a verification email to a registered but unconfirmed user.

    Args:
        body (RequestEmail): Schema containing the user's registered email address.
        background_tasks (BackgroundTasks): FastAPI manager to execute async tasks.
        request (Request): The incoming HTTP request, used to construct the base URL.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A success message indicating whether the email was sent, or
            if the account was already verified.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": messages.USER_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": messages.EMAIL_SENT}


@router.post("/reset_password", status_code=status.HTTP_201_CREATED)
async def request_reset_password(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Initiates the password reset flow for a registered account.

    Looks up the account by email and, if it exists, schedules an email
    containing a short-lived reset link. To avoid leaking which emails are
    registered, the same generic response is returned whether or not the
    account exists.

    Args:
        body (PasswordResetRequest): Schema containing the account's email address.
        background_tasks (BackgroundTasks): FastAPI manager to execute async tasks.
        request (Request): The incoming HTTP request, used to construct the base URL.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A generic confirmation message.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user is not None:
        background_tasks.add_task(
            send_reset_password_email,
            user.email,
            user.username,
            request.base_url,
        )
    return {"message": messages.PASSWORD_RESET_EMAIL_SENT}


@router.post("/reset_password/{token}", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Completes the password reset flow using a valid reset token.

    Verifies the reset token, hashes the supplied new password, persists it,
    and invalidates any cached copy of the user so the change takes effect
    immediately.

    Args:
        token (str): The password reset token from the emailed link.
        body (PasswordResetConfirm): Schema containing the new password.
        db (AsyncSession): Asynchronous database session. Defaults to Dependency(get_db).

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If the token is invalid/expired (400) or the user no
            longer exists (400).
    """
    email = await get_email_from_reset_token(token)

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=messages.INVALID_RESET_TOKEN,
        )

    hashed_password = hash_handler.get_password_hash(body.new_password)
    await user_service.update_password(email, hashed_password)
    await user_cache.invalidate_user(user.username)

    return {"message": messages.PASSWORD_RESET_SUCCESS}
