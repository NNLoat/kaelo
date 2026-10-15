"""add review to case enum

Revision ID: f3a4b5c6d7e8
Revises: d4e5f6a7b8c9
Create Date: 2026-10-15 11:00:00.000000

Adds the ``review`` value to the Postgres ``case`` enum (R12.2). The case column
is a real enum type, so a new value must be added with ALTER TYPE; it cannot run
inside a transaction block, hence the autocommit connection. Downgrade is a
no-op: Postgres cannot drop an enum value.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run in a transaction block.
    # "case" is quoted because it is a SQL reserved keyword.
    with op.get_context().autocommit_block():
        op.execute('ALTER TYPE "case" ADD VALUE IF NOT EXISTS \'review\'')


def downgrade() -> None:
    # Postgres cannot remove an enum value; no-op.
    pass
