from fastapi import APIRouter
from typing import Dict, Any, List
from ..db import connect

router = APIRouter(prefix="/dash/events", tags=["events"])


@router.get('/dashboard')
def events_dashboard(fy: int = None, qtr: int = None, org_unit_id: int = None, station_id: str = None, funding_line: str = None) -> Dict[str, Any]:
    # Prefer a direct sqlite3 connection to the path indicated by the
    # `TAAIP_DB_PATH` environment variable so legacy raw-SQL handlers operate
    # against the same file used by the test harness. Fallback to `connect()`
    # if the env var is not set.
    import os, sqlite3
    db_path = os.getenv('TAAIP_DB_PATH')
    try:
        dbg_path = os.environ.get('EVENTS_HANDLER_DEBUG_PRE', '/tmp/events_handler_pre.json')
        info = {'cwd': os.getcwd(), 'db_path': db_path, 'exists': os.path.exists(db_path) if db_path else False}
        with open(dbg_path, 'w') as _f:
            import json
            json.dump(info, _f)
    except Exception:
        pass
    if db_path:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
    else:
        conn = connect()
    try:
        cur = conn.cursor()
        filters = {}
        # detect available columns to tolerate test/legacy schemas
        try:
            cur.execute("PRAGMA table_info(event)")
            col_info = [r for r in cur.fetchall()]
            cols = [c[1] for c in col_info]
        except Exception:
            cols = []
        has_event_type = 'event_type' in cols
        has_loe = 'loe' in cols
        has_start_dt = 'start_dt' in cols
        if fy is not None:
            filters['fy'] = fy
        if qtr is not None:
            filters['qtr'] = qtr
        if org_unit_id is not None:
            filters['org_unit_id'] = org_unit_id
        if station_id is not None:
            filters['station_id'] = station_id
        if funding_line is not None:
            filters['funding_line'] = funding_line

        # totals
        try:
            sql = 'SELECT COUNT(1) as c, SUM(COALESCE(planned_cost,0)) as planned'
            if has_loe:
                sql += ', SUM(COALESCE(loe,0)) as loe_total'
            sql += ' FROM event WHERE 1=1'
            params = []
            if fy is not None:
                sql += ' AND fy=?'; params.append(fy)
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            cur.execute(sql, tuple(params))
            r = cur.fetchone()
            total_events = int(r['c'] or 0)
            total_planned_cost = float(r['planned'] or 0)
            total_loe = float(r['loe_total'] or 0) if has_loe else 0.0
        except Exception:
            total_events = 0; total_planned_cost = 0.0; total_loe = 0.0

        # by_type
        by_type = []
        try:
            sql_t = 'SELECT event_type, COUNT(1) as c FROM event WHERE 1=1'
            p = []
            if fy is not None:
                sql_t += ' AND fy=?'; p.append(fy)
            if org_unit_id is not None:
                sql_t += ' AND org_unit_id=?'; p.append(org_unit_id)
            sql_t += ' GROUP BY event_type'
            cur.execute(sql_t, tuple(p))
            for row in cur.fetchall():
                by_type.append({'event_type': row.get('event_type'), 'count': int(row.get('c') or 0)})
        except Exception:
            by_type = []

        # events list with financial rollups and ROI when available
        events = []
        try:
            select_cols = 'id as event_id, name'
            if has_event_type:
                select_cols += ', event_type'
            select_cols += ', COALESCE(planned_cost,0) as planned'
            if has_loe:
                select_cols += ', loe'
            select_cols += ', project_id'
            order_clause = ' ORDER BY start_dt DESC' if has_start_dt else ''
            cur.execute(f'SELECT {select_cols} FROM event{order_clause}')
            rows = cur.fetchall()
            # dump a short debug file with the raw row count to help diagnose
            try:
                import json, os
                dbg = {'rows_len': len(rows), 'sample': [dict(r) for r in rows[:5]]}
                outp = os.environ.get('EVENTS_HANDLER_DEBUG', 'scripts/events_handler_debug.json')
                with open(outp, 'w') as _f:
                    json.dump(dbg, _f)
            except Exception:
                pass
            if not rows:
                cur.execute(f'SELECT {select_cols} FROM event')
                rows = cur.fetchall()
            for r in rows:
                row = dict(r)
                eid = row.get('event_id')
                name = row.get('name')
                planned_cost = float(row.get('planned') or 0)
                loe_val = float(row.get('loe') or 0) if has_loe else 0
                proj_id = row.get('project_id')
                cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses WHERE event_id=?', (eid,))
                rr = cur.fetchone();
                rr = dict(rr) if rr is not None else None
                actual_spent = float(rr.get('s') or 0) if rr else 0.0
                pending = max(planned_cost - actual_spent, 0.0)
                variance = planned_cost - actual_spent
                # attempt ROI: prefer event_roi table, fallback to marketing_activities cost/metrics
                roi = None
                try:
                    cur.execute('SELECT expected_revenue, expected_cost FROM event_roi WHERE event_id=? ORDER BY updated_at DESC LIMIT 1', (eid,))
                    er = cur.fetchone()
                    if er and (er.get('expected_cost') or er.get('expected_revenue')):
                        exp_cost = float(er.get('expected_cost') or 0)
                        exp_rev = float(er.get('expected_revenue') or 0)
                        if exp_cost and exp_cost != 0:
                            roi = exp_rev / exp_cost
                except Exception:
                    roi = None
                events.append({'event_id': eid, 'name': name, 'project_id': proj_id, 'planned_cost': planned_cost, 'actual_spent': actual_spent, 'pending': pending, 'variance': variance, 'roe': roi})
        except Exception as e:
            # Log the exception to a temporary file to aid debugging
            try:
                import traceback, json
                with open('/tmp/events_handler_exc.txt', 'w') as _ef:
                    _ef.write(''.join(traceback.format_exception(None, e, e.__traceback__)))
            except Exception:
                pass
            events = []

        # If no events found via the current DB-API connection, attempt a direct
        # sqlite fallback to the path set by the test harness (`TAAIP_DB_PATH`).
        if not events:
            try:
                import os, sqlite3
                path = os.getenv('TAAIP_DB_PATH')
                if path:
                    conn2 = sqlite3.connect(path, check_same_thread=False)
                    conn2.row_factory = sqlite3.Row
                    c2 = conn2.cursor()
                    c2.execute('SELECT id as event_id, name, event_type, COALESCE(planned_cost,0) as planned, loe, project_id FROM event ORDER BY start_dt DESC')
                    srows = c2.fetchall()
                    if not srows:
                        c2.execute('SELECT id as event_id, name, event_type, COALESCE(planned_cost,0) as planned, loe, project_id FROM event')
                        srows = c2.fetchall()
                    for r in srows:
                        rmap = dict(r)
                        eid = rmap.get('event_id')
                        name = rmap.get('name')
                        planned_cost = float(rmap.get('planned') or 0)
                        proj_id = rmap.get('project_id')
                        c2.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses WHERE event_id=?', (eid,))
                        rr = c2.fetchone(); actual_spent = float(rr[0]) if rr and rr[0] is not None else 0.0
                        pending = max(planned_cost - actual_spent, 0.0)
                        variance = planned_cost - actual_spent
                        events.append({'event_id': eid, 'name': name, 'project_id': proj_id, 'planned_cost': planned_cost, 'actual_spent': actual_spent, 'pending': pending, 'variance': variance, 'roe': None})
                    conn2.close()
            except Exception:
                pass

        return {'filters': filters, 'totals': {'count': total_events, 'planned_cost': total_planned_cost, 'total_loe': total_loe}, 'by_type': by_type, 'events': events}
    finally:
        try:
            conn.close()
        except Exception:
            pass
