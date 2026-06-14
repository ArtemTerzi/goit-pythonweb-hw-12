"""Shared pytest fixtures for integration tests.

The whole point here: integration tests must NOT touch a real Postgres.
We swap the production DB for an in-memory SQLite engine and override the
`get_db` dependency so every router runs against it.
"""

import asyncio

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from src.database.models import Base, User, UserRole
from src.database.db import get_db
from src.services.auth import Hash, create_access_token
from src.services import cache as cache_module

engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@event.listens_for(engine.sync_engine, "connect")
def _register_sqlite_functions(dbapi_connection, _connection_record):
    def to_char(value, _fmt):
        if value is None:
            return None
        # SQLite stores DATE as 'YYYY-MM-DD' -> we only need 'MM-DD'.
        return str(value)[5:10]

    dbapi_connection.create_function("to_char", 2, to_char)


test_user = {
    "username": "string",
    "email": "user@example.com",
    "password": "1",
}


regular_user = {
    "username": "regular",
    "email": "regular@example.com",
    "password": "regularpass",
}


test_contact = {
    "id": 1,
    "first_name": "string",
    "last_name": "string",
    "email": "user@example.com",
    "phone_number": "+380501112233",
    "birthday": "2000-01-01",
    "description": "test contact",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            session.add(
                User(
                    username=test_user["username"],
                    email=test_user["email"],
                    hashed_password=Hash().get_password_hash(test_user["password"]),
                    confirmed=True,
                    avatar="https://example.com/avatar.png",
                    role=UserRole.ADMIN,
                )
            )
            session.add(
                User(
                    username=regular_user["username"],
                    email=regular_user["email"],
                    hashed_password=Hash().get_password_hash(
                        regular_user["password"]
                    ),
                    confirmed=True,
                    avatar="https://example.com/regular.png",
                    role=UserRole.USER,
                )
            )
            await session.commit()

    asyncio.run(init_models())


@pytest_asyncio.fixture(autouse=True)
async def fake_redis_cache():
    """Swap the production Redis client for an in-memory fake.

    This keeps the real ``UserCache`` serialization logic under test while
    removing any dependency on a running Redis server. The fake store is reset
    before each test so cached state never leaks between tests.
    """
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await fake.flushall()
    original = cache_module.user_cache.client
    cache_module.user_cache.client = fake
    try:
        yield fake
    finally:
        cache_module.user_cache.client = original
        await fake.aclose()


@pytest_asyncio.fixture()
async def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def get_token():
    return await create_access_token(data={"sub": test_user["username"]})


@pytest_asyncio.fixture()
async def auth_headers(get_token):
    return {"Authorization": f"Bearer {get_token}"}


@pytest_asyncio.fixture()
async def regular_token():
    return await create_access_token(data={"sub": regular_user["username"]})


@pytest_asyncio.fixture()
async def regular_auth_headers(regular_token):
    return {"Authorization": f"Bearer {regular_token}"}
