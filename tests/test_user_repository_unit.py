import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas import UserCreate


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(id=1, username="testuser", email="testuser@example.com")
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_id(user_id=1)

    # Assertions
    assert user is not None
    assert user.id == 1
    assert user.username == "testuser"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_username_without_token(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(
        id=1, username="testuser", email="testuser@example.com", refresh_token=None
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_username(
        username="testuser", refresh_token=None
    )

    # Assertions
    assert user is not None
    assert user.username == "testuser"
    assert user.refresh_token is None


@pytest.mark.asyncio
async def test_get_user_by_username_with_token(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        refresh_token="token_abc",
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_username(
        username="testuser", refresh_token="token_abc"
    )

    # Assertions
    assert user is not None
    assert user.refresh_token == "token_abc"


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(id=1, username="testuser", email="testuser@example.com")
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    user = await user_repository.get_user_by_email(email="testuser@example.com")

    # Assertions
    assert user is not None
    assert user.email == "testuser@example.com"


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    # Setup
    body = UserCreate(
        username="newuser", email="newuser@example.com", password="secret_password"
    )

    # Call method
    result = await user_repository.create_user(
        body=body, avatar="http://gravatar.com/avatar"
    )

    # Assertions
    assert isinstance(result, User)
    assert result.username == "newuser"
    assert result.avatar == "http://gravatar.com/avatar"
    assert (
        result.hashed_password == "secret_password"
    )  # Метод записує пароль як є із схеми
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_token(user_repository, mock_session):
    # Setup
    fake_user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        refresh_token="old_token",
    )

    # Call method
    await user_repository.update_token(user=fake_user, token="new_token")

    # Assertions
    assert fake_user.refresh_token == "new_token"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(fake_user)


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(
        id=1, username="testuser", email="testuser@example.com", confirmed=False
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    await user_repository.confirmed_email(email="testuser@example.com")

    # Assertions
    assert fake_user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(
        id=1, username="testuser", email="testuser@example.com", avatar="old_avatar"
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await user_repository.update_avatar_url(
        email="testuser@example.com", url="http://new_avatar.com"
    )

    # Assertions
    assert result.avatar == "http://new_avatar.com"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(fake_user)


@pytest.mark.asyncio
async def test_update_password(user_repository, mock_session):
    # Setup mock
    mock_result = MagicMock()
    fake_user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        hashed_password="old_hash",
        refresh_token="some_token",
    )
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await user_repository.update_password(
        email="testuser@example.com", hashed_password="new_hash"
    )

    # Assertions
    assert result.hashed_password == "new_hash"
    # Refresh token is cleared so old sessions are invalidated.
    assert result.refresh_token is None
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(fake_user)
