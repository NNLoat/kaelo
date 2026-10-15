"""add papers.domain column

Revision ID: c3d4e5f6a7b8
Revises: b1f2c3d4e5a6
Create Date: 2026-10-14 10:15:00.000000

Introduces ``papers.domain`` (R9.4): the field domain captured at ingestion that
selects the Reproducibility Standard. ``paperdomain`` is a NEW Postgres enum type,
so we create it explicitly on upgrade and drop it on downgrade (mirroring how the
papers migration manages ``scorestatus``). The column is NOT NULL with a
server_default of ``'unknown'`` so existing rows backfill to ``unknown``.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b1f2c3d4e5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


paperdomain = sa.Enum("computer_science", "medicine", "unknown", name="paperdomain")


def upgrade() -> None:
    bind = op.get_bind()
    # Create the new enum type up front; the column add below reuses it.
    paperdomain.create(bind, checkfirst=True)
    op.add_column(
        "papers",
        sa.Column(
            "domain",
            sa.Enum(
                "computer_science",
                "medicine",
                "unknown",
                name="paperdomain",
                create_type=False,
            ),
            # NOT NULL + server_default backfills existing rows to 'unknown' (R9.4).
            nullable=False,
            server_default="unknown",
        ),
    )


def downgrade() -> None:
    op.drop_column("papers", "domain")
    # Postgres keeps the enum type after the column is dropped; remove it so a
    # subsequent upgrade can recreate it (the migration-safety test cycles both).
    paperdomain.drop(op.get_bind(), checkfirst=True)
