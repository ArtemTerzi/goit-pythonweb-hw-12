"""Integration tests for the contacts router (src/api/contacts.py)."""

from datetime import date

import pytest

contact_payload = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+380501112233",
    "birthday": str(date.today()),
    "description": "Best friend",
}


# --------------------------- auth guard ---------------------------
async def test_contacts_require_auth(client):
    response = await client.get("/api/contacts/")
    assert response.status_code == 401, response.text


# ----------------------------- create -----------------------------
async def test_create_contact(client, auth_headers):
    response = await client.post(
        "/api/contacts/", json=contact_payload, headers=auth_headers
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == contact_payload["email"]
    assert data["first_name"] == contact_payload["first_name"]
    assert "id" in data


async def test_create_contact_duplicate_email(client, auth_headers):
    response = await client.post(
        "/api/contacts/", json=contact_payload, headers=auth_headers
    )
    assert response.status_code == 409, response.text


async def test_create_contact_validation_error(client, auth_headers):
    bad = {**contact_payload, "first_name": "Jo"}  # min_length is 3
    response = await client.post("/api/contacts/", json=bad, headers=auth_headers)
    assert response.status_code == 422, response.text


# ------------------------------ read ------------------------------
async def test_read_contacts(client, auth_headers):
    response = await client.get("/api/contacts/", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_read_contacts_with_filter(client, auth_headers):
    response = await client.get("/api/contacts/?first_name=John", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert all("john" in c["first_name"].lower() for c in data)


async def test_read_contact_by_id(client, auth_headers):
    created = await client.post(
        "/api/contacts/",
        json={**contact_payload, "email": "byid@example.com"},
        headers=auth_headers,
    )
    contact_id = created.json()["id"]

    response = await client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == contact_id


async def test_read_contact_not_found(client, auth_headers):
    response = await client.get("/api/contacts/99999", headers=auth_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Contact not found"


# --------------------------- birthdays ----------------------------
async def test_upcoming_birthdays(client, auth_headers):
    response = await client.get("/api/contacts/birthdays", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    # The first contact was created with today's birthday.
    assert any(c["birthday"] == str(date.today()) for c in data)


# ----------------------------- update -----------------------------
async def test_update_contact(client, auth_headers):
    created = await client.post(
        "/api/contacts/",
        json={**contact_payload, "email": "update@example.com"},
        headers=auth_headers,
    )
    contact_id = created.json()["id"]

    # PATCH a non-email field (email omitted -> no duplicate-email check).
    response = await client.patch(
        f"/api/contacts/{contact_id}",
        json={"first_name": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["first_name"] == "Updated"


async def test_update_contact_not_found(client, auth_headers):
    response = await client.patch(
        "/api/contacts/99999",
        json={"first_name": "Nobody"},
        headers=auth_headers,
    )
    assert response.status_code == 404, response.text


# ----------------------------- delete -----------------------------
async def test_delete_contact(client, auth_headers):
    created = await client.post(
        "/api/contacts/",
        json={**contact_payload, "email": "delete@example.com"},
        headers=auth_headers,
    )
    contact_id = created.json()["id"]

    response = await client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == contact_id

    # Now it's gone.
    follow_up = await client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert follow_up.status_code == 404


async def test_delete_contact_not_found(client, auth_headers):
    response = await client.delete("/api/contacts/99999", headers=auth_headers)
    assert response.status_code == 404, response.text
