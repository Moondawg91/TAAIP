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


@router.get("/status-strip", summary="Status strip for home page")
def status_strip():
    conn = connect()
    try:
        cur = conn.cursor()
        # import queue count from import_job_v3 where status != 'committed'
        try:
            cur.execute("SELECT COUNT(1) FROM import_job_v3 WHERE status IS NOT 'committed'")
            queue_count = cur.fetchone()[0] or 0
        except Exception:
            queue_count = 0
        try:
            cur.execute("SELECT MAX(created_at) FROM import_job_v3")
            last_import = cur.fetchone()[0]
        except Exception:
            last_import = None

        systems = {"vantage": "unknown", "emm": "unknown"}
        alerts_count = 0
        try:
            cur.execute("SELECT COUNT(1) FROM home_alerts WHERE record_status='active' AND (acked_at IS NULL OR acked_at='')")
            alerts_count = cur.fetchone()[0] or 0
        except Exception:
            alerts_count = 0

        return {"status": "ok", "systems": systems, "imports": {"queue_count": queue_count, "last_import_at": last_import}, "data": {"last_refresh_utc": None}, "alerts": {"count": alerts_count}}
    finally:
        conn.close()


@router.get("/alerts", summary="List home alerts")
def list_alerts(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, category, title, body, severity, source, effective_at, created_at, acked_at, acked_by FROM home_alerts ORDER BY effective_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status": "ok", "count": len(rows), "alerts": [dict(r) for r in rows]}
        except Exception:
            return {"status": "ok", "count": 0, "alerts": []}
    finally:
        conn.close()


@router.post("/alerts/{alert_id}/ack", summary="Acknowledge an alert")
def ack_alert(alert_id: str):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            now = __import__('time').strftime('%Y-%m-%dT%H:%M:%SZ', __import__('time').gmtime())
            cur.execute("UPDATE home_alerts SET acked_at=?, acked_by=? WHERE id=?", (now, 'system', alert_id))
            conn.commit()
        except Exception:
            pass
        return {"status": "ok"}
    finally:
        conn.close()


@router.get("/flashes", summary="Strategic flash feed")
def flashes(tab: str = 'usarec_ops', limit: int = 50):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, tab, source, title, summary, effective_at, url, created_at FROM home_flashes WHERE tab=? ORDER BY effective_at DESC LIMIT ?", (tab, limit))
            rows = cur.fetchall()
            return {"status": "ok", "count": len(rows), "items": [dict(r) for r in rows]}
        except Exception:
            return {"status": "ok", "count": 0, "items": []}
    finally:
        conn.close()


@router.get("/upcoming", summary="Upcoming items")
def upcoming(window: int = 30, limit: int = 50):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, category, title, start_at, end_at, location, url, created_at FROM home_upcoming ORDER BY start_at ASC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status": "ok", "count": len(rows), "items": [dict(r) for r in rows]}
        except Exception:
            return {"status": "ok", "count": 0, "items": []}
    finally:
        conn.close()


@router.get("/recognition", summary="Recognition / Featured")
def recognition():
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, name, unit, citation, month, year, created_at FROM home_recognition ORDER BY year DESC, month DESC LIMIT 1")
            row = cur.fetchone()
            return {"status": "ok", "featured": dict(row) if row else None}
        except Exception:
            return {"status": "ok", "featured": None}
    finally:
        conn.close()


@router.get("/references", summary="Reference rail items")
def references():
    # deterministic reference list even if DB empty
    refs = [
        {"key": "420t-tor-2026", "label": "420T TOR 2026", "type": "doc", "path_or_url": "/resources/doc-library", "available": False},
        {"key": "ur-601-210", "label": "UR 601-210", "type": "reg", "path_or_url": "/resources/regulations", "available": False},
        {"key": "ur-601-73", "label": "UR 601-73", "type": "reg", "path_or_url": "/resources/regulations", "available": False},
        {"key": "um-3-0", "label": "UM 3-0", "type": "doc", "path_or_url": "/resources/doc-library", "available": False},
        {"key": "roi-calc", "label": "ROI Calculator", "type": "tool", "path_or_url": "/tools/roi", "available": False},
        {"key": "burden-calc", "label": "Burden Calculator", "type": "tool", "path_or_url": "/tools/burden", "available": False},
        {"key": "market-weights", "label": "Market Weights", "type": "data", "path_or_url": "/admin/market-weights", "available": False}
    ]
    # attempt to mark available from DB
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT key, available FROM home_references WHERE key IN (?,?,?,?,?,?,?)", tuple(r['key'] for r in refs))
            rows = cur.fetchall()
            avail_map = {r[0]: bool(r[1]) for r in rows}
            for r in refs:
                if r['key'] in avail_map:
                    r['available'] = avail_map[r['key']]
        except Exception:
            pass
    finally:
        conn.close()
    return {"status": "ok", "items": refs}


@router.get("/virtual-tech-brief", summary="Virtual technician brief")
def virtual_tech_brief():
    # no AI generation yet — return null brief
    return {"status": "ok", "brief": None}
