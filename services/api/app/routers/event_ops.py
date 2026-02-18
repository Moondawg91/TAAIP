from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from ..automation.engine import simple_event_recommendation
from ..db import connect
from .rbac import get_allowed_org_units

router = APIRouter(prefix="/events", tags=["events_ops"])


@router.post("/{event_id}/roi", summary="Compute / persist ROI recommendation for an event")
def compute_event_roi(event_id: int, initiated_by: Optional[str] = 'system', allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    # enforce scope if necessary
    if allowed_orgs is not None:
        if allowed_orgs and event_id is not None:
            # check that event's org_unit is in allowed set
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute('SELECT org_unit_id FROM event WHERE id=?', (event_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail='event_not_found')
                if row['org_unit_id'] not in allowed_orgs:
                    return HTTPException(status_code=403, detail='forbidden')
            finally:
                conn.close()

    try:
        rec = simple_event_recommendation(event_id, created_by=initiated_by)
        if rec.get('error'):
            raise HTTPException(status_code=404, detail=rec.get('error'))
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}/roi", summary="Get latest ROI recommendation for event")
def get_event_roi(event_id: int, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM event WHERE id=?', (event_id,))
        er = cur.fetchone()
        if not er:
            raise HTTPException(status_code=404, detail='event_not_found')
        if allowed_orgs is not None and er['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        cur.execute('SELECT id, scope_type, scope_id, fy, qtr, output_json, created_at FROM ai_recommendation WHERE scope_type=? AND scope_id=? ORDER BY id DESC LIMIT 1', ('event', event_id))
        r = cur.fetchone()
        if not r:
            return {}
        return dict(r)
    finally:
        conn.close()


@router.post("/{event_id}/after_action", summary="Record an after-action / lesson-learned for an event")
def record_after_action(event_id: int, observation: str, recommendation: Optional[str] = None, impact: Optional[str] = None, created_by: Optional[str] = 'system', allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM event WHERE id=?', (event_id,))
        er = cur.fetchone()
        if not er:
            raise HTTPException(status_code=404, detail='event_not_found')
        if allowed_orgs is not None and er['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO lesson_learned(org_unit_id, event_id, observation, recommendation, impact, created_at) VALUES (?,?,?,?,?,?)', (
            er['org_unit_id'], event_id, observation, recommendation, impact, now
        ))
        conn.commit()
        lid = cur.lastrowid
        cur.execute('SELECT * FROM lesson_learned WHERE id=?', (lid,))
        return dict(cur.fetchone())
    finally:
        conn.close()
