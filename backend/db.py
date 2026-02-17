import os
import sqlite3


def db_path() -> str:
    # Prefer explicit env var; fall back to repo-root recruiting.db
    return os.environ.get("DB_PATH") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "recruiting.db")

DDL = [
    """
    CREATE TABLE IF NOT EXISTS raw_import_batches (
      batch_id TEXT PRIMARY KEY,
      source_system TEXT NOT NULL DEFAULT 'upload',
      filename TEXT NOT NULL DEFAULT '',
      file_name TEXT NOT NULL DEFAULT '',
      stored_path TEXT NOT NULL DEFAULT '',
      file_hash TEXT NOT NULL DEFAULT '',
      imported_at TEXT NOT NULL DEFAULT (datetime('now')),
      status TEXT NOT NULL DEFAULT 'received',
      detected_sheet TEXT,
      detected_header_row INTEGER,
      notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id TEXT NOT NULL,
      dataset TEXT NOT NULL,
      cmd TEXT,
      bde TEXT,
      bn TEXT,
      co TEXT,
      stn TEXT,
      zipcode TEXT,
      metric_name TEXT,
      metric_value REAL,
      event_date TEXT
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_facts_batch ON facts(batch_id);
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_kpis (
      batch_id TEXT PRIMARY KEY,
      dataset TEXT NOT NULL,
      total_rows INTEGER NOT NULL,
      total_stations INTEGER,
      total_companies INTEGER,
      total_battalions INTEGER,
      total_brigades INTEGER,
      last_refresh TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_charts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id TEXT NOT NULL,
      chart_key TEXT NOT NULL,
      label TEXT NOT NULL,
      value REAL NOT NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_charts_batch_key ON agg_charts(batch_id, chart_key);
    """,
]


def connect(db_path_arg: str = None):
  path = db_path() if db_path_arg is None else db_path_arg
  con = sqlite3.connect(path, timeout=30, check_same_thread=False)
  # WAL and sensible timeouts reduce "database is locked" errors when concurrent readers/writers exist
  con.execute("PRAGMA journal_mode=WAL;")
  con.execute("PRAGMA synchronous=NORMAL;")
  con.execute("PRAGMA busy_timeout=15000;")
  con.execute("PRAGMA foreign_keys=ON;")
  con.row_factory = sqlite3.Row
  return con


def migrate():
    con = connect()
    try:
        for stmt in DDL:
            con.execute(stmt)
        con.commit()
    finally:
        con.close()


def ensure_not_null_defaults():
    con = connect()
    try:
        con.execute("UPDATE raw_import_batches SET filename = COALESCE(NULLIF(filename,''), 'unknown') WHERE filename IS NULL OR filename = ''")
        con.execute("UPDATE raw_import_batches SET file_name = COALESCE(NULLIF(file_name,''), 'unknown') WHERE file_name IS NULL OR file_name = ''")
        con.commit()
    finally:
        con.close()
