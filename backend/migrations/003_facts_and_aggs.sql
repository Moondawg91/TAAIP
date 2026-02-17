-- 003_facts_and_aggs.sql: ensure indexes for performance
PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_facts_batch ON facts_recruiting(batch_id);
CREATE INDEX IF NOT EXISTS idx_facts_geo ON facts_recruiting(zip, cbsa);
CREATE INDEX IF NOT EXISTS idx_aggs_batch_grain ON aggs_recruiting(batch_id, grain);
