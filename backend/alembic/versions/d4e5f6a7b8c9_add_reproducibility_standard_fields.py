"""add reproducibility_scores.standard_key and criteria columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-15 09:00:00.000000

Adds two additive, nullable columns to ``reproducibility_scores`` (R7.1, R8.8,
R10): ``standard_key`` (the selected Reproducibility Standard key, e.g.
``ml_checklist`` / ``fair`` / ``baseline``) and ``criteria`` (a JSON column
holding the per-Criterion Standard Result). Both are nullable with no server
default, so existing rows need no backfill.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reproducibility_scores",
        sa.Column("standard_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("criteria", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reproducibility_scores", "criteria")
    op.drop_column("reproducibility_scores", "standard_key")
