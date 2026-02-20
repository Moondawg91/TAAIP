from fastapi import APIRouter, Depends
from typing import Dict, Any
from services.api.app import db as dbmod
from .rbac import get_current_user

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def _empty_rollup(name: str) -> Dict[str, Any]:
    return {
        'status': 'ok',
        'dashboard': name,
        'data': {
            'kpis': {},
            'breakdowns': [],
            'trends': [],
            'missing_data': []
        }
    }


def _table_exists(cur, name: str) -> bool:
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False


@router.get('/budget')
def budget_dashboard(current_user: Dict = Depends(get_current_user)):
    """Return a canonical budget rollup: kpis (allocated/obligated/expended), breakdowns by funding_line, trends by fy/qtr."""
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        out = _empty_rollup('budget')
        try:
            if not _table_exists(cur, 'budget_line_item'):
                return out

            # KPIs
            cur.execute("SELECT COALESCE(SUM(allocated_amount),0) as allocated, COALESCE(SUM(obligated_amount),0) as obligated, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item")
            r = cur.fetchone()
            allocated = float(r['allocated'] if isinstance(r, dict) and 'allocated' in r else (r[0] if r and r[0] is not None else 0))
            obligated = float(r['obligated'] if isinstance(r, dict) and 'obligated' in r else (r[1] if r and r[1] is not None else 0))
            expended = float(r['expended'] if isinstance(r, dict) and 'expended' in r else (r[2] if r and r[2] is not None else 0))
            out['data']['kpis'] = {'allocated': allocated, 'obligated': obligated, 'expended': expended, 'remaining': allocated - expended}

            # Breakdown by funding_line
            try:
                cur.execute("SELECT COALESCE(funding_line,'UNKNOWN') as funding_line, COALESCE(SUM(allocated_amount),0) as allocated, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item GROUP BY funding_line ORDER BY allocated DESC LIMIT 50")
                rows = cur.fetchall() or []
                b = []
                for row in rows:
                    if isinstance(row, dict):
                        b.append({'funding_line': row.get('funding_line'), 'allocated': float(row.get('allocated') or 0), 'expended': float(row.get('expended') or 0)})
                    else:
                        b.append({'funding_line': row[0], 'allocated': float(row[1] or 0), 'expended': float(row[2] or 0)})
                out['data']['breakdowns'] = b
            except Exception:
                out['data']['breakdowns'] = []

            # Trends: simple FY/QTR totals if columns exist
            try:
                cols = [c[1] for c in cur.execute("PRAGMA table_info(budget_line_item)").fetchall()]
                if 'fy' in cols and 'qtr' in cols:
                    cur.execute("SELECT fy, qtr, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item GROUP BY fy,qtr ORDER BY fy,qtr LIMIT 100")
                    trends = []
                    for row in cur.fetchall() or []:
                        if isinstance(row, dict):
                            trends.append({'fy': row.get('fy'), 'qtr': row.get('qtr'), 'expended': float(row.get('expended') or 0)})
                        else:
                            trends.append({'fy': row[0], 'qtr': row[1], 'expended': float(row[2] or 0)})
                    out['data']['trends'] = trends
            except Exception:
                out['data']['trends'] = []

        except Exception:
            # keep empty-safe contract
            pass
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/projects')
def projects_dashboard(current_user: Dict = Depends(get_current_user)):
    """Return project rollup: counts, planned/actual costs, breakdowns by org_unit or funding_line."""
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        out = _empty_rollup('projects')
        try:
            if not _table_exists(cur, 'projects'):
                return out
            # counts and sums
            cur.execute("SELECT COUNT(1) as cnt, COALESCE(SUM(planned_cost),0) as planned, COALESCE(SUM(actual_cost),0) as actual FROM projects")
            r = cur.fetchone()
            cnt = int(r['cnt'] if isinstance(r, dict) and 'cnt' in r else (r[0] if r and r[0] is not None else 0))
            planned = float(r['planned'] if isinstance(r, dict) and 'planned' in r else (r[1] if r and r[1] is not None else 0))
            actual = float(r['actual'] if isinstance(r, dict) and 'actual' in r else (r[2] if r and r[2] is not None else 0))
            out['data']['kpis'] = {'count': cnt, 'planned': planned, 'actual': actual, 'remaining': planned - actual}

            # breakdown by org_unit_id
            try:
                cur.execute("SELECT COALESCE(org_unit_id,'UNKNOWN') as org_unit, COALESCE(SUM(planned_cost),0) as planned, COALESCE(SUM(actual_cost),0) as actual FROM projects GROUP BY org_unit_id ORDER BY planned DESC LIMIT 50")
                rows = cur.fetchall() or []
                b = []
                for row in rows:
                    if isinstance(row, dict):
                        b.append({'org_unit': row.get('org_unit'), 'planned': float(row.get('planned') or 0), 'actual': float(row.get('actual') or 0)})
                    else:
                        b.append({'org_unit': row[0], 'planned': float(row[1] or 0), 'actual': float(row[2] or 0)})
                out['data']['breakdowns'] = b
            except Exception:
                out['data']['breakdowns'] = []
        except Exception:
            pass
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/events')
def events_dashboard(current_user: Dict = Depends(get_current_user)):
    """Return events rollup: counts, budget sums, event metrics aggregation."""
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        out = _empty_rollup('events')
        try:
            if not _table_exists(cur, 'events'):
                return out
            # counts and sums
            cur.execute("SELECT COUNT(1) as cnt, COALESCE(SUM(budget),0) as budget_sum FROM events")
            r = cur.fetchone()
            cnt = int(r['cnt'] if isinstance(r, dict) and 'cnt' in r else (r[0] if r and r[0] is not None else 0))
            budget_sum = float(r['budget_sum'] if isinstance(r, dict) and 'budget_sum' in r else (r[1] if r and r[1] is not None else 0))
            out['data']['kpis'] = {'count': cnt, 'budget': budget_sum}

            # aggregate event_metrics conversions and leads
            try:
                if _table_exists(cur, 'event_metrics'):
                    cur.execute("SELECT COALESCE(SUM(conversions),0) as conversions, COALESCE(SUM(leads),0) as leads FROM event_metrics")
                    em = cur.fetchone()
                    conversions = int(em['conversions'] if isinstance(em, dict) and 'conversions' in em else (em[0] if em and em[0] is not None else 0))
                    leads = int(em['leads'] if isinstance(em, dict) and 'leads' in em else (em[1] if em and em[1] is not None else 0))
                    out['data']['kpis'].update({'conversions': conversions, 'leads': leads})
            except Exception:
                pass

            # breakdown by event_type
            try:
                cur.execute("SELECT COALESCE(event_type,'UNKNOWN') as type, COUNT(1) as cnt, COALESCE(SUM(budget),0) as budget FROM events GROUP BY event_type ORDER BY cnt DESC LIMIT 50")
                rows = cur.fetchall() or []
                b = []
                for row in rows:
                    if isinstance(row, dict):
                        b.append({'event_type': row.get('type'), 'count': int(row.get('cnt') or 0), 'budget': float(row.get('budget') or 0)})
                    else:
                        b.append({'event_type': row[0], 'count': int(row[1] or 0), 'budget': float(row[2] or 0)})
                out['data']['breakdowns'] = b
            except Exception:
                out['data']['breakdowns'] = []
        except Exception:
            pass
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/marketing')
def marketing_dashboard(current_user: Dict = Depends(get_current_user)):
    return _empty_rollup('marketing')


@router.get('/funnel')
def funnel_dashboard(current_user: Dict = Depends(get_current_user)):
    return _empty_rollup('funnel')


@router.get('/command')
def command_dashboard(current_user: Dict = Depends(get_current_user)):
    return _empty_rollup('command')


@router.get('/burden')
def burden_dashboard(current_user: Dict = Depends(get_current_user)):
    return _empty_rollup('burden')
