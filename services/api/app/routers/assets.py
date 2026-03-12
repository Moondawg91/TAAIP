from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from .. import db
import json
from .rbac import require_scope

router = APIRouter(prefix="/v2/assets", tags=["assets"])


@router.get('/catalog')
def list_catalog(allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM asset_catalog WHERE enabled=1 ORDER BY asset_name')
        rows = [dict(r) for r in cur.fetchall()]
        # parse json fields
        for r in rows:
            if r.get('supported_objectives'):
                try:
                    r['supported_objectives'] = json.loads(r['supported_objectives'])
                except Exception:
                    pass
            if r.get('supported_tactics'):
                try:
                    r['supported_tactics'] = json.loads(r['supported_tactics'])
                except Exception:
                    pass
        return rows
    finally:
        conn.close()


@router.get('/catalog/{asset_id}')
def get_catalog_item(asset_id: str, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM asset_catalog WHERE asset_id = ? LIMIT 1', (asset_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        r = dict(row)
        try:
            r['supported_objectives'] = json.loads(r.get('supported_objectives') or '[]')
        except Exception:
            pass
        try:
            r['supported_tactics'] = json.loads(r.get('supported_tactics') or '[]')
        except Exception:
            pass
        return r
    finally:
        conn.close()


@router.get('/inventory')
def query_inventory(unit_rsid: Optional[str] = None, status: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM asset_inventory WHERE 1=1'
        params = []
        if unit_rsid:
            q += ' AND (owning_unit_rsid = ? OR holding_unit_rsid = ?)'
            params.extend([unit_rsid, unit_rsid])
        if status:
            q += ' AND status = ?'
            params.append(status)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post('/requests')
def create_request(req: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        created = req.get('created_at') or ''
        # store json fields as text
        requested_ids = None
        if req.get('requested_asset_ids') is not None:
            requested_ids = json.dumps(req.get('requested_asset_ids'))
        cur.execute('INSERT INTO asset_requests(request_id, unit_rsid, event_id, requested_asset_type, requested_asset_ids, priority, needed_start_dt, needed_end_dt, justification, approval_status, approval_chain, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            req.get('request_id'), req.get('unit_rsid'), req.get('event_id'), req.get('requested_asset_type'), requested_ids, req.get('priority'), req.get('needed_start_dt'), req.get('needed_end_dt'), req.get('justification'), req.get('approval_status') or 'draft', json.dumps(req.get('approval_chain') or []), req.get('created_by'), created, created
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/requests')
def list_requests(unit_rsid: Optional[str] = None, fy: Optional[int] = None, qtr: Optional[int] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM asset_requests WHERE 1=1'
        params = []
        if unit_rsid:
            q += ' AND unit_rsid = ?'
            params.append(unit_rsid)
        q += ' ORDER BY created_at DESC'
        cur.execute(q, params)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get('requested_asset_ids'):
                try:
                    r['requested_asset_ids'] = json.loads(r['requested_asset_ids'])
                except Exception:
                    pass
            if r.get('approval_chain'):
                try:
                    r['approval_chain'] = json.loads(r['approval_chain'])
                except Exception:
                    pass
        return rows
    finally:
        conn.close()


@router.patch('/requests/{request_id}')
def patch_request(request_id: str, patch: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        # build simple SET clause
        sets = []
        params = []
        for k, v in patch.items():
            if k == 'requested_asset_ids':
                sets.append('requested_asset_ids = ?')
                params.append(json.dumps(v))
            else:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            raise HTTPException(status_code=400, detail='no fields')
        params.append(request_id)
        q = f"UPDATE asset_requests SET {', '.join(sets)} WHERE request_id = ?"
        cur.execute(q, params)
        conn.commit()
        return {'updated': cur.rowcount}
    finally:
        conn.close()


@router.post('/assignments')
def create_assignment(a: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO asset_assignments(assignment_id, request_id, asset_id, assigned_unit_rsid, assigned_start_dt, assigned_end_dt, assignment_status, notes) VALUES (?,?,?,?,?,?,?,?)', (
            a.get('assignment_id'), a.get('request_id'), a.get('asset_id'), a.get('assigned_unit_rsid'), a.get('assigned_start_dt'), a.get('assigned_end_dt'), a.get('assignment_status') or 'scheduled', a.get('notes')
        ))
        conn.commit()
        return {'id': cur.lastrowid}
    finally:
        conn.close()


@router.get('/assignments')
def list_assignments(unit_rsid: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        q = 'SELECT * FROM asset_assignments WHERE 1=1'
        params = []
        if unit_rsid:
            q += ' AND assigned_unit_rsid = ?'
            params.append(unit_rsid)
        if start:
            q += ' AND assigned_start_dt >= ?'
            params.append(start)
        if end:
            q += ' AND assigned_end_dt <= ?'
            params.append(end)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get('/recommendations')
def recommend_assets(unit_rsid: str = Query(...), desired_effect: str = Query(...), tactic: str = Query(...), top_n: int = 5, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    """Simple recommendation: score enabled assets by matching capability weight and tactic/objective match."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        # find enabled assets that list the tactic/objective
        cur.execute('SELECT * FROM asset_catalog WHERE enabled=1')
        candidates = [dict(r) for r in cur.fetchall()]
        scored = []
        for c in candidates:
            score = 0.0
            try:
                objs = json.loads(c.get('supported_objectives') or '[]')
            except Exception:
                objs = []
            try:
                tactics = json.loads(c.get('supported_tactics') or '[]')
            except Exception:
                tactics = []
            if desired_effect in objs:
                score += 1.0
            if tactic in tactics:
                score += 1.0
            # add capability weights
            cur.execute('SELECT SUM(weight) as w FROM asset_capabilities WHERE asset_id = ?', (c.get('asset_id'),))
            row = cur.fetchone()
            if row and row['w']:
                score += float(row['w'])
            if score > 0:
                reason = []
                if desired_effect in objs:
                    reason.append(f"supports {desired_effect}")
                if tactic in tactics:
                    reason.append(f"matches tactic {tactic}")
                if row and row['w']:
                    reason.append(f"capability_weight={row['w']}")
                scored.append({'asset': c, 'score': score, 'reason': '; '.join(reason)})
        scored.sort(key=lambda x: x['score'], reverse=True)
        return {'unit_rsid': unit_rsid, 'desired_effect': desired_effect, 'tactic': tactic, 'results': scored[:top_n]}
    finally:
        conn.close()
