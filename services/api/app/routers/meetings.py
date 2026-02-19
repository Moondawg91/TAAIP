from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from .. import db
from datetime import datetime
from .rbac import require_scope

router = APIRouter(prefix='/meetings', tags=['meetings'])

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/')
def create_meeting(payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        # optional org filter
        org_unit_id = payload.get('org_unit_id')
        if allowed_orgs is not None and org_unit_id is not None and org_unit_id not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        cur.execute('INSERT INTO meeting(meeting_type, title, purpose, date_time, location, chair, participants_json, created_by, created_at, updated_at, import_job_id, tags, org_unit_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            payload.get('meeting_type'), payload.get('title'), payload.get('purpose'), payload.get('date_time'), payload.get('location'), payload.get('chair'), payload.get('participants_json'), payload.get('created_by'), now_iso(), now_iso(), payload.get('import_job_id'), payload.get('tags'), org_unit_id
        ))
        conn.commit()
        meeting_id = cur.lastrowid
        # auto-create calendar event for meeting
        try:
            cur.execute('INSERT INTO calendar_event(linked_type, linked_id, title, start_dt, end_dt, location, notes, status, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                'meeting', meeting_id, payload.get('title'), payload.get('date_time'), payload.get('date_time'), payload.get('location'), payload.get('purpose'), 'scheduled', payload.get('created_by'), now_iso(), now_iso()
            ))
            conn.commit()
        except Exception:
            # non-fatal if calendar insert fails
            pass
        return {'id': meeting_id}
    finally:
        conn.close()


@router.post('/{meeting_id}/agenda')
def add_agenda(meeting_id: int, item: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM meeting WHERE id=?', (meeting_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail='meeting_not_found')
        if allowed_orgs is not None and m['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO agenda_item(meeting_id, sequence, topic, presenter, decision_required, created_at) VALUES (?,?,?,?,?,?)', (
            meeting_id, item.get('sequence'), item.get('topic'), item.get('presenter'), 1 if item.get('decision_required') else 0, now_iso()
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.post('/{meeting_id}/minutes')
def add_minutes(meeting_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM meeting WHERE id=?', (meeting_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail='meeting_not_found')
        if allowed_orgs is not None and m['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO minutes(meeting_id, summary_text, minutes_json, created_at) VALUES (?,?,?,?)', (
            meeting_id, payload.get('summary_text'), payload.get('minutes_json'), now_iso()
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.post('/{meeting_id}/action')
def add_action(meeting_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM meeting WHERE id=?', (meeting_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail='meeting_not_found')
        if allowed_orgs is not None and m['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO action_item(meeting_id, task_id, owner, suspense_date, status, notes, created_at) VALUES (?,?,?,?,?,?,?)', (
            meeting_id, payload.get('task_id'), payload.get('owner'), payload.get('suspense_date'), payload.get('status'), payload.get('notes'), now_iso()
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.post('/{meeting_id}/decision')
def add_decision(meeting_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM meeting WHERE id=?', (meeting_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail='meeting_not_found')
        if allowed_orgs is not None and m['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO decision(meeting_id, decision_text, decision_date, authority, created_at) VALUES (?,?,?,?,?)', (
            meeting_id, payload.get('decision_text'), payload.get('decision_date'), payload.get('authority'), now_iso()
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()
