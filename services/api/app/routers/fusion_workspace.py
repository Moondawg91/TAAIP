from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from .. import db
from ..db import row_to_dict

router = APIRouter()

@router.get('/fusion_sessions/{fusion_id}')
def get_fusion_summary(fusion_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        # counts for summary
        cur.execute('SELECT COUNT(*) AS cnt FROM fusion_agenda_items WHERE fusion_id=?', (fusion_id,))
        agenda_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) AS cnt FROM fusion_notes WHERE fusion_id=?', (fusion_id,))
        notes_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) AS cnt FROM fusion_findings WHERE fusion_id=?', (fusion_id,))
        findings_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) AS cnt FROM fusion_recommendations WHERE fusion_id=?', (fusion_id,))
        rec_count = cur.fetchone()[0]
        return {
            'fusion_id': fusion_id,
            'agenda_count': agenda_count,
            'notes_count': notes_count,
            'findings_count': findings_count,
            'recommendation_count': rec_count
        }
    finally:
        conn.close()


@router.delete('/fusion_findings/{finding_id}')
def delete_finding(finding_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE fusion_findings SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, finding_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

# Agenda items
@router.get('/fusion_sessions/{fusion_id}/agenda')
def list_agenda(fusion_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM fusion_agenda_items WHERE fusion_id=? ORDER BY order_idx ASC', (fusion_id,))
        else:
            cur.execute('SELECT * FROM fusion_agenda_items WHERE fusion_id=? AND (archived IS NULL OR archived=0) ORDER BY order_idx ASC', (fusion_id,))
        rows = cur.fetchall()
        return [row_to_dict(cur, r) for r in rows]
    finally:
        conn.close()


@router.delete('/fusion_notes/{note_id}')
def delete_note(note_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE fusion_notes SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, note_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

@router.post('/fusion_sessions/{fusion_id}/agenda')
def create_agenda(fusion_id: str, payload: Dict[str, Any] = Body(...)):
    title = payload.get('title')
    description = payload.get('description')
    order_idx = payload.get('order_idx', 0)
    created_by = payload.get('created_by')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO fusion_agenda_items(fusion_id, title, description, order_idx, created_by, created_at, archived) VALUES (?,?,?,?,?,?,?)', (fusion_id, title, description, order_idx, created_by, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.delete('/fusion_recommendations/{rec_id}')
def delete_recommendation(rec_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE fusion_recommendations SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, rec_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

@router.put('/fusion_agenda_items/{item_id}')
def update_agenda(item_id: int, payload: Dict[str, Any] = Body(...)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        fields = []
        vals = []
        for k in ('title','description','order_idx'):
            if k in payload:
                fields.append(f"{k}=?")
                vals.append(payload[k])
        vals.append(item_id)
        if fields:
            cur.execute(f"UPDATE fusion_agenda_items SET {', '.join(fields)}, updated_at=? WHERE id=?", (*vals, db.now_iso(), item_id))
            conn.commit()
        return {'id': item_id}
    finally:
        conn.close()

@router.delete('/fusion_agenda_items/{item_id}')
def delete_agenda(item_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        # soft-archive instead of hard delete
        who = payload.get('archived_by')
        cur.execute('UPDATE fusion_agenda_items SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, item_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

# Notes
@router.get('/fusion_sessions/{fusion_id}/notes')
def list_notes(fusion_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM fusion_notes WHERE fusion_id=? ORDER BY created_at DESC', (fusion_id,))
        else:
            cur.execute('SELECT * FROM fusion_notes WHERE fusion_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (fusion_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()

@router.post('/fusion_sessions/{fusion_id}/notes')
def create_note(fusion_id: str, payload: Dict[str, Any] = Body(...)):
    note_text = payload.get('note_text')
    author = payload.get('author')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO fusion_notes(fusion_id, note_text, author, created_at, archived) VALUES (?,?,?,?,?)', (fusion_id, note_text, author, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()

# Findings
@router.get('/fusion_sessions/{fusion_id}/findings')
def list_findings(fusion_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM fusion_findings WHERE fusion_id=? ORDER BY created_at DESC', (fusion_id,))
        else:
            cur.execute('SELECT * FROM fusion_findings WHERE fusion_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (fusion_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()

@router.post('/fusion_sessions/{fusion_id}/findings')
def create_finding(fusion_id: str, payload: Dict[str, Any] = Body(...)):
    finding_text = payload.get('finding_text')
    severity = payload.get('severity')
    created_by = payload.get('created_by')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO fusion_findings(fusion_id, finding_text, severity, created_by, created_at, archived) VALUES (?,?,?,?,?,?)', (fusion_id, finding_text, severity, created_by, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()

# Recommendations
@router.get('/fusion_sessions/{fusion_id}/recommendations')
def list_recommendations(fusion_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM fusion_recommendations WHERE fusion_id=? ORDER BY created_at DESC', (fusion_id,))
        else:
            cur.execute('SELECT * FROM fusion_recommendations WHERE fusion_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (fusion_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()

@router.post('/fusion_sessions/{fusion_id}/recommendations')
def create_recommendation(fusion_id: str, payload: Dict[str, Any] = Body(...)):
    recommendation_text = payload.get('recommendation_text') or payload.get('text') or payload.get('recommendation')
    created_by = payload.get('created_by')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO fusion_recommendations(fusion_id, recommendation_text, created_by, created_at, archived) VALUES (?,?,?,?,?)', (fusion_id, recommendation_text, created_by, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()

@router.post('/fusion_recommendations/{rec_id}/send_to_twg')
def send_recommendation_to_twg(rec_id: int, payload: Dict[str, Any] = Body(...)):
    # create a TWG board item from the recommendation and mark linked_to_twg
    twg_id = payload.get('twg_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        # fetch recommendation
        cur.execute('SELECT recommendation_text FROM fusion_recommendations WHERE id=?', (rec_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='recommendation not found')
        rec_text = r[0]
        cur.execute('INSERT INTO twg_board_items(twg_id, title, description, linked_recommendation_id, created_at, archived) VALUES (?,?,?,?,?,?)', (twg_id, 'Rec from Fusion', rec_text, rec_id, db.now_iso(), 0))
        cur.execute('UPDATE fusion_recommendations SET linked_to_twg=1 WHERE id=?', (rec_id,))
        conn.commit()
        return {'twg_board_item_id': cur.lastrowid}
    finally:
        conn.close()
