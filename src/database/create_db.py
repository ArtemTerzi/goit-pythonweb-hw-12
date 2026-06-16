"""Utility for ensuring the target PostgreSQL database exists.

PostgreSQL cannot connect to a database that has not been created yet, so the
very first ``alembic upgrade`` (or app start) against a fresh server fails with
``InvalidCatalogNameError``. This module connects to the server's maintenance
``postgres`` database and issues ``CREATE DATABASE`` for the target database if
it is missing, so startup is self-healing.

The connection parameters are derived from the already-resolved ``DB_URL`` in
the application settings, so this works both for component-assembled URLs
(local / docker-compose) and for an explicit URL. Any failure to reach the
maintenance database is treated as non-fatal (e.g. on managed providers where
the database already exists and direct creation is not permitted).
"""

import asyncio

import asyncpg
from sqlalchemy.engine import make_url

from src.conf.config import config


async def create_database_if_not_exists() -> None:
    """Creates the configured database if it does not already exist.

    Connects to the ``postgres`` maintenance database on the same host/port
    using the same credentials as ``DB_URL``, checks ``pg_database`` for the
    target database name, and creates it when absent. Connection errors are
    swallowed so a managed/remote database (which already exists) never blocks
    startup.
    """
    url = make_url(config.DB_URL)
    db_name = url.database

    if not db_name:
        return

    try:
        conn = await asyncpg.connect(
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port or 5432,
            database="postgres",
        )
    except Exception as err:
        print(f"Skipping database auto-create (maintenance DB unreachable): {err}")
        return

    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if exists:
            return
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f'Database "{db_name}" created.')
    finally:
        await conn.close()


def main() -> None:
    """Synchronous entry point so the module can be run as a script."""
    asyncio.run(create_database_if_not_exists())


if __name__ == "__main__":
    main()
