-- 002_import_batches_columns.sql: ensure additional metadata columns exist on raw_import_batches
-- This migration will be applied via migrate.py which performs safe conditional ALTERs for SQLite.

-- marker: python-alter-raw_import_batches
-- columns to ensure: file_name TEXT, detected_sheet TEXT, detected_header_row INTEGER, content_type TEXT, file_size INTEGER, detected_columns TEXT
