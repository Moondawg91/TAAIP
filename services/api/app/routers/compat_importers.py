"""Compatibility endpoints exposing the importer registry and a simple ingest run handshake.

These endpoints provide the minimal contract expected by the frontend while the
Data Hub router continues to offer the richer v2 endpoints.
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
from .. import db as _db
from ..importers import registry as importer_registry
from datetime import datetime
import json

router = APIRouter()


def _now_iso():
    return datetime.utcnow().isoformat()


@router.get('/v1/importers/registry')
def get_registry():
    specs = importer_registry.list_specs()
    return JSONResponse(content={'version': '2026.02', 'importers': specs})


@router.post('/v1/ingest/runs')
def create_ingest_run(payload: Dict[str, Any] = Body(...)):
    # expected fields: dataset_key, schema_version, unit_rsid, source_system, filename, content_type, notes
    required = ['dataset_key', 'schema_version', 'filename']
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f'missing {r}')

    conn = _db.connect()
    cur = conn.cursor()
    created = _now_iso()
    try:
        cur.execute(
            "INSERT INTO ingest_run (dataset_key, schema_version, unit_rsid, source_system, original_filename, content_type, notes, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                payload.get('dataset_key'),
                payload.get('schema_version'),
                payload.get('unit_rsid'),
                payload.get('source_system') or 'UPLOAD',
                payload.get('filename'),
                payload.get('content_type') or 'application/octet-stream',
                payload.get('notes') or None,
                'QUEUED',
                created,
            )
        )
        conn.commit()
        run_id = cur.lastrowid
        ingest_id = f"ing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{run_id}"
        # store a friendly ingest id mapping
        try:
            cur.execute('UPDATE ingest_run SET ingest_run_id=? WHERE id=?', (ingest_id, run_id))
            conn.commit()
        except Exception:
            pass

        upload_url = f"/api/v1/ingest/runs/{ingest_id}/file"
        return JSONResponse(content={'ingest_run_id': ingest_id, 'status': 'QUEUED', 'upload_url': upload_url})
    finally:
        conn.close()


@router.get('/v1/ingest/runs/{ingest_run_id}')
def get_ingest_run(ingest_run_id: str):
    conn = _db.connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM ingest_run WHERE ingest_run_id = ? LIMIT 1', (ingest_run_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='not found')
        # Normalize row to dict
        data = dict(row)
        # coerce json fields if present
        if data.get('warnings'):
            try:
                data['warnings'] = json.loads(data['warnings'])
            except Exception:
                pass
        if data.get('errors'):
            try:
                data['errors'] = json.loads(data['errors'])
            except Exception:
                pass
        return JSONResponse(content=data)
    finally:
        conn.close()
