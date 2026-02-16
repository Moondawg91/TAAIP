"""timekeeping columns

Revision ID: 0003_timekeeping_add_columns
Revises: 0002_phase2_domain
Create Date: 2026-02-15 11:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_timekeeping_add_columns'
down_revision = '0002_phase2_domain'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table to support SQLite (recreates table with new columns)
    with op.batch_alter_table('event_metrics') as batch:
        batch.add_column(sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('marketing_activities') as batch:
        batch.add_column(sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('funnel_transitions') as batch:
        batch.add_column(sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('burden_inputs') as batch:
        batch.add_column(sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('burden_snapshots') as batch:
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('loe_metrics') as batch:
        batch.add_column(sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('decisions') as batch:
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    with op.batch_alter_table('audit_logs') as batch:
        batch.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade():
    op.drop_column('audit_logs', 'updated_at')
    op.drop_column('decisions', 'updated_at')
    op.drop_column('loe_metrics', 'updated_at')
    op.drop_column('loe_metrics', 'created_at')
    op.drop_column('loe_metrics', 'ingested_at')
    op.drop_column('loe_metrics', 'reported_at')
    op.drop_column('burden_snapshots', 'updated_at')
    op.drop_column('burden_inputs', 'updated_at')
    op.drop_column('burden_inputs', 'ingested_at')
    op.drop_column('burden_inputs', 'reported_at')
    op.drop_column('funnel_transitions', 'updated_at')
    op.drop_column('funnel_transitions', 'created_at')
    op.drop_column('funnel_transitions', 'ingested_at')
    op.drop_column('funnel_transitions', 'reported_at')
    op.drop_column('marketing_activities', 'ingested_at')
    op.drop_column('marketing_activities', 'reported_at')
    op.drop_column('event_metrics', 'updated_at')
    op.drop_column('event_metrics', 'ingested_at')
    op.drop_column('event_metrics', 'reported_at')
