from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional
from .. import db
from services.api import importers
import os, hashlib, uuid, datetime, shutil, time, threading

router = APIRouter()


def _ensure_staging_uploads_table(cur):
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS staging_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_key TEXT,
            source_name TEXT,
            uploaded_at TEXT,
            raw_json TEXT,
            validated INTEGER DEFAULT 0
        )
        '''
    )


def _update_ingest_status(
    ingest_id: int,
    new_status: str,
    *,
    set_started: bool = False,
    set_completed: bool = False,
    error_message: Optional[str] = None,
):
    conn = connect()
    cur = conn.cursor()
    try:
        _ensure_staging_uploads_table(cur)
        cur.execute("SELECT raw_json FROM staging_uploads WHERE id = ?", (int(ingest_id),))
        row = cur.fetchone()
        if not row:
            return

        try:
            payload = json.loads(row[0]) if row[0] else {}
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        now = datetime.datetime.utcnow().isoformat()
        payload['status'] = new_status
        if set_started and not payload.get('started_at'):
            payload['started_at'] = now
        if set_completed:
            payload['completed_at'] = now
        if error_message:
            payload['error_message'] = str(error_message)

        cur.execute(
            "UPDATE staging_uploads SET raw_json = ? WHERE id = ?",
            (json.dumps(payload), int(ingest_id)),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def _run_ingest_progression(ingest_id: int, force_fail: bool = False):
    """Advance ingest state from queued -> processing -> completed/failed."""
    try:
        _update_ingest_status(int(ingest_id), 'processing', set_started=True)
        time.sleep(float(os.getenv('UPLOAD_INGEST_SIM_SECONDS', '2.0')))
        if force_fail or os.getenv('UPLOAD_INGEST_FORCE_FAIL', '0') == '1':
            raise RuntimeError('Forced ingest failure (UPLOAD_INGEST_FORCE_FAIL=1)')
        _update_ingest_status(int(ingest_id), 'completed', set_completed=True)
    except Exception as e:
        _update_ingest_status(int(ingest_id), 'failed', set_started=True, set_completed=True, error_message=str(e))

def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/api/v2/uploads')
async def upload_v2(file: UploadFile = File(...), source_system: Optional[str] = Form(None)):
    contents = await file.read()
    # Reject simulation/demo-marked uploads unless explicitly allowed
    if os.getenv('ALLOW_SIMULATION_IMPORTS') != '1':
        try:
            sim_pat = __import__('re').compile(r"\bSIM_|\bsim-|\bdemo-|\bdemo_", __import__('re').IGNORECASE)
            try:
                s = contents.decode('utf-8', errors='ignore')
            except Exception:
                s = ''
            if sim_pat.search(s):
                raise HTTPException(status_code=400, detail="Import rejected: contains simulation/demo markers. Set ALLOW_SIMULATION_IMPORTS=1 to override.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Import validation failed; refused to process file")
    sha = hashlib.sha256(contents).hexdigest()
    upload_id = uuid.uuid4().hex
    # store file
    base_dir = os.getenv('TAAIP_UPLOAD_DIR', 'services/api/.data/imports_v2')
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"{upload_id}_{file.filename}")
    with open(path, 'wb') as fh:
        fh.write(contents)

    # create staging_upload row
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO staging_upload(id, filename, content_type, size_bytes, sha256, source_system, status, created_at) VALUES (?,?,?,?,?,?,?,?)', (upload_id, file.filename, file.content_type, len(contents), sha, source_system, 'RECEIVED', now_iso()))
        conn.commit()
    finally:
        conn.close()

    # detect and run import
    result = importers.run_import(upload_id=upload_id, path=path, filename=file.filename, forced_dataset_id=None, source_system=source_system)
    return result
import json
from fastapi import APIRouter, Body
from services.api.app.db import connect

router = APIRouter()


@router.post("/uploads")
def create_upload(dataset_key: str = Body(...), source_name: str = Body(...), raw_json: object = Body(...)):
    """Store a raw upload into `staging_uploads` for validation/processing."""
    conn = connect()
    cur = conn.cursor()
    try:
        _ensure_staging_uploads_table(cur)
        cur.execute("INSERT INTO staging_uploads(dataset_key, source_name, uploaded_at, raw_json, validated) VALUES (?,?,datetime('now'),?,0)", (dataset_key, source_name, json.dumps(raw_json)))
        conn.commit()
        return {"status": "ok", "staging_id": cur.lastrowid}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}


@router.post('/v2/upload/ingest')
@router.post('/api/v2/upload/ingest')
def ingest_uploaded_document(payload: dict = Body(...)):
    """Ingest trigger for Document Center uploads.

    Records an ingest job row in staging_uploads so upload history surfaces can show activity.
    """
    document_id = str(payload.get('document_id') or '').strip()
    category = str(payload.get('category') or 'general').strip() or 'general'
    source = str(payload.get('source') or 'document_center').strip() or 'document_center'
    filename = str(payload.get('filename') or '').strip()
    force_fail = str(payload.get('force_fail') or '').strip().lower() in {'1', 'true', 'yes'}

    if not document_id:
        return {"status": "error", "message": "document_id is required"}

    conn = connect()
    cur = conn.cursor()
    try:
        _ensure_staging_uploads_table(cur)
        ingest_payload = {
            "document_id": document_id,
            "filename": filename,
            "category": category,
            "source": source,
            "status": "queued",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "force_fail": force_fail,
        }
        cur.execute(
            "INSERT INTO staging_uploads(dataset_key, source_name, uploaded_at, raw_json, validated) VALUES (?,?,datetime('now'),?,0)",
            (category, source, json.dumps(ingest_payload)),
        )
        conn.commit()
        ingest_id = int(cur.lastrowid)
        threading.Thread(target=_run_ingest_progression, args=(ingest_id, force_fail), daemon=True).start()
        return {
            "status": "ok",
            "ingest_id": ingest_id,
            "state": "queued",
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@router.get('/v2/upload/history')
@router.get('/api/v2/upload/history')
def upload_history(limit: int = 100):
    """Upload history with ingest lifecycle fields for Processing and Mapping Status."""
    conn = connect()
    cur = conn.cursor()
    try:
        _ensure_staging_uploads_table(cur)
        cur.execute(
            """
            SELECT id, dataset_key, source_name, uploaded_at, raw_json
            FROM staging_uploads
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit), 500)),),
        )
        rows = cur.fetchall()

        history = []
        for row in rows:
            ingest_id = int(row[0])
            category = str(row[1] or 'general')
            uploaded_at = str(row[3] or '')
            raw = row[4]

            details = {}
            rows_count = 0
            data_preview = []
            try:
                parsed = json.loads(raw) if raw else {}
                if isinstance(parsed, dict):
                    details = parsed
                    rows_count = 1
                    data_preview = [parsed]
                elif isinstance(parsed, list):
                    rows_count = len(parsed)
                    data_preview = parsed[:3]
                    if parsed and isinstance(parsed[0], dict):
                        details = parsed[0]
            except Exception:
                details = {}

            current_status = str(details.get('status') or 'completed')
            created_at = str(details.get('created_at') or uploaded_at)
            started_at = details.get('started_at')
            completed_at = details.get('completed_at')
            error_message = details.get('error_message')
            document_id = details.get('document_id')
            filename = details.get('filename')

            history.append({
                'id': ingest_id,
                'ingest_id': ingest_id,
                'document_id': document_id,
                'filename': filename,
                'category': str(details.get('category') or category),
                'current_status': current_status,
                'created_at': created_at,
                'started_at': started_at,
                'completed_at': completed_at,
                'error_message': error_message,
                # Compatibility fields consumed by existing UI
                'rows_count': rows_count,
                'imported_at': uploaded_at,
                'data': data_preview,
            })

        return {'status': 'ok', 'history': history}
    finally:
        conn.close()


@router.post('/uploads/validate')
def validate_upload(body: dict = Body(...)):
    staging_id = body.get('staging_id')
    try:
        staging_id = int(staging_id)
    except Exception:
        return {"status":"error","message":"staging_id must be integer"}
    """Validate a staging upload: ensure rows contain required fields.
    If validation passes, mark `validated=1`.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, dataset_key, source_name, raw_json, validated FROM staging_uploads WHERE id = ?", (staging_id,))
        row = cur.fetchone()
        if not row:
            return {"status":"error","message":"staging_id not found"}
        raw = row[3]
        try:
            payload = json.loads(raw)
        except Exception as e:
            return {"status":"error","message":"invalid JSON in staging record"}

        errors = []
        missing_units = set()
        parsed = []
        for i, r in enumerate(payload if isinstance(payload, list) else [payload]):
            if not isinstance(r, dict):
                errors.append({"row": i, "error": "row not object"})
                continue
            # accept either date_iso or date_key
            date_iso = r.get('date_iso') or r.get('date')
            unit_key = r.get('unit_key')
            stage = r.get('stage')
            count = r.get('count')
            if not date_iso or not unit_key or stage is None or count is None:
                errors.append({"row": i, "error": "missing required field (date_iso/unit_key/stage/count)"})
                continue
            # normalize date_key
            try:
                # expected YYYY-MM-DD or ISO
                date_key = date_iso.split('T')[0]
            except Exception:
                date_key = date_iso
            # check unit exists
            cur.execute("SELECT unit_key FROM dim_unit WHERE unit_key = ?", (unit_key,))
            if not cur.fetchone():
                missing_units.add(unit_key)
            parsed.append({"date_key": date_key, "unit_key": unit_key, "stage": stage, "count": int(count)})

        result = {"errors": errors, "missing_units": list(missing_units), "rows_validated": len(parsed)}
        if not errors:
            cur.execute("UPDATE staging_uploads SET validated = 1 WHERE id = ?", (staging_id,))
            conn.commit()
        else:
            conn.rollback()
        return {"status":"ok","validation": result}
    except Exception as e:
        conn.rollback()
        return {"status":"error","message": str(e)}


@router.post('/uploads/commit')
def commit_upload(body: dict = Body(...)):
    staging_id = body.get('staging_id')
    try:
        staging_id = int(staging_id)
    except Exception:
        return {"status":"error","message":"staging_id must be integer"}
    """Commit validated staging upload into warehouse fact tables idempotently.
    Currently supports dataset_key that maps to `fact_funnel_daily` when rows contain
    `date_iso`, `unit_key`, `stage`, `count`.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, dataset_key, source_name, raw_json, validated FROM staging_uploads WHERE id = ?", (staging_id,))
        row = cur.fetchone()
        if not row:
            return {"status":"error","message":"staging_id not found"}
        if row[4] != 1:
            return {"status":"error","message":"staging record not validated"}
        dataset_key = row[1]
        raw = row[3]
        payload = json.loads(raw)
        rows = payload if isinstance(payload, list) else [payload]

        # Route commit by dataset_key. Currently support funnel-style datasets.
        if dataset_key and ('funnel' in dataset_key.lower()):
            inserted = 0
            updated = 0
            for r in rows:
                date_iso = r.get('date_iso') or r.get('date')
                unit_key = r.get('unit_key')
                stage = r.get('stage')
                count = int(r.get('count') or 0)
                if not date_iso or not unit_key or stage is None:
                    # skip invalid rows
                    continue
                date_key = date_iso.split('T')[0]
                # ensure dim_date exists
                try:
                    y, m, d = (int(x) for x in date_key.split('-'))
                except Exception:
                    y = m = d = None
                cur.execute("INSERT OR IGNORE INTO dim_date(date_key, date_iso, year, month, day) VALUES (?,?,?,?,?)", (date_key, date_iso, y, m, d))
                # idempotent upsert into fact_funnel_daily (match on date_key, unit_key, stage)
                cur.execute("SELECT id FROM fact_funnel_daily WHERE date_key = ? AND unit_key = ? AND stage = ?", (date_key, unit_key, stage))
                existing = cur.fetchone()
                if existing:
                    cur.execute("UPDATE fact_funnel_daily SET count = ?, ingested_at = datetime('now') WHERE id = ?", (count, existing[0]))
                    updated += 1
                else:
                    cur.execute("INSERT INTO fact_funnel_daily(date_key, unit_key, stage, count, ingested_at) VALUES (?,?,?,?,datetime('now'))", (date_key, unit_key, stage, count))
                    inserted += 1
            conn.commit()
            return {"status":"ok","inserted": inserted, "updated": updated}

        # Unsupported dataset_key for commit
        # Support marketing datasets: insert into fact_marketing
        if dataset_key and 'marketing' in dataset_key.lower():
            committed = 0
            for r in rows:
                try:
                    fid = __import__('uuid').uuid4().hex
                    org = r.get('org_unit_id') or r.get('unit_key') or r.get('org')
                    date = r.get('date_iso') or r.get('date') or r.get('date_key')
                    campaign = r.get('campaign')
                    channel = r.get('channel')
                    impressions = float(r.get('impressions') or 0)
                    engagements = float(r.get('engagements') or 0)
                    clicks = float(r.get('clicks') or 0)
                    conversions = float(r.get('conversions') or 0)
                    cost = float(r.get('cost') or 0)
                except Exception:
                    continue
                cur.execute('INSERT OR REPLACE INTO fact_marketing(id, org_unit_id, date_key, campaign, channel, impressions, engagements, clicks, conversions, cost, source_system, import_job_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                    fid, str(org), str(date)[:10] if date else None, campaign, channel, impressions, engagements, clicks, conversions, cost, None, None, __import__('datetime').datetime.utcnow().isoformat()
                ))
                committed += 1
            conn.commit()
            return {'status': 'ok', 'committed': committed}

        # Support event metrics datasets: insert into event_metrics
        if dataset_key and ('event' in dataset_key.lower() or 'event_metrics' in dataset_key.lower() or 'event_performance' in dataset_key.lower()):
            committed = 0
            for r in rows:
                try:
                    fid = __import__('uuid').uuid4().hex
                    event_id = r.get('event_id') or r.get('event')
                    impressions = int(r.get('impressions') or 0)
                    engagements = int(r.get('engagements') or 0)
                    leads = int(r.get('leads') or 0)
                    appts_made = int(r.get('appts_made') or 0)
                    appts_conducted = int(r.get('appts_conducted') or 0)
                    contracts = int(r.get('contracts') or 0)
                    accessions = int(r.get('accessions') or 0)
                    captured_at = r.get('captured_at') or r.get('date')
                except Exception:
                    continue
                cur.execute('INSERT OR REPLACE INTO event_metrics(id, event_id, impressions, engagements, leads, appts_made, appts_conducted, contracts, accessions, other_json, captured_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                    fid, event_id, impressions, engagements, leads, appts_made, appts_conducted, contracts, accessions, json.dumps(r), captured_at
                ))
                committed += 1
            conn.commit()
            return {'status': 'ok', 'committed': committed}

        return {"status":"error", "message": f"unsupported dataset_key for commit: {dataset_key}"}
    except Exception as e:
        conn.rollback()
        return {"status":"error","message": str(e)}


@router.get('/uploads/list')
def list_uploads(limit: int = 20, offset: int = 0, dataset_key: str = None, source_name: str = None, validated: int = None):
    """List recent staging uploads for admin UI with server-side filtering and pagination.
    Returns: { status:'ok', uploads: [...], total: <int> }
    """
    conn = connect()
    cur = conn.cursor()
    try:
        where = []
        params = []
        if dataset_key:
            where.append("dataset_key = ?")
            params.append(dataset_key)
        if source_name:
            where.append("source_name = ?")
            params.append(source_name)
        if validated is not None:
            where.append("validated = ?")
            params.append(1 if int(validated) else 0)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        # total count for pagination
        count_sql = f"SELECT COUNT(1) FROM staging_uploads {where_sql}"
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()[0]

        list_sql = f"SELECT id, dataset_key, source_name, uploaded_at, validated, raw_json FROM staging_uploads {where_sql} ORDER BY uploaded_at DESC LIMIT ? OFFSET ?"
        params_list = list(params) + [limit, offset]
        cur.execute(list_sql, tuple(params_list))
        rows = cur.fetchall()

        out = []
        for r in rows:
            id_, dataset_key, source_name, uploaded_at, validated_flag, raw = r
            row_count = 0
            preview = None
            try:
                payload = json.loads(raw) if raw else None
                if isinstance(payload, list):
                    row_count = len(payload)
                elif payload is None:
                    row_count = 0
                else:
                    row_count = 1
                preview = (json.dumps(payload)[:200]) if payload is not None else ''
            except Exception:
                preview = str(raw)[:200]
            out.append({
                'id': id_, 'dataset_key': dataset_key, 'source_name': source_name,
                'uploaded_at': uploaded_at, 'validated': bool(validated_flag), 'row_count': row_count, 'preview': preview
            })
        return {'status': 'ok', 'uploads': out, 'total': total}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@router.get('/v2/upload/backups')
@router.get('/api/v2/upload/backups')
def list_backups(limit: int = 50):
    """List available database backups."""
    try:
        backup_dir = os.getenv('TAAIP_BACKUP_DIR', './data/backups')
        if not os.path.exists(backup_dir):
            return {'status': 'ok', 'backups': []}
        
        backups = []
        for filename in sorted(os.listdir(backup_dir), reverse=True)[:limit]:
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath) and filename.endswith('.sqlite3'):
                stat = os.stat(filepath)
                backups.append({
                    'name': filename,
                    'path': filepath,
                    'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size_bytes': stat.st_size
                })
        
        return {'status': 'ok', 'backups': backups}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@router.post('/v2/upload/backup')
@router.post('/api/v2/upload/backup')
def create_backup():
    """Create a backup of the database."""
    try:
        db_path = db.get_db_path()
        backup_dir = os.getenv('TAAIP_BACKUP_DIR', './data/backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'taaip_backup_{timestamp}.sqlite3'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup by copying the database file
        conn = db.connect()
        try:
            # Close connection before copying to ensure file is not locked
            conn.close()
            time.sleep(0.1)
            shutil.copy2(db_path, backup_path)
            return {'status': 'ok', 'backup_path': backup_path, 'filename': backup_filename}
        except Exception as e:
            raise e
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@router.post('/v2/upload/restore')
@router.post('/api/v2/upload/restore')
async def restore_backup(backup_path: str = Form(...)):
    """Restore a database from backup."""
    try:
        current_db_path = db.get_db_path()
        backup_dir = os.getenv('TAAIP_BACKUP_DIR', './data/backups')
        
        # Validate backup path is within backup directory
        backup_realpath = os.path.realpath(backup_path)
        backup_dir_realpath = os.path.realpath(backup_dir)
        
        if not backup_realpath.startswith(backup_dir_realpath):
            return {'status': 'error', 'message': 'Invalid backup path'}
        
        if not os.path.exists(backup_path):
            return {'status': 'error', 'message': 'Backup file not found'}
        
        # Create a safety backup of current DB before restoring
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safety_backup = os.path.join(backup_dir, f'taaip_pre_restore_{timestamp}.sqlite3')
        
        # Close any existing connections
        time.sleep(0.2)
        
        try:
            # Backup current database
            shutil.copy2(current_db_path, safety_backup)
            # Restore from backup
            shutil.copy2(backup_path, current_db_path)
            return {'status': 'ok', 'message': 'Restore completed successfully', 'safety_backup': safety_backup}
        except Exception as e:
            return {'status': 'error', 'message': f'Restore failed: {str(e)}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
