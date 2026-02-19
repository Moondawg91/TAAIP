from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Any, Dict
from ..db import connect
from datetime import datetime
import json
from .rbac import require_scope, require_any_role

router = APIRouter(prefix="/budgets", tags=["budgets"])


def now_iso():
    return datetime.utcnow().isoformat()


def _row_to_dict(cur, row):
    if row is None:
        return None
    try:
        return dict(row)
    except Exception:
        cols = [c[0] for c in cur.description] if cur.description else []
        try:
            return dict(zip(cols, row))
        except Exception:
            # last-resort: return positional mapping
            return {str(i): v for i, v in enumerate(row)}


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/fy", summary="Create FY budget", dependencies=[Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))])
def create_fy_budget(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute("INSERT INTO fy_budget(org_unit_id, fy, total_allocated, created_at, updated_at) VALUES (?,?,?,?,?)",
                    (payload.get('org_unit_id'), payload.get('fy'), payload.get('total_allocated') or 0, now, now))
        conn.commit()
        bid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.fy_budget', 'fy_budget', bid, payload)
        return {"ok": True, "id": bid}
    finally:
        conn.close()


@router.get("/fy", summary="List FY budgets")
def list_fy_budgets(org_unit_id: Optional[int] = None, fy: Optional[int] = None, limit: int = 100, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM fy_budget WHERE 1=1"
        params: List[Any] = []
        if allowed_orgs is not None:
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += " AND org_unit_id=?"; params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f" AND org_unit_id IN ({placeholders})"
                params.extend(allowed_orgs)
        else:
            if org_unit_id is not None:
                sql += " AND org_unit_id=?"; params.append(org_unit_id)
        if fy is not None:
            sql += " AND fy=?"; params.append(fy)
        sql += " ORDER BY fy DESC LIMIT ?"; params.append(limit)
        try:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            out = []
            cols = [c[0] for c in cur.description] if cur.description else []
            for r in rows:
                try:
                    out.append(dict(r))
                except Exception:
                    out.append(dict(zip(cols, r)))
            return out
        except Exception:
            return []
    finally:
        conn.close()


@router.post("/line-item", summary="Create budget line item", dependencies=[Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))])
def create_line_item(payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute('INSERT INTO budget_line_item(fy_budget_id,qtr,event_id,category,vendor,description,amount,status,obligation_date,notes) VALUES (?,?,?,?,?,?,?,?,?,?)', (
            payload.get('fy_budget_id'), payload.get('qtr'), payload.get('event_id'), payload.get('category'), payload.get('vendor'), payload.get('description'), payload.get('amount') or 0, payload.get('status') or 'pending', payload.get('obligation_date'), payload.get('notes')
        ))
        conn.commit()
        lid = cur.lastrowid
        write_audit(conn, payload.get('created_by') or 'system', 'create.budget_line_item', 'budget_line_item', lid, payload)
        return {"ok": True, "id": lid}
    finally:
        conn.close()


@router.get("/line-item", summary="List line items")
def list_line_items(fy_budget_id: Optional[int] = None, event_id: Optional[int] = None, limit: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM budget_line_item WHERE 1=1'
        params: List[Any] = []
        if fy_budget_id is not None:
            # verify fy_budget belongs to allowed orgs when RBAC active
            if allowed_orgs is not None:
                cur.execute('SELECT org_unit_id FROM fy_budget WHERE id=?', (fy_budget_id,))
                fb = cur.fetchone()
                fb_d = _row_to_dict(cur, fb)
                if not fb_d or fb_d.get('org_unit_id') not in allowed_orgs:
                    return []
            sql += ' AND fy_budget_id=?'; params.append(fy_budget_id)
        if event_id is not None:
            if allowed_orgs is not None:
                cur.execute('SELECT org_unit_id FROM event WHERE id=?', (event_id,))
                ev = cur.fetchone()
                ev_d = _row_to_dict(cur, ev)
                if not ev_d or ev_d.get('org_unit_id') not in allowed_orgs:
                    return []
            sql += ' AND event_id=?'; params.append(event_id)
        sql += ' ORDER BY id DESC LIMIT ?'; params.append(limit)
        try:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            out = []
            cols = [c[0] for c in cur.description] if cur.description else []
            for r in rows:
                try:
                    out.append(dict(r))
                except Exception:
                    out.append(dict(zip(cols, r)))
            return out
        except Exception:
            return []
    finally:
        conn.close()
