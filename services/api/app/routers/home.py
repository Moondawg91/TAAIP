from fastapi import APIRouter, Depends
from ..db import connect
from typing import List
from .rbac import get_current_user

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/announcements", summary="List announcements")
def list_announcements(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, org_unit_id, category, title, body, effective_dt, expires_dt, created_at FROM announcement ORDER BY effective_dt DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/system-status", summary="System status updates")
def system_status(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, component, status, message, created_at FROM system_update ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/updates", summary="Recent updates")
def recent_updates(limit: int = 100):
    return system_status(limit=limit)


@router.get("/resources", summary="Resource links")
def resources(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, section, title, url, created_at FROM resource_link ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
