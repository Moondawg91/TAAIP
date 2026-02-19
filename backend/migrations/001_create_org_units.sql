-- Migration: create org_units and org_unit_aliases tables (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS org_units (
  unit_id TEXT PRIMARY KEY,
  level TEXT NOT NULL CHECK(level IN ('USAREC','BDE','BN','CO','STN')),
  unit_code TEXT NOT NULL,
  parent_unit_id TEXT NULL,
  name TEXT NULL,
  metadata TEXT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(level, unit_code),
  FOREIGN KEY(parent_unit_id) REFERENCES org_units(unit_id)
);

CREATE INDEX IF NOT EXISTS idx_org_units_parent ON org_units(parent_unit_id);
CREATE INDEX IF NOT EXISTS idx_org_units_code ON org_units(unit_code);

CREATE TABLE IF NOT EXISTS org_unit_aliases (
  alias_id TEXT PRIMARY KEY,
  alias_code TEXT NOT NULL,
  alias_type TEXT NOT NULL,
  unit_id TEXT NOT NULL,
  source_system TEXT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  FOREIGN KEY(unit_id) REFERENCES org_units(unit_id)
);

-- Unique constraint: alias_code + alias_type + COALESCE(source_system,'')
-- SQLite doesn't support expression-based unique constraints portably, so we'll
-- enforce uniqueness at application level or leave a loose unique index on alias_code/alias_type.
CREATE INDEX IF NOT EXISTS idx_alias_lookup ON org_unit_aliases(alias_code, alias_type);
CREATE INDEX IF NOT EXISTS idx_alias_unit ON org_unit_aliases(unit_id);
