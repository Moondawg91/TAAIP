from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import os, json
from .rbac import require_scope, get_allowed_org_units

router = APIRouter(prefix="/events", tags=["events"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/", summary="Create event")
def create_event(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        payload = payload or {}
        fields = [
            'org_unit_id','name','event_type','start_dt','end_dt','location_name','location_city','location_state','location_zip','cbsa','loe','objective','status','poc','risk_level','created_at','updated_at'
        ]
        now = now_iso()
        cur.execute(
            "INSERT INTO event(org_unit_id,name,event_type,start_dt,end_dt,location_name,location_city,location_state,location_zip,cbsa,loe,objective,status,poc,risk_level,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                payload.get('org_unit_id'), payload.get('name'), payload.get('event_type'), payload.get('start_dt'), payload.get('end_dt'),
                payload.get('location_name'), payload.get('location_city'), payload.get('location_state'), payload.get('location_zip'), payload.get('cbsa'),
                payload.get('loe'), payload.get('objective'), payload.get('status') or 'draft', payload.get('poc'), payload.get('risk_level'), now, now
            )
        )
        conn.commit()
        eid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.event', 'event', eid, {'name': payload.get('name')})
        cur.execute("SELECT * FROM event WHERE id=?", (eid,))
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


@router.get("/{event_id}", summary="Get event")
def get_event(event_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        if allowed_orgs is not None:
            try:
                if row['org_unit_id'] not in allowed_orgs:
                    raise HTTPException(status_code=403, detail='forbidden')
            except Exception:
                pass
        return dict(row)
    finally:
        conn.close()


@router.get("/", summary="List events")
def list_events(org_unit_id: Optional[int] = None, fy: Optional[int] = None, qtr: Optional[int] = None, status: Optional[str] = None, limit: int = 100, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM event WHERE 1=1"
        params: List[Any] = []
        if allowed_orgs is not None:
            # restricted user: if org_unit_id supplied, ensure it's within allowed
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += " AND org_unit_id=?"
                params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f" AND org_unit_id IN ({placeholders})"
                params.extend(allowed_orgs)
        else:
            if org_unit_id is not None:
                sql += " AND org_unit_id=?"
                params.append(org_unit_id)
        if status is not None:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY start_dt DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.put("/{event_id}", summary="Update event")
def update_event(event_id: int, payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        payload = payload or {}
        now = now_iso()
        # simple update of provided fields
        allowed = ['name','event_type','start_dt','end_dt','location_name','location_city','location_state','location_zip','cbsa','loe','objective','status','poc','risk_level']
        set_clause = ','.join([f"{k}=?" for k in allowed if k in payload.keys()])
        params = [payload[k] for k in allowed if k in payload.keys()]
        if set_clause:
            sql = f"UPDATE event SET {set_clause}, updated_at=? WHERE id=?"
            params.append(now)
            params.append(event_id)
            cur.execute(sql, tuple(params))
            conn.commit()
        write_audit(conn, payload.get('updated_by') or 'system', 'update.event', 'event', event_id, payload)
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


@router.delete("/{event_id}", summary="Archive event")
def delete_event(event_id: int, reason: Optional[str] = None):
    conn = connect()
    try:
        cur = conn.cursor()
        # soft delete: set status to archived and updated_at
        cur.execute("UPDATE event SET status=?, updated_at=? WHERE id=?", ('archived', now_iso(), event_id))
        conn.commit()
        write_audit(conn, 'system', 'archive.event', 'event', event_id, {'reason': reason})
        return {"ok": True}
    finally:
        conn.close()
