import os
import uuid
import hashlib
import json
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends, Body
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


def _ensure_doc_library_schema(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(doc_library_item)")
    existing = {str(r[1]).lower() for r in cur.fetchall()}
    wanted = {
        'source_type': "ALTER TABLE doc_library_item ADD COLUMN source_type TEXT",
        'classification_confidence': "ALTER TABLE doc_library_item ADD COLUMN classification_confidence REAL",
        'classified_by': "ALTER TABLE doc_library_item ADD COLUMN classified_by TEXT",
        'classified_at': "ALTER TABLE doc_library_item ADD COLUMN classified_at TEXT",
        'document_status': "ALTER TABLE doc_library_item ADD COLUMN document_status TEXT DEFAULT 'unclassified'",
        'updated_at': "ALTER TABLE doc_library_item ADD COLUMN updated_at TEXT",
    }
    for col, ddl in wanted.items():
        if col not in existing:
            cur.execute(ddl)
    conn.commit()


def _normalize_document_type(value: str):
    raw = (value or '').strip().lower()
    mapping = {
        'regulations': 'regulation',
        'regulation': 'regulation',
        'usarec_messages': 'usarec_message',
        'usarec_message': 'usarec_message',
        'historical': 'historical_data',
        'historical_data': 'historical_data',
        'general': 'general_document',
        'general_document': 'general_document',
        'dataset': 'dataset',
        'planning_reference': 'planning_reference',
    }
    return mapping.get(raw, raw or 'general_document')


def _extract_auto_tags(title: str, filename: str, source_type: str):
    text = f"{title} {filename} {source_type}".lower()
    tags = set()

    keyword_map = {
        'regulation': ['regulation', 'manual', 'doctrine', 'policy', 'pam', 'tc', 'ur', 'um', 'fm', 'adp', 'adrp'],
        'mission': ['mission'],
        'market': ['market'],
        'targeting': ['targeting'],
        'fusion': ['fusion'],
        'twg': ['twg'],
        'board': ['board'],
        'school_recruiting': ['school', 'recruiting'],
        'budget': ['budget'],
        'roi': ['roi'],
        'usarec_message': ['usarec', 'message', 'milper'],
        'historical': ['historical', 'archive'],
        'battalion': ['battalion', 'bn'],
        'brigade': ['brigade', 'bde'],
        'station': ['station'],
        'event': ['event'],
        'marketing': ['marketing'],
        'planning': ['planning', 'coa'],
    }

    for tag, keys in keyword_map.items():
        if any(k in text for k in keys):
            tags.add(tag)

    ext = os.path.splitext(filename or '')[1].lower().lstrip('.')
    if ext:
        tags.add(f"type_{ext}")

    for token in re.split(r'[^a-z0-9]+', (filename or '').lower()):
        if token and len(token) > 3 and token in {'mission', 'market', 'targeting', 'fusion', 'twg', 'budget', 'event', 'marketing'}:
            tags.add(token)

    return sorted(tags)


def _classify_document(title: str, filename: str, source_type: str, suggested_type: str = ''):
    text = f"{title} {filename}".lower()
    ext = os.path.splitext(filename or '')[1].lower()
    forced = _normalize_document_type(suggested_type)

    if 'historical' in text or 'archive' in text:
        doc_type = 'historical_data'
        confidence = 0.9
    elif any(k in text for k in ['message', 'usarec', 'milper']):
        doc_type = 'usarec_message'
        confidence = 0.92
    elif re.search(r"\b(ur|um|tc|pam|fm|adp|adrp)\b", text) or any(k in text for k in ['regulation', 'manual', 'doctrine', 'policy']):
        doc_type = 'regulation'
        confidence = 0.9
    elif 'planning' in text or 'coa' in text:
        doc_type = 'planning_reference'
        confidence = 0.82
    elif source_type == 'data_hub_upload':
        doc_type = 'dataset'
        confidence = 0.9
    elif ext in {'.csv', '.xls', '.xlsx'} and any(k in text for k in ['data', 'dataset', 'metrics', 'funnel', 'market', 'roi', 'budget', 'event', 'lead']):
        doc_type = 'dataset'
        confidence = 0.8
    elif ext in {'.csv', '.xls', '.xlsx'}:
        doc_type = 'historical_data'
        confidence = 0.72
    else:
        doc_type = 'general_document'
        confidence = 0.65

    if forced in {'regulation', 'usarec_message', 'historical_data', 'general_document', 'dataset', 'planning_reference'} and forced != 'general_document':
        doc_type = forced
        confidence = max(confidence, 0.95)

    status = 'classified' if confidence >= 0.75 else 'needs_review'
    return {
        'document_type': doc_type,
        'classification_confidence': round(confidence, 2),
        'classified_by': 'system',
        'classified_at': now_iso(),
        'document_status': status,
        'tags': _extract_auto_tags(title, filename, source_type),
    }


@router.post("/upload", summary="Upload document", dependencies=[Depends(require_any_role('USAREC_ADMIN','CO_CMD','BDE_CMD','BN_CMD'))])
async def upload_doc(file: UploadFile = File(...), title: str = Form(...), org_unit_id: int = Form(None), doc_type: str = Form(None), tags: str = Form(None), uploaded_by: str = Form(None), source_type: str = Form(None)):
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
        _ensure_doc_library_schema(conn)
        now = now_iso()
        source = (source_type or '').strip() or 'uploaded'
        parsed_tags = {}
        if tags:
            try:
                parsed_tags = json.loads(tags)
                if not isinstance(parsed_tags, dict):
                    parsed_tags = {}
            except Exception:
                parsed_tags = {}

        classification = _classify_document(title=title, filename=filename, source_type=source, suggested_type=doc_type or parsed_tags.get('category', ''))
        merged_tags = dict(parsed_tags)
        merged_tags['auto_tags'] = classification['tags']
        merged_tags.setdefault('source', source)

        cur.execute(
            """
            INSERT INTO doc_library_item(
                id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by,
                created_at, source_type, classification_confidence, classified_by, classified_at,
                document_status, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                item_id,
                org_unit_id,
                title,
                classification['document_type'],
                json.dumps(merged_tags),
                1,
                now,
                uploaded_by,
                now,
                source,
                classification['classification_confidence'],
                classification['classified_by'],
                classification['classified_at'],
                classification['document_status'],
                now,
            ),
        )
        cur.execute("INSERT INTO doc_blob(id, item_id, filename, content_type, size_bytes, sha256, path, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (blob_id, item_id, filename, file.content_type or 'application/octet-stream', size, sha256, dest, now))
        conn.commit()
        write_audit(conn, uploaded_by or 'system', 'upload.doc', 'doc_library_item', item_id, {
            'filename': filename,
            'document_type': classification['document_type'],
            'source_type': source,
            'classification_confidence': classification['classification_confidence'],
        })
        return {"item_id": item_id, "blob_id": blob_id, "download": f"/api/docs/{item_id}/download"}
    finally:
        conn.close()


@router.get("/list", summary="List documents")
def list_docs(org_unit_id: int = Query(None), tag: str = Query(None), doc_type: str = Query(None), limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        _ensure_doc_library_schema(conn)
        sql = """
            SELECT id, org_unit_id, title, doc_type, tags_json, version, effective_dt, uploaded_by,
                   created_at, source_type, classification_confidence, classified_by, classified_at,
                   document_status, updated_at
            FROM doc_library_item WHERE 1=1
        """
        params = []
        if org_unit_id is not None:
            sql += " AND org_unit_id=?"; params.append(org_unit_id)
        if doc_type:
            sql += " AND doc_type=?"; params.append(_normalize_document_type(doc_type))
        if tag:
            sql += " AND tags_json LIKE ?"
            params.append(f"%{tag}%")
        sql += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = []
        for r in cur.fetchall():
            row = dict(r)
            row['document_type'] = row.get('doc_type')
            rows.append(row)
        return rows
    finally:
        conn.close()


@router.patch("/{item_id}/classification", summary="Manual classification override")
def update_doc_classification(item_id: str, payload: dict = Body(...)):
    conn = connect()
    try:
        cur = conn.cursor()
        _ensure_doc_library_schema(conn)
        cur.execute("SELECT id, tags_json FROM doc_library_item WHERE id=?", (item_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')

        raw_tags = row['tags_json'] if 'tags_json' in row.keys() else '{}'
        tags_obj = {}
        try:
            tags_obj = json.loads(raw_tags or '{}')
            if not isinstance(tags_obj, dict):
                tags_obj = {}
        except Exception:
            tags_obj = {}

        document_type = _normalize_document_type(str(payload.get('document_type') or payload.get('doc_type') or 'general_document'))
        source_type = str(payload.get('source_type') or tags_obj.get('source') or 'uploaded')
        tags = payload.get('tags')
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        if not isinstance(tags, list):
            tags = []

        tags_obj['manual_tags'] = tags
        tags_obj['all_tags'] = sorted(set(list(tags_obj.get('auto_tags') or []) + tags))
        tags_obj['source'] = source_type

        who = str(payload.get('classified_by') or payload.get('updated_by') or 'user')
        now = now_iso()
        cur.execute(
            """
            UPDATE doc_library_item
               SET doc_type=?, tags_json=?, source_type=?, classification_confidence=?,
                   classified_by=?, classified_at=?, document_status='classified', updated_at=?
             WHERE id=?
            """,
            (document_type, json.dumps(tags_obj), source_type, 1.0, who, now, now, item_id),
        )
        conn.commit()
        write_audit(conn, who, 'override.doc.classification', 'doc_library_item', item_id, {
            'document_type': document_type,
            'source_type': source_type,
            'tags': tags,
        })
        return {'status': 'ok', 'item_id': item_id, 'document_type': document_type, 'tags': tags_obj.get('all_tags', [])}
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
