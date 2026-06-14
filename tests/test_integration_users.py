"""Integration tests for the users router (src/api/users.py)."""

import io
from unittest.mock import MagicMock, patch

import pytest

from src.api.users import limiter as users_limiter
from tests.conftest import test_user, regular_user


@pytest.fixture(autouse=True)
def disable_rate_limit():
    # /users/me is decorated with @limiter.limit("5/minute"); turn it off so
    # repeated test runs don't trip the limiter.
    users_limiter.enabled = False
    yield
    users_limiter.enabled = True


async def test_me_requires_auth(client):
    response = await client.get("/api/users/me")
    assert response.status_code == 401, response.text


async def test_me(client, auth_headers):
    response = await client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]


async def test_update_avatar(client, auth_headers):
    """An admin user (seeded test_user) is allowed to change their avatar."""
    fake_url = "https://res.cloudinary.com/demo/image/upload/avatar.png"

    mock_service = MagicMock()
    mock_service.upload_file.return_value = fake_url

    with patch("src.api.users.UploadFileService", return_value=mock_service):
        file = {"file": ("avatar.png", io.BytesIO(b"fake-image-bytes"), "image/png")}
        response = await client.patch(
            "/api/users/avatar", headers=auth_headers, files=file
        )

    assert response.status_code == 200, response.text
    assert response.json()["avatar"] == fake_url


async def test_update_avatar_forbidden_for_regular_user(
    client, regular_auth_headers
):
    """A regular (non-admin) user must not be able to change the avatar."""
    mock_service = MagicMock()
    mock_service.upload_file.return_value = "https://example.com/x.png"

    with patch("src.api.users.UploadFileService", return_value=mock_service):
        file = {"file": ("avatar.png", io.BytesIO(b"bytes"), "image/png")}
        response = await client.patch(
            "/api/users/avatar", headers=regular_auth_headers, files=file
        )

    assert response.status_code == 403, response.text


async def test_update_avatar_requires_auth(client):
    file = {"file": ("avatar.png", io.BytesIO(b"x"), "image/png")}
    response = await client.patch("/api/users/avatar", files=file)
    assert response.status_code == 401, response.text
