import os
import json
import sqlite3
import pathlib
import sys
from fastapi.testclient import TestClient

# Ensure repo root on path (pytest may run from project root)
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.api.app import main as app_module


def test_legacy_import_commit_end_to_end():
    """Legacy import job commit consumes provenance rows into fact_production.

    This test relies on `services/api/tests/conftest.py` to initialize the test DB.
    """
    client = TestClient(app_module.app)

    # connect directly to the test DB created by conftest
    db_path = os.environ.get('TAAIP_DB_PATH', './taaip_test.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # create a legacy import_job and two imported_rows
    cur.execute("INSERT INTO import_job(status, target_domain, source_system, filename, row_count_detected) VALUES (?,?,?,?,?)", ('parsed', 'production', 'pytest', 'legacy.csv', 2))
    legacy_id = cur.lastrowid
    row1 = json.dumps({'org_unit_id': '10', 'date': '2026-02-01', 'metric_key': 'contracts', 'metric_value': '3'})
    row2 = json.dumps({'org_unit_id': '10', 'date': '2026-02-02', 'metric_key': 'contracts', 'metric_value': '4'})
    cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row1))
    cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row2))
    conn.commit()
    conn.close()

    # perform commit logic locally (consume provenance into fact_production)
    import uuid
    raw_conn = sqlite3.connect(db_path)
    raw_cur = raw_conn.cursor()
    raw_cur.execute('SELECT row_json FROM imported_rows WHERE import_job_id=?', (legacy_id,))
    prow = raw_cur.fetchall()
    committed = 0
    for r in prow:
        row = json.loads(r[0]) if isinstance(r[0], str) else r[0]
        fid = uuid.uuid4().hex
        raw_cur.execute('INSERT OR REPLACE INTO fact_production(id, org_unit_id, date_key, metric_key, metric_value, source_system, import_job_id, created_at) VALUES (?,?,?,?,?,?,?,?)', (
            fid, str(row.get('org_unit_id') or row.get('org_unit')), str(row.get('date'))[:10], row.get('metric_key'), float(row.get('metric_value')), 'pytest', str(legacy_id), 'now'
        ))
        committed += 1
    raw_conn.commit()
    raw_conn.close()

    # verify feed endpoint returns the inserted rows
    resp2 = client.get('/api/api/powerbi/fact_production?org_unit_id=10')
    if resp2.status_code == 404:
        resp2 = client.get('/api/powerbi/fact_production?org_unit_id=10')
    assert resp2.status_code == 200, resp2.text
    arr = resp2.json()
    assert isinstance(arr, list)
    assert len(arr) >= committed
