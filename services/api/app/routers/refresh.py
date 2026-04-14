from __future__ import annotations

import hashlib
import json
import os
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import ingest
from ..database import get_db
from ..runtime_env import apply_runtime_environment
from ..services import refresh_admin
from .admin_v2 import require_admin_manage

router = APIRouter(prefix="/refresh", tags=["refresh"])


def _username(user: Any) -> str:
    if isinstance(user, dict):
        return str(user.get('username') or 'system')
    return str(getattr(user, 'username', 'system'))


def _ensure_upload_dir(source_id: int) -> str:
    settings = apply_runtime_environment()
    source_dir = os.path.join(settings['refresh_upload_dir'], f"source_{source_id}")
    os.makedirs(source_dir, exist_ok=True)
    return source_dir


def _json_field(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return fallback
    return fallback


@router.get('/sources')
def list_sources(current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    rows = db.execute(text("SELECT * FROM refresh_sources ORDER BY name ASC")).mappings().all()
    sources = []
    for row in rows:
        item = dict(row)
        item['required_merge_keys'] = _json_field(item.get('required_merge_keys'), [])
        item['mapping_profile'] = _json_field(item.get('mapping_profile'), {})
        sources.append(item)
    return {'status': 'ok', 'sources': sources}


@router.post('/sources')
def create_source(body: dict = Body(...), current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    name = (body.get('name') or '').strip()
    if not name:
        raise HTTPException(status_code=400, detail={'code': 'name_required', 'message': 'name required'})

    canonical_target = refresh_admin.resolve_source_key(body.get('canonical_target') or name)
    required_merge_keys = body.get('required_merge_keys') or refresh_admin.default_merge_keys(canonical_target)
    mapping_profile = body.get('mapping_profile') or {}
    mapping_profile.setdefault('downstream_surfaces', (refresh_admin.SOURCE_REGISTRY.get(canonical_target) or {}).get('downstream_surfaces', []))

    existing = db.execute(text("SELECT id FROM refresh_sources WHERE name = :name"), {'name': name}).scalar()
    params = {
        'name': name,
        'description': body.get('description'),
        'canonical_target': canonical_target,
        'file_types': body.get('file_types', 'csv,xlsx'),
        'required_merge_keys': json.dumps(required_merge_keys),
        'mapping_profile': json.dumps(mapping_profile),
        'owner': body.get('owner') or _username(current_user),
        'default_mode': body.get('default_mode', 'replace'),
        'trusted': str(body.get('trusted', True)).lower(),
        'auto_commit': str(body.get('auto_commit', False)).lower(),
    }

    if existing:
        db.execute(
            text(
                """
                UPDATE refresh_sources
                SET description = :description,
                    canonical_target = :canonical_target,
                    file_types = :file_types,
                    required_merge_keys = :required_merge_keys,
                    mapping_profile = :mapping_profile,
                    owner = :owner,
                    default_mode = :default_mode,
                    trusted = :trusted,
                    auto_commit = :auto_commit
                WHERE id = :id
                """
            ),
            {**params, 'id': existing},
        )
        db.commit()
        return {'status': 'ok', 'id': existing, 'name': name, 'canonical_target': canonical_target, 'updated': True}

    db.execute(
        text(
            """
            INSERT INTO refresh_sources (
                name, description, canonical_target, file_types, required_merge_keys,
                mapping_profile, owner, default_mode, trusted, auto_commit, created_at
            ) VALUES (
                :name, :description, :canonical_target, :file_types, :required_merge_keys,
                :mapping_profile, :owner, :default_mode, :trusted, :auto_commit, datetime('now')
            )
            """
        ),
        params,
    )
    db.commit()
    source_id = db.execute(text("SELECT id FROM refresh_sources WHERE name = :name"), {'name': name}).scalar()
    return {'status': 'ok', 'id': source_id, 'name': name, 'canonical_target': canonical_target, 'required_merge_keys': required_merge_keys}


@router.post('/sources/{source_id}/upload')
def upload_refresh(source_id: int, file: UploadFile = File(...), current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    row = db.execute(text("SELECT * FROM refresh_sources WHERE id = :id"), {'id': source_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail={'code': 'source_not_found', 'message': 'source not found'})

    contents = file.file.read()
    upload_dir = _ensure_upload_dir(source_id)
    path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{file.filename}")
    with open(path, 'wb') as handle:
        handle.write(contents)

    checksum = hashlib.sha256(contents).hexdigest()
    try:
        profile = ingest.profile_file(path)
    except Exception:
        profile = {'sheets': [], 'columns': [], 'sample': []}

    try:
        df = ingest.read_file_to_df(path)
    except Exception as exc:
        validation = {
            'valid': False,
            'code': 'invalid_schema',
            'message': f'Unable to parse the uploaded dataset: {exc}',
            'missing_columns': [],
            'lineage': {
                'canonical_target': row.get('canonical_target'),
                'detected_source': refresh_admin.resolve_source_key(row.get('canonical_target'), file.filename, []),
                'filename': file.filename,
                'row_count_detected': 0,
                'detected_columns': [],
                'downstream_surfaces': [],
            },
        }
        df = None
    else:
        validation = refresh_admin.validate_uploaded_frame(df, canonical_target=row.get('canonical_target'), filename=file.filename)

    combined_profile = {'file_profile': profile, 'validation': validation}
    job_status = 'validated' if validation.get('valid') else validation.get('code', 'invalid_schema')
    row_count = int(validation.get('lineage', {}).get('row_count_detected') or 0)

    db.execute(
        text(
            """
            INSERT INTO refresh_jobs (source_id, filename, stored_path, checksum, uploaded_by, uploaded_at, status, row_count, profile)
            VALUES (:source_id, :filename, :stored_path, :checksum, :uploaded_by, datetime('now'), :status, :row_count, :profile)
            """
        ),
        {
            'source_id': source_id,
            'filename': file.filename,
            'stored_path': path,
            'checksum': checksum,
            'uploaded_by': _username(current_user),
            'status': job_status,
            'row_count': row_count,
            'profile': json.dumps(combined_profile),
        },
    )
    db.commit()
    job_id = db.execute(text("SELECT id FROM refresh_jobs WHERE stored_path = :stored_path ORDER BY id DESC LIMIT 1"), {'stored_path': path}).scalar()

    if validation.get('valid') and df is not None:
        rows = df.to_dict(orient='records')
        for index, staged_row in enumerate(rows, start=1):
            db.execute(
                text("INSERT INTO refresh_staging_rows (job_id, row_number, row_json) VALUES (:job_id, :row_number, :row_json)"),
                {'job_id': job_id, 'row_number': index, 'row_json': json.dumps(staged_row, default=str)},
            )
        db.commit()
        return {
            'status': 'validated',
            'job_id': job_id,
            'row_count': len(rows),
            'profile': profile,
            'validation': validation,
            'lineage': validation.get('lineage'),
        }

    raise HTTPException(status_code=400, detail=refresh_admin.build_error_detail(validation, job_id=job_id))


@router.get('/jobs/{job_id}')
def job_status(job_id: int, current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    row = db.execute(text("SELECT * FROM refresh_jobs WHERE id = :id"), {'id': job_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail={'code': 'job_not_found', 'message': 'job not found'})
    item = dict(row)
    item['profile'] = refresh_admin.parse_profile(item.get('profile'))
    return item


@router.post('/jobs/{job_id}/commit')
def commit_job(job_id: int, body: dict = Body(default={}), current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    job = db.execute(text("SELECT * FROM refresh_jobs WHERE id = :id"), {'id': job_id}).mappings().fetchone()
    if not job:
        raise HTTPException(status_code=404, detail={'code': 'job_not_found', 'message': 'job not found'})

    source = db.execute(text("SELECT * FROM refresh_sources WHERE id = :id"), {'id': job['source_id']}).mappings().fetchone()
    if not source:
        raise HTTPException(status_code=404, detail={'code': 'source_not_found', 'message': 'source not found'})

    profile = refresh_admin.parse_profile(job.get('profile'))
    validation = profile.get('validation') or {}
    if validation and not validation.get('valid', False):
        raise HTTPException(status_code=400, detail=refresh_admin.build_error_detail(validation, job_id=job_id))

    staged_rows = db.execute(
        text("SELECT row_json FROM refresh_staging_rows WHERE job_id = :job_id ORDER BY row_number ASC"),
        {'job_id': job_id},
    ).scalars().all()
    if not staged_rows:
        detail = {'code': 'no_data', 'message': 'No staged data is available to commit.', 'job_id': job_id}
        db.execute(text("UPDATE refresh_jobs SET status = :status WHERE id = :id"), {'status': 'no_data', 'id': job_id})
        db.commit()
        raise HTTPException(status_code=400, detail=detail)

    staged = [json.loads(row) for row in staged_rows]
    mode = body.get('mode') or source.get('default_mode') or 'replace'
    if mode not in {'replace', 'upsert'}:
        raise HTTPException(status_code=400, detail={'code': 'unsupported_mode', 'message': 'unsupported mode', 'job_id': job_id})

    merge_keys = body.get('merge_keys') or _json_field(source.get('required_merge_keys'), []) or validation.get('merge_keys') or []
    source_id = int(job['source_id'])
    before_row_count = db.execute(text("SELECT COUNT(*) FROM refresh_dataset_rows WHERE source_id = :source_id"), {'source_id': source_id}).scalar() or 0
    version = str(uuid.uuid4())
    notes = json.dumps({'lineage': validation.get('lineage', {}), 'mode': mode})

    try:
        db.execute(
            text(
                "INSERT INTO dataset_versions (source_id, version, checksum, created_by, created_at, row_count, notes) VALUES (:source_id, :version, :checksum, :created_by, datetime('now'), 0, :notes)"
            ),
            {
                'source_id': source_id,
                'version': version,
                'checksum': job.get('checksum'),
                'created_by': _username(current_user),
                'notes': notes,
            },
        )
        version_id = db.execute(text("SELECT id FROM dataset_versions WHERE version = :version ORDER BY id DESC LIMIT 1"), {'version': version}).scalar()

        if mode == 'replace':
            db.execute(text("DELETE FROM refresh_dataset_rows WHERE source_id = :source_id"), {'source_id': source_id})
            for row in staged:
                db.execute(
                    text("INSERT INTO refresh_dataset_rows (source_id, version_id, row_json, created_at) VALUES (:source_id, :version_id, :row_json, datetime('now'))"),
                    {'source_id': source_id, 'version_id': version_id, 'row_json': json.dumps(row, default=str)},
                )
        else:
            if not merge_keys:
                raise HTTPException(status_code=400, detail={'code': 'merge_keys_required', 'message': 'merge_keys required for upsert', 'job_id': job_id})
            current_rows = db.execute(text("SELECT row_json FROM refresh_dataset_rows WHERE source_id = :source_id"), {'source_id': source_id}).scalars().all()
            index = {}
            for raw in current_rows:
                existing = json.loads(raw)
                key = tuple(str(existing.get(k)) for k in merge_keys)
                index[key] = existing
            for row in staged:
                key = tuple(str(row.get(k)) for k in merge_keys)
                index[key] = {**index.get(key, {}), **row}
            db.execute(text("DELETE FROM refresh_dataset_rows WHERE source_id = :source_id"), {'source_id': source_id})
            for row in index.values():
                db.execute(
                    text("INSERT INTO refresh_dataset_rows (source_id, version_id, row_json, created_at) VALUES (:source_id, :version_id, :row_json, datetime('now'))"),
                    {'source_id': source_id, 'version_id': version_id, 'row_json': json.dumps(row, default=str)},
                )

        new_count = db.execute(
            text("SELECT COUNT(*) FROM refresh_dataset_rows WHERE source_id = :source_id AND version_id = :version_id"),
            {'source_id': source_id, 'version_id': version_id},
        ).scalar() or 0

        db.execute(text("UPDATE dataset_versions SET row_count = :row_count WHERE id = :id"), {'row_count': new_count, 'id': version_id})
        db.execute(
            text(
                "INSERT INTO refresh_history (job_id, version_id, mode, status, applied_by, applied_at, row_count_before, row_count_after, notes) VALUES (:job_id, :version_id, :mode, :status, :applied_by, datetime('now'), :row_count_before, :row_count_after, :notes)"
            ),
            {
                'job_id': job_id,
                'version_id': version_id,
                'mode': mode,
                'status': 'applied',
                'applied_by': _username(current_user),
                'row_count_before': before_row_count,
                'row_count_after': new_count,
                'notes': notes,
            },
        )

        existing_active = db.execute(text("SELECT id FROM dataset_active WHERE source_id = :source_id"), {'source_id': source_id}).scalar()
        if existing_active:
            db.execute(
                text("UPDATE dataset_active SET version_id = :version_id, bound_at = datetime('now'), bound_by = :bound_by WHERE source_id = :source_id"),
                {'version_id': version_id, 'bound_by': _username(current_user), 'source_id': source_id},
            )
        else:
            db.execute(
                text("INSERT INTO dataset_active (source_id, version_id, bound_at, bound_by) VALUES (:source_id, :version_id, datetime('now'), :bound_by)"),
                {'source_id': source_id, 'version_id': version_id, 'bound_by': _username(current_user)},
            )

        db.execute(text("UPDATE refresh_jobs SET status = :status WHERE id = :id"), {'status': 'committed', 'id': job_id})
        db.commit()
        return {'status': 'ok', 'job_id': job_id, 'version_id': version_id, 'row_count': new_count, 'lineage': validation.get('lineage', {})}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        db.execute(text("UPDATE refresh_jobs SET status = :status WHERE id = :id"), {'status': 'failed', 'id': job_id})
        db.commit()
        raise HTTPException(status_code=500, detail={'code': 'refresh_apply_failed', 'message': str(exc), 'job_id': job_id})


@router.get('/sources/{source_id}/current')
def get_current(source_id: int, limit: int = 100, current_user: Dict[str, Any] = Depends(require_admin_manage), db: Session = Depends(get_db)):
    refresh_admin.ensure_refresh_schema(db)
    version_id = db.execute(text("SELECT version_id FROM dataset_active WHERE source_id = :source_id"), {'source_id': source_id}).scalar()
    if not version_id:
        raise HTTPException(status_code=404, detail={'code': 'no_active_version', 'message': 'no active version'})
    rows = db.execute(
        text("SELECT row_json FROM refresh_dataset_rows WHERE source_id = :source_id AND version_id = :version_id LIMIT :limit"),
        {'source_id': source_id, 'version_id': version_id, 'limit': limit},
    ).scalars().all()
    return {'status': 'ok', 'version_id': version_id, 'rows': [json.loads(row) for row in rows]}
