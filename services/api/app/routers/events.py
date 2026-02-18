from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import os, json
from .rbac import require_scope, get_allowed_org_units, require_not_role

router = APIRouter(prefix="/events", tags=["events"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/", summary="Create event")
def create_event(payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
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
def update_event(event_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
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
def delete_event(event_id: int, reason: Optional[str] = None, user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
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


# --- Event domain: plans, risks, ROI, AAR


@router.post("/{event_id}/plans", summary="Create plan for event")
def create_event_plan(event_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT org_unit_id FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        now = now_iso()
        cur.execute(
            "INSERT INTO event_plan(event_id, org_unit_id, plan_type, title, description, metadata_json, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                event_id, org_unit, payload.get('plan_type'), payload.get('title'), payload.get('description'), json.dumps(payload.get('metadata') or {}), (user or {}).get('username') or 'system', now, now
            )
        )
        conn.commit()
        pid = cur.lastrowid
        write_audit(conn, (user or {}).get('username') or 'system', 'create.event_plan', 'event_plan', pid, {'event_id': event_id})
        cur.execute("SELECT * FROM event_plan WHERE id=?", (pid,))
        row = cur.fetchone()
        return dict(row)
    finally:
        conn.close()


@router.get("/{event_id}/plans", summary="List plans for event")
def list_event_plans(event_id: int, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            return []
        cur.execute("SELECT * FROM event_plan WHERE event_id=? AND record_status='active' ORDER BY created_at DESC", (event_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.put("/{event_id}/plans/{plan_id}", summary="Update plan for event")
def update_event_plan(event_id: int, plan_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT org_unit_id FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        now = now_iso()
        allowed = ['plan_type','title','description','metadata_json']
        set_clause = ','.join([f"{k}=?" for k in allowed if k in payload.keys() or (k=='metadata_json' and 'metadata' in payload)])
        params = [payload.get(k) if k!='metadata_json' else json.dumps(payload.get('metadata') or {}) for k in allowed if k in payload.keys() or (k=='metadata_json' and 'metadata' in payload)]
        if set_clause:
            sql = f"UPDATE event_plan SET {set_clause}, updated_at=? WHERE id=? AND event_id=?"
            params.append(now)
            params.append(plan_id)
            params.append(event_id)
            cur.execute(sql, tuple(params))
            conn.commit()
        write_audit(conn, (user or {}).get('username') or 'system', 'update.event_plan', 'event_plan', plan_id, payload)
        cur.execute("SELECT * FROM event_plan WHERE id=?", (plan_id,))
        row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


@router.delete("/{event_id}/plans/{plan_id}", summary="Archive plan")
def delete_event_plan(event_id: int, plan_id: int, user: Dict = Depends(require_not_role('station_view'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE event_plan SET record_status='archived', updated_at=? WHERE id=? AND event_id=?", (now_iso(), plan_id, event_id))
        conn.commit()
        write_audit(conn, (user or {}).get('username') or 'system', 'archive.event_plan', 'event_plan', plan_id, {'event_id': event_id})
        return {"ok": True}
    finally:
        conn.close()


# Risks

@router.post("/{event_id}/risks", summary="Create risk for event")
def create_event_risk(event_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT org_unit_id FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        now = now_iso()
        cur.execute("INSERT INTO event_risk(event_id, org_unit_id, title, likelihood, impact, mitigation, metadata_json, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (event_id, org_unit, payload.get('title'), payload.get('likelihood'), payload.get('impact'), payload.get('mitigation'), json.dumps(payload.get('metadata') or {}), (user or {}).get('username') or 'system', now, now))
        conn.commit()
        rid = cur.lastrowid
        write_audit(conn, (user or {}).get('username') or 'system', 'create.event_risk', 'event_risk', rid, {'event_id': event_id})
        cur.execute("SELECT * FROM event_risk WHERE id=?", (rid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get("/{event_id}/risks", summary="List risks for event")
def list_event_risks(event_id: int, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            return []
        cur.execute("SELECT * FROM event_risk WHERE event_id=? AND record_status='active' ORDER BY created_at DESC", (event_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ROI

@router.post("/{event_id}/roi", summary="Create ROI snapshot for event")
def create_event_roi(event_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT org_unit_id FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        now = now_iso()
        cur.execute("INSERT INTO event_roi(event_id, org_unit_id, metrics_json, expected_revenue, expected_cost, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                    (event_id, org_unit, json.dumps(payload.get('metrics') or {}), payload.get('expected_revenue'), payload.get('expected_cost'), (user or {}).get('username') or 'system', now, now))
        conn.commit()
        rid = cur.lastrowid
        write_audit(conn, (user or {}).get('username') or 'system', 'create.event_roi', 'event_roi', rid, {'event_id': event_id})
        cur.execute("SELECT * FROM event_roi WHERE id=?", (rid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get("/{event_id}/roi", summary="List ROI snapshots for event")
def list_event_roi(event_id: int, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            return []
        cur.execute("SELECT * FROM event_roi WHERE event_id=? AND record_status='active' ORDER BY created_at DESC", (event_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# AAR

@router.post("/{event_id}/aar", summary="Create AAR for event")
def create_event_aar(event_id: int, payload: Dict[str, Any], user: Dict = Depends(require_not_role('station_view')), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT org_unit_id FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        now = now_iso()
        cur.execute("INSERT INTO event_aar(event_id, org_unit_id, summary, lessons_json, recommendations, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                    (event_id, org_unit, payload.get('summary'), json.dumps(payload.get('lessons') or {}), payload.get('recommendations'), (user or {}).get('username') or 'system', now, now))
        conn.commit()
        aid = cur.lastrowid
        write_audit(conn, (user or {}).get('username') or 'system', 'create.event_aar', 'event_aar', aid, {'event_id': event_id})
        cur.execute("SELECT * FROM event_aar WHERE id=?", (aid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get("/{event_id}/aar", summary="List AARs for event")
def list_event_aars(event_id: int, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE id=?", (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        org_unit = ev['org_unit_id']
        if allowed_orgs is not None and org_unit not in allowed_orgs:
            return []
        cur.execute("SELECT * FROM event_aar WHERE event_id=? AND record_status='active' ORDER BY created_at DESC", (event_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
