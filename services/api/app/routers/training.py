from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import json

router = APIRouter(prefix="/training", tags=["training"])
from .rbac import require_scope


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/course", summary="Create course")
def create_course(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO training_course(title,description,created_at) VALUES (?,?,?)', (payload.get('title'), payload.get('description'), now))
        conn.commit()
        cid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.course', 'training_course', cid, payload)
        cur.execute('SELECT * FROM training_course WHERE id=?', (cid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get("/courses", summary="List courses")
def list_courses(limit: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        # if courses are scoped by org_unit, filter when allowed_orgs provided
        try:
            cur.execute("PRAGMA table_info(training_course)")
            cols = [c[1] for c in cur.fetchall()]
            if 'org_unit_id' in cols and allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                cur.execute(f'SELECT * FROM training_course WHERE org_unit_id IN ({placeholders}) ORDER BY created_at DESC LIMIT ?', (*allowed_orgs, limit))
                return [dict(r) for r in cur.fetchall()]
        except Exception:
            pass
        cur.execute('SELECT * FROM training_course ORDER BY created_at DESC LIMIT ?', (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/assign", summary="Assign course")
def assign_course(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO training_assignment(course_id,assigned_to,assigned_at,due_dt) VALUES (?,?,?,?)', (payload.get('course_id'), payload.get('assigned_to'), now, payload.get('due_dt')))
        conn.commit()
        aid = cur.lastrowid
        write_audit(conn, payload.get('assigned_by') or 'system', 'assign.course', 'training_assignment', aid, payload)
        cur.execute('SELECT * FROM training_assignment WHERE id=?', (aid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.post("/complete", summary="Complete assignment")
def complete_assignment(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO training_completion(assignment_id,completed_by,completed_at,score) VALUES (?,?,?,?)', (payload.get('assignment_id'), payload.get('completed_by'), now, payload.get('score')))
        conn.commit()
        cid = cur.lastrowid
        write_audit(conn, payload.get('completed_by') or 'system', 'complete.assignment', 'training_completion', cid, payload)
        cur.execute('SELECT * FROM training_completion WHERE id=?', (cid,))
        return dict(cur.fetchone())
    finally:
        conn.close()
