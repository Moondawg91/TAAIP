"""add loe evaluation history

Revision ID: 20260412_001
Revises: 
Create Date: 2026-04-12 16:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loe_evaluation_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("loe_id", sa.String(), nullable=False),
        sa.Column("evaluated_at", sa.String(), nullable=False),
        sa.Column("met_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("at_risk_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("not_met_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("unknown_count", sa.Integer(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("loe_evaluation_history")
