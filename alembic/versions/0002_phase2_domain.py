"""phase2 canonical domain models

Revision ID: 0002_phase2_domain
Revises: 0001_initial_schema
Create Date: 2026-02-15 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_phase2_domain'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('station_rsid', sa.String(length=4), sa.ForeignKey('stations.rsid'), nullable=True),
        sa.Column('brigade_prefix', sa.String(length=1), nullable=True),
        sa.Column('battalion_prefix', sa.String(length=2), nullable=True),
        sa.Column('company_prefix', sa.String(length=3), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='planned'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'event_metrics',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('event_id', sa.String(), sa.ForeignKey('events.id'), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('leads_generated', sa.Integer(), nullable=True),
        sa.Column('leads_qualified', sa.Integer(), nullable=True),
        sa.Column('conversions', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('cost_per_lead', sa.Float(), nullable=True),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'marketing_activities',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('event_id', sa.String(), sa.ForeignKey('events.id'), nullable=True),
        sa.Column('station_rsid', sa.String(length=4), sa.ForeignKey('stations.rsid'), nullable=True),
        sa.Column('brigade_prefix', sa.String(length=1), nullable=True),
        sa.Column('battalion_prefix', sa.String(length=2), nullable=True),
        sa.Column('company_prefix', sa.String(length=3), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('campaign_name', sa.String(), nullable=True),
        sa.Column('channel', sa.String(), nullable=True),
        sa.Column('data_source', sa.String(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=True),
        sa.Column('engagements', sa.Integer(), nullable=True),
        sa.Column('clicks', sa.Integer(), nullable=True),
        sa.Column('conversions', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('reporting_date', sa.Date(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'funnel_stages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('stage_name', sa.String(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True)
    )

    op.create_table(
        'funnel_transitions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('lead_key', sa.String(), nullable=False),
        sa.Column('station_rsid', sa.String(length=4), sa.ForeignKey('stations.rsid'), nullable=False),
        sa.Column('brigade_prefix', sa.String(length=1), nullable=True),
        sa.Column('battalion_prefix', sa.String(length=2), nullable=True),
        sa.Column('company_prefix', sa.String(length=3), nullable=True),
        sa.Column('from_stage', sa.String(), sa.ForeignKey('funnel_stages.id'), nullable=True),
        sa.Column('to_stage', sa.String(), sa.ForeignKey('funnel_stages.id'), nullable=True),
        sa.Column('transition_reason', sa.String(), nullable=True),
        sa.Column('technician_user', sa.String(), nullable=True),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'burden_inputs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('scope_value', sa.String(), nullable=False),
        sa.Column('mission_requirement', sa.Integer(), nullable=False),
        sa.Column('recruiter_strength', sa.Integer(), nullable=False),
        sa.Column('reporting_date', sa.Date(), nullable=False),
        sa.Column('source_system', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'burden_snapshots',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('scope_value', sa.String(), nullable=False),
        sa.Column('reporting_date', sa.Date(), nullable=False),
        sa.Column('mission_requirement', sa.Integer(), nullable=False),
        sa.Column('recruiter_strength', sa.Integer(), nullable=False),
        sa.Column('burden_ratio', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'loes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('scope_value', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'loe_metrics',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('loe_id', sa.String(), sa.ForeignKey('loes.id'), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('warn_threshold', sa.Float(), nullable=True),
        sa.Column('fail_threshold', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('rationale', sa.String(), nullable=True),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        'decisions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('scope_value', sa.String(), nullable=False),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('scope_type', sa.String(), nullable=True),
        sa.Column('scope_value', sa.String(), nullable=True),
        sa.Column('before_json', sa.JSON(), nullable=True),
        sa.Column('after_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # seed default funnel stages (idempotent)
    bind = op.get_bind()
    dialect = bind.dialect.name
    stages = [
        ('lead', 'lead', 1),
        ('prospect', 'prospect', 2),
        ('appointment_made', 'appointment_made', 3),
        ('appointment_conducted', 'appointment_conducted', 4),
        ('test', 'test', 5),
        ('test_pass', 'test_pass', 6),
        ('physical', 'physical', 7),
        ('enlist', 'enlist', 8),
    ]
    for sid, name, order in stages:
        if dialect == 'sqlite':
            sql = "INSERT OR IGNORE INTO funnel_stages (id, stage_name, sequence_order) VALUES (:id, :name, :order)"
        else:
            # Postgres and others that support ON CONFLICT
            sql = "INSERT INTO funnel_stages (id, stage_name, sequence_order) VALUES (:id, :name, :order) ON CONFLICT (id) DO NOTHING"
        op.execute(sa.text(sql), {'id': sid, 'name': name, 'order': order})


def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('decisions')
    op.drop_table('loe_metrics')
    op.drop_table('loes')
    op.drop_table('burden_snapshots')
    op.drop_table('burden_inputs')
    op.drop_table('funnel_transitions')
    op.drop_table('funnel_stages')
    op.drop_table('marketing_activities')
    op.drop_table('event_metrics')
    op.drop_table('events')
