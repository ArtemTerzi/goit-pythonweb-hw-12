"""Unit tests for the Redis-backed user cache (src/services/cache.py)."""

from datetime import datetime

import fakeredis.aioredis
import pytest

from src.database.models import User, UserRole
from src.services.cache import UserCache


@pytest.fixture
async def cache():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await client.flushall()
    yield UserCache(client, ttl=60)
    await client.aclose()


def _make_user() -> User:
    user = User(
        id=42,
        username="cached_user",
        email="cached@example.com",
        hashed_password="hash",
        refresh_token="rt",
        confirmed=True,
        avatar="https://example.com/a.png",
        role=UserRole.ADMIN,
    )
    user.created_at = datetime(2024, 1, 1, 12, 0, 0)
    user.updated_at = datetime(2024, 1, 2, 12, 0, 0)
    return user


@pytest.mark.asyncio
async def test_set_and_get_roundtrip(cache):
    user = _make_user()
    await cache.set_user(user)

    cached = await cache.get_user("cached_user")
    assert cached is not None
    assert cached.id == 42
    assert cached.username == "cached_user"
    assert cached.email == "cached@example.com"
    assert cached.hashed_password == "hash"
    assert cached.refresh_token == "rt"
    assert cached.confirmed is True
    assert cached.avatar == "https://example.com/a.png"
    assert cached.role == UserRole.ADMIN
    assert cached.created_at == datetime(2024, 1, 1, 12, 0, 0)
    assert cached.updated_at == datetime(2024, 1, 2, 12, 0, 0)


@pytest.mark.asyncio
async def test_get_miss_returns_none(cache):
    assert await cache.get_user("does_not_exist") is None


@pytest.mark.asyncio
async def test_invalidate_user(cache):
    user = _make_user()
    await cache.set_user(user)
    assert await cache.get_user("cached_user") is not None

    await cache.invalidate_user("cached_user")
    assert await cache.get_user("cached_user") is None


@pytest.mark.asyncio
async def test_corrupt_payload_is_a_miss(cache):
    # A non-JSON value under a valid key must be treated as a cache miss.
    await cache.client.set(UserCache._key("cached_user"), "not-json")
    assert await cache.get_user("cached_user") is None


@pytest.mark.asyncio
async def test_default_role_when_missing(cache):
    # Older cached payloads without a role should default to USER.
    await cache.client.set(
        UserCache._key("legacy"),
        '{"id":1,"username":"legacy","email":"l@e.com",'
        '"hashed_password":"h","refresh_token":null,"confirmed":true,'
        '"avatar":"a","role":null,"created_at":null,"updated_at":null}',
    )
    cached = await cache.get_user("legacy")
    assert cached is not None
    assert cached.role == UserRole.USER
