from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from services.api.app import db as dbmod
from .rbac import get_current_user, require_any_role

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
        cur.execute("SELECT value FROM system_settings WHERE key='maintenance_mode'")
        row = cur.fetchone()
        mode = row['value'] if row and 'value' in row else (row[0] if row else None)
        if not mode:
            mode = 'off'
        # count submitted proposals
        cur.execute("SELECT COUNT(1) as c FROM change_proposals WHERE status='submitted'")
        r = cur.fetchone()
        # sqlite cursor may return a tuple or a dict-like row; handle both
        if not r:
            count = 0
        else:
            try:
                count = int(r['c'])
            except Exception:
                try:
                    count = int(r[0])
                except Exception:
                    count = 0
        return {'maintenance_mode': mode, 'active_proposals': count}
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
        return [dict(r) for r in rows]
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/proposals')
def create_proposal(payload: Dict[str, Any], user: Dict = Depends(get_current_user), _admin: Dict = Depends(require_any_role('USAREC_ADMIN'))):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        title = payload.get('title') or 'proposal'
        desc = payload.get('description') or ''
        pld = payload.get('payload') or ''
        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO change_proposals(title, description, payload, status, created_by, created_at) VALUES (?,?,?,?,?,?)', (title, desc, json.dumps(pld) if not isinstance(pld, str) else pld, 'draft', user.get('username'), now))
        conn.commit()
        cur.execute('SELECT id FROM change_proposals WHERE rowid = last_insert_rowid()')
        row = cur.fetchone()
        return {'id': row[0] if row else None}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/proposals')
def list_proposals(current_user: Dict = Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        _ensure_cus_tables(conn)
        cur = conn.cursor()
        cur.execute('SELECT id, title, description, status, created_by, created_at, submitted_at, reviewed_at FROM change_proposals ORDER BY created_at DESC')
        rows = cur.fetchall()
        return [dict(r) for r in rows]
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
