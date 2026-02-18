from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from ..db import connect
from .rbac import require_scope

router = APIRouter(prefix="/boards", tags=["boards"])


@router.post('/', summary='Create a board')
def create_board(payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    name = payload.get('name')
    org_unit_id = payload.get('org_unit_id')
    description = payload.get('description')
    if not name:
        raise HTTPException(status_code=400, detail='missing_name')
    if allowed_orgs is not None and org_unit_id is not None and org_unit_id not in allowed_orgs:
        raise HTTPException(status_code=403, detail='forbidden')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO board(name, org_unit_id, description) VALUES (?,?,?)', (name, org_unit_id, description))
        conn.commit()
        bid = cur.lastrowid
        cur.execute('SELECT * FROM board WHERE id=?', (bid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.post('/{board_id}/sessions', summary='Create a board session')
def create_session(board_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    fy = payload.get('fy')
    qtr = payload.get('qtr')
    session_dt = payload.get('session_dt')
    notes = payload.get('notes')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM board WHERE id=?', (board_id,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO board_session(board_id, fy, qtr, session_dt, notes) VALUES (?,?,?,?,?)', (board_id, fy, qtr, session_dt, notes))
        conn.commit()
        sid = cur.lastrowid
        cur.execute('SELECT * FROM board_session WHERE id=?', (sid,))
        return dict(cur.fetchone())
    finally:
        conn.close()


@router.get('/{board_id}/sessions', summary='List board sessions')
def list_sessions(board_id: int, limit: int = 100, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM board WHERE id=?', (board_id,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('SELECT * FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT ?', (board_id, limit))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/{board_id}/qbr', summary='Simple QBR export for a board (JSON)')
def board_qbr(board_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id, name FROM board WHERE id=?', (board_id,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        # gather latest session and snapshots
        cur.execute('SELECT id, fy, qtr, session_dt, notes FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT 1', (board_id,))
        s = cur.fetchone()
        # aggregate metrics for last 5 sessions
        cur.execute('SELECT id FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT 5', (board_id,))
        sess_ids = [r[0] for r in cur.fetchall()]
        metrics = []
        if sess_ids:
            placeholders = ','.join(['?'] * len(sess_ids))
            cur.execute(f'SELECT metric_key, SUM(metric_value) as total_value, COUNT(*) as cnt FROM board_metric_snapshot WHERE board_session_id IN ({placeholders}) GROUP BY metric_key', tuple(sess_ids))
            metrics = [dict(r) for r in cur.fetchall()]
        # include counts
        cur.execute('SELECT COUNT(*) as sessions_count FROM board_session WHERE board_id=?', (board_id,))
        sc = cur.fetchone()
        return {'board': dict(b), 'latest_session': dict(s) if s else None, 'sessions_count': sc[0] if sc else 0, 'metrics': metrics}
    finally:
        conn.close()



@router.post('/{board_id}/metrics', summary='Add a metric snapshot to a board session')
def add_board_metric(board_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    board_session_id = payload.get('board_session_id')
    metric_key = payload.get('metric_key')
    metric_value = payload.get('metric_value')
    captured_at = payload.get('captured_at')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM board WHERE id=?', (board_id,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        if not captured_at:
            captured_at = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO board_metric_snapshot(board_session_id, metric_key, metric_value, captured_at) VALUES (?,?,?,?)', (board_session_id, metric_key, metric_value, captured_at))
        conn.commit()
        mid = cur.lastrowid
        cur.execute('SELECT * FROM board_metric_snapshot WHERE id=?', (mid,))
        return dict(cur.fetchone())
    finally:
        conn.close()
