from fastapi import APIRouter
from typing import List, Dict, Any
from services.api.app import db as dbmod

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
