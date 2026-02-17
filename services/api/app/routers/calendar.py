from fastapi import APIRouter, Depends
from .. import db
from datetime import datetime
from typing import Optional
from .rbac import require_scope

router = APIRouter(prefix='/api/calendar', tags=['calendar'])

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/')
def create_event(payload: dict):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO calendar_event(linked_type, linked_id, title, start_dt, end_dt, location, notes, status, created_by, created_at, updated_at, import_job_id, tags) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            payload.get('linked_type'), payload.get('linked_id'), payload.get('title'), payload.get('start_dt'), payload.get('end_dt'), payload.get('location'), payload.get('notes'), payload.get('status'), payload.get('created_by'), now_iso(), now_iso(), payload.get('import_job_id'), payload.get('tags')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/')
def list_events(start: str = None, end: str = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM calendar_event WHERE 1=1 '
        params = []
        if start:
            q += ' AND start_dt >= ?'
            params.append(start)
        if end:
            q += ' AND end_dt <= ?'
            params.append(end)
        # apply org_unit filtering only if calendar_event table has org_unit_id
        try:
            cur.execute("PRAGMA table_info(calendar_event)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                q += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        except Exception:
            pass
        q += ' ORDER BY start_dt'
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
