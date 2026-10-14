"""create generation tables

Revision ID: 8f3c1a9b2d47
Revises: 4027d4a36d03
Create Date: 2026-10-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8f3c1a9b2d47'
down_revision: Union[str, None] = '4027d4a36d03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # generations first — generation_jobs.generation_id FKs into it.
    op.create_table(
        'generations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('paper_ref', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('case', sa.Enum('generate', 'align', 'writer', name='case'), nullable=False),
        sa.Column('files', sa.JSON(), nullable=False),
        sa.Column('code_quality_score', sa.Float(), nullable=False),
        sa.Column('code_quality_rationale', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('disclaimer', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('is_latest', sa.Boolean(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generations_owner_id'), 'generations', ['owner_id'], unique=False)
    op.create_index(op.f('ix_generations_paper_ref'), 'generations', ['paper_ref'], unique=False)
    op.create_index(op.f('ix_generations_is_latest'), 'generations', ['is_latest'], unique=False)

    op.create_table(
        'generation_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('paper_ref', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        # Reuses the 'case' enum created by the generations table above.
        sa.Column('case', sa.Enum('generate', 'align', 'writer', name='case', create_type=False), nullable=False),
        sa.Column('state', sa.Enum('pending', 'running', 'succeeded', 'failed', 'refused', name='jobstate'), nullable=False),
        sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('generation_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column('updated_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['generation_id'], ['generations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generation_jobs_owner_id'), 'generation_jobs', ['owner_id'], unique=False)
    op.create_index(op.f('ix_generation_jobs_paper_ref'), 'generation_jobs', ['paper_ref'], unique=False)
    op.create_index(op.f('ix_generation_jobs_state'), 'generation_jobs', ['state'], unique=False)

    # Partial unique indexes — autogenerate omits WHERE clauses, so hand-added.
    # At most one in-flight job per (owner, paper, case) (R4.2, R8.4).
    op.create_index(
        'uq_generation_jobs_inflight',
        'generation_jobs',
        ['owner_id', 'paper_ref', 'case'],
        unique=True,
        postgresql_where=sa.text("state IN ('pending', 'running')"),
    )
    # At most one latest Generation per (owner, paper, case) (R5.6).
    op.create_index(
        'uq_generations_latest',
        'generations',
        ['owner_id', 'paper_ref', 'case'],
        unique=True,
        postgresql_where=sa.text('is_latest'),
    )


def downgrade() -> None:
    op.drop_index('uq_generations_latest', table_name='generations')
    op.drop_index('uq_generation_jobs_inflight', table_name='generation_jobs')
    op.drop_index(op.f('ix_generation_jobs_state'), table_name='generation_jobs')
    op.drop_index(op.f('ix_generation_jobs_paper_ref'), table_name='generation_jobs')
    op.drop_index(op.f('ix_generation_jobs_owner_id'), table_name='generation_jobs')
    op.drop_table('generation_jobs')
    op.drop_index(op.f('ix_generations_is_latest'), table_name='generations')
    op.drop_index(op.f('ix_generations_paper_ref'), table_name='generations')
    op.drop_index(op.f('ix_generations_owner_id'), table_name='generations')
    op.drop_table('generations')
    # Drop the enum types so a down/up cycle is repeatable (migration test).
    sa.Enum(name='jobstate').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='case').drop(op.get_bind(), checkfirst=True)
