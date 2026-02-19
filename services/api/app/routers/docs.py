import os
import uuid
import hashlib
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from ..db import connect
from datetime import datetime
from .rbac import require_scope, require_any_role

DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.data', 'docs')
os.makedirs(DATA_ROOT, exist_ok=True)

router = APIRouter(prefix="/docs", tags=["docs"])


def now_iso():
    return datetime.utcnow().isoformat()


def write_audit(conn, who, action, entity, entity_id, meta=None):
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)",
                (who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()))
    conn.commit()


@router.post("/upload", summary="Upload document", dependencies=[Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))])
async def upload_doc(file: UploadFile = File(...), title: str = Form(...), org_unit_id: int = Form(None), doc_type: str = Form(None), tags: str = Form(None), uploaded_by: str = Form(None)):
    item_id = str(uuid.uuid4())
    blob_id = str(uuid.uuid4())
    item_path = os.path.join(DATA_ROOT, item_id)
    os.makedirs(item_path, exist_ok=True)
    filename = file.filename
    dest = os.path.join(item_path, filename)
    content = await file.read()
    with open(dest, 'wb') as fh:
        fh.write(content)
    sha256 = hashlib.sha256(content).hexdigest()
    size = len(content)

    conn = connect()
    try:
        cur = conn.cursor()
        now = now_iso()
        cur.execute("INSERT INTO doc_library_item(id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (item_id, org_unit_id, title, doc_type, tags or '[]', 1, now, uploaded_by, now))
        cur.execute("INSERT INTO doc_blob(id, item_id, filename, content_type, size_bytes, sha256, path, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (blob_id, item_id, filename, file.content_type or 'application/octet-stream', size, sha256, dest, now))
        conn.commit()
        write_audit(conn, uploaded_by or 'system', 'upload.doc', 'doc_library_item', item_id, {'filename': filename})
        return {"item_id": item_id, "blob_id": blob_id, "download": f"/api/docs/{item_id}/download"}
    finally:
        conn.close()


@router.get("/list", summary="List documents")
def list_docs(org_unit_id: int = Query(None), tag: str = Query(None), doc_type: str = Query(None), limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = "SELECT id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by, created_at FROM doc_library_item WHERE 1=1"
        params = []
        if org_unit_id is not None:
            sql += " AND org_unit_id=?"; params.append(org_unit_id)
        if doc_type:
            sql += " AND doc_type=?"; params.append(doc_type)
        sql += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{item_id}/download", summary="Download document")
def download_doc(item_id: str):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT path, filename, content_type FROM doc_blob WHERE item_id=? LIMIT 1", (item_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail='not found')
        path = r['path'] if 'path' in r.keys() else r[0]
        content_type = r['content_type'] if 'content_type' in r.keys() else 'application/octet-stream'
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
