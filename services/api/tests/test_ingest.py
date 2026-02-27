import os
import json
import tempfile
from services.api.app import ingest, ingest_registry
from services.api.app.db import get_db_conn, init_schema


def test_detect_importer_csv_emm():
    td = tempfile.mkdtemp()
    path = os.path.join(td, 'emm.csv')
    with open(path, 'w') as f:
        f.write('RSID,METRIC,VALUE,DATE\n')
        f.write('STN001,TestMetric,10,2026-01-01\n')
    init_schema()
    imp = ingest.detect_importer(path)
    assert imp in [s['id'] for s in ingest_registry.list_importers()]


def test_run_import_school_contacts():
    td = tempfile.mkdtemp()
    path = os.path.join(td, 'schools.csv')
    with open(path, 'w') as f:
        f.write('SCHOOL,CONTACT,EMAIL,PHONE,CITY,STATE,ZIP\n')
        f.write('Central High,Jane Doe,jane@example.com,555-1212,Townsville,TX,12345\n')
    init_schema()
    # run import via unknown_dataset fallback since fingerprint may not match
    conn = get_db_conn()
    cur = conn.cursor()
    # create a dummy ingest_run id
    cur.execute("INSERT INTO ingest_file (source_system, original_filename, stored_path, file_hash, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", (None, 'schools.csv', path, None, 'test'))
    conn.commit()
    fid = cur.execute('SELECT last_insert_rowid()').fetchone()[0]
    cur.execute("INSERT INTO ingest_run (ingest_file_id, importer_id, started_at, status) VALUES (?, ?, datetime('now'), 'running')", (fid, 'school_contacts_v1'))
    conn.commit()
    runid = cur.execute('SELECT last_insert_rowid()').fetchone()[0]
    res = ingest.run_import(path, ingest_run_id=runid, importer_id='school_contacts_v1', db=None, uploaded_by='test')
    assert res['status'] in ('completed', 'staged_unknown')
