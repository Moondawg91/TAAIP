-- Migration: create raw_import_batches and raw_import_columns (staging)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_import_batches (
  batch_id TEXT PRIMARY KEY,
  source_system TEXT,
  uploaded_filename TEXT,
  file_hash TEXT,
  filesize INTEGER,
  sheet_name TEXT,
  header_row INTEGER,
  detected_dataset_type TEXT,
  detected_columns_json TEXT,
  row_count INTEGER,
  status TEXT DEFAULT 'uploaded',
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS raw_import_columns (
  id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL,
  original_col TEXT,
  normalized_col TEXT,
  confidence REAL DEFAULT 1.0,
  chosen_field TEXT,
  FOREIGN KEY(batch_id) REFERENCES raw_import_batches(batch_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_batch_id ON raw_import_columns(batch_id);
