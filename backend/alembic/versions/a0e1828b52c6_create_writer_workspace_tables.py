"""create writer workspace tables

Revision ID: a0e1828b52c6
Revises: 8f3c1a9b2d47
Create Date: 2026-10-14 07:01:54.020382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a0e1828b52c6'
down_revision: Union[str, None] = '8f3c1a9b2d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # paper_claims first — the two child tables FK into it.
    op.create_table(
        'paper_claims',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('paper_ref_normalized', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column('paper_ref_original', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        # one claim per Writer per paper (R5.3, R9.3)
        sa.UniqueConstraint('owner_id', 'paper_ref_normalized'),
    )
    op.create_index(op.f('ix_paper_claims_owner_id'), 'paper_claims', ['owner_id'], unique=False)
    op.create_index(op.f('ix_paper_claims_paper_ref_normalized'), 'paper_claims', ['paper_ref_normalized'], unique=False)

    op.create_table(
        'writer_manuscripts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('claim_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        # ON DELETE CASCADE: deleting a claim removes its manuscript (R9.6).
        # autogenerate omits ondelete — hand-added.
        sa.ForeignKeyConstraint(['claim_id'], ['paper_claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # unique: at most one manuscript per claim (R9.4)
    op.create_index(op.f('ix_writer_manuscripts_claim_id'), 'writer_manuscripts', ['claim_id'], unique=True)

    op.create_table(
        'writer_source_files',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('claim_id', sa.Uuid(), nullable=False),
        sa.Column('path', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
        sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        # ON DELETE CASCADE: deleting a claim removes its source files (R9.6).
        # autogenerate omits ondelete — hand-added.
        sa.ForeignKeyConstraint(['claim_id'], ['paper_claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # one row per file within a claim (R9.5)
        sa.UniqueConstraint('claim_id', 'path'),
    )
    op.create_index(op.f('ix_writer_source_files_claim_id'), 'writer_source_files', ['claim_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_writer_source_files_claim_id'), table_name='writer_source_files')
    op.drop_table('writer_source_files')
    op.drop_index(op.f('ix_writer_manuscripts_claim_id'), table_name='writer_manuscripts')
    op.drop_table('writer_manuscripts')
    op.drop_index(op.f('ix_paper_claims_paper_ref_normalized'), table_name='paper_claims')
    op.drop_index(op.f('ix_paper_claims_owner_id'), table_name='paper_claims')
    op.drop_table('paper_claims')
