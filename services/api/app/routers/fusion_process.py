from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from ..db import connect, row_to_dict
from .rbac import require_perm
from datetime import datetime
import json

router = APIRouter(prefix="/fusion_process", tags=["fusion_process"])


def now_iso():
    return datetime.utcnow().isoformat()


@router.get('/', summary='List fusion sessions', dependencies=[Depends(require_perm('pages.command_center.view'))])
def list_sessions(limit: int = 100, include_archived: bool = False):
    conn = connect()
    try:
        cur = conn.cursor()
        # filter out archived sessions by default
        try:
            cur.execute('PRAGMA table_info(fusion_process)')
            cols = [r[1] for r in cur.fetchall()]
        except Exception:
            cols = []
        if 'archived' in cols and not include_archived:
            cur.execute('SELECT id, fusion_id, session_date, participants, insights, actions, status, created_at FROM fusion_process WHERE (archived IS NULL OR archived=0) ORDER BY session_date DESC LIMIT ?', (limit,))
        else:
            cur.execute('SELECT id, fusion_id, session_date, participants, insights, actions, status, created_at FROM fusion_process ORDER BY session_date DESC LIMIT ?', (limit,))
        rows = cur.fetchall()
        out = []
        for r in rows:
            try:
                if isinstance(r, dict):
                    rec = r
                else:
                    rec = {'id': r[0], 'fusion_id': r[1], 'session_date': r[2], 'participants': r[3], 'insights': r[4], 'actions': r[5], 'status': r[6], 'created_at': r[7]}
                # normalize participants JSON
                parts = rec.get('participants')
                if isinstance(parts, str):
                    try:
                        parts = json.loads(parts)
                    except Exception:
                        parts = [parts]
                rec['participants'] = parts or []
                out.append(rec)
            except Exception:
                continue
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/', summary='Create fusion session', dependencies=[Depends(require_perm('pages.command_center.edit'))])
def create_session(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        participants = payload.get('participants')
        if isinstance(participants, (list, tuple)):
            participants = json.dumps(participants)
        # attempt to insert archived flag when schema supports it
        try:
            cur.execute('PRAGMA table_info(fusion_process)')
            fcols = [r[1] for r in cur.fetchall()]
        except Exception:
            fcols = []
        if 'archived' in fcols:
            cur.execute('INSERT INTO fusion_process(fusion_id, session_date, participants, insights, actions, status, created_at, archived) VALUES (?,?,?,?,?,?,?,?)', (
                payload.get('fusion_id'), payload.get('session_date'), participants, payload.get('insights'), payload.get('actions'), payload.get('status') or 'draft', now, 0
            ))
        else:
            cur.execute('INSERT INTO fusion_process(fusion_id, session_date, participants, insights, actions, status, created_at) VALUES (?,?,?,?,?,?,?)', (
                payload.get('fusion_id'), payload.get('session_date'), participants, payload.get('insights'), payload.get('actions'), payload.get('status') or 'draft', now
            ))
        conn.commit()
        sid = cur.lastrowid
        cur.execute('SELECT id, fusion_id, session_date, participants, insights, actions, status, created_at FROM fusion_process WHERE id=?', (sid,))
        row = cur.fetchone()
        return row_to_dict(cur, row)
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.put('/{id}', summary='Update fusion session', dependencies=[Depends(require_perm('pages.command_center.edit'))])
def update_session(id: int, payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM fusion_process WHERE id=?', (id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='not found')
        participants = payload.get('participants')
        if isinstance(participants, (list, tuple)):
            participants = json.dumps(participants)
        cur.execute('UPDATE fusion_process SET fusion_id=?, session_date=?, participants=?, insights=?, actions=?, status=? WHERE id=?', (
            payload.get('fusion_id'), payload.get('session_date'), participants, payload.get('insights'), payload.get('actions'), payload.get('status'), id
        ))
        conn.commit()
        cur.execute('SELECT id, fusion_id, session_date, participants, insights, actions, status, created_at FROM fusion_process WHERE id=?', (id,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.delete('/{id}', summary='Archive fusion session', dependencies=[Depends(require_perm('pages.command_center.edit'))])
def delete_session(id: int, payload: Dict[str, Any] = None):
    payload = payload or {}
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM fusion_process WHERE id=?', (id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='not found')
        who = payload.get('archived_by') if isinstance(payload, dict) else None
        # prefer soft-archive when schema supports it
        try:
            cur.execute('PRAGMA table_info(fusion_process)')
            cols = [r[1] for r in cur.fetchall()]
        except Exception:
            cols = []
        if 'archived' in cols:
            try:
                cur.execute('UPDATE fusion_process SET archived=1, archived_at=?, archived_by=? WHERE id=?', (now_iso(), who, id))
                conn.commit()
                return {'status': 'archived'}
            except Exception:
                # fall through to hard delete
                pass
        # fallback: hard delete (only if archiving not possible)
        cur.execute('DELETE FROM fusion_process WHERE id=?', (id,))
        conn.commit()
        return {'status': 'deleted'}
    finally:
        try:
            conn.close()
        except Exception:
            pass
