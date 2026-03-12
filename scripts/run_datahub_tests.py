#!/usr/bin/env python3
import sys
import requests
from datetime import date

BASE = 'http://127.0.0.1:8000'

def main():
    today = date.today()
    from services.api.app import scope
    s = scope.parse_scope_params({})
    fy = s['fy']
    qtr = s['qtr_num']
    rsm = s['rsm_month']
    params = {'unit_rsid': 'USAREC', 'fy': fy, 'qtr_num': qtr, 'rsm_month': rsm}
    print('Testing enlistments by BN...')
    r = requests.get(f"{BASE}/api/v2/analytics/enlistments/bn", params=params)
    print(r.status_code)
    print(r.text)
    print('Testing EMM events...')
    r2 = requests.get(f"{BASE}/api/v2/analytics/emm/events", params=params)
    print(r2.status_code)
    print(r2.text)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
import sys, os, json, datetime, uuid, argparse
sys.path.insert(0, os.getcwd())
from services.api.app.db import connect
from services.api.app.importers import parse as parse_mod
from services.api.app.importers import detect as detect_mod
from services.api.app import migrations
from services.api.app.importers import usarec_g2_enlistments_by_bn, emm_portal

# default upload dir next to this script
DEFAULT_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "test_uploads")


def discover_files(upload_dir: str):
    exts = ('.xlsx', '.xls', '.csv')
    out = []
    if not os.path.isdir(upload_dir):
        return []
    for name in sorted(os.listdir(upload_dir)):
        if name.startswith('~$'):
            continue
        if not name.lower().endswith(exts):
            continue
        out.append(os.path.join(upload_dir, name))
    return out


def main():
    parser = argparse.ArgumentParser(description='Run Data Hub importer smoke tests against test uploads')
    parser.add_argument('--dir', dest='upload_dir', default=DEFAULT_UPLOAD_DIR, help='Upload directory to scan')
    parser.add_argument('--only', dest='only', default=None, help='Only run files that contain this substring')
    args = parser.parse_args()

    conn = connect()
    cur = conn.cursor()
    # ensure migrations and registry
    migrations.apply_migrations(conn)
    try:
        migrations.seed_default_registry(conn)
    except Exception:
        pass
    # get registry
    cur.execute('SELECT dataset_key, display_name, detection_keywords, required_columns, optional_columns, file_types, source_system FROM dataset_registry WHERE enabled=1')
    reg = [dict(r) for r in cur.fetchall()]

    # discover files
    candidates = discover_files(args.upload_dir)
    if args.only:
        candidates = [p for p in candidates if args.only.lower() in os.path.basename(p).lower()]
    files = [(p, os.path.basename(p)) for p in candidates]

    for path, fname in files:
        print('\n--- Processing', fname)
        try:
            sheets, headers, df = parse_mod.parse_file(path, fname)
            print('Parsed headers:', headers)
        except Exception as e:
            print('Parse failed:', e)
            continue
        dk, conf, matched = detect_mod.detect_dataset(fname, sheets, headers, reg, hint=None)
        print('Detected:', dk, 'confidence', conf)
        # create run
        run_id = f"run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        created = datetime.datetime.utcnow().isoformat()
        cur.execute('INSERT INTO import_run_v2 (run_id, filename, status, storage_path, created_at) VALUES (?,?,?,?,?)', (run_id, fname, 'queued', path, created))
        conn.commit()
        # find entry
        entry = None
        for r in reg:
            if r.get('dataset_key') == dk:
                entry = r
                break
        if not entry:
            print('No registry entry; marking failed')
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed','no registry', run_id))
            conn.commit()
            continue
        # run loader
        ctx = {'dataset_key': dk, 'source_system': entry.get('source_system')}
        cur.execute('UPDATE import_run_v2 SET dataset_key=?, detected_confidence=?, status=?, started_at=? WHERE run_id=?', (dk, conf, 'running', datetime.datetime.utcnow().isoformat(), run_id))
        conn.commit()
        rows_loaded = 0
        try:
            if dk and dk.startswith('USAREC_G2_ENLISTMENTS'):
                rows_loaded = usarec_g2_enlistments_by_bn.process_and_load(df, ctx, conn, run_id)
            elif dk and (dk.startswith('EMM_PORTAL') or dk == 'EMM_PORTAL_EVENTS'):
                rows_loaded = emm_portal.process_and_load(df, ctx, conn, run_id)
            else:
                print('No loader for', dk)
        except Exception as e:
            print('Loader error', e)
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', str(e), run_id))
            conn.commit()
            continue
        cur.execute('UPDATE import_run_v2 SET status=?, rows_in=?, rows_loaded=?, ended_at=? WHERE run_id=?', ('success', len(df.index) if hasattr(df,'index') else 0, rows_loaded, datetime.datetime.utcnow().isoformat(), run_id))
        conn.commit()
        print('Run', run_id, 'loaded', rows_loaded)

    # run validation SQLs
    print('\n--- Validation queries')
    print('\nRecent import runs:')
    for row in cur.execute('SELECT run_id, dataset_key, status, rows_in, rows_loaded, error_summary, started_at, ended_at FROM import_run_v2 ORDER BY started_at DESC LIMIT 10'):
        print(row)

    print('\nBN enlistments summary:')
    for row in cur.execute('SELECT rsid, bn_name, SUM(enlistments) AS enlistments FROM fact_enlistments_bn GROUP BY rsid, bn_name ORDER BY enlistments DESC LIMIT 25'):
        print(row)

    print('\nEMM activities by FY:')
    for row in cur.execute('SELECT fy, COUNT(*) AS activities, COUNT(DISTINCT activity_id) AS unique_ids FROM fact_emm_activity GROUP BY fy ORDER BY fy DESC'):
        print(row)

    conn.close()

if __name__ == '__main__':
    main()
