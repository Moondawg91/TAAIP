from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from .. import db
from datetime import datetime
from .rbac import require_scope

router = APIRouter(prefix='/api/benchmarks', tags=['benchmarks'])

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/cost')
def create_benchmark(b: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO cost_benchmark(kpi_type, stage, tactic, threshold_low, threshold_mid, threshold_high, fiscal_year, org_scope, created_by, created_at, updated_at, import_job_id, tags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            b.get('kpi_type'), b.get('stage'), b.get('tactic'), b.get('threshold_low'), b.get('threshold_mid'), b.get('threshold_high'), b.get('fiscal_year'), b.get('org_scope'), b.get('created_by'), now_iso(), now_iso(), b.get('import_job_id'), b.get('tags')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/cost')
def list_benchmarks(org_scope: str = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if org_scope:
            # enforce that requested scope is allowed
            if allowed_orgs is not None and org_scope not in allowed_orgs:
                return []
            cur.execute('SELECT * FROM cost_benchmark WHERE org_scope=? ORDER BY fiscal_year DESC', (org_scope,))
        else:
            cur.execute('SELECT * FROM cost_benchmark ORDER BY fiscal_year DESC')
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post('/roi/compute')
def compute_roi(payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    # compute CPM, CPE, CPL and store roi_result
    spend = float(payload.get('spend', 0) or 0)
    impressions = int(payload.get('impressions', 0) or 0)
    engagements = int(payload.get('engagements', 0) or 0)
    leads = int(payload.get('leads', 0) or 0)
    appts = int(payload.get('appts', 0) or 0)
    contracts = int(payload.get('contracts', 0) or 0)
    accessions = int(payload.get('accessions', 0) or 0)

    CPM = (spend / (impressions/1000)) if impressions else None
    CPE = (spend / engagements) if engagements else None
    CPL = (spend / leads) if leads else None

    # derive some ratios
    CPAppt = (spend / appts) if appts else None
    CPCntr = (spend / contracts) if contracts else None
    ROI = None
    opp_cost = None

    # optional enforcement if payload contains org_scope
    org_scope = payload.get('org_scope')
    if allowed_orgs is not None and org_scope is not None and org_scope not in allowed_orgs:
        raise HTTPException(status_code=403, detail='forbidden')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO roi_result(period_start, period_end, org_scope, spend, impressions, engagements, leads, appts, contracts, accessions, CPM, CPE, CPL, CPAppt, CPCntr, ROI, opp_cost, created_by, created_at, updated_at, import_job_id, tags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            payload.get('period_start'), payload.get('period_end'), payload.get('org_scope'), spend, impressions, engagements, leads, appts, contracts, accessions, CPM, CPE, CPL, CPAppt, CPCntr, ROI, opp_cost, payload.get('created_by'), now_iso(), now_iso(), payload.get('import_job_id'), payload.get('tags')
        ))
        conn.commit()
        return {'id': cur.lastrowid, 'CPM': CPM, 'CPE': CPE, 'CPL': CPL}
    finally:
        conn.close()
