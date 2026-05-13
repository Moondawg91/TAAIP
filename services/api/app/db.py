
def table_has_cols(conn, table_name: str, cols_needed: list) -> bool:
    """Check if a table has all required columns."""
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        existing = [r[1] for r in cur.fetchall()]
        return all(c in existing for c in cols_needed)
    except Exception:
        return False


def row_to_dict(row) -> dict:
    """Convert sqlite3.Row to dict."""
    if hasattr(row, 'keys'):
        return {k: row[k] for k in row.keys()}
    return dict(row)


def connect():
    """Alias for get_db_conn for backward compatibility."""
    return get_db_conn()


def get_db_path() -> str:
    """Get the database file path from DATABASE_URL or environment."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    return "./data/taaip.sqlite3"


def get_documents_path() -> str:
    """Return documents directory path used by document routers."""
    return os.environ.get("DOCUMENTS_PATH", "./data/documents")


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check whether a specific column exists in a table."""
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in cur.fetchall()]
        return column_name in cols
    except Exception:
        return False


def safe_add_column(conn, table_name: str, column_def: str) -> bool:
    """Add a column if it does not already exist.

    column_def must start with the column name, e.g. "foo TEXT DEFAULT ''".
    """
    try:
        col_name = column_def.strip().split()[0]
        if column_exists(conn, table_name, col_name):
            return False
        cur = conn.cursor()
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
        conn.commit()
        return True
    except Exception:
        return False

import os
import sqlite3
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.api.app.models import Base
from services.api.app import models_domain  # noqa: F401
from services.api.app import models_ingest  # noqa: F401


def _resolve_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    db_path = os.environ.get("TAAIP_DB_PATH", "./data/taaip.sqlite3")
    if not db_path.startswith("sqlite:///"):
        db_path = f"sqlite:///{Path(db_path).expanduser().resolve()}"
    os.environ["DATABASE_URL"] = db_path
    return db_path


DATABASE_URL = _resolve_database_url()

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    future=True,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def init_schema() -> None:
    """Backward-compatible alias used by runtime preflight."""
    init_db()


def get_db_conn():
    """Return a raw DB-API connection for legacy router code paths."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    return engine.raw_connection()


def execute_with_retry(cur, query: str, params=None, retries: int = 5, backoff: float = 0.05):
    """Execute a SQL statement with retry for transient SQLite lock errors."""
    if params is None:
        params = ()

    last_err = None
    for attempt in range(retries):
        try:
            return cur.execute(query, params)
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "locked" not in msg and "busy" not in msg:
                raise
            last_err = exc
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            raise

    if last_err is not None:
        raise last_err
