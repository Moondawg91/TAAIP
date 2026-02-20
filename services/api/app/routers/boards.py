from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from ..db import connect, row_to_dict
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
        # Ensure board tables exist for legacy/compat scenarios
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            org_unit_id INTEGER,
            description TEXT,
            created_at TEXT,
            record_status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS board_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER,
            fy INTEGER,
            qtr INTEGER,
            session_dt TEXT,
            notes TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS board_metric_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_session_id INTEGER,
            metric_key TEXT,
            metric_value REAL,
            captured_at TEXT
        );
        ''')
        cur.execute('INSERT INTO board(name, org_unit_id, description) VALUES (?,?,?)', (name, org_unit_id, description))
        conn.commit()
        bid = cur.lastrowid
        cur.execute('SELECT * FROM board WHERE id=?', (bid,))
        return row_to_dict(cur, cur.fetchone())
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
        b = row_to_dict(cur, cur.fetchone())
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('INSERT INTO board_session(board_id, fy, qtr, session_dt, notes) VALUES (?,?,?,?,?)', (board_id, fy, qtr, session_dt, notes))
        conn.commit()
        sid = cur.lastrowid
        cur.execute('SELECT * FROM board_session WHERE id=?', (sid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.get('/{board_id}/sessions', summary='List board sessions')
def list_sessions(board_id: int, limit: int = 100, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id FROM board WHERE id=?', (board_id,))
        b = row_to_dict(cur, cur.fetchone())
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute('SELECT * FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT ?', (board_id, limit))
        rows = cur.fetchall()
        return [row_to_dict(cur, r) for r in rows]
    finally:
        conn.close()


@router.get('/{board_id}/qbr', summary='Simple QBR export for a board (JSON)')
def board_qbr(board_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT org_unit_id, name FROM board WHERE id=?', (board_id,))
        b = row_to_dict(cur, cur.fetchone())
        if not b:
            raise HTTPException(status_code=404, detail='board_not_found')
        if allowed_orgs is not None and b['org_unit_id'] not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        # gather latest session and snapshots
        cur.execute('SELECT id, fy, qtr, session_dt, notes FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT 1', (board_id,))
        s = row_to_dict(cur, cur.fetchone())
        # aggregate metrics for last 5 sessions
        cur.execute('SELECT id FROM board_session WHERE board_id=? ORDER BY id DESC LIMIT 5', (board_id,))
        sess_ids = [r['id'] for r in cur.fetchall()]
        metrics = []
        if sess_ids:
            placeholders = ','.join(['?'] * len(sess_ids))
            cur.execute(f'SELECT metric_key, SUM(metric_value) as total_value, COUNT(*) as cnt FROM board_metric_snapshot WHERE board_session_id IN ({placeholders}) GROUP BY metric_key', tuple(sess_ids))
            metrics = [dict(r) for r in cur.fetchall()]
        # include counts
        cur.execute('SELECT COUNT(*) as sessions_count FROM board_session WHERE board_id=?', (board_id,))
        sc = row_to_dict(cur, cur.fetchone())
        return {'board': b, 'latest_session': s if s else None, 'sessions_count': sc.get('sessions_count', 0) if sc else 0, 'metrics': metrics}
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
        b = row_to_dict(cur, cur.fetchone())
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
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()
