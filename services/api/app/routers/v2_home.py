from fastapi import APIRouter
from ..db import connect

router = APIRouter(prefix="/v2/home", tags=["home"])


def _rows_to_list(rows):
    return [dict(r) for r in rows]


@router.get('/news')
def news(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, org_unit_id, category, title, body, effective_dt, expires_dt, created_at FROM announcement ORDER BY effective_dt DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return {"status": "ok", "data": _rows_to_list(rows)}
    finally:
        conn.close()


@router.get('/updates')
def updates(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, component, status, message, created_at FROM system_update ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return {"status": "ok", "data": _rows_to_list(rows)}
    finally:
        conn.close()


@router.get('/quick-links')
def quick_links(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, section, title, url, created_at FROM resource_link ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return {"status": "ok", "data": _rows_to_list(rows)}
    finally:
        conn.close()
