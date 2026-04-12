from fastapi import APIRouter, Depends
from typing import Optional
from .. import db
from ..db import get_db_path
from datetime import datetime
from .rbac import require_scope
from ..data.funnel_loader import load_funnel_data

router = APIRouter(prefix='/analytics', tags=['analytics'])

def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return None


@router.get('/summary')
def summary(scope: Optional[str] = None, period_start: Optional[str] = None, period_end: Optional[str] = None, allowed_orgs: Optional[list] = None):
    """Return small summary shaped for the frontend KPI row.

    Contract: {"leads":{"active":N}, "contracts":{"total":M}, "conversion":{"pct":P}}
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        # try funnel_event first (if present)
        try:
            cur.execute("PRAGMA table_info(funnel_event)")
            cols = [c[1] for c in cur.fetchall()]
            if 'leads' in cols or 'contracts' in cols:
                q = 'SELECT SUM(COALESCE(leads,0)) as leads_sum, SUM(COALESCE(contracts,0)) as contracts_sum FROM funnel_event WHERE 1=1'
                params = []
                if period_start:
                    q += ' AND timestamp >= ?'; params.append(period_start)
                if period_end:
                    q += ' AND timestamp <= ?'; params.append(period_end)
                if 'org_unit_id' in cols and allowed_orgs:
                    placeholders = ','.join(['?'] * len(allowed_orgs))
                    q += f' AND org_unit_id IN ({placeholders})'
                    params.extend(allowed_orgs)
                cur.execute(q, tuple(params))
                r = cur.fetchone()
                leads = int(r['leads_sum'] or 0)
                contracts = int(r['contracts_sum'] or 0)
                conv = round((contracts / leads * 100), 1) if leads else None
                return {'leads': {'active': leads}, 'contracts': {'total': contracts}, 'conversion': {'pct': conv}}
        except Exception:
            pass

        # fallback: try fact_production metric keys
        try:
            cur.execute("PRAGMA table_info(fact_production)")
            cols = [c[1] for c in cur.fetchall()]
            q = "SELECT metric_key, SUM(metric_value) as total FROM fact_production WHERE 1=1 GROUP BY metric_key"
            params = []
            if period_start:
                q = q.replace('WHERE 1=1', 'WHERE date_key>=? AND date_key<=?')
                params = [period_start, period_end or period_start]
            cur.execute(q, tuple(params))
            fetched = cur.fetchall()
            rows = {r.get('metric_key'): float(r.get('total') or 0) for r in fetched}
            if rows:
                leads = int(rows.get('leads') or rows.get('active_leads') or 0)
                contracts = int(rows.get('contracts') or 0)
                conv = round((contracts / leads * 100), 1) if leads else None
                return {'leads': {'active': leads}, 'contracts': {'total': contracts}, 'conversion': {'pct': conv}}
        except Exception:
            pass

        # fallback: if a simple `leads` table exists, use its count
        try:
            cur.execute("PRAGMA table_info(leads)")
            lcols = [c[1] for c in cur.fetchall()]
            if lcols:
                cur.execute('SELECT COUNT(1) as c FROM leads')
                r = cur.fetchone()
                leads = int(r['c'] or 0)
                # try contract-like tables
                contracts = 0
                try:
                    cur.execute("SELECT COUNT(1) as c FROM fact_school_contracts")
                    rc = cur.fetchone(); contracts = int(rc['c'] or 0)
                except Exception:
                    contracts = 0
                conv = round((contracts / leads * 100), 1) if leads else None
                return {'leads': {'active': leads}, 'contracts': {'total': contracts}, 'conversion': {'pct': conv}}
        except Exception:
            pass

        # final fallback: empty zeros
        return {'leads': {'active': 0}, 'contracts': {'total': 0}, 'conversion': {'pct': None}}
    finally:
        conn.close()


@router.get('/debug/dbpath')
def debug_dbpath():
    import os
    p = get_db_path()
    try:
        abs_p = os.path.abspath(p)
    except Exception:
        abs_p = p
    # try a quick count of leads if table exists
    cnt = None
    try:
        conn = db.connect(); cur = conn.cursor()
        cur.execute("PRAGMA table_info(leads)")
        cols = cur.fetchall()
        if cols:
            cur.execute('SELECT COUNT(1) as c FROM leads')
            r = cur.fetchone(); cnt = int(r['c'] or 0)
        conn.close()
    except Exception:
        cnt = None
    return {'db_path': p, 'db_path_abs': abs_p, 'leads_count': cnt}


@router.get('/dashboard')
def get_dashboard():
    events, summary = load_funnel_data()

    # 🔥 HARD DEBUG CHECK
    print("SUMMARY SAMPLE:")
    print(summary.head(5))

    total_leads = int(summary["lead_at"].notna().sum())
    total_applicants = int(summary["applicant_at"].notna().sum())
    total_dep = int(summary["dep_at"].notna().sum())
    total_ship = int(summary["ship_at"].notna().sum())

    return {
        "funnel": {
            "lead": int(total_leads),
            "applicant": int(total_applicants),
            "dep": int(total_dep),
            "ship": int(total_ship),
        }
    }


@router.get('/funnel')
def funnel(scope: Optional[str] = None, period_start: Optional[str] = None, period_end: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT stage_key, SUM(count) as total_count, SUM(leads) as leads FROM funnel_event WHERE 1=1'
        params = []
        if period_start:
            q += ' AND timestamp >= ?'
            params.append(period_start)
        if period_end:
            q += ' AND timestamp <= ?'
            params.append(period_end)
        try:
            cur.execute("PRAGMA table_info(funnel_event)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                q += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        except Exception:
            pass
        q += ' GROUP BY stage_key ORDER BY total_count DESC'
        cur.execute(q, params)
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.get('/qbr')
def qbr(scope: Optional[str] = None, fy: Optional[int] = None, quarter: Optional[int] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    # simple QBR table: return roi_result rows filtered by fiscal year/quarter
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM roi_result WHERE 1=1'
        params = []
        if fy:
            q += ' AND substr(period_start,1,4) = ?'
            params.append(str(fy))
        try:
            cur.execute("PRAGMA table_info(roi_result)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                q += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        except Exception:
            pass
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
