-- 1) Org dimension (canonical)
CREATE TABLE IF NOT EXISTS org_units (
  org_unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL CHECK(level IN ('CMD','BDE','BN','CO','STN')),
  code TEXT NOT NULL,
  name TEXT,
  parent_code TEXT,
  parent_level TEXT,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(level, code)
);

CREATE INDEX IF NOT EXISTS idx_org_units_parent ON org_units(parent_level, parent_code);

-- 2) Alias table (RSID vs STN vs other naming in raw files)
CREATE TABLE IF NOT EXISTS org_unit_aliases (
  alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
  alias_code TEXT NOT NULL,
  alias_type TEXT NOT NULL,
  canonical_level TEXT NOT NULL,
  canonical_code TEXT NOT NULL,
  source_system TEXT,
  created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(alias_type, alias_code)
);

CREATE INDEX IF NOT EXISTS idx_org_alias_lookup ON org_unit_aliases(alias_type, alias_code);

-- 3) Raw ingest batch tracking (PowerBI-like lineage)
CREATE TABLE IF NOT EXISTS raw_import_batches (
  batch_id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL,
  dataset_key TEXT,
  filename TEXT,
  file_hash TEXT,
  status TEXT DEFAULT 'received',
  header_row INTEGER,
  row_count INTEGER,
  notes TEXT,
  imported_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
