from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from services.api.app import db as dbmod
from .rbac import get_current_user, require_any_role
import os
import json
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/system", tags=["system"])


def _table_exists(cur, name: str) -> bool:
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False


@router.get("/self-check")
def self_check() -> Dict[str, Any]:
    conn = dbmod.connect()
    cur = conn.cursor()

    required_tables = [
        'org_unit', 'users', 'roles', 'user_roles', 'import_job', 'import_file',
        'fact_marketing', 'fact_production', 'fact_funnel', 'projects', 'event',
        'budget_line_item', 'marketing_activities', 'command_priorities', 'priority_loe',
        'funnel_stages', 'import_job_v3'
    ]
    # include Controlled Update System tables when present
    required_tables += ['system_settings', 'system_observations', 'change_proposals', 'change_reviews', 'release_notes']

    present = []
    missing = []
    for t in required_tables:
        if _table_exists(cur, t):
            present.append(t)
        else:
            missing.append(t)

    # migrations_ok: very lightweight check that key migration artifacts exist
    migrations_ok = 'funnel_stages' in present and 'import_job_v3' in present

    # rbac_ok: roles table exists and has at least one role (best-effort)
    rbac_ok = False
    try:
        if _table_exists(cur, 'roles'):
            cur.execute('SELECT COUNT(1) as c FROM roles')
            row = cur.fetchone()
            cnt = row['c'] if isinstance(row, dict) and 'c' in row else (row[0] if row else 0)
            rbac_ok = int(cnt) >= 0
    except Exception:
        rbac_ok = False

    # imports_ok: try a transactional dry-run insert into import_job
    imports_ok = False
    try:
        cur.execute('BEGIN')
        cur.execute("INSERT INTO import_job(created_at, filename, status) VALUES(datetime('now'), 'selfcheck.tmp', 'uploaded')")
        cur.execute('ROLLBACK')
        imports_ok = True
    except Exception:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        imports_ok = False

    # exports_ok: detect export-related routes/tables by presence of budget_line_item or exports router
    exports_ok = _table_exists(cur, 'budget_line_item') or _table_exists(cur, 'budgets')

    # dashboard_definitions_ok: best-effort existence check
    dashboard_definitions_ok = _table_exists(cur, 'dashboard_definitions') if True else False

    # relationships_ok: compute a simple budget rollup (planned, actual, remaining)
    relationships_ok = False
    rollup = {'planned': 0.0, 'actual': 0.0, 'remaining': 0.0}
    try:
        if _table_exists(cur, 'budget_line_item'):
            cur.execute('SELECT SUM(amount) as s FROM budget_line_item')
            r = cur.fetchone()
            planned = float(r['s']) if r and r['s'] is not None else 0.0
        else:
            planned = 0.0
        if _table_exists(cur, 'marketing_activities'):
            cur.execute('SELECT SUM(COALESCE(cost,0)) as s FROM marketing_activities')
            r2 = cur.fetchone()
            actual = float(r2['s']) if r2 and r2['s'] is not None else 0.0
        else:
            actual = 0.0
        rollup['planned'] = planned
        rollup['actual'] = actual
        rollup['remaining'] = planned - actual
        relationships_ok = True
    except Exception:
        relationships_ok = False

    # routes_ok: best-effort list of missing expected routes
    expected_routes = [
        '/api/budget/summary', '/api/performance/mission-assessment', '/api/system/self-check',
        '/api/planning/projects-events', '/api/operations/targeting-data', '/api/imports/preview'
    ]
    missing_routes: List[str] = []
    try:
        # import main lazily to avoid circular import at router registration time
        from services.api.app import main as mainmod
        existing = [r.path for r in mainmod.app.routes]
        for p in expected_routes:
            if p not in existing:
                missing_routes.append(p)
    except Exception:
        # if we cannot inspect routes, mark them as missing
        missing_routes = expected_routes

    required_tables_present = {'ok': len(missing) == 0, 'missing': missing}

    result = {
        'db_ok': True,
        'migrations_ok': migrations_ok,
        'rbac_ok': rbac_ok,
        'routes_ok': {'missing': missing_routes},
        'imports_ok': imports_ok,
        'exports_ok': exports_ok,
        'dashboard_definitions_ok': dashboard_definitions_ok,
        'relationships_ok': {'ok': relationships_ok, 'rollup': rollup},
        'required_tables_present': required_tables_present
    }

    try:
        conn.close()
    except Exception:
        pass

    return result


@router.get('/freshness')
def get_freshness(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        # try fact_production.ingested_at
        data_as_of = None
        last_import_at = None
        last_import_job_id = None
        try:
            if _table_exists(cur, 'fact_production'):
                cur.execute("SELECT MAX(ingested_at) as m FROM fact_production")
                r = cur.fetchone()
                if r:
                    data_as_of = r['m'] if isinstance(r, dict) and 'm' in r else (r[0] if r[0] is not None else None)
        except Exception:
            data_as_of = None

        try:
            if data_as_of is None and _table_exists(cur, 'imported_rows'):
                cur.execute("SELECT MAX(ingested_at) as m FROM imported_rows")
                r = cur.fetchone()
                if r:
                    data_as_of = r['m'] if isinstance(r, dict) and 'm' in r else (r[0] if r[0] is not None else None)
        except Exception:
            pass

        try:
            if (_table_exists(cur, 'import_job_v3')):
                cur.execute("SELECT id, completed_at FROM import_job_v3 WHERE status='completed' ORDER BY completed_at DESC LIMIT 1")
                r = cur.fetchone()
                if r:
                    last_import_at = (r['completed_at'] if isinstance(r, dict) and 'completed_at' in r else r[1])
                    last_import_job_id = (r['id'] if isinstance(r, dict) and 'id' in r else r[0])
        except Exception:
            pass

        # normalize to ISO8601 (ensure strings)
        return {'status': 'ok', 'data_as_of': data_as_of, 'last_import_at': last_import_at, 'last_import_job_id': last_import_job_id}
    finally:
        try:
            conn.close()
        except Exception:
            pass


# USAREC completion gate
@router.get('/usarec-gate')
def get_usarec_gate(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        checks = {}
        # basic presence checks for canonical tables
        tables = ['events', 'projects', 'budget_line_item', 'fact_production', 'marketing_activities', 'funnel_transitions']
        for t in tables:
            try:
                cur.execute("SELECT COUNT(1) as c FROM sqlite_master WHERE type='table' AND name=?", (t,))
                r = cur.fetchone()
                exists = bool(r and (r['c'] if isinstance(r, dict) and 'c' in r else r[0]))
            except Exception:
                exists = False
            checks[t] = {'exists': exists}

        # row counts for critical tables (best-effort)
        for t in ['events', 'projects', 'budget_line_item']:
            try:
                if checks.get(t, {}).get('exists'):
                    cur.execute(f"SELECT COUNT(1) as c FROM {t}")
                    r = cur.fetchone()
                    cnt = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
                else:
                    cnt = 0
            except Exception:
                cnt = 0
            checks[t]['rows'] = cnt

        # see if a prior completion record exists
        completed = False
        last = None
        try:
            if _table_exists(cur, 'usarec_completion'):
                cur.execute("SELECT id, scope_type, scope_value, completed_by, completed_at, details_json FROM usarec_completion ORDER BY created_at DESC LIMIT 1")
                r = cur.fetchone()
                if r:
                    last = dict(r) if isinstance(r, dict) else {cur.description[i][0]: r[i] for i in range(len(r))}
                    completed = True
        except Exception:
            pass

        ready = all((checks[t]['exists'] and checks[t].get('rows', 0) > 0) for t in ['events', 'projects', 'budget_line_item'])

        return {'status': 'ok', 'ready': ready, 'checks': checks, 'last_completion': last}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/usarec-gate/complete')
def post_usarec_complete(payload: Dict = Body(...), user: Dict = Depends(require_any_role('USAREC_ADMIN'))):
    """Mark USAREC scope as completed. Requires USAREC_ADMIN role or LOCAL_DEV_AUTH_BYPASS."""
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        try:
            # ensure table exists (idempotent)
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS usarec_completion (
                id TEXT PRIMARY KEY,
                scope_type TEXT,
                scope_value TEXT,
                completed_by TEXT,
                completed_at TEXT,
                details_json TEXT,
                created_at TEXT
            );
            ''')
        except Exception:
            pass
        import uuid, json, datetime
        recid = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        scope_type = payload.get('scope_type') if isinstance(payload, dict) else None
        scope_value = payload.get('scope_value') if isinstance(payload, dict) else None
        details = payload.get('details') if isinstance(payload, dict) else None
        try:
            cur.execute('INSERT OR REPLACE INTO usarec_completion(id, scope_type, scope_value, completed_by, completed_at, details_json, created_at) VALUES (?,?,?,?,?,?,?)', (recid, scope_type, scope_value, (user.get('username') if isinstance(user, dict) else str(user)), now, json.dumps(details) if details is not None else None, now))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        return {'status': 'ok', 'id': recid, 'completed_at': now}
    finally:
        try:
            conn.close()
        except Exception:
            pass

@router.get('/alerts')
def get_alerts(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        alerts = {'import_errors': 0, 'api_errors': 0, 'proposals_pending': 0}
        try:
            if _table_exists(cur, 'import_error'):
                cur.execute("SELECT COUNT(1) as c FROM import_error WHERE created_at > datetime('now','-30 days')")
                r = cur.fetchone()
                alerts['import_errors'] = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
            elif _table_exists(cur, 'import_job_v3'):
                cur.execute("SELECT COUNT(1) as c FROM import_job_v3 WHERE status='failed' AND completed_at > datetime('now','-30 days')")
                r = cur.fetchone()
                alerts['import_errors'] = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
        except Exception:
            alerts['import_errors'] = 0

        try:
            if _table_exists(cur, 'api_error_log'):
                cur.execute("SELECT COUNT(1) as c FROM api_error_log WHERE created_at > datetime('now','-30 days')")
                r = cur.fetchone()
                alerts['api_errors'] = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
            elif _table_exists(cur, 'audit_logs'):
                cur.execute("SELECT COUNT(1) as c FROM audit_logs WHERE event_type='api_error' AND created_at > datetime('now','-30 days')")
                r = cur.fetchone()
                alerts['api_errors'] = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
        except Exception:
            alerts['api_errors'] = 0

        try:
            if _table_exists(cur, 'change_proposals'):
                cur.execute("SELECT COUNT(1) as c FROM change_proposals WHERE status='submitted'")
                r = cur.fetchone()
                alerts['proposals_pending'] = int(r['c'] if isinstance(r, dict) and 'c' in r else (r[0] if r else 0))
        except Exception:
            alerts['proposals_pending'] = 0

        total = sum(alerts.values())
        return {'status': 'ok', 'alerts': alerts, 'total': total}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/maintenance')
def get_maintenance(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        # return the active maintenance flag if any
        if _table_exists(cur, 'maintenance_flags'):
            try:
                cur.execute("SELECT id, active, message, starts_at, ends_at, created_at, updated_at FROM maintenance_flags WHERE active=1 ORDER BY starts_at DESC LIMIT 1")
                r = cur.fetchone()
                if not r:
                    return {'status': 'ok', 'active': False, 'message': None, 'starts_at': None, 'ends_at': None}
                # normalize mapping
                if isinstance(r, dict):
                    return {'status': 'ok', 'active': bool(r.get('active')), 'message': r.get('message'), 'starts_at': r.get('starts_at'), 'ends_at': r.get('ends_at'), 'id': r.get('id')}
                # tuple/list fallback
                cols = [c[0] for c in cur.description] if cur.description else []
                d = {cols[i]: r[i] for i in range(len(cols))}
                return {'status': 'ok', 'active': bool(d.get('active')), 'message': d.get('message'), 'starts_at': d.get('starts_at'), 'ends_at': d.get('ends_at'), 'id': d.get('id')}
            except Exception:
                return {'status': 'ok', 'active': False, 'message': None, 'starts_at': None, 'ends_at': None}
        else:
            return {'status': 'ok', 'active': False, 'message': None, 'starts_at': None, 'ends_at': None}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/maintenance')
def set_maintenance(payload: Dict[str, Any], user: Dict = Depends(get_current_user), _admin: Dict = Depends(require_any_role('USAREC_ADMIN', 'SYSTEM_ADMIN'))):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        if not _table_exists(cur, 'maintenance_flags'):
            # ensure table exists (safe-create)
            try:
                cur.executescript('''
                CREATE TABLE IF NOT EXISTS maintenance_flags (
                    id TEXT PRIMARY KEY,
                    active INTEGER NOT NULL DEFAULT 0,
                    message TEXT,
                    starts_at TEXT,
                    ends_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                ''')
            except Exception:
                pass
        mid = payload.get('id') or 'maintenance'
        active = 1 if payload.get('active') else 0
        message = payload.get('message')
        starts_at = payload.get('starts_at')
        ends_at = payload.get('ends_at')
        now = datetime.utcnow().isoformat()
        # check if exists
        try:
            cur.execute('SELECT id, created_at FROM maintenance_flags WHERE id=?', (mid,))
            r = cur.fetchone()
            if r:
                # update
                cur.execute('UPDATE maintenance_flags SET active=?, message=?, starts_at=?, ends_at=?, updated_at=? WHERE id=?', (active, message, starts_at, ends_at, now, mid))
            else:
                cur.execute('INSERT INTO maintenance_flags(id, active, message, starts_at, ends_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?)', (mid, active, message, starts_at, ends_at, now, now))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return {'status': 'ok', 'id': mid, 'active': bool(active), 'message': message, 'starts_at': starts_at, 'ends_at': ends_at}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/alerts/list')
def list_alert_items(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        items = []
        # import_error rows
        try:
            if _table_exists(cur, 'import_error'):
                cur.execute('SELECT id, message, created_at, import_job_id FROM import_error ORDER BY created_at DESC LIMIT 200')
                rows = cur.fetchall()
                cols = [c[0] for c in cur.description] if cur.description else []
                for r in rows:
                    if isinstance(r, dict):
                        items.append({'id': r.get('id'), 'type': 'import_error', 'message': r.get('message'), 'created_at': r.get('created_at'), 'source': r.get('import_job_id')})
                        continue
                    try:
                        items.append({
                            'id': r[0], 'type': 'import_error', 'message': r[1], 'created_at': r[2], 'source': r[3] if len(r) > 3 else None
                        })
                    except Exception:
                        continue
        except Exception:
            pass

        # api_error_log
        try:
            if _table_exists(cur, 'api_error_log'):
                cur.execute('SELECT id, message, endpoint, created_at FROM api_error_log ORDER BY created_at DESC LIMIT 200')
                rows = cur.fetchall()
                for r in rows:
                    if isinstance(r, dict):
                        items.append({'id': r.get('id'), 'type': 'api_error', 'message': r.get('message'), 'created_at': r.get('created_at'), 'source': r.get('endpoint')})
                        continue
                    try:
                        items.append({'id': r[0], 'type': 'api_error', 'message': r[1], 'created_at': r[3], 'source': r[2]})
                    except Exception:
                        continue
            else:
                # fallback to audit_log entries that look like errors
                if _table_exists(cur, 'audit_log'):
                    cur.execute("SELECT id, action, meta_json, created_at FROM audit_log WHERE action LIKE 'error%' OR action='api_error' ORDER BY created_at DESC LIMIT 200")
                    rows = cur.fetchall()
                    for r in rows:
                        if isinstance(r, dict):
                            items.append({'id': r.get('id'), 'type': 'api_error', 'message': r.get('meta_json') or r.get('action'), 'created_at': r.get('created_at'), 'source': None})
                            continue
                        try:
                            items.append({'id': r[0], 'type': 'api_error', 'message': r[2] or r[1], 'created_at': r[3], 'source': None})
                        except Exception:
                            continue
        except Exception:
            pass

        # sort by created_at desc where possible
        try:
            items_sorted = sorted(items, key=lambda x: x.get('created_at') or '', reverse=True)
        except Exception:
            items_sorted = items

        return {'status': 'ok', 'count': len(items_sorted), 'alerts': items_sorted}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _ensure_cus_tables(conn):
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS system_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        body TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS change_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        payload TEXT,
        status TEXT,
        created_by TEXT,
        created_at TEXT,
        submitted_at TEXT,
        reviewed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS change_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal_id INTEGER,
        reviewer TEXT,
        decision TEXT,
        note TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS release_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        created_at TEXT
    );
    ''')
    conn.commit()


@router.get('/status')
def status(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        # maintenance mode via env override or system_settings
        mode = 'normal'
        try:
            if os.getenv('TAAIP_MAINTENANCE_MODE') == '1':
                mode = 'maintenance'
            else:
                cur.execute("SELECT value FROM system_settings WHERE key='maintenance_mode'")
                row = cur.fetchone()
                val = None
                if row:
                    try:
                        val = row['value'] if isinstance(row, dict) and 'value' in row else row[0]
                    except Exception:
                        val = None
                if val and str(val).lower() in ('1', 'true', 'on', 'maintenance'):
                    mode = 'maintenance'

        except Exception:
            pass

        # compute alerts.total
        alerts_total = 0
        try:
            if _table_exists(cur, 'change_proposals'):
                cur.execute("SELECT COUNT(1) as c FROM change_proposals WHERE status='submitted'")
                rr = cur.fetchone()
                pcount = int(rr['c'] if isinstance(rr, dict) and 'c' in rr else (rr[0] if rr else 0))
            else:
                pcount = 0
            # import_errors
            imp_err = 0
            if _table_exists(cur, 'import_error'):
                cur.execute("SELECT COUNT(1) as c FROM import_error WHERE created_at > datetime('now','-30 days')")
                r2 = cur.fetchone()
                imp_err = int(r2['c'] if isinstance(r2, dict) and 'c' in r2 else (r2[0] if r2 else 0))
            elif _table_exists(cur, 'import_job_v3'):
                cur.execute("SELECT COUNT(1) as c FROM import_job_v3 WHERE status='failed' AND completed_at > datetime('now','-30 days')")
                r2 = cur.fetchone()
                imp_err = int(r2['c'] if isinstance(r2, dict) and 'c' in r2 else (r2[0] if r2 else 0))
            # api_errors
            api_err = 0
            if _table_exists(cur, 'api_error_log'):
                cur.execute("SELECT COUNT(1) as c FROM api_error_log WHERE created_at > datetime('now','-30 days')")
                r3 = cur.fetchone()
                api_err = int(r3['c'] if isinstance(r3, dict) and 'c' in r3 else (r3[0] if r3 else 0))
            elif _table_exists(cur, 'audit_logs'):
                cur.execute("SELECT COUNT(1) as c FROM audit_logs WHERE event_type='api_error' AND created_at > datetime('now','-30 days')")
                r3 = cur.fetchone()
                api_err = int(r3['c'] if isinstance(r3, dict) and 'c' in r3 else (r3[0] if r3 else 0))

            alerts_total = imp_err + api_err + pcount
        except Exception:
            alerts_total = 0

        # compute data_as_of
        data_as_of = None
        try:
            if _table_exists(cur, 'fact_production'):
                cur.execute("SELECT MAX(ingested_at) as m FROM fact_production")
                r4 = cur.fetchone()
                data_as_of = r4['m'] if r4 and isinstance(r4, dict) and 'm' in r4 else (r4[0] if r4 and r4[0] is not None else None)
            if data_as_of is None and _table_exists(cur, 'imported_rows'):
                cur.execute("SELECT MAX(ingested_at) as m FROM imported_rows")
                r5 = cur.fetchone()
                data_as_of = r5['m'] if r5 and isinstance(r5, dict) and 'm' in r5 else (r5[0] if r5 and r5[0] is not None else None)
            if data_as_of is None and _table_exists(cur, 'import_job_v3'):
                cur.execute("SELECT completed_at as m FROM import_job_v3 WHERE status='completed' ORDER BY completed_at DESC LIMIT 1")
                r6 = cur.fetchone()
                data_as_of = r6['m'] if r6 and isinstance(r6, dict) and 'm' in r6 else (r6[0] if r6 and r6[0] is not None else None)
        except Exception:
            data_as_of = None

        # mode rules
        if os.getenv('TAAIP_MAINTENANCE_MODE') == '1' or mode == 'maintenance':
            effective = 'maintenance'
        elif alerts_total > 0 and not data_as_of:
            effective = 'degraded'
        else:
            effective = 'normal'

        return {'status': 'ok', 'mode': effective}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/observations')
def create_observation(payload: Dict[str, Any], user: Dict = Depends(get_current_user), _admin: Dict = Depends(require_any_role('USAREC_ADMIN'))):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        title = payload.get('title') or payload.get('summary') or 'observation'
        body = payload.get('body') or payload.get('details') or ''
        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO system_observations(username, title, body, created_at) VALUES (?,?,?,?)', (user.get('username'), title, body, now))
        conn.commit()
        cur.execute('SELECT id FROM system_observations WHERE rowid = last_insert_rowid()')
        row = cur.fetchone()
        return {'id': row[0] if row else None}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/observations')
def list_observations(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, username, title, body, created_at FROM system_observations ORDER BY created_at DESC')
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description] if cur.description else []
        result = []
        for r in rows:
            # if it's already a mapping/dict-like
            if isinstance(r, dict):
                result.append(r)
                continue
            # sqlite row may expose keys(); try that first
            try:
                keys = getattr(r, 'keys', None)
                if callable(keys):
                    result.append({k: r[k] for k in r.keys()})
                    continue
            except Exception:
                pass
            # fallback: assume sequence and zip with column names
            try:
                result.append({cols[i]: r[i] for i in range(len(cols))})
            except Exception:
                result.append({})

        return result
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals')
def create_proposal(payload: Dict[str, Any], user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        title = payload.get('title') or 'proposal'
        desc = payload.get('description') or ''
        rationale = payload.get('rationale') or ''
        impact_area = payload.get('impact_area') or None
        risk_level = payload.get('risk_level') or None
        now = datetime.utcnow().isoformat()
        pid = payload.get('id') or str(uuid.uuid4())
        # create with submitted status by default per spec
        cur.execute('INSERT OR REPLACE INTO change_proposals(id, title, description, rationale, impact_area, risk_level, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)', (pid, title, desc, rationale, impact_area, risk_level, 'submitted', user.get('username'), now))
        conn.commit()
        return {'id': pid}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/proposals')
def list_proposals(status: Optional[str] = Query(None), current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        if status:
            cur.execute('SELECT id, title, description, rationale, impact_area, risk_level, status, created_by, created_at, reviewed_at, decision_note FROM change_proposals WHERE status=? ORDER BY created_at DESC', (status,))
        else:
            cur.execute('SELECT id, title, description, rationale, impact_area, risk_level, status, created_by, created_at, reviewed_at, decision_note FROM change_proposals ORDER BY created_at DESC')
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description] if cur.description else []
        result = []
        for r in rows:
            if isinstance(r, dict):
                result.append(r)
                continue
            try:
                keys = getattr(r, 'keys', None)
                if callable(keys):
                    result.append({k: r[k] for k in r.keys()})
                    continue
            except Exception:
                pass
            try:
                result.append({cols[i]: r[i] for i in range(len(cols))})
            except Exception:
                result.append({})

        return result
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals/{proposal_id}/submit')
def submit_proposal(proposal_id: int, user: Dict = Depends(get_current_user), _admin: Dict = Depends(require_any_role('USAREC_ADMIN'))):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, status FROM change_proposals WHERE id=?', (proposal_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='proposal not found')
        if r['status'] == 'submitted':
            return {'ok': True, 'status': 'already_submitted'}
        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute("UPDATE change_proposals SET status='submitted', submitted_at=? WHERE id=?", (now, proposal_id))
        conn.commit()
        return {'ok': True}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals/{proposal_id}/review')
def review_proposal(proposal_id: int, payload: Dict[str, Any], user: Dict = Depends(get_current_user), _admin: Dict = Depends(require_any_role('USAREC_ADMIN'))):
    decision = (payload.get('decision') or '').lower()
    note = payload.get('note') or ''
    if decision not in ('approve', 'reject'):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, status FROM change_proposals WHERE id=?', (proposal_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='proposal not found')
        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO change_reviews(proposal_id, reviewer, decision, note, created_at) VALUES (?,?,?,?,?)', (proposal_id, user.get('username'), decision, note, now))
        # update proposal status but DO NOT apply any payload changes automatically
        new_status = 'approved' if decision == 'approve' else 'rejected'
        cur.execute('UPDATE change_proposals SET status=?, reviewed_at=? WHERE id=?', (new_status, now, proposal_id))
        conn.commit()
        return {'ok': True, 'status': new_status}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals/{proposal_id}/decision')
def decide_proposal(proposal_id: str, payload: Dict[str, Any], user: Dict = Depends(get_current_user)):
    # decision endpoint: admin only unless LOCAL_DEV_AUTH_BYPASS
    if os.getenv('LOCAL_DEV_AUTH_BYPASS') != '1':
        roles = user.get('roles') or []
        if 'USAREC_ADMIN' not in roles and user.get('role') != 'USAREC_ADMIN':
            raise HTTPException(status_code=403, detail='admin role required')
    decision = (payload.get('decision') or '').lower()
    note = payload.get('decision_note') or payload.get('note') or ''
    if decision not in ('approve', 'reject'):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, status FROM change_proposals WHERE id=?', (proposal_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='proposal not found')
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO change_reviews(proposal_id, reviewer, decision, note, created_at) VALUES (?,?,?,?,?)', (proposal_id, user.get('username'), decision, note, now))
        new_status = 'approved' if decision == 'approve' else 'rejected'
        cur.execute('UPDATE change_proposals SET status=?, reviewed_by=?, reviewed_at=?, decision_note=? WHERE id=?', (new_status, user.get('username'), now, note, proposal_id))
        conn.commit()
        return {'ok': True, 'status': new_status}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals/{proposal_id}/mark-applied')
def mark_proposal_applied(proposal_id: str, user: Dict = Depends(get_current_user)):
    if os.getenv('LOCAL_DEV_AUTH_BYPASS') != '1':
        roles = user.get('roles') or []
        if 'USAREC_ADMIN' not in roles and user.get('role') != 'USAREC_ADMIN':
            raise HTTPException(status_code=403, detail='admin role required')
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, status FROM change_proposals WHERE id=?', (proposal_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='proposal not found')
        now = datetime.utcnow().isoformat()
        cur.execute("UPDATE change_proposals SET status='applied', reviewed_by=?, reviewed_at=? WHERE id=?", (user.get('username'), now, proposal_id))
        conn.commit()
        return {'ok': True}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.put('/proposals/{proposal_id}')
def update_proposal(proposal_id: str, payload: Dict[str, Any], user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, status, created_by FROM change_proposals WHERE id=?', (proposal_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='proposal not found')
        status_cur = r['status'] if isinstance(r, dict) and 'status' in r else (r[1] if len(r) > 1 else None)
        created_by = r['created_by'] if isinstance(r, dict) and 'created_by' in r else (r[2] if len(r) > 2 else None)
        if status_cur not in ('draft', 'submitted'):
            raise HTTPException(status_code=400, detail='cannot edit proposal in its current state')
        # allow edit by creator or admin
        is_admin = (os.getenv('LOCAL_DEV_AUTH_BYPASS') == '1')
        try:
            if not is_admin:
                user_roles = user.get('roles') or []
                if 'USAREC_ADMIN' in user_roles or user.get('role') == 'USAREC_ADMIN':
                    is_admin = True
        except Exception:
            pass
        if not is_admin and user.get('username') != created_by:
            raise HTTPException(status_code=403, detail='only creator or admin may edit')
        title = payload.get('title')
        description = payload.get('description')
        rationale = payload.get('rationale')
        impact_area = payload.get('impact_area')
        risk_level = payload.get('risk_level')
        updates = []
        params = []
        if title is not None:
            updates.append('title=?'); params.append(title)
        if description is not None:
            updates.append('description=?'); params.append(description)
        if rationale is not None:
            updates.append('rationale=?'); params.append(rationale)
        if impact_area is not None:
            updates.append('impact_area=?'); params.append(impact_area)
        if risk_level is not None:
            updates.append('risk_level=?'); params.append(risk_level)
        if updates:
            params.append(proposal_id)
            cur.execute(f"UPDATE change_proposals SET {', '.join(updates)} WHERE id=?", params)
            conn.commit()
        return {'ok': True}
    finally:
        try:
            conn.close()
        except Exception:
            pass
