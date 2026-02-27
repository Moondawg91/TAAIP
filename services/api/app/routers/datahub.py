"""Data Hub router: file uploads, import runs, history, and previews.
Lightweight implementation that delegates detection/parsing to the importers
registry under services.api.app.importers.
"""
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import hashlib
import json
from datetime import datetime
from .. import db as _db
from .rbac import require_perm

from ..importers import registry as importer_registry

router = APIRouter()


def _now_iso():
    return datetime.utcnow().isoformat()


@router.post("/v2/datahub/uploads", dependencies=[Depends(require_perm('datahub.upload'))])
async def upload_file(file: UploadFile = File(...), dry_run: int = Query(0)):
    # read bytes
    body = await file.read()
    if not body:
        raise HTTPException(status_code=400, detail="empty file")
    max_bytes = int(os.getenv('DATAHUB_MAX_BYTES', str(25 * 1024 * 1024)))
    if len(body) > max_bytes:
        raise HTTPException(status_code=413, detail="file too large")

    sha = hashlib.sha256(body).hexdigest()
    docs = _db.get_documents_path()
    dest_dir = os.path.join(docs, 'datahub_uploads')
    os.makedirs(dest_dir, exist_ok=True)
    stored_name = f"{sha}_{file.filename}"
    stored_path = os.path.join(dest_dir, stored_name)

    conn = _db.connect()
    cur = conn.cursor()

    # dedupe by sha: only write file bytes if not present
    cur.execute("SELECT id, stored_path FROM import_file WHERE sha256 = ?", (sha,))
    row = cur.fetchone()
    if row:
        import_file_id = row['id']
        stored_path = row['stored_path']
    else:
        with open(stored_path, 'wb') as fh:
            fh.write(body)
        now = _now_iso()
        cur.execute(
            "INSERT INTO import_file (sha256, original_filename, stored_path, content_type, byte_size, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
            (sha, file.filename, stored_path, file.content_type or 'application/octet-stream', len(body), now)
        )
        import_file_id = cur.lastrowid
        conn.commit()

    # detect importer
    try:
        detection = importer_registry.detect_importer(body, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"detection failed: {e}")

    started = _now_iso()
    cur.execute(
        "INSERT INTO import_run (import_file_id, source_system, dataset_key, status, started_at, detected_signature_json, dry_run) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (import_file_id, detection.get('source_system'), detection.get('dataset_key'), 'RECEIVED', started, json.dumps(detection), 1 if dry_run else 0)
    )
    import_run_id = cur.lastrowid
    conn.commit()

    # run parser/validator (dry-run or commit)
    try:
        result = importer_registry.run_import(detection, body, import_run_id, dry_run=bool(dry_run))
        status = 'VALIDATED' if dry_run else ( 'IMPORTED' if result.get('success', True) else 'FAILED')
        finished = _now_iso()
        cur.execute(
            "UPDATE import_run SET status = ?, finished_at = ?, rows_in = ?, rows_inserted = ?, rows_rejected = ?, warnings_json = ?, errors_json = ? WHERE id = ?",
            (
                status,
                finished,
                result.get('rows_in', 0),
                result.get('rows_inserted', 0),
                result.get('rows_rejected', 0),
                json.dumps(result.get('warnings', [])) if result.get('warnings') is not None else None,
                json.dumps(result.get('errors', [])) if result.get('errors') is not None else None,
                import_run_id,
            )
        )
        conn.commit()
    except Exception as e:
        finished = _now_iso()
        cur.execute("UPDATE import_run SET status = ?, finished_at = ?, errors_json = ? WHERE id = ?", ('FAILED', finished, json.dumps([str(e)]), import_run_id))
        conn.commit()
        raise HTTPException(status_code=500, detail=f"import failed: {e}")

    out = {
        'import_run_id': import_run_id,
        'detection': detection,
        'result': {k: result.get(k) for k in ('rows_in','rows_inserted','rows_rejected','warnings','errors')},
    }
    if dry_run:
        out['preview'] = result.get('preview')

    return JSONResponse(content=out)


@router.get('/v2/datahub/supported')
def supported():
    specs = importer_registry.list_specs()
    return JSONResponse(content={'specs': specs})


@router.get('/v2/datahub/imports')
def list_imports(limit: int = 50, source_system: str = None, dataset_key: str = None):
    conn = _db.connect()
    cur = conn.cursor()
    q = "SELECT * FROM import_run ORDER BY id DESC LIMIT ?"
    params = [limit]
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    return JSONResponse(content={'imports': rows})


@router.get('/v2/datahub/imports/{import_id}')
def get_import(import_id: int):
    conn = _db.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_run WHERE id = ?", (import_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404)
    cur.execute("SELECT * FROM import_row_error WHERE import_run_id = ? ORDER BY id ASC", (import_id,))
    errors = [dict(r) for r in cur.fetchall()]
    res = dict(row)
    res['row_errors'] = errors
    return JSONResponse(content=res)


@router.get('/v2/datahub/imports/{import_id}/preview')
def import_preview(import_id: int, limit: int = 50):
    conn = _db.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM import_run WHERE id = ?", (import_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404)
    dataset = row['dataset_key']
    # naive preview: query few rows from normalized tables depending on dataset
    if dataset and dataset.startswith('emm'):
        cur.execute("SELECT * FROM emm_event WHERE source_import_run_id = ? LIMIT ?", (import_id, limit))
        return JSONResponse(content={'rows': [dict(r) for r in cur.fetchall()]})
    if dataset and dataset.startswith('alrl'):
        cur.execute("SELECT * FROM alrl_school WHERE source_import_run_id = ? LIMIT ?", (import_id, limit))
        return JSONResponse(content={'rows': [dict(r) for r in cur.fetchall()]})
    if dataset and dataset.startswith('g2'):
        cur.execute("SELECT * FROM g2_market_metric WHERE source_import_run_id = ? LIMIT ?", (import_id, limit))
        return JSONResponse(content={'rows': [dict(r) for r in cur.fetchall()]})
    # fallback: return stg rows
    cur.execute("SELECT row_number, row_json FROM stg_raw_dataset WHERE ingest_run_id = ? LIMIT ?", (import_id, limit))
    return JSONResponse(content={'rows': [dict(r) for r in cur.fetchall()]})
