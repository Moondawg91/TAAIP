from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..db import connect, row_to_dict
from datetime import datetime
from .rbac import require_any_role
from uuid import uuid4

router = APIRouter(prefix="/projects/command_priorities", tags=["command_priorities"])


def _now():
    return datetime.utcnow().isoformat()


@router.get("/{scope}")
def list_priorities(scope: str, allowed: Optional[list] = Depends(lambda: None)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, org_unit_id as owner_scope, title, description, created_at, updated_at FROM command_priorities WHERE org_unit_id=? ORDER BY rank", (scope,))
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        # include LOEs for each (use priority_loe linking table)
        for p in rows:
            cur.execute("SELECT l.id, l.title, l.description, l.created_at, l.created_by FROM loes l JOIN priority_loe pl ON pl.loe_id=l.id WHERE pl.priority_id=? ORDER BY pl.id LIMIT 5", (p['id'],))
            p['loes'] = [row_to_dict(cur, r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.post("/{scope}", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def create_priority(scope: str, payload: dict):
    title = payload.get('title')
    description = payload.get('description')
    conn = connect()
    try:
        cur = conn.cursor()
        # enforce limit 3 per scope
        cur.execute("SELECT COUNT(1) as c FROM command_priorities WHERE org_unit_id=?", (scope,))
        if cur.fetchone()[0] >= 3:
            raise HTTPException(status_code=400, detail='max_priorities')
        now = _now()
        cur.execute("INSERT INTO command_priorities(org_unit_id, title, description, rank, created_at, updated_at) VALUES (?,?,?,?,?,?)", (scope, title, description, 99, now, now))
        conn.commit()
        pid = cur.lastrowid
        cur.execute("SELECT id, org_unit_id as owner_scope, title, description, created_at, updated_at FROM command_priorities WHERE id=?", (pid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.put("/{scope}/{priority_id}", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def update_priority(scope: str, priority_id: int, payload: dict):
    title = payload.get('title')
    description = payload.get('description')
    conn = connect()
    try:
        cur = conn.cursor()
        now = _now()
        cur.execute("UPDATE command_priorities SET title=?, description=?, updated_at=? WHERE id=? AND org_unit_id=?", (title, description, now, priority_id, scope))
        conn.commit()
        cur.execute("SELECT id, org_unit_id as owner_scope, title, description, created_at, updated_at FROM command_priorities WHERE id=?", (priority_id,))
        row = row_to_dict(cur, cur.fetchone())
        if not row:
            raise HTTPException(status_code=404, detail='not_found')
        return row
    finally:
        conn.close()


@router.get("/{scope}/{priority_id}/loes")
def list_loes(scope: str, priority_id: int):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, id as loe_id, title, description, sort_order, created_at, updated_at FROM loes WHERE priority_id=? ORDER BY sort_order LIMIT 5", (priority_id,))
        return [row_to_dict(cur, r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.post("/{scope}/{priority_id}/loes", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def create_loe(scope: str, priority_id: int, payload: dict):
    title = payload.get('title')
    description = payload.get('description')
    conn = connect()
    try:
        cur = conn.cursor()
        # enforce 5 LOEs per priority
        cur.execute("SELECT COUNT(1) FROM loes WHERE priority_id=?", (priority_id,))
        if cur.fetchone()[0] >= 5:
            raise HTTPException(status_code=400, detail='max_loes')
        now = _now()
        loe_id = str(uuid4())
        # insert into domain loes table; set scope_type 'PR' with scope_value as priority id for traceability
        cur.execute("INSERT INTO loes(id, scope_type, scope_value, title, description, created_by, created_at) VALUES (?,?,?,?,?,?,?)", (loe_id, 'PR', str(priority_id), title, description, 'system', now))
        # link via priority_loe
        cur.execute("INSERT INTO priority_loe(priority_id, loe_id, created_at) VALUES (?,?,?)", (priority_id, loe_id, now))
        conn.commit()
        cur.execute("SELECT id, title, description, created_at, created_by FROM loes WHERE id=?", (loe_id,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.put("/{scope}/{priority_id}/loes/{loe_id}", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def update_loe(scope: str, priority_id: int, loe_id: str, payload: dict):
    title = payload.get('title')
    description = payload.get('description')
    sort_order = payload.get('sort_order')
    conn = connect()
    try:
        cur = conn.cursor()
        now = _now()
        cur.execute("UPDATE loes SET title=?, description=?, sort_order=?, updated_at=? WHERE id=? AND priority_id=?", (title, description, sort_order or 0, now, loe_id, priority_id))
        conn.commit()
        cur.execute("SELECT id, title, description, sort_order, created_at, updated_at FROM loes WHERE id=?", (loe_id,))
        row = row_to_dict(cur, cur.fetchone())
        if not row:
            raise HTTPException(status_code=404, detail='not_found')
        return row
    finally:
        conn.close()


@router.delete("/{scope}/{priority_id}/loes/{loe_id}", dependencies=[Depends(require_any_role("usarec_admin", "co_cmd"))])
def delete_loe(scope: str, priority_id: int, loe_id: str):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM loes WHERE id=? AND priority_id=?", (loe_id, priority_id))
        conn.commit()
        return {"deleted": True}
    finally:
        conn.close()
