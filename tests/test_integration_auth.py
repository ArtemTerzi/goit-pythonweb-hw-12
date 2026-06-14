"""Integration tests for the auth router (src/api/auth.py)."""

from unittest.mock import Mock

import pytest

from src.conf import messages
from src.services.auth import (
    create_email_token,
    create_refresh_token,
    create_reset_password_token,
)
from tests.conftest import test_user

new_user = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
}


# ----------------------------- signup -----------------------------
async def test_signup(client, monkeypatch):
    """send_email runs in a background task and hits an SMTP server -> mock it."""
    monkeypatch.setattr("src.api.auth.send_email", Mock())

    response = await client.post("/api/auth/signup", json=new_user)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == new_user["username"]
    assert data["email"] == new_user["email"]
    assert "hashed_password" not in data
    assert "password" not in data
    assert "avatar" in data


async def test_signup_duplicate_username(client, monkeypatch):
    monkeypatch.setattr("src.api.auth.send_email", Mock())

    response = await client.post(
        "/api/auth/signup",
        json={**new_user, "email": "another@gmail.com"},
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"] == messages.USER_EMAIL_OR_NAME_ALREADY_EXISTS


async def test_signup_duplicate_email(client, monkeypatch):
    monkeypatch.setattr("src.api.auth.send_email", Mock())

    response = await client.post(
        "/api/auth/signup",
        json={**new_user, "username": "another_name"},
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"] == messages.USER_EMAIL_OR_NAME_ALREADY_EXISTS


# ----------------------------- login ------------------------------
async def test_login_not_confirmed(client):
    """agent007 was created above but never confirmed."""
    response = await client.post(
        "/api/auth/login",
        data={"username": new_user["username"], "password": new_user["password"]},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == messages.USER_NOT_CONFIRMED


async def test_login_success(client):
    """The seeded user is confirmed."""
    response = await client.post(
        "/api/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    response = await client.post(
        "/api/auth/login",
        data={"username": test_user["username"], "password": "wrong"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == messages.INVALID_CREDENTIALS


async def test_login_wrong_username(client):
    response = await client.post(
        "/api/auth/login",
        data={"username": "no_such_user", "password": test_user["password"]},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == messages.INVALID_CREDENTIALS


async def test_login_validation_error(client):
    """Missing password -> OAuth2 form validation fails."""
    response = await client.post(
        "/api/auth/login", data={"username": test_user["username"]}
    )
    assert response.status_code == 422, response.text
    assert "detail" in response.json()


# ------------------------ confirmed_email -------------------------
async def test_confirmed_email_success(client):
    token = create_email_token({"sub": new_user["email"]})
    response = await client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    assert response.json()["message"] == messages.USER_CONFIRMED


async def test_confirmed_email_already_confirmed(client):
    token = create_email_token({"sub": test_user["email"]})
    response = await client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200, response.text
    assert response.json()["message"] == messages.USER_ALREADY_CONFIRMED


async def test_confirmed_email_invalid_token(client):
    response = await client.get("/api/auth/confirmed_email/not-a-valid-token")
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == messages.UNEXISTING_TOKEN


async def test_confirmed_email_user_not_found(client):
    """Valid token, but the email doesn't belong to any user."""
    token = create_email_token({"sub": "ghost@example.com"})
    response = await client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.UNVERIFIED_CREDENTIALS


# -------------------------- refresh-token -------------------------
async def test_refresh_token_success(client):
    login = await client.post(
        "/api/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh-token", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_refresh_token_malformed(client):
    """A non-JWT string fails to decode -> handled as a credentials error."""
    response = await client.post(
        "/api/auth/refresh-token", json={"refresh_token": "garbage-token"}
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == messages.UNVERIFIED_CREDENTIALS


async def test_refresh_token_unknown_user(client):
    """Valid refresh JWT, but no user in DB carries this refresh token."""
    bogus = await create_refresh_token(data={"sub": "ghost_user"})
    response = await client.post(
        "/api/auth/refresh-token", json={"refresh_token": bogus}
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == messages.INVALID_REFRESH_TOKEN


# ----------------------------- secret -----------------------------
async def test_secret_requires_auth(client):
    response = await client.get("/api/auth/secret")
    assert response.status_code == 401, response.text


async def test_secret_with_token(client, auth_headers):
    response = await client.get("/api/auth/secret", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["owner"] == test_user["username"]


# -------------------------- request_email -------------------------
async def test_request_email_already_confirmed(client):
    response = await client.post(
        "/api/auth/request_email", json={"email": test_user["email"]}
    )
    assert response.status_code == 201, response.text
    assert response.json()["message"] == messages.USER_ALREADY_CONFIRMED


async def test_request_email_sent(client, monkeypatch):
    monkeypatch.setattr("src.api.auth.send_email", Mock())
    """ Register a brand-new, unconfirmed user."""
    await client.post(
        "/api/auth/signup",
        json={
            "username": "pending_user",
            "email": "pending_user@example.com",
            "password": "password123",
        },
    )
    response = await client.post(
        "/api/auth/request_email", json={"email": "pending_user@example.com"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["message"] == messages.EMAIL_SENT


# ------------------------- password reset -------------------------
reset_user = {
    "username": "reset_me",
    "email": "reset_me@example.com",
    "password": "oldpassword",
}


async def test_reset_password_request_unknown_email(client, monkeypatch):
    """Unknown emails get the same generic response (no account enumeration)."""
    mock_send = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send)

    response = await client.post(
        "/api/auth/reset_password", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["message"] == messages.PASSWORD_RESET_EMAIL_SENT
    mock_send.assert_not_called()


async def test_reset_password_request_existing_email(client, monkeypatch):
    """Existing accounts trigger the reset email background task."""
    mock_send = Mock()
    monkeypatch.setattr("src.api.auth.send_email", Mock())
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send)

    # Register + confirm a dedicated user for the reset flow.
    await client.post("/api/auth/signup", json=reset_user)
    token = create_email_token({"sub": reset_user["email"]})
    await client.get(f"/api/auth/confirmed_email/{token}")

    response = await client.post(
        "/api/auth/reset_password", json={"email": reset_user["email"]}
    )
    assert response.status_code == 201, response.text
    assert response.json()["message"] == messages.PASSWORD_RESET_EMAIL_SENT
    mock_send.assert_called_once()


async def test_reset_password_invalid_token(client):
    response = await client.post(
        "/api/auth/reset_password/not-a-valid-token",
        json={"new_password": "brandnewpass"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.INVALID_RESET_TOKEN


async def test_reset_password_wrong_token_type(client):
    """An email-confirmation token must not be accepted as a reset token."""
    wrong_token = create_email_token({"sub": reset_user["email"]})
    response = await client.post(
        f"/api/auth/reset_password/{wrong_token}",
        json={"new_password": "brandnewpass"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.INVALID_RESET_TOKEN


async def test_reset_password_unknown_user(client):
    """Valid reset token, but no user with that email."""
    token = create_reset_password_token({"sub": "ghost@example.com"})
    response = await client.post(
        f"/api/auth/reset_password/{token}",
        json={"new_password": "brandnewpass"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.INVALID_RESET_TOKEN


async def test_reset_password_success_and_login(client):
    """A valid reset changes the password; old fails, new works."""
    token = create_reset_password_token({"sub": reset_user["email"]})
    new_password = "freshpassword123"

    response = await client.post(
        f"/api/auth/reset_password/{token}",
        json={"new_password": new_password},
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == messages.PASSWORD_RESET_SUCCESS

    # Old password no longer works.
    old_login = await client.post(
        "/api/auth/login",
        data={"username": reset_user["username"], "password": reset_user["password"]},
    )
    assert old_login.status_code == 401, old_login.text

    # New password works.
    new_login = await client.post(
        "/api/auth/login",
        data={"username": reset_user["username"], "password": new_password},
    )
    assert new_login.status_code == 201, new_login.text
    assert "access_token" in new_login.json()
