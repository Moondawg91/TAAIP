from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from .. import db
from ..db import row_to_dict

router = APIRouter()

@router.get('/targeting_boards/{board_id}')
def get_board_summary(board_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM board_decisions WHERE board_id=?', (board_id,))
        decisions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM board_decisions WHERE board_id=? AND status='approved'", (board_id,))
        approved = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM board_decisions WHERE board_id=? AND status='deferred'", (board_id,))
        deferred = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM board_execution_items WHERE board_id=?', (board_id,))
        exec_items = cur.fetchone()[0]
        return {'board_id': board_id, 'decisions_total': decisions, 'approved': approved, 'deferred': deferred, 'execution_items': exec_items}
    finally:
        conn.close()

# Decisions
@router.get('/targeting_boards/{board_id}/decisions')
def list_decisions(board_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM board_decisions WHERE board_id=? ORDER BY created_at DESC', (board_id,))
        else:
            cur.execute('SELECT * FROM board_decisions WHERE board_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (board_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()

@router.post('/targeting_boards/{board_id}/decisions')
def create_decision(board_id: str, payload: Dict[str, Any] = Body(...)):
    decision_text = payload.get('decision_text')
    created_by = payload.get('created_by')
    status = payload.get('status','pending')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO board_decisions(board_id, decision_text, status, decided_at, created_by, created_at, archived) VALUES (?,?,?,?,?,?,?)', (board_id, decision_text, status, payload.get('decided_at'), created_by, db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()

@router.post('/board_decisions/{decision_id}/create_execution')
def create_execution_from_decision(decision_id: int, payload: Dict[str, Any] = Body(...)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT board_id, decision_text FROM board_decisions WHERE id=?', (decision_id,))
        d = cur.fetchone()
        if not d:
            raise HTTPException(status_code=404, detail='decision not found')
        board_id = d[0]
        details = payload.get('details') or d[1]
        cur.execute('INSERT INTO board_execution_items(board_id, title, details, status, created_at) VALUES (?,?,?,?,?)', (board_id, payload.get('title') or 'Execution for decision', details, 'open', db.now_iso()))
        conn.commit()
        return {'execution_item_id': cur.lastrowid}
    finally:
        conn.close()

# Execution items
@router.get('/targeting_boards/{board_id}/execution_items')
def list_execution_items(board_id: str, include_archived: bool = False):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if include_archived:
            cur.execute('SELECT * FROM board_execution_items WHERE board_id=? ORDER BY created_at DESC', (board_id,))
        else:
            cur.execute('SELECT * FROM board_execution_items WHERE board_id=? AND (archived IS NULL OR archived=0) ORDER BY created_at DESC', (board_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.delete('/board_decisions/{decision_id}')
def delete_board_decision(decision_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE board_decisions SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, decision_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()


@router.delete('/board_execution_items/{execution_id}')
def delete_board_execution(execution_id: int, payload: Dict[str, Any] = Body({})):
    conn = db.connect()
    try:
        cur = conn.cursor()
        who = payload.get('archived_by') if payload and isinstance(payload, dict) else None
        cur.execute('UPDATE board_execution_items SET archived=1, archived_at=?, archived_by=? WHERE id=?', (db.now_iso(), who, execution_id))
        conn.commit()
        return {'status': 'archived'}
    finally:
        conn.close()

@router.post('/targeting_boards/{board_id}/execution_items')
def create_execution_item(board_id: str, payload: Dict[str, Any] = Body(...)):
    title = payload.get('title')
    details = payload.get('details')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO board_execution_items(board_id, title, details, status, created_at, archived) VALUES (?,?,?,?,?,?)', (board_id, title, details, payload.get('status','open'), db.now_iso(), 0))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()
