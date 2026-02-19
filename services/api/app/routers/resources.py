import os
import json
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from ..db import connect
from .. import storage
from .rbac import require_any_role

router = APIRouter(prefix="/resources", tags=["resources"])


def now_iso():
    return datetime.utcnow().isoformat()


@router.post('/docs/upload', dependencies=[Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))])
async def upload_doc(
    file: UploadFile = File(...),
    title: str = Form(...),
    org_unit_id: int = Form(None),
    doc_type: str = Form(None),
    tags: str = Form(None),
    effective_date: str = Form(None),
    uploaded_by: str = Form(None),
):
    meta = await storage.save_upload(file)
    item_id = str(uuid.uuid4())
    blob_id = str(uuid.uuid4())
    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute(
            "INSERT INTO doc_library_item(id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by, created_at, record_status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (item_id, org_unit_id, title, doc_type, tags or '[]', 1, effective_date or now, uploaded_by, now, 'active'),
        )
        cur.execute(
            "INSERT INTO doc_blob(id, item_id, filename, content_type, size_bytes, sha256, path, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (blob_id, item_id, meta['original_name'], file.content_type or 'application/octet-stream', meta['size'], meta['sha256'], meta['stored_path'], now),
        )
        conn.commit()
        # audit
        try:
            cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)", (uploaded_by or 'system', 'upload.resource', 'doc_library_item', item_id, json.dumps({'blob_id': blob_id, 'filename': meta['original_name']}), now))
            conn.commit()
        except Exception:
            pass
        return {"item_id": item_id, "blob_id": blob_id, "download": f"/api/resources/docs/{item_id}/download"}
    finally:
        conn.close()


@router.get('/docs', summary='List resource documents')
def list_docs(org_unit_id: int = Query(None), doc_type: str = Query(None), tag: str = Query(None), limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = "SELECT id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by, created_at, record_status FROM doc_library_item WHERE 1=1"
        params = []
        if org_unit_id is not None:
            sql += " AND org_unit_id=?"; params.append(org_unit_id)
        if doc_type:
            sql += " AND doc_type=?"; params.append(doc_type)
        sql += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/docs/{item_id}/download', summary='Download resource document')
def download_doc(item_id: str):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT path, filename, content_type FROM doc_blob WHERE item_id=? LIMIT 1", (item_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='not found')
        path = r['path'] if 'path' in r.keys() else r[0]
        content_type = r.get('content_type') if isinstance(r, dict) else (r[2] if len(r) > 2 else 'application/octet-stream')
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail='file missing')
        def iterfile():
            with open(path, 'rb') as fh:
                while True:
                    chunk = fh.read(8192)
                    if not chunk:
                        break
                    yield chunk
        return StreamingResponse(iterfile(), media_type=content_type)
    finally:
        conn.close()


@router.put('/docs/{item_id}', summary='Update document metadata')
def update_doc(item_id: str, title: str = Form(None), tags: str = Form(None), doc_type: str = Form(None), bump_version: bool = Form(False), updated_by: str = Form(None)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, version FROM doc_library_item WHERE id=?", (item_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        ver = int(row['version'] if 'version' in row.keys() else row[1] or 1)
        if bump_version:
            ver += 1
        now = now_iso()
        cur.execute("UPDATE doc_library_item SET title=?, tags_json=?, doc_type=?, version=?, updated_at=? WHERE id=?", (title or row.get('title') if isinstance(row, dict) else title or row[0], tags or row.get('tags_json') if isinstance(row, dict) else tags, doc_type or row.get('doc_type') if isinstance(row, dict) else doc_type, ver, now, item_id))
        conn.commit()
        try:
            cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)", (updated_by or 'system', 'update.resource', 'doc_library_item', item_id, json.dumps({'bump_version': bump_version}), now))
            conn.commit()
        except Exception:
            pass
        return {"status": "ok", "id": item_id, "version": ver}
    finally:
        conn.close()
