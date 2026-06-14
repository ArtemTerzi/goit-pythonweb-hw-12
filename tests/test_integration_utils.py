"""Integration tests for the utils router (src/api/utils.py)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from main import app
from src.conf import messages
from src.database.db import get_db


async def test_healthchecker(client):
    response = await client.get("/api/healthchecker")
    assert response.status_code == 200, response.text
    assert response.json()["message"] == messages.SUCCESSFUL_HEALTHCHECK


async def test_healthchecker_misconfigured_db(client):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session = AsyncMock()
    session.execute.return_value = result

    async def override():
        yield session

    app.dependency_overrides[get_db] = override
    try:
        response = await client.get("/api/healthchecker")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500, response.text
    assert response.json()["detail"] == messages.FAILED_CONNECT_TO_DB


async def test_healthchecker_db_error(client):
    session = AsyncMock()
    session.execute.side_effect = Exception("boom")

    async def override():
        yield session

    app.dependency_overrides[get_db] = override
    try:
        response = await client.get("/api/healthchecker")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500, response.text
    assert response.json()["detail"] == messages.FAILED_CONNECT_TO_DB
