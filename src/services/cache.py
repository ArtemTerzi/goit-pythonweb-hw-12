"""Redis caching service module.

Provides a thin wrapper around an asynchronous Redis client used to cache
authenticated users so that ``get_current_user`` does not need to query the
database on every request.

The cached payload is a JSON serialization of the fields required to
reconstruct a detached :class:`~src.database.models.User` instance. This keeps
the authorization dependency fast while still returning an ORM-compatible
object to the route handlers.
"""

import json
from datetime import datetime
from typing import Optional

import redis.asyncio as redis

from src.conf.config import config
from src.database.models import User, UserRole


class UserCache:
    """Caches :class:`User` objects in Redis keyed by username.

    Attributes:
        client (redis.Redis): The asynchronous Redis client.
        ttl (int): Time-to-live, in seconds, applied to every cached user.
    """

    def __init__(self, client: redis.Redis, ttl: int = config.REDIS_CACHE_TTL):
        """Initializes the cache wrapper.

        Args:
            client (redis.Redis): An asynchronous Redis client instance.
            ttl (int): Expiration time in seconds for cached entries.
        """
        self.client = client
        self.ttl = ttl

    @staticmethod
    def _key(username: str) -> str:
        """Builds the Redis key for a given username.

        Args:
            username (str): The username to build a key for.

        Returns:
            str: The namespaced Redis key.
        """
        return f"user:{username}"

    @staticmethod
    def _serialize(user: User) -> str:
        """Serializes a User ORM object into a JSON string.

        Args:
            user (User): The user instance to serialize.

        Returns:
            str: JSON representation of the user's stored fields.
        """
        role = user.role
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "refresh_token": user.refresh_token,
            "confirmed": user.confirmed,
            "avatar": user.avatar,
            "role": role.value if isinstance(role, UserRole) else role,
            "created_at": (user.created_at.isoformat() if user.created_at else None),
            "updated_at": (user.updated_at.isoformat() if user.updated_at else None),
        }
        return json.dumps(data)

    @staticmethod
    def _deserialize(raw: str) -> User:
        """Reconstructs a detached User object from cached JSON.

        Args:
            raw (str): The JSON string previously produced by ``_serialize``.

        Returns:
            User: A detached (not session-bound) User instance.
        """
        data = json.loads(raw)
        user = User(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            hashed_password=data["hashed_password"],
            refresh_token=data["refresh_token"],
            confirmed=data["confirmed"],
            avatar=data["avatar"],
            role=UserRole(data["role"]) if data.get("role") else UserRole.USER,
        )
        if data.get("created_at"):
            user.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            user.updated_at = datetime.fromisoformat(data["updated_at"])
        return user

    async def get_user(self, username: str) -> Optional[User]:
        """Fetches a cached user by username.

        Any Redis-side error is swallowed and treated as a cache miss so that
        a Redis outage degrades gracefully to direct database access.

        Args:
            username (str): The username to look up.

        Returns:
            User | None: The cached User, or None on a miss/error.
        """
        try:
            raw = await self.client.get(self._key(username))
        except Exception:
            return None
        if raw is None:
            return None
        try:
            return self._deserialize(raw)
        except (ValueError, KeyError):
            return None

    async def set_user(self, user: User) -> None:
        """Stores a user in the cache with the configured TTL.

        Args:
            user (User): The user to cache.
        """
        try:
            await self.client.set(
                self._key(user.username), self._serialize(user), ex=self.ttl
            )
        except Exception:
            # Caching is best-effort; never break the request on a cache error.
            pass

    async def invalidate_user(self, username: str) -> None:
        """Removes a user from the cache.

        Should be called whenever a user's persisted state changes (e.g.
        password reset, avatar update, token refresh).

        Args:
            username (str): The username whose cache entry should be cleared.
        """
        try:
            await self.client.delete(self._key(username))
        except Exception:
            pass


redis_client: redis.Redis = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)
"""Module-level asynchronous Redis client shared across the application."""

user_cache = UserCache(redis_client)
"""Shared :class:`UserCache` instance used by the authentication layer."""
