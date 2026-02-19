from fastapi import APIRouter
from typing import Dict, Any, List
from ..db import connect

router = APIRouter(prefix="/dash/projects", tags=["projects"])


@router.get('/dashboard')
def projects_dashboard(fy: int = None, qtr: int = None, org_unit_id: int = None, station_id: str = None, funding_line: str = None) -> Dict[str, Any]:
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
            sql = 'SELECT COUNT(1) as c, SUM(COALESCE(planned_cost,0)) as planned, SUM(COALESCE(percent_complete,0)) as pct FROM projects WHERE 1=1'
            params = []
            if fy is not None:
                sql += ' AND fy=?'; params.append(fy)
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            if funding_line is not None:
                sql += ' AND funding_line=?'; params.append(funding_line)
            cur.execute(sql, tuple(params))
            r = cur.fetchone()
            total_projects = int(r['c'] or 0)
            total_planned_cost = float(r['planned'] or 0)
            avg_pct = float(r['pct'] or 0)
        except Exception:
            total_projects = 0; total_planned_cost = 0.0; avg_pct = 0.0

        # by_status
        by_status = []
        try:
            sql_s = 'SELECT status, COUNT(1) as c FROM projects WHERE 1=1'
            p = []
            if fy is not None:
                sql_s += ' AND fy=?'; p.append(fy)
            if org_unit_id is not None:
                sql_s += ' AND org_unit_id=?'; p.append(org_unit_id)
            sql_s += ' GROUP BY status'
            cur.execute(sql_s, tuple(p))
            for row in cur.fetchall():
                by_status.append({'status': row.get('status'), 'count': int(row.get('c') or 0)})
        except Exception:
            by_status = []

        # projects list with financial rollups (planned, actual_spent, pending, variance)
        projects = []
        try:
            cur.execute('SELECT project_id, title, COALESCE(planned_cost,0) as planned FROM projects ORDER BY updated_at DESC')
            rows = cur.fetchall()
            if not rows:
                # fallback: try without relying on updated_at ordering or fy filter
                cur.execute('SELECT project_id, title, COALESCE(planned_cost,0) as planned FROM projects')
                rows = cur.fetchall()
            for r in rows:
                pid = r.get('project_id')
                title = r.get('title')
                planned_cost = float(r.get('planned') or 0)
                cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses WHERE project_id=?', (pid,))
                rr = cur.fetchone(); actual_spent = float(rr['s']) if rr and rr.get('s') is not None else 0.0
                pending = max(planned_cost - actual_spent, 0.0)
                variance = planned_cost - actual_spent
                projects.append({'project_id': pid, 'title': title, 'planned_cost': planned_cost, 'actual_spent': actual_spent, 'pending': pending, 'variance': variance})
        except Exception:
            projects = []

        return {'filters': filters, 'totals': {'count': total_projects, 'planned_cost': total_planned_cost, 'avg_percent_complete': avg_pct}, 'by_status': by_status, 'projects': projects}
    finally:
        try:
            conn.close()
        except Exception:
            pass
