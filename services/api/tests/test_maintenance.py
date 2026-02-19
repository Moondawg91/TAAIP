import os
import json
import tempfile
from services.api.app import db
from services.api.app.routers import maintenance
from pprint import pprint


def setup_test_db(tmp_path):
    os.environ['TAAIP_DB_PATH'] = str(tmp_path / 'taaip_test.db')
    db.init_schema()
    return os.environ['TAAIP_DB_PATH']


def test_purge_archived_dry_run(tmp_path):
    db_path = setup_test_db(tmp_path)
    # call purge_archived in dry-run mode; should return structured result with ints
    res = maintenance.purge_archived(days=30, tables=None, dry_run=True, current_user={'username':'dev.user','roles':['usarec_admin']})
    assert res['status'] == 'ok'
    assert 'purged' in res
    for k, v in res['purged'].items():
        # values should be dicts for allowed tables
        assert isinstance(v, dict) or v == 'error' or v == 'invalid_table'


def test_trigger_schedule_creates_runs(tmp_path):
    db_path = setup_test_db(tmp_path)
    conn = db.connect()
    cur = conn.cursor()
    params = {'tasks': ['dedupe', 'purge'], 'days': 7}
    cur.execute('INSERT INTO maintenance_schedules(name, enabled, interval_minutes, params_json, created_at) VALUES (?,?,?,?,?)', ('unit-auto', 1, 1, json.dumps(params), '2026-02-17T00:00:00Z'))
    conn.commit()
    sid = cur.lastrowid
    conn.close()

    admin_user = {'username':'dev.user','roles':['usarec_admin']}
    # trigger schedule directly
    res = maintenance.trigger_schedule(sid, current_user=admin_user)
    assert res['status'] == 'ok'
    assert isinstance(res['results'], list)

    # ensure runs logged
    conn = db.connect()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as c FROM maintenance_runs WHERE schedule_id=?', (sid,))
    c = cur.fetchone()[0]
    conn.close()
    assert c >= 1
