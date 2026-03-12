-- Minimal canonical warehouse schema (Phase-1)
-- dim_unit, dim_date, staging_uploads, metric_definition, fact_funnel_daily

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_unit (
    unit_key TEXT PRIMARY KEY,
    rsid TEXT,
    display_name TEXT,
    echelon_type TEXT,
    parent_key TEXT,
    sort_order INTEGER
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key TEXT PRIMARY KEY,
    date_iso TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER
);

CREATE TABLE IF NOT EXISTS staging_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_key TEXT,
    source_name TEXT,
    uploaded_at TEXT,
    raw_json TEXT,
    validated INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metric_definition (
    metric_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    sql_definition TEXT
);

CREATE TABLE IF NOT EXISTS fact_funnel_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key TEXT,
    unit_key TEXT,
    stage TEXT,
    count INTEGER,
    ingested_at TEXT,
    FOREIGN KEY(date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY(unit_key) REFERENCES dim_unit(unit_key)
);

-- End of minimal schema
