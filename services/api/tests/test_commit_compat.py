import os
import json
import sqlite3
import tempfile
from fastapi.testclient import TestClient
import sys
import pathlib

# ensure repo root is on sys.path so `services` package imports resolve
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.api.app.main import app
from services.api.app import db as tdb


def setup_temp_db():
    fd, path = tempfile.mkstemp(prefix="taaip_test_", suffix=".sqlite3")
    os.close(fd)
    os.environ['TAAIP_DB_PATH'] = path
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    tdb.init_db()
    return path


def test_commit_v3_compat():
    path = setup_temp_db()
    client = TestClient(app)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # create a legacy import_job
    cur.execute("INSERT INTO import_job(status, target_domain, source_system, filename, row_count_detected) VALUES (?,?,?,?,?)", ('parsed', 'production', 'legacy_test', 'legacy.csv', 2))
    legacy_id = cur.lastrowid

    # insert two imported_rows for legacy job
    row1 = json.dumps({'org_unit_id': '10', 'date': '2026-02-01', 'metric_key': 'contracts', 'metric_value': '3'})
    row2 = json.dumps({'org_unit_id': '10', 'date': '2026-02-02', 'metric_key': 'contracts', 'metric_value': '4'})
    cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row1))
    cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row2))

    # create a v3 import_job that references same filename so compat can resolve
    v3id = 'testv3_' + os.urandom(6).hex()
    cur.execute('INSERT INTO import_job_v3(id, created_at, created_by, dataset_key, source_system, filename, file_sha256, status, row_count, error_count, notes, scope_org_unit_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
        v3id, '2026-02-26T00:00:00Z', None, 'production', 'legacy_test', 'legacy.csv', None, 'uploaded', 0, 0, None, None
    ))

    conn.commit()
    conn.close()

    # call compat commit endpoint with v3 id
    resp = client.post('/api/api/import/compat/commit_v3', json={'import_job_id': v3id, 'mode': 'append'})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get('status') == 'ok'
    # commit_result should include imported count from legacy commit
    assert data.get('commit_result') and (data['commit_result'].get('imported') == 2 or data['commit_result'].get('committed_rows') == 2)

    # cleanup
    try:
        os.remove(path)
    except Exception:
        pass
