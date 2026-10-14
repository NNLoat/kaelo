"""add cancelled to jobstate enum

Revision ID: b1f2c3d4e5a6
Revises: a0e1828b52c6
Create Date: 2026-10-14 09:30:00.000000

Adds the ``cancelled`` value to the Postgres ``jobstate`` enum (R9). The job
state column is a real enum type, so a new value must be added with ALTER TYPE;
it cannot run inside a transaction block, hence the autocommit connection.
Downgrade is a no-op: Postgres cannot drop an enum value.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b1f2c3d4e5a6"
down_revision: Union[str, None] = "a0e1828b52c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run in a transaction block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE jobstate ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # Postgres cannot remove an enum value; no-op.
    pass
