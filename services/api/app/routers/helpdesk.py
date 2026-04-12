from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect, row_to_dict
from datetime import datetime
from .rbac import require_any_role, require_perm

router = APIRouter(prefix="/tickets", tags=["helpdesk"])

def now_iso():
    return datetime.utcnow().isoformat()


@router.post("/", summary="Create ticket")
def create_ticket(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO tickets(title,category,description,priority,status,created_by,created_at) VALUES (?,?,?,?,?,?,?)', (
            payload.get('title'), payload.get('category'), payload.get('description'), payload.get('priority') or 'medium', payload.get('status') or 'open', payload.get('created_by') or 'anonymous', now
        ))
        conn.commit()
        tid = cur.lastrowid
        cur.execute('SELECT * FROM tickets WHERE id=?', (tid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.get("/", summary="List tickets")
def list_tickets(limit: int = 100, status: Optional[str] = None):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM tickets WHERE (archived IS NULL OR archived=0)'
        params: List[Any] = []
        if status:
            sql += ' AND status=?'
            params.append(status)
        sql += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, tuple(params))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{ticket_id}", summary="Get ticket")
def get_ticket(ticket_id: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='not found')
        return row_to_dict(cur, r)
    finally:
        conn.close()


@router.put("/{ticket_id}", summary="Update ticket")
def update_ticket(ticket_id: int, payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM tickets WHERE id=?', (ticket_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='not found')
        now = now_iso()
        cur.execute('UPDATE tickets SET title=?, category=?, description=?, priority=?, status=?, updated_at=? WHERE id=?', (
            payload.get('title'), payload.get('category'), payload.get('description'), payload.get('priority'), payload.get('status'), now, ticket_id
        ))
        conn.commit()
        cur.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.delete("/{ticket_id}", summary="Archive ticket")
def delete_ticket(ticket_id: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM tickets WHERE id=?', (ticket_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='not found')
        # soft-delete
        cur.execute('UPDATE tickets SET archived=1, updated_at=? WHERE id=?', (now_iso(), ticket_id))
        conn.commit()
        return {'status': 'ok'}
    finally:
        conn.close()
