"""add created_at/updated_at to funnel_stages

Revision ID: 0004_fix_loemetric_and_funnelstage_timestamps
Revises: 0003_timekeeping_add_columns
Create Date: 2026-02-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_fix_loemetric_and_funnelstage_timestamps'
down_revision = '0003_timekeeping_add_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at and updated_at to funnel_stages; use batch_alter_table for SQLite
    with op.batch_alter_table('funnel_stages') as batch:
        batch.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))


def downgrade():
    op.drop_column('funnel_stages', 'updated_at')
    op.drop_column('funnel_stages', 'created_at')
