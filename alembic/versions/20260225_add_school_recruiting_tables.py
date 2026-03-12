"""Add school recruiting columns and ensure schema compatibility

Revision ID: 20260225_add_school_recruiting_tables
Revises: 
Create Date: 2026-02-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260225_add_school_recruiting_tables'
down_revision = None
branch_labels = None
depends_on = None


def _has_column(conn, table, col):
    res = conn.execute(sa.text(f"PRAGMA table_info('{table}')")).fetchall()
    cols = [r[1] for r in res]
    return col in cols


def upgrade():
    conn = op.get_bind()
    # ensure schools table has modern columns
    try:
        if not _has_column(conn, 'schools', 'school_name'):
            # if a legacy 'name' column exists, add school_name and copy
            op.execute("ALTER TABLE schools ADD COLUMN school_name TEXT")
            try:
                op.execute("UPDATE schools SET school_name = name WHERE school_name IS NULL AND name IS NOT NULL")
            except Exception:
                pass
        if not _has_column(conn, 'schools', 'zip_code'):
            op.execute("ALTER TABLE schools ADD COLUMN zip_code TEXT")
            try:
                op.execute("UPDATE schools SET zip_code = zip WHERE zip_code IS NULL AND zip IS NOT NULL")
            except Exception:
                pass
    except Exception:
        # table may not exist yet; ignore
        pass

    # ensure school_milestones has linked_event_id
    try:
        if not _has_column(conn, 'school_milestones', 'linked_event_id'):
            op.execute("ALTER TABLE school_milestones ADD COLUMN linked_event_id TEXT")
    except Exception:
        pass


def downgrade():
    # Alembic downgrades for ALTER TABLE ADD COLUMN are non-trivial; no-op
    pass
