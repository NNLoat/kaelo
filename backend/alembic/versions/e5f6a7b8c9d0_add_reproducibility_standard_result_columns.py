"""add reproducibility standard result columns

Revision ID: e5f6a7b8c9d0
Revises: f3a4b5c6d7e8
Create Date: 2026-10-18 12:10:00.000000

Adds the remaining six additive, nullable columns of the full Standard Result to
``reproducibility_scores`` (R7.1, R10.7). Revision ``d4e5f6a7b8c9`` already added
``standard_key`` and ``criteria``; this completes the model from
``scoring_rule.md`` v1.2:

- ``field_of_study`` — "medicine" / "computer_science" / "unknown"
- ``score_q`` — S_Q, the Q-group (0.30) sub-score
- ``score_d`` — S_D, the D + Q/D group (0.70) sub-score
- ``categories`` — seven per-display-category rows {category, score, points_lost}
- ``discrepancies`` — D criteria scored 0 by contradiction
- ``reference_versions`` — reference versions scored against (scoring_rule.md §8)

All columns are nullable with no server default, so existing rows need no
backfill.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reproducibility_scores",
        sa.Column("field_of_study", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("score_q", sa.Float(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("score_d", sa.Float(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("categories", sa.JSON(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("discrepancies", sa.JSON(), nullable=True),
    )
    op.add_column(
        "reproducibility_scores",
        sa.Column("reference_versions", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reproducibility_scores", "reference_versions")
    op.drop_column("reproducibility_scores", "discrepancies")
    op.drop_column("reproducibility_scores", "categories")
    op.drop_column("reproducibility_scores", "score_d")
    op.drop_column("reproducibility_scores", "score_q")
    op.drop_column("reproducibility_scores", "field_of_study")
