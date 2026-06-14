import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, ContactUpdate
from conftest import test_user, test_contact


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    return User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password="hashed_password",
        confirmed=True,
    )


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()

    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=test_contact["id"],
            first_name=test_contact["first_name"],
            last_name=test_contact["last_name"],
            email=test_contact["email"],
            phone_number=test_contact["phone_number"],
            birthday=contact_birthday,
            description=test_contact["description"],
            user=user,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contacts = await contact_repository.get_contacts(
        skip=0, limit=10, first_name=None, last_name=None, email=None, user=user
    )

    # Assertions
    assert len(contacts) == 1
    assert contacts[0].first_name == "string"
    assert contacts[0].email == "user@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()

    existing_contact = Contact(
        id=1,
        first_name=test_contact["first_name"],
        last_name=test_contact["last_name"],
        email=test_contact["email"],
        phone_number=test_contact["phone_number"],
        birthday=contact_birthday,
        user=user,
    )
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contact = await contact_repository.get_contact_by_id(contact_id=1, user=user)

    # Assertions
    assert contact is not None
    assert contact.id == 1
    assert contact.first_name == "string"


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user):
    # Setup
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()
    contact_data = ContactModel(
        first_name="string",
        last_name="string",
        email="new_contact@example.com",
        phone_number="string",
        birthday=contact_birthday,
        description="string",
    )

    # Call method
    result = await contact_repository.create_contact(body=contact_data, user=user)

    # Assertions
    assert isinstance(result, Contact)
    assert result.first_name == "string"
    assert result.email == "new_contact@example.com"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user):
    # Setup
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()
    update_data = ContactUpdate(first_name="updated name")

    existing_contact = Contact(
        id=1,
        first_name="old name",
        last_name="string",
        email="user@example.com",
        phone_number="string",
        birthday=contact_birthday,
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.update_contact(
        contact_id=1, body=update_data, user=user
    )

    # Assertions
    assert result is not None
    assert result.first_name == "updated name"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_update_contact_not_found(contact_repository, mock_session, user):
    # Setup
    update_data = ContactUpdate(first_name="updated name")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.update_contact(
        contact_id=1, body=update_data, user=user
    )

    # Assertions
    assert result is None


@pytest.mark.asyncio
async def test_remove_contact(contact_repository, mock_session, user):
    # Setup
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()
    existing_contact = Contact(
        id=1,
        first_name="string",
        last_name="string",
        email="user@example.com",
        phone_number="string",
        birthday=contact_birthday,
        user=user,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.remove_contact(contact_id=1, user=user)

    # Assertions
    assert result is not None
    assert result.first_name == "string"
    mock_session.delete.assert_awaited_once_with(existing_contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_contact_not_found(contact_repository, mock_session, user):
    # Setup
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.remove_contact(contact_id=1, user=user)

    # Assertions
    assert result is None


@pytest.mark.asyncio
async def test_get_contact_by_email(contact_repository, mock_session, user):
    # Setup
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()
    existing_contact = Contact(
        id=1,
        first_name="string",
        last_name="string",
        email="user@example.com",
        phone_number="string",
        birthday=contact_birthday,
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.get_contact_by_email(
        email="user@example.com", user=user
    )

    # Assertions
    assert result is not None
    assert result.email == "user@example.com"


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_repository, mock_session, user):
    # Setup
    contact_birthday = datetime.strptime(test_contact["birthday"], "%Y-%m-%d").date()
    existing_contact = Contact(
        id=1,
        first_name="string",
        last_name="string",
        email="user@example.com",
        phone_number="string",
        birthday=contact_birthday,
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.get_upcoming_birthdays(user=user)

    # Assertions
    assert len(result) == 1
    assert result[0].email == "user@example.com"
