"""postgres baseline from sqlite snapshot

Revision ID: 20260506_000001
Revises:
Create Date: 2026-05-06 00:00:01
"""

from typing import Sequence, Union
from pathlib import Path
import re

from alembic import op


revision: str = "20260506_000001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "postgresql_schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    statements = [part.strip() for part in sql.split(";")]
    fk_statements = []
    for statement in statements:
        if not statement:
            continue
        if statement in {"BEGIN", "COMMIT"}:
            continue
        if statement.startswith('CREATE TABLE '):
            match = re.match(r'CREATE TABLE\s+"([^"]+)"\s*\(', statement)
            table_name = match.group(1) if match else None
            lines = statement.splitlines()
            kept_lines = []
            for line in lines:
                if 'FOREIGN KEY' in line:
                    if table_name:
                        fk_statements.append((table_name, line.strip().rstrip(',')))
                    continue
                kept_lines.append(line)
            for idx in range(len(kept_lines) - 1, -1, -1):
                if kept_lines[idx].strip() and kept_lines[idx].strip() != ')':
                    kept_lines[idx] = kept_lines[idx].rstrip(',')
                    break
            statement = "\n".join(kept_lines)
        statement = statement.replace("datetime('now')", "CURRENT_TIMESTAMP")
        statement = statement.replace('datetime("now")', 'CURRENT_TIMESTAMP')
        op.execute(statement)

    for table_name, fk_line in fk_statements:
        constraint_match = re.search(r'CONSTRAINT\s+("[^"]+"|\S+)\s+FOREIGN KEY', fk_line)
        constraint_name = constraint_match.group(1) if constraint_match else None
        if constraint_name:
            alter_sql = f'ALTER TABLE "{table_name}" ADD {fk_line}'
        else:
            alter_sql = f'ALTER TABLE "{table_name}" ADD {fk_line}'
        op.execute(alter_sql)


def downgrade() -> None:
    pass
