from fastapi import APIRouter
from typing import Dict, Any, List
from ..db import connect

router = APIRouter(prefix="/dash/performance", tags=["performance"])


@router.get('/dashboard')
def performance_dashboard(fy: int = None, qtr: int = None, org_unit_id: int = None, station_id: str = None) -> Dict[str, Any]:
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

        # top metrics: sum of fact_production metrics for the period
        try:
            sql = 'SELECT metric_key, SUM(metric_value) as total FROM fact_production WHERE 1=1'
            params = []
            if fy is not None or qtr is not None:
                # best-effort: match dim_time via date_key prefix when fy/qtr present
                pass
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            sql += ' GROUP BY metric_key ORDER BY total DESC LIMIT 20'
            cur.execute(sql, tuple(params))
            top_metrics = [{'metric_key': r.get('metric_key'), 'total': float(r.get('total') or 0)} for r in cur.fetchall()]
        except Exception:
            top_metrics = []

        # funnel summary: aggregated counts from fact_funnel
        funnel = []
        try:
            sqlf = 'SELECT stage, SUM(count_value) as c FROM fact_funnel WHERE 1=1'
            pf = []
            if org_unit_id is not None:
                sqlf += ' AND org_unit_id=?'; pf.append(org_unit_id)
            sqlf += ' GROUP BY stage ORDER BY c DESC'
            cur.execute(sqlf, tuple(pf))
            for r in cur.fetchall():
                funnel.append({'stage': r.get('stage'), 'count': int(r.get('c') or 0)})
        except Exception:
            funnel = []

        # priorities: top 3 command priorities
        priorities = []
        try:
            cur.execute('SELECT id, title, description, rank FROM command_priorities ORDER BY rank ASC LIMIT 3')
            for r in cur.fetchall():
                priorities.append({'id': r.get('id'), 'title': r.get('title'), 'description': r.get('description'), 'rank': r.get('rank')})
        except Exception:
            priorities = []

        # loes: top 5 LOEs
        loes = []
        try:
            cur.execute('SELECT id, name, description, fy, qtr FROM loe ORDER BY created_at DESC LIMIT 5')
            for r in cur.fetchall():
                loes.append({'id': r.get('id'), 'name': r.get('name'), 'description': r.get('description'), 'fy': r.get('fy'), 'qtr': r.get('qtr')})
        except Exception:
            loes = []

        # metrics comparison: compare latest two mission_assessments if available
        metrics_comparison = []
        try:
            import json
            cur.execute('SELECT metrics_json, created_at FROM mission_assessments ORDER BY updated_at DESC LIMIT 2')
            rows = cur.fetchall()
            if rows and len(rows) >= 1:
                latest = rows[0]
                latest_metrics = None
                try:
                    latest_metrics = json.loads(latest.get('metrics_json') or '{}')
                except Exception:
                    latest_metrics = {}
                baseline = None
                if len(rows) > 1:
                    try:
                        baseline = json.loads(rows[1].get('metrics_json') or '{}')
                    except Exception:
                        baseline = {}
                metrics_comparison = [{'baseline': baseline, 'actual': latest_metrics}]
        except Exception:
            metrics_comparison = []

        # missing data hints
        missing_data = []
        try:
            cur.execute('SELECT COUNT(1) as c FROM mission_assessments')
            r = cur.fetchone(); if_ma = int(r.get('c') or 0)
            if if_ma == 0:
                missing_data.append('No mission assessments present')
        except Exception:
            missing_data.append('mission_assessments table missing')
        try:
            cur.execute('SELECT COUNT(1) as c FROM projects')
            r = cur.fetchone(); if_p = int(r.get('c') or 0)
            if if_p == 0:
                missing_data.append('No projects present')
        except Exception:
            missing_data.append('projects table missing')

        return {
            'filters': filters,
            'top_metrics': top_metrics,
            'funnel': funnel,
            'priorities': priorities,
            'loes': loes,
            'metrics_comparison': metrics_comparison,
            'missing_data': missing_data
        }
        
    finally:
        try:
            conn.close()
        except Exception:
            pass
