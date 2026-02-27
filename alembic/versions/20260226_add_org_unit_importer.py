"""add org_unit table for importer

Revision ID: 20260226_add_org_unit_importer
Revises: 20260225_add_school_recruiting_tables
Create Date: 2026-02-26 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260226_add_org_unit_importer'
down_revision = '20260225_add_school_recruiting_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'org_unit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('echelon', sa.String(), nullable=True),
        sa.Column('rsid', sa.String(), nullable=False, unique=True),
        sa.Column('parent_rsid', sa.String(), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('org_unit.id'), nullable=True),
        sa.Column('uic', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('record_status', sa.String(), nullable=True, server_default='active')
    )
    op.create_index('ix_org_unit_rsid', 'org_unit', ['rsid'])
    op.create_index('ix_org_unit_parent_rsid', 'org_unit', ['parent_rsid'])
    op.create_index('ix_org_unit_echelon', 'org_unit', ['echelon'])


def downgrade():
    op.drop_index('ix_org_unit_echelon', table_name='org_unit')
    op.drop_index('ix_org_unit_parent_rsid', table_name='org_unit')
    op.drop_index('ix_org_unit_rsid', table_name='org_unit')
    op.drop_table('org_unit')
