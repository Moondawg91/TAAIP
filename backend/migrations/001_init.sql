-- 001_init.sql: create core ingestion and modeled tables
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_import_batches (
  batch_id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL DEFAULT 'upload',
  filename TEXT NOT NULL DEFAULT '',
  stored_path TEXT NOT NULL DEFAULT '',
  file_hash TEXT NOT NULL DEFAULT '',
  imported_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'received',
  notes TEXT
);

CREATE TABLE IF NOT EXISTS raw_import_rows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL,
  row_index INTEGER,
  row_json TEXT,
  inserted_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(batch_id) REFERENCES raw_import_batches(batch_id)
);

CREATE TABLE IF NOT EXISTS facts_recruiting (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL,
  metric_date TEXT,
  cbsa TEXT,
  zip TEXT,
  station TEXT,
  company TEXT,
  battalion TEXT,
  brigade TEXT,
  command TEXT,
  metric_name TEXT,
  metric_value REAL,
  source_file TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(batch_id) REFERENCES raw_import_batches(batch_id)
);

CREATE TABLE IF NOT EXISTS aggs_recruiting (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT NOT NULL,
  grain TEXT,
  dim1 TEXT,
  dim2 TEXT,
  metric_name TEXT,
  metric_value REAL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(batch_id) REFERENCES raw_import_batches(batch_id)
);

CREATE TABLE IF NOT EXISTS dashboard_specs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id TEXT,
  spec_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
