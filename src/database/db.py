"""Database session management module.

Provides utility classes and dependency functions for creating asynchronous
database engines, session makers, and managing session lifecycles.
"""

import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import config
from src.conf import messages


class DatabaseSessionManager:
    """Manages asynchronous database engines and session makers.

    Responsible for initializing the connection engine, creating active
    asynchronous database sessions, and handling context management
    including automatic rollbacks and session closing.
    """

    def __init__(self, url: str):
        """Initializes the DatabaseSessionManager with a connection string.

        Args:
            url (str): The database connection URL (e.g. postgresql+asyncpg://...).
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """An async context manager that yields a new database session.

        Handles transactions gracefully by issuing a rollback on SQLAlchemyError
        and ensuring the session is closed under all circumstances upon exit.

        Yields:
            AsyncSession: A newly instantiated asynchronous database session.

        Raises:
            Exception: If the session maker has not been properly initialized.
            SQLAlchemyError: Propagates any database errors encountered during execution.
        """
        if self._session_maker is None:
            raise Exception(messages.DB_SESSION_IS_NOT_INIT)
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(config.DB_URL)


async def get_db():
    """FastAPI dependency to retrieve an asynchronous database session.

    Yields:
        AsyncSession: An active database session managed via the context manager.
    """
    async with sessionmanager.session() as session:
        yield session
