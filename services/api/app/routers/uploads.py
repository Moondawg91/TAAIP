from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional
from .. import db
from services.api import importers
import os, hashlib, uuid, datetime

router = APIRouter()

def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/api/v2/uploads')
async def upload_v2(file: UploadFile = File(...), source_system: Optional[str] = Form(None)):
    contents = await file.read()
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
        cur.execute("INSERT INTO staging_uploads(dataset_key, source_name, uploaded_at, raw_json, validated) VALUES (?,?,datetime('now'),?,0)", (dataset_key, source_name, json.dumps(raw_json)))
        conn.commit()
        return {"status": "ok", "staging_id": cur.lastrowid}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}


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
