from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from .. import auth
from .. import ingest
import os, json, hashlib

router = APIRouter(prefix="/refresh", tags=["refresh"])


def _ensure_upload_dir():
    tmpdir = './data/refresh_uploads'
    os.makedirs(tmpdir, exist_ok=True)
    return tmpdir


@router.post('/sources')
def create_source(body: dict, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    name = body.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    # persist minimal source
    sql = "INSERT INTO refresh_sources (name, description, canonical_target, file_types, required_merge_keys, mapping_profile, owner, default_mode, trusted, auto_commit, created_at) VALUES (:n,:d,:t,:ft,:keys,:mp,:o,:dm,:tr,:ac, datetime('now'))"
    params = {
        'n': name,
        'd': body.get('description'),
        't': body.get('canonical_target'),
        'ft': body.get('file_types', 'csv,xlsx'),
        'keys': json.dumps(body.get('required_merge_keys') or []),
        'mp': json.dumps(body.get('mapping_profile') or {}),
        'o': body.get('owner'),
        'dm': body.get('default_mode', 'replace'),
        'tr': str(body.get('trusted', False)).lower(),
        'ac': str(body.get('auto_commit', False)).lower()
    }
    db.execute(text(sql), params)
    db.commit()
    id_val = db.execute(text("SELECT id FROM refresh_sources WHERE name = :n ORDER BY id DESC LIMIT 1"), {'n': name}).scalar()
    return {'id': id_val, 'name': name}


@router.post('/sources/{source_id}/upload')
def upload_refresh(source_id: int, file: UploadFile = File(...), user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # verify source exists
    row = db.execute(text("SELECT * FROM refresh_sources WHERE id = :id"), {'id': source_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='source not found')
    tmpdir = _ensure_upload_dir()
    path = os.path.join(tmpdir, file.filename)
    contents = file.file.read()
    with open(path, 'wb') as f:
        f.write(contents)
    # checksum
    h = hashlib.sha256()
    h.update(contents)
    ch = h.hexdigest()
    # profile file (use existing ingest helpers)
    try:
        profile = ingest.profile_file(path)
    except Exception:
        profile = {"sheets": [], "columns": [], "sample": []}
    # create job
    sql = "INSERT INTO refresh_jobs (source_id, filename, stored_path, checksum, uploaded_by, uploaded_at, status, row_count, profile) VALUES (:src,:fn,:p,:ch,:u, datetime('now'), :st, :rc, :prof)"
    db.execute(text(sql), {'src': source_id, 'fn': file.filename, 'p': path, 'ch': ch, 'u': getattr(user, 'username', str(user)), 'st': 'uploaded', 'rc': 0, 'prof': json.dumps(profile)})
    db.commit()
    job_id = db.execute(text("SELECT id FROM refresh_jobs WHERE stored_path = :p AND filename = :fn ORDER BY id DESC LIMIT 1"), {'p': path, 'fn': file.filename}).scalar()
    # load rows into refresh_staging_rows
    try:
        df = ingest.read_file_to_df(path)
    except Exception:
        df = None
    count = 0
    if df is not None:
        rows = df.to_dict(orient='records')
        stmt = "INSERT INTO refresh_staging_rows (job_id, row_number, row_json) VALUES (:jid, :rn, :rj)"
        for i, rr in enumerate(rows, start=1):
            db.execute(text(stmt), {'jid': job_id, 'rn': i, 'rj': json.dumps(rr, default=str)})
            count += 1
        db.commit()
    # update job row_count
    db.execute(text("UPDATE refresh_jobs SET row_count = :rc WHERE id = :id"), {'rc': count, 'id': job_id})
    db.commit()
    return {'job_id': job_id, 'row_count': count, 'profile': profile}


@router.get('/jobs/{job_id}')
def job_status(job_id: int, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM refresh_jobs WHERE id = :id"), {'id': job_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='job not found')
    return dict(row)


@router.post('/jobs/{job_id}/commit')
def commit_job(job_id: int, body: dict, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    mode = body.get('mode', 'replace')
    merge_keys = body.get('merge_keys', [])
    # load job
    job = db.execute(text("SELECT * FROM refresh_jobs WHERE id = :id"), {'id': job_id}).mappings().fetchone()
    if not job:
        raise HTTPException(status_code=404, detail='job not found')
    source_id = job['source_id']
    # count staging rows
    rows = db.execute(text("SELECT id, row_number, row_json FROM refresh_staging_rows WHERE job_id = :jid ORDER BY row_number"), {'jid': job_id}).mappings().all()
    staged = [json.loads(r['row_json']) for r in rows]

    # compute before count
    before_row_count = db.execute(text("SELECT COUNT(*) as c FROM refresh_dataset_rows WHERE source_id = :sid"), {'sid': source_id}).scalar() or 0

    # create new dataset_version
    import uuid
    ver = str(uuid.uuid4())
    checksum = job['checksum']
    res = db.execute(text("INSERT INTO dataset_versions (source_id, version, checksum, created_by, created_at, row_count) VALUES (:sid, :ver, :ch, :by, datetime('now'), :rc)"), {'sid': source_id, 'ver': ver, 'ch': checksum, 'by': getattr(user, 'username', str(user)), 'rc': 0})
    db.commit()
    # debug: count rows for this source
    try:
        cnt = db.execute(text("SELECT COUNT(*) FROM dataset_versions WHERE source_id = :sid"), {'sid': source_id}).scalar()
        print('DEBUG: dataset_versions_count_for_source', source_id, cnt)
    except Exception:
        print('DEBUG: failed to count dataset_versions')
    version_id = getattr(res, 'lastrowid', None) or (getattr(res, 'cursor', None) and getattr(res.cursor, 'lastrowid', None))
    if not version_id:
        version_id = db.execute(text("SELECT id FROM dataset_versions WHERE version = :ver ORDER BY id DESC LIMIT 1"), {'ver': ver}).scalar()
    print('DEBUG: resolved_version_id', version_id, 'version_str', ver)
    try:
        all_vs = db.execute(text("SELECT id, version, source_id, row_count FROM dataset_versions ORDER BY id"), {}).mappings().all()
        print('DEBUG: all dataset_versions rows:', all_vs)
    except Exception:
        print('DEBUG: failed to list dataset_versions')

    # apply according to mode
    if mode == 'replace':
        # remove existing rows for source and insert staged rows as new version
        db.execute(text("DELETE FROM refresh_dataset_rows WHERE source_id = :sid"), {'sid': source_id})
        stmt = "INSERT INTO refresh_dataset_rows (source_id, version_id, row_json, created_at) VALUES (:sid, :vid, :rj, datetime('now'))"
        for r in staged:
            db.execute(text(stmt), {'sid': source_id, 'vid': version_id, 'rj': json.dumps(r, default=str)})
        db.commit()
    elif mode == 'upsert':
        # load current rows and index by merge_keys
        if not merge_keys:
            # try to pull from source registry
            srow = db.execute(text("SELECT required_merge_keys FROM refresh_sources WHERE id = :id"), {'id': source_id}).mappings().fetchone()
            if srow and srow['required_merge_keys']:
                try:
                    merge_keys = json.loads(srow['required_merge_keys'])
                except Exception:
                    merge_keys = []
        if not merge_keys:
            raise HTTPException(status_code=400, detail='merge_keys required for upsert')
        cur_rows = db.execute(text("SELECT row_json FROM refresh_dataset_rows WHERE source_id = :sid"), {'sid': source_id}).scalars().all()
        existing = [json.loads(r) for r in cur_rows]
        index = {}
        for er in existing:
            key = tuple(str(er.get(k)) for k in merge_keys)
            index[key] = er
        # apply staged changes
        for sr in staged:
            key = tuple(str(sr.get(k)) for k in merge_keys)
            index[key] = {**index.get(key, {}), **sr}
        # write merged set as new version: delete old and insert merged
        db.execute(text("DELETE FROM refresh_dataset_rows WHERE source_id = :sid"), {'sid': source_id})
        stmt = "INSERT INTO refresh_dataset_rows (source_id, version_id, row_json, created_at) VALUES (:sid, :vid, :rj, datetime('now'))"
        for v in index.values():
            db.execute(text(stmt), {'sid': source_id, 'vid': version_id, 'rj': json.dumps(v, default=str)})
        db.commit()
    else:
        raise HTTPException(status_code=400, detail='unsupported mode')

    # update dataset_versions row_count
    new_count = db.execute(text("SELECT COUNT(*) as c FROM refresh_dataset_rows WHERE source_id = :sid AND version_id = :vid"), {'sid': source_id, 'vid': version_id}).scalar() or 0
    db.execute(text("UPDATE dataset_versions SET row_count = :rc WHERE id = :id"), {'rc': new_count, 'id': version_id})
    db.commit()

    # update refresh_history
    db.execute(text("INSERT INTO refresh_history (job_id, version_id, mode, status, applied_by, applied_at, row_count_before, row_count_after) VALUES (:jid, :vid, :m, :st, :by, datetime('now'), :b, :a)"), {'jid': job_id, 'vid': version_id, 'm': mode, 'st': 'applied', 'by': getattr(user, 'username', str(user)), 'b': before_row_count, 'a': new_count})
    db.commit()

    # set active version pointer
    # upsert into dataset_active
    had = db.execute(text("SELECT * FROM dataset_active WHERE source_id = :sid"), {'sid': source_id}).mappings().fetchone()
    if had:
        db.execute(text("UPDATE dataset_active SET version_id = :vid, bound_at = datetime('now'), bound_by = :by WHERE source_id = :sid"), {'vid': version_id, 'by': getattr(user, 'username', str(user)), 'sid': source_id})
    else:
        db.execute(text("INSERT INTO dataset_active (source_id, version_id, bound_at, bound_by) VALUES (:sid, :vid, datetime('now'), :by)"), {'sid': source_id, 'vid': version_id, 'by': getattr(user, 'username', str(user))})
    db.commit()

    # mark job completed
    db.execute(text("UPDATE refresh_jobs SET status = :st WHERE id = :id"), {'st': 'committed', 'id': job_id})
    db.commit()

    print('DEBUG: returning job/vid/count', job_id, version_id, new_count)
    return {'job_id': job_id, 'version_id': version_id, 'row_count': new_count}


@router.get('/sources/{source_id}/current')
def get_current(source_id: int, limit: int = 100, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    vid = db.execute(text("SELECT version_id FROM dataset_active WHERE source_id = :sid"), {'sid': source_id}).scalar()
    if not vid:
        raise HTTPException(status_code=404, detail='no active version')
    rows = db.execute(text("SELECT row_json FROM refresh_dataset_rows WHERE source_id = :sid AND version_id = :vid LIMIT :lim"), {'sid': source_id, 'vid': vid, 'lim': limit}).scalars().all()
    return {'version_id': vid, 'rows': [json.loads(r) for r in rows]}
