from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import json
from .rbac import require_scope

router = APIRouter(prefix="/projects", tags=["projects"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/", summary="Create project")
def create_project(payload: Dict[str, Any]):
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


@router.get("/{project_id}", summary="Get project")
def get_project(project_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM project WHERE id=?', (project_id,))
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


@router.get("/", summary="List projects")
def list_projects(org_unit_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM project WHERE 1=1'
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
        if status is not None:
            sql += ' AND status=?'; params.append(status)
        sql += ' ORDER BY created_at DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# Compatibility: LOE endpoints integrated into the main `projects` router.
@router.post('/loes', summary='Create LOE')
def create_loe(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO loe(org_unit_id, fy, qtr, name, description) VALUES (?,?,?,?,?)', (
            payload.get('org_unit_id'), payload.get('fy'), payload.get('qtr'), payload.get('name'), payload.get('description')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/loes', summary='List LOEs')
def list_loes(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM loe ORDER BY id DESC LIMIT ?', (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get('/project/{project_id}/tasks')
def list_tasks(project_id: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM task WHERE project_id=? ORDER BY due_dt', (project_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
