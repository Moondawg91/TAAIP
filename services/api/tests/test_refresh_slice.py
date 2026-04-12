import os
import json
import sqlite3
import tempfile
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app import database


def setup_temp_db(tmp_path):
    db_path = str(tmp_path / 'taaip_refresh_test.db')
    os.environ['TAAIP_DB_PATH'] = db_path
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    try:
        database.reload_engine_if_needed()
    except Exception:
        pass
    from services.api.app import db as app_db
    app_db.init_schema()
    # create refresh-related tables expected by the new slice
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS refresh_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            canonical_target TEXT,
            file_types TEXT,
            required_merge_keys TEXT,
            mapping_profile TEXT,
            owner TEXT,
            default_mode TEXT,
            trusted TEXT,
            auto_commit TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            filename TEXT,
            stored_path TEXT,
            checksum TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT,
            status TEXT,
            row_count INTEGER,
            profile TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_staging_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            row_number INTEGER,
            row_json TEXT
        );
        CREATE TABLE IF NOT EXISTS dataset_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version TEXT,
            checksum TEXT,
            created_by TEXT,
            created_at TEXT,
            row_count INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_dataset_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version_id INTEGER,
            row_json TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            version_id INTEGER,
            mode TEXT,
            status TEXT,
            applied_by TEXT,
            applied_at TEXT,
            row_count_before INTEGER,
            row_count_after INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS dataset_active (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER UNIQUE,
            version_id INTEGER,
            bound_at TEXT,
            bound_by TEXT
        );
    ''')
    conn.commit()
    conn.close()
    return db_path


def test_refresh_end_to_end(tmp_path):
    db_path = setup_temp_db(tmp_path)
    client = TestClient(app)

    # 1) create source
    resp = client.post('/api/refresh/sources', json={
        'name': 'Vantage Funnel Report',
        'description': 'Test source',
        'canonical_target': 'vantage.funnel',
        'required_merge_keys': ['id'],
        'mapping_profile': {'columns': []}
    })
    assert resp.status_code == 200
    sid = resp.json().get('id')
    assert sid is not None

    # 2) upload small CSV
    csv_content = 'id,name,value\n1,Alice,10\n2,Bob,20\n'
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w') as f:
        f.write(csv_content)

    with open(path, 'rb') as fh:
        files = {'file': ('test1.csv', fh, 'text/csv')}
        resp2 = client.post(f'/api/refresh/sources/{sid}/upload', files=files)
    assert resp2.status_code == 200
    jr = resp2.json()
    job_id = jr.get('job_id')
    assert job_id is not None
    assert jr.get('row_count') == 2

    # 3) verify job status
    resp3 = client.get(f'/api/refresh/jobs/{job_id}')
    assert resp3.status_code == 200
    assert resp3.json().get('row_count') == 2

    # 4) commit replace
    resp4 = client.post(f'/api/refresh/jobs/{job_id}/commit', json={'mode': 'replace'})
    assert resp4.status_code == 200
    cret = resp4.json()
    version_id = cret.get('version_id')
    assert version_id is not None

    # 5) verify dataset_versions and dataset_active
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id, version, row_count FROM dataset_versions WHERE id = ?', (version_id,))
    dv = cur.fetchone()
    assert dv is not None
    cur.execute('SELECT version_id FROM dataset_active WHERE source_id = ?', (sid,))
    av = cur.fetchone()
    assert av is not None and av['version_id'] == version_id

    # 6) fetch current active rows
    resp5 = client.get(f'/api/refresh/sources/{sid}/current')
    assert resp5.status_code == 200
    data = resp5.json()
    assert data.get('version_id') == version_id
    rows = data.get('rows')
    assert isinstance(rows, list) and len(rows) == 2
    ids = sorted([int(r['id']) for r in rows])
    assert ids == [1, 2]

    # 7) upload second CSV (one updated, one new) and commit upsert
    csv2 = 'id,name,value\n1,Alice,15\n3,Carol,30\n'
    fd2, path2 = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd2, 'w') as f:
        f.write(csv2)
    with open(path2, 'rb') as fh2:
        files = {'file': ('test2.csv', fh2, 'text/csv')}
        resp6 = client.post(f'/api/refresh/sources/{sid}/upload', files=files)
    assert resp6.status_code == 200
    job2 = resp6.json().get('job_id')
    assert job2 is not None

    # commit upsert with merge key 'id'
    resp7 = client.post(f'/api/refresh/jobs/{job2}/commit', json={'mode': 'upsert', 'merge_keys': ['id']})
    assert resp7.status_code == 200
    v2 = resp7.json().get('version_id')
    assert v2 is not None and v2 != version_id

    # verify merged rows: ids 1 (value 15),2 (20),3 (30)
    resp8 = client.get(f'/api/refresh/sources/{sid}/current')
    assert resp8.status_code == 200
    current = resp8.json()
    rows2 = {int(r['id']): r for r in current.get('rows')}
    assert set(rows2.keys()) == {1, 2, 3}
    assert rows2[1]['value'] in (15, '15')
    assert rows2[2]['value'] in (20, '20')
    assert rows2[3]['value'] in (30, '30')

    # 9) verify refresh_history has entries for both commits
    cur.execute('SELECT job_id, version_id, mode, status FROM refresh_history WHERE job_id IN (?,?)', (job_id, job2))
    hist = cur.fetchall()
    assert len(hist) >= 2
    conn.close()
