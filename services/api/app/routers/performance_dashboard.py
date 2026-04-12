from fastapi import APIRouter
from typing import Dict, Any, List
from ..db import connect
import os

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
            r = cur.fetchone()
            try:
                if_ma = int(r.get('c') or 0) if isinstance(r, dict) else int(r[0] or 0)
            except Exception:
                if_ma = 0
            if if_ma == 0:
                missing_data.append('No mission assessments present')
        except Exception:
            missing_data.append('mission_assessments table missing')
        try:
            cur.execute('SELECT COUNT(1) as c FROM projects')
            r = cur.fetchone()
            try:
                if_p = int(r.get('c') or 0) if isinstance(r, dict) else int(r[0] or 0)
            except Exception:
                if_p = 0
            if if_p == 0:
                missing_data.append('No projects present')
        except Exception:
            missing_data.append('projects table missing')

        # build conversion_trend (last 12 date_keys if available)
        conversion_trend = []
        try:
            cur.execute("SELECT date_key, SUM(CASE WHEN metric_key='leads' THEN metric_value ELSE 0 END) as leads, SUM(CASE WHEN metric_key='contracts' THEN metric_value ELSE 0 END) as contracts FROM fact_production WHERE 1=1 GROUP BY date_key ORDER BY date_key DESC LIMIT 12")
            rows = cur.fetchall()
            # rows are latest-first; reverse for chronological order
            for r in reversed(rows):
                leads = float(r.get('leads') or 0)
                contracts = float(r.get('contracts') or 0)
                pct = round((contracts / leads * 100), 1) if leads else None
                conversion_trend.append({'period': r.get('date_key'), 'leads': int(leads), 'contracts': int(contracts), 'conversion_pct': pct})
        except Exception:
            conversion_trend = []

        # fallback: use fact_funnel_daily if present
        if not conversion_trend:
            try:
                cur.execute("PRAGMA table_info(fact_funnel_daily)")
                if cur.fetchall():
                    cur.execute("SELECT date_key, SUM(COALESCE(count,0)) as leads FROM fact_funnel_daily GROUP BY date_key ORDER BY date_key DESC LIMIT 12")
                    rows = cur.fetchall()
                    for r in reversed(rows):
                        leads = int(r.get('leads') or 0)
                        conversion_trend.append({'period': r.get('date_key'), 'leads': leads, 'contracts': 0, 'conversion_pct': None})
            except Exception:
                pass

        # build stations ranking: aggregate by org_unit/dim_org_unit.name
        stations = []
        try:
            cur.execute("SELECT fp.org_unit_id as org_id, d.name as name, SUM(CASE WHEN fp.metric_key='leads' THEN fp.metric_value ELSE 0 END) as leads, SUM(CASE WHEN fp.metric_key='contracts' THEN fp.metric_value ELSE 0 END) as contracts FROM fact_production fp LEFT JOIN dim_org_unit d ON d.id = fp.org_unit_id WHERE 1=1 GROUP BY fp.org_unit_id ORDER BY contracts DESC LIMIT 10")
            for r in cur.fetchall():
                leads = float(r.get('leads') or 0)
                contracts = float(r.get('contracts') or 0)
                pct = round((contracts / leads * 100), 1) if leads else None
                stations.append({'name': r.get('name') or str(r.get('org_id')), 'leads': int(leads), 'contracts': int(contracts), 'conversion_pct': pct})
        except Exception:
            stations = []

        # fallback: derive top stations from `leads` table grouped by school_id
        # NOTE: disabled by default to prevent demo/simulated leads from affecting live dashboards
        if not stations:
            if os.getenv('ALLOW_LEAD_FALLBACK') == '1':
                try:
                    cur.execute("PRAGMA table_info(leads)")
                    if cur.fetchall():
                        cur.execute("SELECT school_id, COUNT(1) as c FROM leads WHERE school_id IS NOT NULL GROUP BY school_id ORDER BY c DESC LIMIT 10")
                        for r in cur.fetchall():
                            sid = r[0]
                            cnt = int(r[1] or 0)
                            # try to resolve school name
                            name = None
                            try:
                                cur.execute('SELECT name FROM schools WHERE school_id=?', (sid,))
                                rr = cur.fetchone()
                                if rr:
                                    name = rr.get('name')
                            except Exception:
                                name = None
                            stations.append({'name': name or str(sid), 'leads': cnt, 'contracts': 0, 'conversion_pct': None})
                except Exception:
                    pass

        # metrics: echo top_metrics into simpler metric array for frontend convenience
        metrics = []
        try:
            for m in top_metrics:
                metrics.append({'metric_key': m.get('metric_key'), 'metric_value': m.get('total')})
        except Exception:
            metrics = []

        return {
            'filters': filters,
            'top_metrics': top_metrics,
            'funnel': funnel,
            'priorities': priorities,
            'loes': loes,
            'metrics_comparison': metrics_comparison,
            'missing_data': missing_data,
            'conversion_trend': conversion_trend,
            'stations': stations,
            'metrics': metrics
        }
        
    finally:
        try:
            conn.close()
        except Exception:
            pass
