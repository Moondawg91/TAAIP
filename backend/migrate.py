import os
import sqlite3
import time
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _ensure_schema_migrations(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            applied_at TEXT
        )
        """
    )
    conn.commit()


def _applied_migrations(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT name FROM schema_migrations")
    return {r[0] for r in cur.fetchall()}


def _apply_sql_file(conn: sqlite3.Connection, path: Path):
    sql = path.read_text()
    cur = conn.cursor()
    # execute script (multiple statements)
    cur.executescript(sql)
    conn.commit()


def _ensure_columns_on_raw_import_batches(conn: sqlite3.Connection):
    # safe conditional ALTER TABLE for SQLite
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(raw_import_batches)")
    existing = {r[1] for r in cur.fetchall()}  # name is at index 1
    needed = {
        'file_name': "TEXT",
        'detected_sheet': "TEXT",
        'detected_header_row': "INTEGER",
        'content_type': "TEXT",
        'file_size': "INTEGER",
        'detected_columns': "TEXT",
    }
    for col, coltype in needed.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE raw_import_batches ADD COLUMN {col} {coltype}")
    conn.commit()


def apply_all(db_path_arg: str = None):
    # determine DB path
    db_path = db_path_arg or os.environ.get('DB_PATH') or os.path.join(os.path.dirname(__file__), '..', 'recruiting.db')
    db_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=15000;")
        _ensure_schema_migrations(conn)
        applied = _applied_migrations(conn)

        # gather migration files
        files = sorted([p for p in MIGRATIONS_DIR.iterdir() if p.is_file() and p.suffix in ('.sql',)])
        for f in files:
            name = f.name
            if name in applied:
                continue
            # special-case marker in 002 to run python alters
            if name.endswith('002_import_batches_columns.sql'):
                _ensure_columns_on_raw_import_batches(conn)
            else:
                _apply_sql_file(conn, f)
            # record applied
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO schema_migrations (name, applied_at) VALUES (?, datetime('now'))", (name,))
            conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    apply_all()
