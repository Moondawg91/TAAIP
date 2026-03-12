from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect
from datetime import datetime
import json
from .rbac import get_allowed_org_units, get_current_user, require_not_role, require_scope

router = APIRouter(prefix="/school-program", tags=["school-program"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                    (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
        conn.commit()
    except Exception:
        pass


@router.get('/readiness', summary='School program readiness')
def readiness():
    # Return an empty-safe readiness structure; other readiness checks may be added later
    return { 'status': 'ok', 'blocking': [] }


@router.get('/summary', summary='School program summary')
def summary(qs: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        # Simple empty-safe summary: counts of schools and recent milestones
        try:
            cur.execute('SELECT COUNT(*) as c FROM schools WHERE record_status!=? OR record_status IS NULL', ('archived',))
            cnt = cur.fetchone()
            total = cnt[0] if cnt else 0
        except Exception:
            total = 0
        # recent milestones
        milestones = []
        try:
            cur.execute('SELECT id, school_id, milestone_type, milestone_date FROM school_milestones ORDER BY milestone_date DESC LIMIT 10')
            rows = cur.fetchall()
            milestones = [dict(r) for r in rows]
        except Exception:
            milestones = []
        return { 'status': 'ok', 'total_schools': total, 'recent_milestones': milestones }
    finally:
        conn.close()


@router.get('/schools', summary='List schools')
def list_schools(limit: int = 200, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, school_type, city, state, zip, cbsa_code FROM schools WHERE record_status!=? OR record_status IS NULL ORDER BY name LIMIT ?', ('archived', limit))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/schools/{school_id}', summary='Get school')
def get_school(school_id: str, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM schools WHERE id=?', (school_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        return dict(row)
    finally:
        conn.close()
