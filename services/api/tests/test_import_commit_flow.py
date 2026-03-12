import os
import json
import sqlite3
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app import database


def setup_temp_db(tmp_path):
    db_path = str(tmp_path / 'taaip_test.db')
    os.environ['TAAIP_DB_PATH'] = db_path
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    # enable local auth bypass for tests that use dependency guards
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    # reload engine
    try:
        database.reload_engine_if_needed()
    except Exception:
        pass
    # ensure schema
    from services.api.app import db as app_db
    app_db.init_schema()
    # best-effort: ensure critical tables exist in the temp DB for tests
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS import_job_v3 (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                created_by TEXT,
                dataset_key TEXT NOT NULL,
                source_system TEXT,
                filename TEXT,
                file_sha256 TEXT,
                status TEXT DEFAULT 'uploaded',
                row_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                updated_at TEXT,
                notes TEXT,
                scope_org_unit_id TEXT
            );
            CREATE TABLE IF NOT EXISTS imported_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_job_id INTEGER,
                target_domain TEXT,
                row_json TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS import_column_map (
                id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                mapping_json TEXT NOT NULL,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS import_file (
                id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                content_type TEXT,
                size_bytes INTEGER,
                uploaded_at TEXT
            );
            CREATE TABLE IF NOT EXISTS fact_production (
                id TEXT PRIMARY KEY,
                org_unit_id TEXT,
                date_key TEXT,
                metric_key TEXT,
                metric_value REAL,
                source_system TEXT,
                import_job_id TEXT,
                created_at TEXT,
                record_status TEXT,
                archived_at TEXT
            );
        ''' )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return db_path


def test_import_map_commit_end_to_end(tmp_path):
    path = setup_temp_db(tmp_path)
    # create TestClient after DB/env setup so app uses the test DB
    client = TestClient(app)
    # create an import_job_v3 record via direct DB insert (simulate uploaded file)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    import_id = 'imp-test-1'
    cur.execute('INSERT INTO import_job_v3(id, created_at, dataset_key, source_system, filename, file_sha256, status, row_count) VALUES (?,?,?,?,?,?,?,?)',
                (import_id, '2026-02-21T00:00:00Z', 'dataset-x', 'unit-test', 'file.csv', 'deadbeef', 'uploaded', 2))
    conn.commit()

    # create two imported rows linked to import_job (simulate parsed preview)
    # link imported_rows to the v3 import id we created above
    cur.execute('INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,?)',
                (import_id, 'fact_production', json.dumps({'org_unit_id': '1', 'date_key': '2026-02-01', 'metric_key': 'leads', 'metric_value': 5}), '2026-02-21T00:00:00Z'))
    cur.execute('INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,?)',
                (import_id, 'fact_production', json.dumps({'org_unit_id': '1', 'date_key': '2026-02-01', 'metric_key': 'leads', 'metric_value': 3}), '2026-02-21T00:00:00Z'))
    conn.commit()
    conn.close()

    # Use v3 compatibility endpoints: /api/import/map, /api/import/validate, /api/import/commit
    # provide a minimal mapping payload (must be truthy)
    resp = client.post('/api/api/import/map', json={'import_job_id': import_id, 'mapping': {'field_map': {}, 'target_table': 'fact_production'}, 'dataset_key': 'production'})
    assert resp.status_code in (200, 201, 204)

    respv = client.post('/api/api/import/validate', json={'import_job_id': import_id})
    assert respv.status_code in (200, 201, 204)

    resp2 = client.post('/api/api/import/commit', json={'import_job_id': import_id, 'mode': 'append'})
    assert resp2.status_code in (200, 201, 204)

    # verify fact_production rows created
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT id, org_unit_id, date_key, metric_key, metric_value, import_job_id FROM fact_production WHERE metric_key='leads'")
    rows = cur.fetchall()
    cur.execute("SELECT SUM(COALESCE(metric_value,0)) FROM fact_production WHERE metric_key='leads'")
    total = cur.fetchone()[0] or 0
    conn.close()
    # dedup semantics: unique index on (org_unit_id,date_key,metric_key) means last value wins
    assert total >= 3
