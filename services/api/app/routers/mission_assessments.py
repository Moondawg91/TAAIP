from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from ..db import connect, row_to_dict
from datetime import datetime
from uuid import uuid4
from .rbac import require_any_role

router = APIRouter(prefix="/mission_assessments", tags=["mission_assessments"])


def _now():
    return datetime.utcnow().isoformat()


@router.get("/latest")
def get_latest(period_type: Optional[str] = None, scope: Optional[str] = None):
    """Return the latest mission assessment for the given scope and period_type."""
    conn = connect()
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM mission_assessments WHERE 1=1"
        params = []
        if period_type:
            sql += ' AND period_type=?'; params.append(period_type)
        if scope:
            sql += ' AND scope=?'; params.append(scope)
        sql += ' ORDER BY created_at DESC LIMIT 1'
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        if not row:
            return {}
        return row_to_dict(cur, row)
    finally:
        conn.close()


@router.post("/", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def upsert_assessment(payload: Dict[str, Any]):
    """Create or update a mission assessment snapshot."""
    period_type = payload.get('period_type')
    period_value = payload.get('period_value')
    scope = payload.get('scope')
    metrics = payload.get('metrics')
    narrative = payload.get('narrative')
    if not period_type or not period_value or not scope:
        raise HTTPException(status_code=400, detail='missing_fields')
    conn = connect()
    try:
        cur = conn.cursor()
        now = _now()
        # upsert by id if provided, otherwise create new id
        aid = payload.get('id') or str(uuid4())
        cur.execute('INSERT OR REPLACE INTO mission_assessments(id, period_type, period_value, scope, metrics_json, narrative, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)', (
            aid, period_type, str(period_value), scope, (metrics and (str(metrics) if isinstance(metrics, str) else str(metrics))) or '{}', narrative or '', now, now
        ))
        conn.commit()
        cur.execute('SELECT * FROM mission_assessments WHERE id=?', (aid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()
