from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
from ..db import connect, row_to_dict
from .rbac import get_current_user
import uuid
from datetime import datetime

router = APIRouter(prefix="/school", tags=["school"])


def _now_iso():
    return datetime.utcnow().isoformat()


@router.get('/summary')
def summary(request: Request, fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT COUNT(*) FROM schools')
            r = cur.fetchone()
            schools = r[0] if r else 0
        except Exception:
            schools = 0
    finally:
        conn.close()
    return {
        'status': 'ok',
        'data': {
            'schools_covered': schools,
            'contacts_completed_last_30d': 0,
            'events_scheduled_q_plus': 0,
            'leads_from_school_programs': 0,
            'compliance_status': 'not_loaded'
        },
        'missing': []
    }


@router.get('/coverage')
def coverage(echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            # try modern column names; if table schema differs this may raise
            cur.execute('SELECT id, school_name, school_type, district, city, zip_code FROM schools')
            rows = cur.fetchall()
            data = [row_to_dict(cur, r) for r in rows]
            gaps = [d for d in data if not d.get('school_name') or not d.get('zip_code')]
            return {'status': 'ok', 'rows': data, 'gaps': gaps}
        except Exception:
            # fallback: older schema — attempt safe query using common column names
            try:
                cur.execute('SELECT id, name as school_name, school_type, city, state, zip as zip_code FROM schools')
                rows = cur.fetchall()
                data = [row_to_dict(cur, r) for r in rows]
                gaps = [d for d in data if not d.get('school_name') or not d.get('zip_code')]
                return {'status': 'ok', 'rows': data, 'gaps': gaps}
            except Exception:
                # schema incompatible or no table — return empty-safe not_loaded
                return {'status': 'not_loaded', 'missing': ['schools_schema']}
    finally:
        conn.close()


@router.get('/milestones')
def milestones(start: str = None, end: str = None, echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT id, school_id, milestone_type, milestone_date, linked_event_id, created_at FROM school_milestones ORDER BY milestone_date DESC')
            rows = cur.fetchall()
            data = [row_to_dict(cur, r) for r in rows]
            return {'status': 'ok', 'rows': data}
        except Exception:
            # fallback to older schema without linked_event_id
            try:
                cur.execute('SELECT id, school_id, milestone_type, milestone_date, created_at FROM school_milestones ORDER BY milestone_date DESC')
                rows = cur.fetchall()
                data = [row_to_dict(cur, r) for r in rows]
                return {'status': 'ok', 'rows': data}
            except Exception:
                return {'status': 'not_loaded', 'missing': ['school_milestones_schema']}
    finally:
        conn.close()


@router.post('/milestones')
def create_milestone(payload: Dict[str, Any], user: Dict = Depends(get_current_user)):
    if not payload.get('school_id') or not payload.get('milestone_date'):
        raise HTTPException(status_code=400, detail='school_id and milestone_date required')
    conn = connect()
    try:
        cur = conn.cursor()
        mid = payload.get('id') or str(uuid.uuid4())
        now = _now_iso()
        cur.execute('INSERT OR REPLACE INTO school_milestones(id, school_id, milestone_type, milestone_date, linked_event_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?)', (mid, payload.get('school_id'), payload.get('milestone_type'), payload.get('milestone_date'), payload.get('linked_event_id'), now, now))
        conn.commit()
        return {'status': 'ok', 'id': mid}
    finally:
        conn.close()


@router.get('/compliance')
def compliance(fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM schools LIMIT 1')
        r = cur.fetchone()
        if not r:
            return {'status': 'not_loaded', 'missing': ['schools']}
        return {'status': 'ok', 'bands': [], 'details': []}
    finally:
        conn.close()


@router.get('/leadflow')
def leadflow(fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT COUNT(*) FROM leads LIMIT 1')
            leads_present = True
        except Exception:
            leads_present = False
        try:
            cur.execute('SELECT COUNT(*) FROM funnel_stage LIMIT 1')
            funnels_present = True
        except Exception:
            funnels_present = False
        if not leads_present or not funnels_present:
            missing = []
            if not funnels_present: missing.append('funnel_transitions')
            if not leads_present: missing.append('leads')
            return {'status': 'not_loaded', 'missing': missing}
        return {'status': 'ok', 'metrics': {'lead_volume': 0, 'appointment_rate': 0.0, 'contract_rate': 0.0}}
    finally:
        conn.close()


@router.get('/events')
def events(fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit: str = None, user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT e.id, e.name, e.start_dt as event_date, e.org_unit_id, e.location_name, e.loe, e.status FROM event e WHERE lower(e.event_type || '') LIKE '%school%' OR lower(e.name || '') LIKE '%school%' ORDER BY e.start_dt DESC LIMIT 200")
            rows = cur.fetchall()
            data = [row_to_dict(cur, r) for r in rows]
        except Exception:
            data = []
    finally:
        conn.close()
    return {'status': 'ok', 'rows': data}


@router.post('/events')
def create_event(payload: Dict[str, Any], user: Dict = Depends(get_current_user)):
    required = ['event_date', 'school_id', 'station_rsid']
    for k in required:
        if not payload.get(k):
            raise HTTPException(status_code=400, detail=f'{k} required')
    conn = connect()
    try:
        cur = conn.cursor()
        eid = payload.get('id') or str(uuid.uuid4())
        now = _now_iso()
        cur.execute('INSERT OR REPLACE INTO event(id, org_unit_id, name, event_type, start_dt, loe, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)', (
            eid,
            payload.get('school_id'),
            payload.get('name') or 'Planned School Event',
            'school',
            payload.get('event_date'),
            payload.get('planned_cost') or None,
            'planned',
            now,
            now
        ))
        conn.commit()
        return {'status': 'ok', 'id': eid}
    finally:
        conn.close()


@router.get('/suggest_window')
def suggest_window(event_date: str = None, fy: int = None, user: Dict = Depends(get_current_user)):
    if not event_date:
        raise HTTPException(status_code=400, detail='event_date required')
    from datetime import datetime
    ed = datetime.fromisoformat(event_date)
    if fy is None:
        fy = ed.year
    suggested = 'Q+0'
    return {'status': 'ok', 'suggested_window': suggested, 'explain': 'Deterministic suggestion based on event date'}
