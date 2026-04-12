from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from .. import db
from ..db import row_to_dict

router = APIRouter()

@router.get('/twg_sessions/{twg_id}')
def get_twg_summary(twg_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM twg_agenda_items WHERE twg_id=?', (twg_id,))
        agenda = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM twg_minutes WHERE twg_id=?', (twg_id,))
        minutes = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM twg_tasks WHERE twg_id=?', (twg_id,))
        tasks = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM twg_board_items WHERE twg_id=?', (twg_id,))
        items = cur.fetchone()[0]
        return {'twg_id': twg_id, 'agenda_count': agenda, 'minutes_count': minutes, 'tasks_count': tasks, 'board_items_count': items}
    finally:
        conn.close()

# Board items
@router.get('/twg_sessions/{twg_id}/board_items')
def list_board_items(twg_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM twg_board_items WHERE twg_id=? ORDER BY created_at DESC', (twg_id,))
        else:
            cur.execute('SELECT * FROM twg_board_items WHERE twg_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (twg_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()

@router.post('/twg_sessions/{twg_id}/board_items')
def create_board_item(twg_id: str, payload: Dict[str, Any] = Body(...)):
    title = payload.get('title')
    description = payload.get('description')
    linked_recommendation_id = payload.get('linked_recommendation_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO twg_board_items(twg_id, title, description, linked_recommendation_id, created_at, archived) VALUES (?,?,?,?,?,?)', (twg_id, title, description, linked_recommendation_id, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.delete('/twg_board_items/{item_id}')
def delete_board_item(item_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE twg_board_items SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, item_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

@router.post('/twg_board_items/{item_id}/send_to_board')
def send_twg_item_to_board(item_id: int, payload: Dict[str, Any] = Body(...)):
    # create a board_decision placeholder
    board_id = payload.get('board_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT title, description FROM twg_board_items WHERE id=?', (item_id,))
        it = cur.fetchone()
        if not it:
            raise HTTPException(status_code=404, detail='twg item not found')
        title = it[0]
        desc = it[1]
        cur.execute('INSERT INTO board_decisions(board_id, decision_text, status, created_by, created_at) VALUES (?,?,?,?,?)', (board_id, desc or title, 'pending', payload.get('created_by'), db.now_iso()))
        conn.commit()
        return {'board_decision_id': cur.lastrowid}
    finally:
        conn.close()
