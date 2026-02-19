from fastapi import APIRouter, Depends
from typing import Optional
from .. import db
from datetime import datetime
from .rbac import require_scope

router = APIRouter(prefix='/analytics', tags=['analytics'])

def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return None


@router.get('/summary')
def summary(scope: Optional[str] = None, period_start: Optional[str] = None, period_end: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    # produce KPI summary aggregating funnel_event rows
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT SUM(spend) as spend_sum, SUM(impressions) as impressions_sum, SUM(engagements) as engagements_sum, SUM(leads) as leads_sum, SUM(appts_made) as appts_made_sum, SUM(contracts) as contracts_sum, SUM(accessions) as accessions_sum FROM funnel_event WHERE 1=1'
        params = []
        if period_start:
            q += ' AND timestamp >= ?'
            params.append(period_start)
        if period_end:
            q += ' AND timestamp <= ?'
            params.append(period_end)
        # apply org_unit filter when available
        try:
            cur.execute("PRAGMA table_info(funnel_event)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                q += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        except Exception:
            pass
        cur.execute(q, params)
        r = cur.fetchone()
        spend = r['spend_sum'] or 0
        impressions = r['impressions_sum'] or 0
        engagements = r['engagements_sum'] or 0
        leads = r['leads_sum'] or 0
        appts = r['appts_made_sum'] or 0
        contracts = r['contracts_sum'] or 0
        accessions = r['accessions_sum'] or 0

        cpm = (spend / (impressions/1000)) if impressions else None
        cpe = (spend / engagements) if engagements else None
        cpl = (spend / leads) if leads else None

        return {
            'spend': spend,
            'impressions': impressions,
            'engagements': engagements,
            'leads': leads,
            'appts': appts,
            'contracts': contracts,
            'accessions': accessions,
            'CPM': cpm,
            'CPE': cpe,
            'CPL': cpl
        }
    finally:
        conn.close()


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
