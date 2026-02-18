from fastapi import APIRouter, HTTPException, Depends
from ..db import connect
from datetime import datetime
import json
from .rbac import require_roles, get_current_user
import uuid

router = APIRouter(prefix="/automation", tags=["automation"])


def now_iso():
    return datetime.utcnow().isoformat()


@router.post("/run", summary="Create automation job")
def run_job(payload: dict, current_user: dict = Depends(get_current_user)):
    # admin-only in production; local dev bypass allowed by get_current_user
    roles = (current_user.get('roles') or [])
    if not any(r in roles for r in ('USAREC_ADMIN', 'CO_CMD', 'BDE_CMD', 'BN_CMD')):
        raise HTTPException(status_code=403, detail='forbidden')
    job_id = str(uuid.uuid4())
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO automation_job(id, job_type, status, input_json, output_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?)', (
            job_id, payload.get('job_type') or 'unknown', 'queued', json.dumps(payload.get('input') or {}), json.dumps({}), now, now
        ))
        conn.commit()
        return {"status":"ok", "job_id": job_id}
    finally:
        conn.close()
from fastapi import APIRouter, HTTPException
from typing import Optional
from ..automation.engine import run_automation_for
from ..db import connect

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post('/run', summary='Trigger automation run')
def trigger_run(trigger: str = 'manual', target_type: str = 'event', target_id: Optional[int] = None, initiated_by: Optional[str] = 'system'):
    try:
        res = run_automation_for(trigger, target_type, target_id, initiated_by)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/runs')
def list_runs(limit: int = 50):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, started_at, finished_at, status FROM automation_run_log ORDER BY id DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
