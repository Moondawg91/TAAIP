from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from ..db import connect
from datetime import datetime
import json

router = APIRouter()


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post('/projects')
def compat_create_project(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO project(org_unit_id,loe_id,event_id,name,description,status,start_dt,end_dt,roi_target,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
            payload.get('org_unit_id'), payload.get('loe_id'), payload.get('event_id'), payload.get('name'), payload.get('description'), payload.get('status') or 'draft', payload.get('start_dt'), payload.get('end_dt'), payload.get('roi_target'), now, now
        ))
        conn.commit()
        pid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.project', 'project', pid, payload)
        cur.execute('SELECT * FROM project WHERE id=?', (pid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get('/powerbi/events')
def compat_powerbi_events(org_unit_id: Optional[int] = None, limit: int = 1000):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT id as event_id, org_unit_id, name, event_type, start_dt, end_dt, location_city, location_state, cbsa, loe, status, created_at, updated_at FROM event WHERE 1=1'
        params = []
        if org_unit_id is not None:
            sql += ' AND org_unit_id=?'; params.append(org_unit_id)
        sql += ' ORDER BY start_dt DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
