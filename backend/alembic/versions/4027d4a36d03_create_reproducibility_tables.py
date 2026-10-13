"""create reproducibility tables

Revision ID: 4027d4a36d03
Revises: 2b1ee4974c08
Create Date: 2026-10-13 11:53:20.597986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '4027d4a36d03'
down_revision: Union[str, None] = '2b1ee4974c08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('experiment_setups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('paper_id', sa.Integer(), nullable=False),
    sa.Column('hyperparameters', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('datasets', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('environment', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
    sa.Column('updated_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiment_setups_paper_id'), 'experiment_setups', ['paper_id'], unique=True)
    op.create_table('reproducibility_scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('paper_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    # Reuses the existing 'scorestatus' enum (created by the papers migration).
    sa.Column('status', sa.Enum('pending', 'ready', 'unavailable', name='scorestatus', create_type=False), nullable=False),
    sa.Column('code_quality_score', sa.Float(), nullable=True),
    sa.Column('repo_exists', sa.Boolean(), nullable=True),
    sa.Column('repo_inspectable', sa.Boolean(), nullable=True),
    sa.Column('setup_completeness', sa.Float(), nullable=True),
    sa.Column('explanation', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
    sa.Column('updated_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
    sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reproducibility_scores_paper_id'), 'reproducibility_scores', ['paper_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_reproducibility_scores_paper_id'), table_name='reproducibility_scores')
    op.drop_table('reproducibility_scores')
    op.drop_index(op.f('ix_experiment_setups_paper_id'), table_name='experiment_setups')
    op.drop_table('experiment_setups')
