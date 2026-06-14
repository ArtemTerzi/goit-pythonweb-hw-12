"""Add role column to users

Revision ID: a1b2c3d4e5f6
Revises: 730e35c7520b
Create Date: 2026-06-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "730e35c7520b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Native PostgreSQL ENUM type backing the UserRole enum.
user_role_enum = sa.Enum("USER", "ADMIN", name="userrole")


def upgrade() -> None:
    """Upgrade schema: add the ``role`` column to ``users``."""
    bind = op.get_bind()
    # Create the enum type explicitly so the ADD COLUMN below can reference it.
    user_role_enum.create(bind, checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="USER",
        ),
    )
    # Drop the server-side default now that existing rows are backfilled;
    # the application layer supplies the default for new rows.
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    """Downgrade schema: drop the ``role`` column and its enum type."""
    op.drop_column("users", "role")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
