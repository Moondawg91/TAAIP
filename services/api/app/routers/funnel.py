from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from .. import db
from datetime import datetime
from .rbac import require_scope

router = APIRouter(prefix="/api/funnel", tags=["funnel"])

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.get('/stages')
def list_stages(allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM funnel_stage ORDER BY seq_order')
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.post('/stages')
def create_stage(stage: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        created = now_iso()
        cur.execute('INSERT INTO funnel_stage(stage_key, name, seq_order, stage_type, created_by, created_at, updated_at, import_job_id, tags) VALUES (?,?,?,?,?,?,?,?,?)', (
            stage.get('stage_key'), stage.get('name'), stage.get('seq_order'), stage.get('stage_type'), stage.get('created_by'), created, created, stage.get('import_job_id'), stage.get('tags')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.post('/events')
def ingest_event(evt: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        created = now_iso()
        # optional org filter: if event payload includes org_unit_id, enforce scope
        org_unit_id = evt.get('org_unit_id') or evt.get('org_unit')
        if allowed_orgs is not None and org_unit_id is not None and org_unit_id not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO funnel_event(timestamp, source, stage_key, count, cost, impressions, engagements, leads, appts_made, appts_conducted, contracts, accessions, created_by, created_at, updated_at, import_job_id, tags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            evt.get('timestamp'), evt.get('source'), evt.get('stage_key'), evt.get('count') or 0, evt.get('cost') or 0.0, evt.get('impressions') or 0, evt.get('engagements') or 0, evt.get('leads') or 0, evt.get('appts_made') or 0, evt.get('appts_conducted') or 0, evt.get('contracts') or 0, evt.get('accessions') or 0, evt.get('created_by'), created, created, evt.get('import_job_id'), evt.get('tags')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/events')
def query_events(scope: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM funnel_event WHERE 1=1 '
        params = []
        if start:
            q += ' AND timestamp >= ?'
            params.append(start)
        if end:
            q += ' AND timestamp <= ?'
            params.append(end)
        # apply optional org filter when funnel_event has org_unit_id
        try:
            cur.execute("PRAGMA table_info(funnel_event)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                q += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        except Exception:
            pass
        q += ' ORDER BY timestamp'
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
