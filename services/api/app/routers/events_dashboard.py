from fastapi import APIRouter
from typing import Dict, Any, List
from ..db import connect

router = APIRouter(prefix="/dash/events", tags=["events"])


@router.get('/dashboard')
def events_dashboard(fy: int = None, qtr: int = None, org_unit_id: int = None, station_id: str = None, funding_line: str = None) -> Dict[str, Any]:
    conn = connect()
    try:
        cur = conn.cursor()
        filters = {}
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
            sql = 'SELECT COUNT(1) as c, SUM(COALESCE(planned_cost,0)) as planned, SUM(COALESCE(loe,0)) as loe_total FROM event WHERE 1=1'
            params = []
            if fy is not None:
                sql += ' AND fy=?'; params.append(fy)
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            cur.execute(sql, tuple(params))
            r = cur.fetchone()
            total_events = int(r['c'] or 0)
            total_planned_cost = float(r['planned'] or 0)
            total_loe = float(r['loe_total'] or 0)
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
            cur.execute('SELECT id as event_id, name, event_type, COALESCE(planned_cost,0) as planned, loe, project_id FROM event ORDER BY start_dt DESC')
            rows = cur.fetchall()
            if not rows:
                cur.execute('SELECT id as event_id, name, event_type, COALESCE(planned_cost,0) as planned, loe, project_id FROM event')
                rows = cur.fetchall()
            for r in rows:
                eid = r.get('event_id')
                name = r.get('name')
                planned_cost = float(r.get('planned') or 0)
                loe_val = float(r.get('loe') or 0)
                proj_id = r.get('project_id')
                cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses WHERE event_id=?', (eid,))
                rr = cur.fetchone(); actual_spent = float(rr['s']) if rr and rr.get('s') is not None else 0.0
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
        except Exception:
            events = []

        return {'filters': filters, 'totals': {'count': total_events, 'planned_cost': total_planned_cost, 'total_loe': total_loe}, 'by_type': by_type, 'events': events}
    finally:
        try:
            conn.close()
        except Exception:
            pass
