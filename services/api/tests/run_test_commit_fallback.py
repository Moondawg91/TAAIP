import os
import json
import sqlite3
import tempfile
from fastapi.testclient import TestClient
import pathlib
import sys

# ensure repo root on path
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.api.app.main import app
from services.api.app import db as tdb


def run():
    fd, path = tempfile.mkstemp(prefix="taaip_test_", suffix=".sqlite3")
    os.close(fd)
    os.environ['TAAIP_DB_PATH'] = path
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    tdb.init_db()

    with TestClient(app) as client:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("INSERT INTO import_job(status, target_domain, source_system, filename, row_count_detected) VALUES (?,?,?,?,?)", ('parsed', 'production', 'legacy_test', 'legacy.csv', 2))
        legacy_id = cur.lastrowid
        row1 = json.dumps({'org_unit_id': '10', 'date': '2026-02-01', 'metric_key': 'contracts', 'metric_value': '3'})
        row2 = json.dumps({'org_unit_id': '10', 'date': '2026-02-02', 'metric_key': 'contracts', 'metric_value': '4'})
        cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row1))
        cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row2))
        conn.commit()
        conn.close()

        resp = client.post('/api/api/import/commit', json={'import_job_id': str(legacy_id), 'mode': 'append'})
        print('commit status', resp.status_code, resp.text)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get('committed_rows') == 2

        # Try the feed path. routers are mounted under /api and some endpoints include
        # an extra /api prefix in their route; try both variants.
        resp2 = client.get('/api/powerbi/fact_production?org_unit_id=10')
        if resp2.status_code == 404:
            resp2 = client.get('/api/api/powerbi/fact_production?org_unit_id=10')
        print('feed status', resp2.status_code, resp2.text)
        assert resp2.status_code == 200
        arr = resp2.json()
        assert isinstance(arr, list) and len(arr) >= 2

    os.remove(path)
    print('run_test_commit_fallback: OK')


if __name__ == '__main__':
    run()
