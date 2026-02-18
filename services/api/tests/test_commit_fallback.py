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

# Set env to use a temp DB
from services.api.app.main import app
from services.api.app import db as tdb

client = TestClient(app)


def setup_temp_db():
    fd, path = tempfile.mkstemp(prefix="taaip_test_", suffix=".sqlite3")
    os.close(fd)
    os.environ['TAAIP_DB_PATH'] = path
    # ensure LOCAL_DEV_AUTH_BYPASS for dependency
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    # init schema
    tdb.init_db()
    return path
    import os
    import json
    import sqlite3
    import tempfile
    from fastapi.testclient import TestClient

    # Set env to use a temp DB
    from services.api.app.main import app
    from services.api.app import db as tdb

    client = TestClient(app)


    def setup_temp_db():
        fd, path = tempfile.mkstemp(prefix="taaip_test_", suffix=".sqlite3")
        os.close(fd)
        os.environ['TAAIP_DB_PATH'] = path
        # ensure LOCAL_DEV_AUTH_BYPASS for dependency
        os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
        # init schema
        tdb.init_db()
        return path


    def test_legacy_commit_fallback():
        path = setup_temp_db()
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # insert a legacy import_job
        cur.execute("INSERT INTO import_job(status, target_domain, source_system, filename, row_count_detected) VALUES (?,?,?,?,?)", ('parsed', 'production', 'legacy_test', 'legacy.csv', 2))
        legacy_id = cur.lastrowid
        # insert two imported_rows linked to legacy import_job id
        row1 = json.dumps({'org_unit_id': '10', 'date': '2026-02-01', 'metric_key': 'contracts', 'metric_value': '3'})
        row2 = json.dumps({'org_unit_id': '10', 'date': '2026-02-02', 'metric_key': 'contracts', 'metric_value': '4'})
        cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row1))
        cur.execute("INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,datetime('now'))", (legacy_id, 'production', row2))
        conn.commit()
        conn.close()

        # Call the commit endpoint with the legacy numeric id
        resp = client.post('/api/api/import/commit', json={'import_job_id': str(legacy_id), 'mode': 'append'})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get('committed_rows') == 2

        # verify rows in fact_production
        resp2 = client.get('/api/api/powerbi/fact_production?org_unit_id=10')
        assert resp2.status_code == 200
        arr = resp2.json()
        assert isinstance(arr, list)
        # cleanup
        os.remove(path)