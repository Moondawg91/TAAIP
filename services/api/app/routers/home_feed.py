from fastapi import APIRouter, Depends, HTTPException
from ..db import connect
from .. import auth
import uuid, time, os

router = APIRouter(prefix="/home", tags=["home_feed"])

def _now_iso():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


@router.get('/flash', summary='List flash items')
def list_flash(limit: int = 25):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, body, category, source, effective_date, created_at, created_by FROM home_flash_items ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status": "ok", "items": [dict(r) for r in rows]}
        except Exception:
            return {"status": "ok", "items": []}
    finally:
        conn.close()


@router.post('/flash', summary='Create flash item')
def create_flash(payload: dict, effective=Depends(auth.get_effective_user)):
    # allow master or dev bypass
    if not effective or (not (effective.get('permissions') and '*' in effective.get('permissions')) and 'system_admin' not in [r.lower() for r in (effective.get('roles') or [])] and os.getenv('LOCAL_DEV_AUTH_BYPASS','0') not in ('1','true','True')):
        raise HTTPException(status_code=403, detail='forbidden')
    now = _now_iso()
    id = payload.get('id') or str(uuid.uuid4())
    title = payload.get('title','')
    body = payload.get('body','')
    category = payload.get('category','MUST_KNOW')
    source = payload.get('source')
    effective_date = payload.get('effective_date')
    created_by = effective.get('sub') if effective else 'system'
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO home_flash_items (id,title,body,category,source,effective_date,created_at,created_by) VALUES (?,?,?,?,?,?,?,?)", (id,title,body,category,source,effective_date,now,created_by))
        conn.commit()
        return {"status":"ok","id":id}
    finally:
        conn.close()


@router.get('/messages', summary='List messages')
def list_messages(limit: int = 25):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, body, priority, created_at, created_by FROM home_messages ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status":"ok","items":[dict(r) for r in rows]}
        except Exception:
            return {"status":"ok","items":[]}
    finally:
        conn.close()


@router.post('/messages', summary='Create message')
def create_message(payload: dict, effective=Depends(auth.get_effective_user)):
    if not effective or (not (effective.get('permissions') and '*' in effective.get('permissions')) and 'system_admin' not in [r.lower() for r in (effective.get('roles') or [])] and os.getenv('LOCAL_DEV_AUTH_BYPASS','0') not in ('1','true','True')):
        raise HTTPException(status_code=403, detail='forbidden')
    now = _now_iso()
    id = payload.get('id') or str(uuid.uuid4())
    title = payload.get('title','')
    body = payload.get('body','')
    priority = payload.get('priority','INFO')
    created_by = effective.get('sub') if effective else 'system'
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO home_messages (id,title,body,priority,created_at,created_by) VALUES (?,?,?,?,?,?)", (id,title,body,priority,now,created_by))
        conn.commit()
        return {"status":"ok","id":id}
    finally:
        conn.close()


@router.get('/recognition', summary='List recognition')
def list_recognition(limit: int = 25):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, body, person_name, unit, created_at, created_by FROM home_recognition ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status":"ok","items":[dict(r) for r in rows]}
        except Exception:
            return {"status":"ok","items":[]}
    finally:
        conn.close()


@router.post('/recognition', summary='Create recognition')
def create_recognition(payload: dict, effective=Depends(auth.get_effective_user)):
    if not effective or (not (effective.get('permissions') and '*' in effective.get('permissions')) and 'system_admin' not in [r.lower() for r in (effective.get('roles') or [])] and os.getenv('LOCAL_DEV_AUTH_BYPASS','0') not in ('1','true','True')):
        raise HTTPException(status_code=403, detail='forbidden')
    now = _now_iso()
    id = payload.get('id') or str(uuid.uuid4())
    title = payload.get('title','')
    body = payload.get('body','')
    person_name = payload.get('person_name')
    unit = payload.get('unit')
    created_by = effective.get('sub') if effective else 'system'
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO home_recognition (id,title,body,person_name,unit,created_at,created_by) VALUES (?,?,?,?,?,?,?)", (id,title,body,person_name,unit,now,created_by))
        conn.commit()
        return {"status":"ok","id":id}
    finally:
        conn.close()


@router.get('/upcoming', summary='List upcoming')
def list_upcoming(limit: int = 25):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, body, event_date, tag, created_at, created_by FROM home_upcoming ORDER BY event_date ASC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return {"status":"ok","items":[dict(r) for r in rows]}
        except Exception:
            return {"status":"ok","items":[]}
    finally:
        conn.close()


@router.post('/upcoming', summary='Create upcoming')
def create_upcoming(payload: dict, effective=Depends(auth.get_effective_user)):
    if not effective or (not (effective.get('permissions') and '*' in effective.get('permissions')) and 'system_admin' not in [r.lower() for r in (effective.get('roles') or [])] and os.getenv('LOCAL_DEV_AUTH_BYPASS','0') not in ('1','true','True')):
        raise HTTPException(status_code=403, detail='forbidden')
    now = _now_iso()
    id = payload.get('id') or str(uuid.uuid4())
    title = payload.get('title','')
    body = payload.get('body')
    event_date = payload.get('event_date')
    tag = payload.get('tag')
    created_by = effective.get('sub') if effective else 'system'
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO home_upcoming (id,title,body,event_date,tag,created_at,created_by) VALUES (?,?,?,?,?,?,?)", (id,title,body,event_date,tag,now,created_by))
        conn.commit()
        return {"status":"ok","id":id}
    finally:
        conn.close()


@router.get('/reference-rails', summary='List reference rails')
def list_reference_rails():
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, title, kind, target, created_at FROM home_reference_rails ORDER BY created_at DESC")
            rows = cur.fetchall()
            return {"status":"ok","items":[dict(r) for r in rows]}
        except Exception:
            return {"status":"ok","items":[]}
    finally:
        conn.close()


@router.post('/reference-rails', summary='Create reference rail')
def create_reference_rail(payload: dict, effective=Depends(auth.get_effective_user)):
    if not effective or (not (effective.get('permissions') and '*' in effective.get('permissions')) and 'system_admin' not in [r.lower() for r in (effective.get('roles') or [])] and os.getenv('LOCAL_DEV_AUTH_BYPASS','0') not in ('1','true','True')):
        raise HTTPException(status_code=403, detail='forbidden')
    now = _now_iso()
    id = payload.get('id') or str(uuid.uuid4())
    title = payload.get('title','')
    kind = payload.get('kind','DOC')
    target = payload.get('target','')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO home_reference_rails (id,title,kind,target,created_at) VALUES (?,?,?,?,?)", (id,title,kind,target,now))
        conn.commit()
        return {"status":"ok","id":id}
    finally:
        conn.close()
