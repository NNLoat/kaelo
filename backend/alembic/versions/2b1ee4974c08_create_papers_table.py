"""create papers table

Revision ID: 2b1ee4974c08
Revises: e2c54f4d46fe
Create Date: 2026-10-13 09:47:49.939834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2b1ee4974c08'
down_revision: Union[str, None] = 'e2c54f4d46fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('papers',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
    sa.Column('authors', sa.JSON(), nullable=True),
    sa.Column('abstract', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('published_date', sa.Date(), nullable=True),
    sa.Column('doi', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('arxiv_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('sources', sa.JSON(), nullable=True),
    sa.Column('source_links', sa.JSON(), nullable=True),
    sa.Column('repo_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('relevance_score', sa.Float(), nullable=True),
    sa.Column('relevance_status', sa.Enum('pending', 'ready', 'unavailable', name='scorestatus'), nullable=False),
    sa.Column('relevance_blurb', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('reproducibility_score', sa.Float(), nullable=True),
    sa.Column('reproducibility_status', sa.Enum('pending', 'ready', 'unavailable', name='scorestatus'), nullable=False),
    sa.Column('final_score', sa.Float(), nullable=True),
    sa.Column('final_status', sa.Enum('pending', 'ready', 'unavailable', name='scorestatus'), nullable=False),
    sa.Column('experiment_setup', sa.JSON(), nullable=True),
    sa.Column('created_at', sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_papers_arxiv_id'), 'papers', ['arxiv_id'], unique=False)
    op.create_index(op.f('ix_papers_doi'), 'papers', ['doi'], unique=False)
    op.create_index(op.f('ix_papers_title'), 'papers', ['title'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_papers_title'), table_name='papers')
    op.drop_index(op.f('ix_papers_doi'), table_name='papers')
    op.drop_index(op.f('ix_papers_arxiv_id'), table_name='papers')
    op.drop_table('papers')
    # Postgres keeps the enum type after the table is dropped; remove it so a
    # subsequent upgrade can recreate it (the migration-safety test cycles both).
    sa.Enum(name='scorestatus').drop(op.get_bind(), checkfirst=True)
