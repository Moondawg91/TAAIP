"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-02-15 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # enums
    market_enum = sa.Enum('MK', 'MW', 'MO', 'SU', 'UNK', name='marketcategory')
    userrole_enum = sa.Enum('USAREC','BRIGADE_420T','BATTALION_420T','FUSION','BRIGADE_VIEW','BATTALION_VIEW','COMPANY_CMD','STATION_VIEW','SYSADMIN', name='userrole')
    market_enum.create(op.get_bind(), checkfirst=True)
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # commands
    op.create_table(
        'commands',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('command', sa.String(), nullable=False, unique=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # brigades
    op.create_table(
        'brigades',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brigade_prefix', sa.String(length=1), nullable=False),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('command_id', sa.Integer(), sa.ForeignKey('commands.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('brigade_prefix', 'command_id', name='uq_brigade_cmd')
    )

    # battalions
    op.create_table(
        'battalions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('battalion_prefix', sa.String(length=2), nullable=False),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('brigade_id', sa.Integer(), sa.ForeignKey('brigades.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('battalion_prefix', 'brigade_id', name='uq_battalion_bde')
    )

    # companies
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_prefix', sa.String(length=3), nullable=False),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('battalion_id', sa.Integer(), sa.ForeignKey('battalions.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('company_prefix', 'battalion_id', name='uq_company_bn')
    )

    # stations
    op.create_table(
        'stations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('rsid', sa.String(length=4), nullable=False, unique=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # station_zip_coverage
    op.create_table(
        'station_zip_coverage',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('station_rsid', sa.String(length=4), sa.ForeignKey('stations.rsid'), nullable=False),
        sa.Column('zip_code', sa.String(length=5), nullable=False),
        sa.Column('market_category', market_enum, nullable=False, server_default='UNK'),
        sa.Column('source_file', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('station_rsid', 'zip_code', name='uq_station_zip')
    )

    # market_category_weights
    op.create_table(
        'market_category_weights',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category', market_enum, nullable=False, unique=True),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('role', userrole_enum, nullable=False),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # ingest tables
    op.create_table(
        'transform_recipes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'ingested_files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'ingest_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('file_id', sa.Integer(), sa.ForeignKey('ingested_files.id')),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('transform_recipes.id'), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('report', sa.JSON(), nullable=True),
        sa.Column('run_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('ingest_runs')
    op.drop_table('ingested_files')
    op.drop_table('transform_recipes')
    op.drop_table('users')
    op.drop_table('market_category_weights')
    op.drop_table('station_zip_coverage')
    op.drop_table('stations')
    op.drop_table('companies')
    op.drop_table('battalions')
    op.drop_table('brigades')
    op.drop_table('commands')

    # drop enums
    market_enum = sa.Enum(name='marketcategory')
    userrole_enum = sa.Enum(name='userrole')
    market_enum.drop(op.get_bind(), checkfirst=True)
    userrole_enum.drop(op.get_bind(), checkfirst=True)
