from fastapi import APIRouter, Depends, HTTPException
from .. import db
from datetime import datetime
from typing import Optional
from .rbac import require_scope
from uuid import uuid4

router = APIRouter(prefix='/calendar', tags=['calendar'])

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _fetch_as_dicts(cur):
    rows = cur.fetchall()
    out = []
    cols = [c[0] for c in cur.description] if getattr(cur, 'description', None) else []
    for r in rows:
        try:
            if hasattr(r, 'keys'):
                out.append({k: r[k] for k in r.keys()})
            elif isinstance(r, dict):
                out.append(r)
            else:
                out.append({cols[i]: r[i] for i in range(min(len(cols), len(r)))})
        except Exception:
            try:
                out.append(dict(r))
            except Exception:
                out.append({})
    return out


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
        return _fetch_as_dicts(cur)
    finally:
        conn.close()


@router.get('/events')
def list_calendar_events(start: Optional[str] = None, end: Optional[str] = None, scope: Optional[str] = None, limit: int = 500):
    """List entries from `calendar_events` (migration-safe)."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        # prefer calendar_events table if present
        try:
            cur.execute("PRAGMA table_info(calendar_events)")
            cols = cur.fetchall()
            if cols:
                sql = 'SELECT event_id as id, org_unit_id as scope, title, start_dt as start_ts, end_dt as end_ts, location, record_status FROM calendar_events WHERE 1=1'
                params = []
                if scope:
                    sql += ' AND org_unit_id=?'; params.append(scope)
                if start:
                    sql += ' AND start_dt>=?'; params.append(start)
                if end:
                    sql += ' AND end_dt<=?'; params.append(end)
                sql += ' ORDER BY start_dt DESC LIMIT ?'; params.append(limit)
                cur.execute(sql, tuple(params))
                return _fetch_as_dicts(cur)
        except Exception:
            pass
        # fallback to legacy calendar_event table
        return list_events(start, end)
    finally:
        conn.close()


@router.post('/events')
def create_calendar_event(payload: dict):
    """Create an event in `calendar_events` if available, otherwise fallback."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(calendar_events)")
            cols = [c[1] for c in cur.fetchall()]
            if cols:
                eid = payload.get('event_id') or str(uuid4())
                now = datetime.utcnow().isoformat()
                cur.execute('INSERT INTO calendar_events(event_id, org_unit_id, title, start_dt, end_dt, location, created_at, record_status) VALUES (?,?,?,?,?,?,?,?)', (
                    eid, payload.get('org_unit_id'), payload.get('title'), payload.get('start_dt'), payload.get('end_dt'), payload.get('location'), now, payload.get('record_status') or 'active'
                ))
                conn.commit()
                cur.execute('SELECT event_id as id, org_unit_id as scope, title, start_dt as start_ts, end_dt as end_ts, location, created_at FROM calendar_events WHERE event_id=?', (eid,))
                row = cur.fetchone()
                return ({k: row[k] for k in row.keys()} if row and hasattr(row, 'keys') else dict(row) if row else {})
        except Exception:
            pass
        # fallback to existing create_event
        return create_event(payload)
    finally:
        conn.close()


@router.put('/events/{event_id}')
def update_calendar_event(event_id: str, payload: dict):
    conn = db.connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(calendar_events)")
            cols = [c[1] for c in cur.fetchall()]
            if cols:
                cur.execute('UPDATE calendar_events SET title=?, start_dt=?, end_dt=?, location=?, record_status=? WHERE event_id=?', (
                    payload.get('title'), payload.get('start_dt'), payload.get('end_dt'), payload.get('location'), payload.get('record_status'), event_id
                ))
                conn.commit()
                cur.execute('SELECT event_id as id, org_unit_id as scope, title, start_dt as start_ts, end_dt as end_ts, location, created_at FROM calendar_events WHERE event_id=?', (event_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail='not_found')
                return dict(row)
        except Exception:
            pass
        # fallback to update via calendar_event schema
        # reuse existing update via select/insert sequence
        raise HTTPException(status_code=404, detail='not_found')
    finally:
        conn.close()


@router.delete('/events/{event_id}')
def delete_calendar_event(event_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA table_info(calendar_events)")
            cols = [c[1] for c in cur.fetchall()]
            if cols:
                cur.execute('DELETE FROM calendar_events WHERE event_id=?', (event_id,))
                conn.commit()
                return {'deleted': True}
        except Exception:
            pass
        # fallback: try legacy
        cur.execute('DELETE FROM calendar_event WHERE id=?', (event_id,))
        conn.commit()
        return {'deleted': True}
    finally:
        conn.close()
