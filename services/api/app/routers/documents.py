from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from ..db import connect, get_documents_path
import os
import uuid
import datetime

router = APIRouter()


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + 'Z'


@router.post('/documents/upload')
async def upload_document(file: UploadFile = File(...), title: str = Form(None), description: str = Form(None), tags: str = Form(None)):
    """Upload a file and register it in the `documents` table."""
    content = await file.read()
    docs_dir = get_documents_path()
    # create a collision-resistant stored filename
    uid = uuid.uuid4().hex
    safe_name = os.path.basename(file.filename or 'unnamed')
    stored_filename = f"{uid}_{safe_name}"
    stored_path = os.path.join(docs_dir, stored_filename)
    try:
        with open(stored_path, 'wb') as fh:
            fh.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {e}")

    conn = connect()
    cur = conn.cursor()
    doc_id = uid
    uploaded_at = _now_iso()
    content_type = getattr(file, 'content_type', None)
    size = len(content) if content is not None else 0
    uploaded_by = os.getenv('LOCAL_DEV_USER') or ( 'master' if os.getenv('LOCAL_DEV_AUTH_BYPASS') == '1' else 'unknown')
    try:
        cur.execute(
            "INSERT INTO documents (id, filename, stored_path, content_type, size, uploaded_by, uploaded_at, description, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, safe_name, stored_path, content_type, size, uploaded_by, uploaded_at, description, tags)
        )
        conn.commit()
    except Exception as e:
        # attempt to remove stored file on DB failure
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")

    return {
        'id': doc_id,
        'filename': safe_name,
        'content_type': content_type,
        'size': size,
        'uploaded_by': uploaded_by,
        'uploaded_at': uploaded_at,
        'description': description,
        'tags': tags
    }


@router.get('/documents')
def list_documents():
    """List uploaded documents metadata."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, content_type, size, uploaded_by, uploaded_at, description, tags FROM documents ORDER BY uploaded_at DESC")
    rows = cur.fetchall()
    # convert sqlite3.Row to dict
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'filename': r['filename'],
            'content_type': r['content_type'],
            'size': r['size'],
            'uploaded_by': r['uploaded_by'],
            'uploaded_at': r['uploaded_at'],
            'description': r['description'],
            'tags': r['tags']
        })
    return result


@router.get('/documents/{doc_id}/download')
def download_document(doc_id: str):
    """Download a stored document by id."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT filename, stored_path, content_type FROM documents WHERE id=?", (doc_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    stored_path = row['stored_path']
    filename = row['filename']
    content_type = row['content_type'] or 'application/octet-stream'
    if not os.path.exists(stored_path):
        raise HTTPException(status_code=404, detail="Stored file missing")
    return FileResponse(path=stored_path, media_type=content_type, filename=filename)
