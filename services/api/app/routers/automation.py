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
