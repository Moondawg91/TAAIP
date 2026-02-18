import os, sqlite3
from datetime import datetime

DB = os.getenv("DB_PATH") or "/app/recruiting.db"

DDL = [
"""
CREATE TABLE IF NOT EXISTS raw_import_batches (
  batch_id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL,
  filename TEXT NOT NULL,
  stored_path TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  imported_at TEXT NOT NULL,
  detected_profile TEXT,
  status TEXT NOT NULL DEFAULT 'received',
  notes TEXT
);
""",
"""
CREATE TABLE IF NOT EXISTS raw_import_tables (
  batch_id TEXT NOT NULL,
  sheet_name TEXT,
  table_index INTEGER NOT NULL DEFAULT 0,
  header_row_index INTEGER,
  detected_profile TEXT,
  column_map_json TEXT,
  row_count INTEGER,
  preview_json TEXT,
  PRIMARY KEY (batch_id, table_index),
  FOREIGN KEY (batch_id) REFERENCES raw_import_batches(batch_id)
);
"""
]

def main():
  con = sqlite3.connect(DB)
  cur = con.cursor()
  for stmt in DDL:
    cur.execute(stmt)
  con.commit()
  con.close()
  print(f"OK: raw import tables ensured in {DB}")

if __name__ == "__main__":
  main()
