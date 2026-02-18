from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import json
from .rbac import require_scope, require_roles, require_any_role, get_current_user

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


# NOTE: `get_project` moved lower in the file to avoid parameterized path
# shadowing static routes like '/command_priorities'. See re-inserted
# definition further below.


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
def create_loe(payload: Dict[str, Any], current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO loe(org_unit_id, fy, qtr, name, description, created_at) VALUES (?,?,?,?,?,?)', (
                payload.get('org_unit_id'), payload.get('fy'), payload.get('qtr'), payload.get('name'), payload.get('description'), now_iso()
            ))
            conn.commit()
            return {'id': cur.lastrowid}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get('/loes', summary='List LOEs')
def list_loes(limit: int = 100, scope: Optional[str] = None):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM loe WHERE 1=1'
        params: List[Any] = []
        if scope:
            try:
                scope_id = int(scope)
                sql += ' AND org_unit_id=?'
                params.append(scope_id)
            except Exception:
                # non-numeric scope - ignore filter
                pass
        sql += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.put('/loes/{loe_id}', summary='Update LOE')
def update_loe(loe_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        # allow updating name, description, fy, qtr, org_unit_id
        cur.execute('UPDATE loe SET name=?, description=?, fy=?, qtr=?, org_unit_id=? WHERE id=?', (
            payload.get('name'), payload.get('description'), payload.get('fy'), payload.get('qtr'), payload.get('org_unit_id'), loe_id
        ))
        conn.commit()
        cur.execute('SELECT * FROM loe WHERE id=?', (loe_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        return dict(row)
    finally:
        conn.close()


@router.delete('/loes/{loe_id}', summary='Delete LOE')
def delete_loe(loe_id: int, current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM loe WHERE id=?', (loe_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        cur.execute('DELETE FROM loe WHERE id=?', (loe_id,))
        conn.commit()
        return {'status': 'ok'}
    finally:
        conn.close()


# Command Priorities endpoints
@router.get('/command_priorities', summary='List command priorities')
def list_command_priorities(limit: int = 100, scope: Optional[str] = None):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM command_priorities WHERE 1=1'
        params: List[Any] = []
        if scope:
            try:
                scope_id = int(scope)
                sql += ' AND org_unit_id=?'
                params.append(scope_id)
            except Exception:
                pass
        sql += ' ORDER BY rank ASC LIMIT ?'
        params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post('/command_priorities', summary='Create command priority')
def create_command_priority(payload: Dict[str, Any], current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO command_priorities(org_unit_id,title,description,rank,created_at,updated_at) VALUES (?,?,?,?,?,?)', (
            payload.get('org_unit_id'), payload.get('title'), payload.get('description'), payload.get('rank') or 0, now, now
        ))
        conn.commit()
        pid = cur.lastrowid
        cur.execute('SELECT * FROM command_priorities WHERE id=?', (pid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.put('/command_priorities/{pid}', summary='Update command priority')
def update_command_priority(pid: int, payload: Dict[str, Any], current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('UPDATE command_priorities SET title=?, description=?, rank=?, updated_at=? WHERE id=?', (
            payload.get('title'), payload.get('description'), payload.get('rank') or 0, now, pid
        ))
        conn.commit()
        cur.execute('SELECT * FROM command_priorities WHERE id=?', (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        return dict(row)
    finally:
        conn.close()


@router.delete('/command_priorities/{pid}', summary='Delete command priority')
def delete_command_priority(pid: int, current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM command_priorities WHERE id=?', (pid,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='not found')
        cur.execute('DELETE FROM priority_loe WHERE priority_id=?', (pid,))
        cur.execute('DELETE FROM command_priorities WHERE id=?', (pid,))
        conn.commit()
        return {'status': 'ok'}
    finally:
        conn.close()


@router.get('/command_priorities/{pid}/loes', summary='List LOEs assigned to a priority')
def list_priority_loes(pid: int, scope: Optional[str] = None):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT l.* FROM loe l JOIN priority_loe p ON p.loe_id = l.id WHERE p.priority_id=?'
        params: List[Any] = [pid]
        if scope:
            try:
                scope_id = int(scope)
                sql += ' AND l.org_unit_id=?'
                params.append(scope_id)
            except Exception:
                pass
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post('/command_priorities/{pid}/loes', summary='Assign LOE to priority')
def assign_loe_to_priority(pid: int, payload: Dict[str, Any], current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    loe_id = payload.get('loe_id')
    if not loe_id:
        raise HTTPException(status_code=400, detail='missing loe_id')
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        try:
            cur.execute('INSERT OR IGNORE INTO priority_loe(priority_id, loe_id, created_at) VALUES (?,?,?)', (pid, loe_id, now))
            conn.commit()
        except Exception:
            pass
        # return currently assigned LOEs (ensure table name 'loe' used)
        cur.execute('SELECT l.* FROM loe l JOIN priority_loe p ON p.loe_id = l.id WHERE p.priority_id=?', (pid,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete('/command_priorities/{pid}/loes/{loe_id}', summary='Remove LOE from priority')
def remove_loe_from_priority(pid: int, loe_id: str, current_user: Dict = Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM priority_loe WHERE priority_id=? AND loe_id=?', (pid, loe_id))
        conn.commit()
        return {'status': 'ok'}
    finally:
        conn.close()


# Re-inserted: Get single project (moved so static routes match first)
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


@router.get('/project/{project_id}/tasks')
def list_tasks(project_id: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM task WHERE project_id=? ORDER BY due_dt', (project_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
