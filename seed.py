"""Seed script: create pre-confirmed users for local development.

Run it AFTER the database tables exist (i.e. after applying migrations):

    poetry run alembic upgrade head
    poetry run python seed.py

It inserts an administrator and a regular user, both already ``confirmed``, so
you can log in immediately without going through registration and email
confirmation. Users are matched by email, so existing ones are skipped — the
script is safe to run repeatedly.

Default credentials (intended for LOCAL development only — change them before
using anywhere real):

    admin / admin12345   (role: admin)
    user / user12345    (role: user)
"""

import asyncio

from sqlalchemy import select

from src.database.db import sessionmanager
from src.database.models import User, UserRole
from src.services.auth import Hash

hash_handler = Hash()

SEED_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin12345",
        "role": UserRole.ADMIN,
    },
    {
        "username": "user",
        "email": "user@example.com",
        "password": "user12345",
        "role": UserRole.USER,
    },
]


async def seed_users() -> None:
    """Inserts the seed users, skipping any that already exist (by email)."""
    async with sessionmanager.session() as session:
        created = 0
        for data in SEED_USERS:
            result = await session.execute(
                select(User).where(User.email == data["email"])
            )
            if result.scalar_one_or_none() is not None:
                print(f"• {data['email']} already exists — skipping")
                continue

            user = User(
                username=data["username"],
                email=data["email"],
                hashed_password=hash_handler.get_password_hash(data["password"]),
                confirmed=True,
                role=data["role"],
                avatar=None,
            )
            session.add(user)
            created += 1
            print(
                f"✓ created {data['role'].value}: "
                f"{data['email']} / {data['password']}"
            )

        await session.commit()
        print(f"\nDone. {created} user(s) created.")


def main() -> None:
    """Synchronous entry point so the module can be run as a script."""
    asyncio.run(seed_users())


if __name__ == "__main__":
    main()
