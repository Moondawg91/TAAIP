"""postgres baseline from sqlite snapshot

Revision ID: 20260506_000001
Revises: 
Create Date: 2026-05-06 00:00:01
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pathlib import Path

revision: str = "20260506_000001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema_path = Path(__file__).resolve().parents[3] / "app" / "postgresql_schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    op.execute(sa.text(sql))


def downgrade() -> None:
    # Non-destructive project policy: no drop operations in baseline downgrade.
    pass
