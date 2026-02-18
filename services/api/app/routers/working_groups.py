from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import json
from .rbac import require_scope

router = APIRouter(prefix="/working-groups", tags=["working_groups"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/", summary="Create working group")
def create_wg(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO working_group(org_unit_id,name,wg_type,description,created_at) VALUES (?,?,?,?,?)', (
            payload.get('org_unit_id'), payload.get('name'), payload.get('wg_type'), payload.get('description'), now
        ))
        conn.commit()
        wid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.working_group', 'working_group', wid, payload)
        cur.execute('SELECT * FROM working_group WHERE id=?', (wid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get("/", summary="List working groups")
def list_wgs(org_unit_id: Optional[int] = None, limit: int = 100, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM working_group WHERE 1=1'
        params: List[Any] = []
        if allowed_orgs is not None:
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        else:
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
        sql += ' ORDER BY id DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/{wg_id}/meeting", summary="Create meeting in working group")
def create_meeting(wg_id: int, payload: Dict[str, Any]):
    # link via org_unit_id if provided
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO meeting(org_unit_id,title,meeting_type,start_dt,end_dt,location,qtr,fy,notes) VALUES (?,?,?,?,?,?,?,?,?)', (
            payload.get('org_unit_id'), payload.get('title'), payload.get('meeting_type'), payload.get('start_dt'), payload.get('end_dt'), payload.get('location'), payload.get('qtr'), payload.get('fy'), payload.get('notes')
        ))
        conn.commit()
        mid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.meeting', 'meeting', mid, payload)
        cur.execute('SELECT * FROM meeting WHERE id=?', (mid,))
        return dict(cur.fetchone())
    finally:
        conn.close()
