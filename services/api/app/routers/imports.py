from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Body
from typing import Dict, List, Optional, Any
from .. import db
from .rbac import require_scope
import os, hashlib, json, csv, io, datetime, re, uuid, pathlib

try:
    import openpyxl
except Exception:
    openpyxl = None

router = APIRouter()


def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def audit(conn, who: str, action: str, entity: str, entity_id: int = None, meta: dict = None):
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)', (
            who or 'system', action, entity, entity_id, json.dumps(meta or {}), now_iso()
        ))
        conn.commit()
    except Exception:
        pass


@router.post('/api/import/upload')
async def upload_file(file: UploadFile = File(...), uploaded_by: Optional[str] = None, target_domain: Optional[str] = 'generic', allowed_orgs: Optional[list] = Depends(require_scope('STATION'))) -> Dict:
    # create job row first so we can store file under a safe per-job folder
    conn = db.connect()
    try:
        cur = conn.cursor()
        created_at = now_iso()
        cur.execute("INSERT INTO import_job(filename_original, file_type, file_size_bytes, sha256_hash, uploaded_by_user_id, uploaded_at, status, target_domain, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (file.filename, os.path.splitext(file.filename)[1].lstrip('.').lower(), 0, None, uploaded_by, created_at, 'uploaded', target_domain, created_at, created_at))
        jid = cur.lastrowid
        conn.commit()
        try:
            audit(conn, uploaded_by or 'uploader', 'import.upload', 'import_job', jid, {'filename': file.filename, 'target_domain': target_domain})
        except Exception:
            pass
    finally:
        conn.close()

    # store file in per-job folder
    base_dir = os.getenv('TAAIP_UPLOAD_DIR', 'services/api/.data/imports')
    job_dir = os.path.join(base_dir, f"job_{jid}")
    os.makedirs(job_dir, exist_ok=True)
    contents = await file.read()
    sha = hashlib.sha256(contents).hexdigest()
    fname = f"original{os.path.splitext(file.filename)[1].lower()}"
    path = os.path.join(job_dir, fname)
    with open(path, 'wb') as fh:
        fh.write(contents)

    # update job with sha and file size
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE import_job SET sha256_hash=?, file_size_bytes=?, file_type=?, updated_at=? WHERE id=?', (sha, len(contents), os.path.splitext(file.filename)[1].lstrip('.').lower(), now_iso(), jid))
        # also create a v3 import_job id for provenance tracking
        import_job_uuid = uuid.uuid4().hex
        try:
            cur.execute('INSERT OR REPLACE INTO import_job_v3(id, created_at, created_by, dataset_key, source_system, filename, file_sha256, status, row_count, error_count, notes, scope_org_unit_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
                import_job_uuid, now_iso(), uploaded_by, target_domain or 'generic', None, file.filename, sha, 'uploaded', 0, 0, None, None
            ))
        except Exception:
            pass
        # record import_file metadata
        file_id = uuid.uuid4().hex
        try:
            cur.execute('INSERT OR REPLACE INTO import_file(id, import_job_id, stored_path, content_type, size_bytes, uploaded_at) VALUES (?,?,?,?,?,?)', (
                file_id, import_job_uuid, path, file.content_type or os.path.splitext(file.filename)[1].lstrip('.').lower(), len(contents), now_iso()
            ))
        except Exception:
            pass
        conn.commit()
        return {'import_job_id': import_job_uuid, 'legacy_job_id': jid}
    finally:
        conn.close()



@router.post('/api/import/parse')
def parse_job_v3(payload: Dict[str, Any] = Body(...), sheet: Optional[str] = None, max_preview: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    import_job_id = payload.get('import_job_id')
    if not import_job_id:
        raise HTTPException(status_code=400, detail='missing import_job_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT stored_path, size_bytes FROM import_file WHERE import_job_id=? ORDER BY uploaded_at DESC LIMIT 1', (import_job_id,))
        f = cur.fetchone()
        if not f:
            raise HTTPException(status_code=404, detail='uploaded file not found')
        path = f['stored_path'] if 'stored_path' in f.keys() else f[0]
        if not os.path.isfile(path):
            raise HTTPException(status_code=500, detail='uploaded file missing on disk')
        ext = os.path.splitext(path)[1].lower()
        preview = []
        columns = []
        # reuse parsing logic from existing function where possible
        if ext in ('.csv', '.txt'):
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                reader = csv.DictReader(fh)
                for i, r in enumerate(reader):
                    if i >= max_preview: break
                    preview.append({k: (v if v is not None else '') for k, v in r.items()})
            columns = list(preview[0].keys()) if preview else []
        elif ext == '.json':
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    preview = data[:max_preview]
                    columns = sorted(list(set().union(*(d.keys() for d in preview))) ) if preview else []
                elif isinstance(data, dict):
                    def flatten(d, parent=''):
                        items = {}
                        for k, v in d.items():
                            key = f"{parent}.{k}" if parent else k
                            if isinstance(v, dict):
                                items.update(flatten(v, key))
                            else:
                                items[key] = v
                        return items
                    flat = flatten(data)
                    preview = [flat]
                    columns = list(flat.keys())
        elif ext in ('.xlsx', '.xls'):
            try:
                import openpyxl as _openpyxl
            except Exception:
                raise HTTPException(status_code=202, detail='xlsx_parser_missing')
            wb = _openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheet_name = sheet or wb.sheetnames[0]
            ws = wb[sheet_name]
            rows = ws.iter_rows(values_only=True)
            try:
                header = next(rows)
            except StopIteration:
                header = []
            for i, r in enumerate(rows):
                if i >= max_preview: break
                rowobj = {str(header[j]) if header and j < len(header) and header[j] is not None else f'col_{j}': (r[j] if j < len(r) else None) for j in range(len(r))}
                preview.append(rowobj)
            columns = list(preview[0].keys()) if preview else []
        else:
            if ext == '.sql':
                # safe SQL parse: do NOT execute. Provide preview of first N non-empty lines and detect INSERT targets
                with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                    lines = [l.strip() for l in fh.readlines() if l.strip()]
                preview_lines = lines[:max_preview]
                preview = [{'sql': l} for l in preview_lines]
                columns = ['sql']
            else:
                raise HTTPException(status_code=400, detail='unsupported_file_type')

        # store preview in import_job_v3 notes (simple) and update row_count
        cur.execute('UPDATE import_job_v3 SET row_count=? , status=?, notes=? WHERE id=?', (len(preview), 'parsed', json.dumps({'columns': columns, 'preview_sample_count': len(preview)}), import_job_id))
        # also store preview rows into imported_rows (fallback provenance)
        for i, r in enumerate(preview):
            cur.execute('INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,?)', (import_job_id, payload.get('dataset_key','generic'), json.dumps(r), now_iso()))
        conn.commit()
        return {'status':'ok', 'import_job_id': import_job_id, 'columns': columns, 'preview_rows': preview[:50], 'row_count': len(preview)}
    finally:
        conn.close()


@router.post('/api/import/map')
def map_v3(payload: Dict[str, Any] = Body(...), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    import_job_id = payload.get('import_job_id')
    mapping = payload.get('mapping')
    dataset_key = payload.get('dataset_key')
    source_system = payload.get('source_system')
    scope_org = payload.get('scope_org_unit_id')
    if not import_job_id or not mapping:
        raise HTTPException(status_code=400, detail='missing fields')
    conn = db.connect()
    try:
        cur = conn.cursor()
        map_id = uuid.uuid4().hex
        cur.execute('INSERT INTO import_column_map(id, import_job_id, mapping_json, created_at) VALUES (?,?,?,?)', (map_id, import_job_id, json.dumps(mapping), now_iso()))
        cur.execute('UPDATE import_job_v3 SET dataset_key=?, source_system=?, scope_org_unit_id=?, status=?, updated_at=? WHERE id=?', (dataset_key, source_system, scope_org, 'mapped', now_iso(), import_job_id))
        conn.commit()
        return {'status':'ok', 'import_job_id': import_job_id}
    finally:
        conn.close()


@router.post('/api/import/validate')
def validate_v3(payload: Dict[str, Any] = Body(...), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    import_job_id = payload.get('import_job_id')
    if not import_job_id:
        raise HTTPException(status_code=400, detail='missing import_job_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT mapping_json FROM import_column_map WHERE import_job_id=? ORDER BY created_at DESC LIMIT 1', (import_job_id,))
        mrow = cur.fetchone()
        mapping = json.loads(mrow['mapping_json']) if mrow and mrow['mapping_json'] else {}
        # dataset_key is stored on the import_job_v3 record; fall back to payload if absent
        cur.execute('SELECT dataset_key FROM import_job_v3 WHERE id=? LIMIT 1', (import_job_id,))
        jrow = cur.fetchone()
        dataset = jrow['dataset_key'] if jrow and 'dataset_key' in jrow.keys() and jrow['dataset_key'] else (payload.get('dataset_key') if payload else None)
        # fetch imported_rows for this job
        cur.execute('SELECT id, row_json FROM imported_rows WHERE import_job_id=? LIMIT 1000', (import_job_id,))
        rows = cur.fetchall()
        errors = 0
        sample_errors = []
        for i, r in enumerate(rows):
            row = json.loads(r['row_json']) if isinstance(r['row_json'], str) else r['row_json']
            # basic validations depending on dataset
            if dataset == 'production':
                # require org_unit_id, date (YYYY-MM-DD), metric_key, metric_value
                org = row.get(mapping.get('org_unit_id')) if mapping.get('org_unit_id') else row.get('org_unit_id') or row.get('org_unit')
                date = row.get(mapping.get('date_key')) if mapping.get('date_key') else row.get('date') or row.get('date_key')
                metric = row.get(mapping.get('metric_key')) if mapping.get('metric_key') else row.get('metric_key')
                value = row.get(mapping.get('metric_value')) if mapping.get('metric_value') else row.get('metric_value')
                # org check
                if not org:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'org_unit', 'missing org identifier', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'org_unit', 'message':'missing org identifier'})
                # date check
                try:
                    if date:
                        _ = datetime.datetime.strptime(str(date)[:10], '%Y-%m-%d')
                    else:
                        raise Exception()
                except Exception:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'date', 'invalid date', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'date', 'message':'invalid date'})
                # numeric value
                try:
                    float(value)
                except Exception:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'metric_value', 'not numeric', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'metric_value', 'message':'not numeric'})
            elif dataset == 'marketing':
                # check date and org
                date = row.get(mapping.get('date_key')) if mapping.get('date_key') else row.get('date')
                if not date:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'date', 'missing date', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'date', 'message':'missing date'})
            elif dataset == 'funnel':
                org = row.get(mapping.get('org_unit_id')) if mapping.get('org_unit_id') else row.get('org_unit_id') or row.get('org_unit')
                date = row.get(mapping.get('date_key')) if mapping.get('date_key') else row.get('date') or row.get('date_key')
                stage = row.get(mapping.get('stage')) if mapping.get('stage') else row.get('stage')
                count = row.get(mapping.get('count_value')) if mapping.get('count_value') else row.get('count_value')
                if not org:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'org_unit', 'missing org identifier', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'org_unit', 'message':'missing org identifier'})
                try:
                    if date:
                        _ = datetime.datetime.strptime(str(date)[:10], '%Y-%m-%d')
                    else:
                        raise Exception()
                except Exception:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'date', 'invalid date', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'date', 'message':'invalid date'})
                try:
                    float(count)
                except Exception:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, 'count_value', 'not numeric', now_iso()))
                    sample_errors.append({'row': i+1, 'field':'count_value', 'message':'not numeric'})
            elif dataset == 'org_units':
                # require id and type
                uid = row.get(mapping.get('id')) if mapping.get('id') else row.get('id')
                utype = row.get(mapping.get('type')) if mapping.get('type') else row.get('type')
                if not uid or not utype:
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, None, 'missing id or type', now_iso()))
                    sample_errors.append({'row': i+1, 'message':'missing id or type'})
            else:
                # generic checks: non-empty row
                if not any(row.values()):
                    errors += 1
                    cur.execute('INSERT INTO import_error(id, import_job_id, row_index, field, message, created_at) VALUES (?,?,?,?,?,?)', (uuid.uuid4().hex, import_job_id, i+1, None, 'empty row', now_iso()))
                    sample_errors.append({'row': i+1, 'message':'empty row'})

        cur.execute('UPDATE import_job_v3 SET error_count=?, status=?, updated_at=? WHERE id=?', (errors, ('validated' if errors==0 else 'validated_with_errors'), now_iso(), import_job_id))
        conn.commit()
        return {'status':'ok', 'import_job_id': import_job_id, 'error_count': errors, 'sample_errors': sample_errors[:50]}
    finally:
        conn.close()


@router.post('/api/import/commit')
def commit_v3(payload: Dict[str, Any] = Body(...), allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    import_job_id = payload.get('import_job_id')
    mode = payload.get('mode', 'append')
    if not import_job_id:
        raise HTTPException(status_code=400, detail='missing import_job_id')
    conn = db.connect()
    try:
        cur = conn.cursor()
        # Try v3 import_job first
        cur.execute('SELECT dataset_key, source_system, scope_org_unit_id FROM import_job_v3 WHERE id=?', (import_job_id,))
        job = cur.fetchone()
        rows = []
        legacy_mode = False
        if job:
            dataset = job['dataset_key'] if 'dataset_key' in job.keys() else job[0]
            source_system = job['source_system'] if 'source_system' in job.keys() else job[1]
            scope_org = job['scope_org_unit_id'] if 'scope_org_unit_id' in job.keys() else job[2]
            # fetch v3 stored preview rows
            cur.execute('SELECT row_json FROM imported_rows WHERE import_job_id=?', (import_job_id,))
            rows = cur.fetchall()
            # load mapping if present
            cur.execute('SELECT mapping_json FROM import_column_map WHERE import_job_id=? ORDER BY created_at DESC LIMIT 1', (import_job_id,))
            mrow = cur.fetchone()
            mapping = json.loads(mrow['mapping_json']) if mrow and mrow['mapping_json'] else {}
        else:
            # fallback: support legacy numeric import_job id
            try:
                legacy_id = int(import_job_id)
            except Exception:
                legacy_id = None
            if legacy_id is not None:
                cur.execute('SELECT id, target_domain, source_system, filename FROM import_job WHERE id=?', (legacy_id,))
                ljob = cur.fetchone()
                if ljob:
                    legacy_mode = True
                    dataset = ljob['target_domain'] if 'target_domain' in ljob.keys() else (ljob[1] if len(ljob) > 1 else 'generic')
                    source_system = ljob['source_system'] if 'source_system' in ljob.keys() else None
                    scope_org = None
                    # fetch legacy imported_rows where import_job_id is numeric
                    cur.execute('SELECT row_json FROM imported_rows WHERE import_job_id=?', (legacy_id,))
                    rows = cur.fetchall()
                else:
                    raise HTTPException(status_code=404, detail='job not found')
            else:
                raise HTTPException(status_code=404, detail='job not found')
        committed = 0
        for r in rows:
            row = json.loads(r['row_json']) if isinstance(r['row_json'], str) else r['row_json']
            if dataset == 'production':
                # use mapping when provided
                org = row.get(mapping.get('org_unit_id')) if mapping.get('org_unit_id') else (row.get('org_unit_id') or row.get('org_unit'))
                date = row.get(mapping.get('date_key')) if mapping.get('date_key') else (row.get('date') or row.get('date_key'))
                metric = row.get(mapping.get('metric_key')) if mapping.get('metric_key') else row.get('metric_key')
                val = row.get(mapping.get('metric_value')) if mapping.get('metric_value') else row.get('metric_value')
                if not org or not date or metric is None or val is None:
                    continue
                fid = uuid.uuid4().hex
                if mode and str(mode).startswith('replace'):
                    # archive any existing active rows matching the business key
                    try:
                        cur.execute('UPDATE fact_production SET record_status=?, archived_at=? WHERE org_unit_id=? AND date_key=? AND metric_key=? AND (record_status IS NULL OR record_status="active")', ('archived', now_iso(), str(org), str(date)[:10], str(metric)))
                    except Exception:
                        pass
                cur.execute('INSERT OR REPLACE INTO fact_production(id, org_unit_id, date_key, metric_key, metric_value, source_system, import_job_id, created_at) VALUES (?,?,?,?,?,?,?,?)', (fid, str(org), str(date)[:10], str(metric), float(val), source_system, import_job_id, now_iso()))
                committed += 1
            elif dataset == 'marketing':
                fid = uuid.uuid4().hex
                org = row.get(mapping.get('org_unit_id')) if mapping.get('org_unit_id') else (row.get('org_unit_id') or row.get('org_unit'))
                date = row.get(mapping.get('date_key')) if mapping.get('date_key') else (row.get('date') or row.get('date_key'))
                if mode and str(mode).startswith('replace'):
                    try:
                        cur.execute('UPDATE fact_marketing SET record_status=?, archived_at=? WHERE org_unit_id=? AND date_key=? AND (record_status IS NULL OR record_status="active")', ('archived', now_iso(), str(org), str(date)[:10] if date else None))
                    except Exception:
                        pass
                cur.execute('INSERT OR REPLACE INTO fact_marketing(id, org_unit_id, date_key, campaign, channel, impressions, engagements, clicks, conversions, cost, source_system, import_job_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                    fid, str(org), str(date)[:10] if date else None, row.get(mapping.get('campaign') if mapping.get('campaign') else 'campaign') if mapping else row.get('campaign'), row.get(mapping.get('channel') if mapping.get('channel') else 'channel') if mapping else row.get('channel'), float(row.get(mapping.get('impressions') if mapping.get('impressions') else 'impressions') or 0), float(row.get(mapping.get('engagements') if mapping.get('engagements') else 'engagements') or 0), float(row.get(mapping.get('clicks') if mapping.get('clicks') else 'clicks') or 0), float(row.get(mapping.get('conversions') if mapping.get('conversions') else 'conversions') or 0), float(row.get(mapping.get('cost') if mapping.get('cost') else 'cost') or 0), source_system, import_job_id, now_iso()
                ))
                committed += 1
            elif dataset == 'event_performance' or dataset == 'event_metrics':
                # map into event_metrics table
                fid = uuid.uuid4().hex
                event_id = row.get(mapping.get('event_id')) if mapping.get('event_id') else row.get('event_id') or row.get('event')
                try:
                    impressions = int(row.get(mapping.get('impressions')) or row.get('impressions') or 0)
                except Exception:
                    impressions = 0
                try:
                    engagements = int(row.get(mapping.get('engagements')) or row.get('engagements') or 0)
                except Exception:
                    engagements = 0
                try:
                    captured_at = row.get(mapping.get('captured_at')) if mapping.get('captured_at') else row.get('captured_at') or row.get('date')
                except Exception:
                    captured_at = None
                cur.execute('INSERT OR REPLACE INTO event_metrics(id, event_id, impressions, engagements, leads, appts_made, appts_conducted, contracts, accessions, other_json, captured_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                    fid, event_id, impressions, engagements, int(row.get('leads') or 0), int(row.get('appts_made') or 0), int(row.get('appts_conducted') or 0), int(row.get('contracts') or 0), int(row.get('accessions') or 0), json.dumps(row), captured_at
                ))
                committed += 1
            else:
                # fallback: keep in imported_rows only
                continue
        # Update provenance status on the correct table
        if legacy_mode:
            try:
                cur.execute('UPDATE import_job SET status=?, row_count_detected=? WHERE id=?', ('committed', committed, legacy_id))
            except Exception:
                pass
        else:
            cur.execute('UPDATE import_job_v3 SET status=?, row_count=?, updated_at=? WHERE id=?', ('committed', committed, now_iso(), import_job_id))
        conn.commit()
        return {'status':'ok', 'import_job_id': import_job_id, 'committed_rows': committed}
    finally:
        conn.close()


@router.get('/api/import/jobs')
def list_import_jobs(limit: int = 100):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM import_job_v3 ORDER BY created_at DESC LIMIT ?', (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get('/api/import/jobs/{import_job_id}')
def get_import_job(import_job_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM import_job_v3 WHERE id=?', (import_job_id,))
        job = cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail='not found')
        cur.execute('SELECT * FROM import_file WHERE import_job_id=? ORDER BY uploaded_at DESC', (import_job_id,))
        files = [dict(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM import_column_map WHERE import_job_id=? ORDER BY created_at DESC', (import_job_id,))
        maps = [dict(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM import_error WHERE import_job_id=? ORDER BY created_at LIMIT 100', (import_job_id,))
        errs = [dict(r) for r in cur.fetchall()]
        return {'job': dict(job), 'files': files, 'mappings': maps, 'errors': errs}
    finally:
        conn.close()


@router.get('/api/import/templates/{dataset_key}')
def get_template(dataset_key: str):
    # very small in-code templates
    templates = {
        'production': {
            'csv_header': 'org_unit_id,date,metric_key,metric_value',
            'fields': ['org_unit_id','date','metric_key','metric_value']
        },
        'marketing': {
            'csv_header': 'org_unit_id,date,campaign,channel,impressions,engagements,clicks,conversions,cost',
            'fields': ['org_unit_id','date','campaign','channel','impressions','engagements','clicks','conversions','cost']
        },
        'org_units': {
            'csv_header': 'id,name,type,parent_id,rsid,uic,city,state,zip',
            'fields': ['id','name','type','parent_id','rsid','uic','city','state','zip']
        }
        ,
        'funnel': {
            'csv_header': 'org_unit_id,date,stage,count_value',
            'fields': ['org_unit_id','date','stage','count_value']
        }
    }
    return templates.get(dataset_key, {'csv_header':'','fields':[]})


@router.post('/api/import/{job_id}/parse')
def parse_job(job_id: int, sheet: Optional[str] = None, max_preview: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, filename_original, sha256_hash, file_type FROM import_job WHERE id=?', (job_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='import job not found')
        uploads_base = os.getenv('TAAIP_UPLOAD_DIR', 'services/api/.data/imports')
        job_dir = os.path.join(uploads_base, f'job_{job_id}')
        if not os.path.isdir(job_dir):
            raise HTTPException(status_code=500, detail='uploaded file missing')
        # expected stored as original.ext
        candidates = [os.path.join(job_dir, f) for f in os.listdir(job_dir) if f.startswith('original')]
        if not candidates:
            raise HTTPException(status_code=500, detail='uploaded file missing')
        path = candidates[0]
        ext = os.path.splitext(path)[1].lower()
        preview = []
        columns = []
        # CSV/TXT
        if ext in ('.csv', '.txt'):
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                reader = csv.DictReader(fh)
                for i, r in enumerate(reader):
                    if i >= max_preview: break
                    preview.append({k: (v if v is not None else '') for k, v in r.items()})
            columns = list(preview[0].keys()) if preview else []
        elif ext == '.json':
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    preview = data[:max_preview]
                    columns = sorted(list(set().union(*(d.keys() for d in preview))) ) if preview else []
                elif isinstance(data, dict):
                    # flatten nested dicts to dot notation
                    def flatten(d, parent=''):
                        items = {}
                        for k, v in d.items():
                            key = f"{parent}.{k}" if parent else k
                            if isinstance(v, dict):
                                items.update(flatten(v, key))
                            else:
                                items[key] = v
                        return items
                    flat = flatten(data)
                    preview = [flat]
                    columns = list(flat.keys())
                else:
                    preview = []
        elif ext in ('.xlsx', '.xls'):
            if openpyxl is None:
                cur.execute('UPDATE import_job SET status=?, notes=?, updated_at=? WHERE id=?', ('mapping_required', 'XLSX parsing requires openpyxl. Install it in the services/api venv.', now_iso(), job_id))
                conn.commit()
                raise HTTPException(status_code=202, detail='mapping_required')
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheet_name = sheet or wb.sheetnames[0]
            ws = wb[sheet_name]
            rows = ws.iter_rows(values_only=True)
            try:
                header = next(rows)
            except StopIteration:
                header = []
            for i, r in enumerate(rows):
                if i >= max_preview: break
                rowobj = {str(header[j]) if header and j < len(header) and header[j] is not None else f'col_{j}': (r[j] if j < len(r) else None) for j in range(len(r))}
                preview.append(rowobj)
            columns = list(preview[0].keys()) if preview else []
        elif ext in ('.sql',):
            # attempt to parse simple INSERT INTO ... VALUES (...) statements
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                sql = fh.read()
            inserts = re.findall(r"INSERT\s+INTO\s+[^()]+\(([^)]+)\)\s+VALUES\s*\(([^;]+?)\)", sql, flags=re.IGNORECASE)
            if not inserts:
                # try parsing VALUES (...) without column list
                vals = re.findall(r"VALUES\s*\(([^;]+?)\)", sql, flags=re.IGNORECASE)
                if not vals:
                    cur.execute('UPDATE import_job SET status=?, notes=?, updated_at=? WHERE id=?', ('mapping_required', 'SQL file not in simple INSERT/VALUES form. Provide mapping.', now_iso(), job_id))
                    conn.commit()
                    raise HTTPException(status_code=202, detail='mapping_required')
                # produce preview rows with generic col_1..N
                for i, v in enumerate(vals[:max_preview]):
                    parts = [p.strip().strip("'\"") for p in v.split(',')]
                    preview.append({f'col_{j+1}': parts[j] if j < len(parts) else None for j in range(len(parts))})
                columns = list(preview[0].keys()) if preview else []
            else:
                # take first insert structure
                cols = [c.strip().strip('"\'') for c in inserts[0][0].split(',')]
                vals = inserts[0][1]
                parts = [p.strip().strip("'\"") for p in vals.split(',')]
                preview.append({cols[j] if j < len(cols) else f'col_{j+1}': parts[j] if j < len(parts) else None for j in range(len(parts))})
                columns = cols
        else:
            cur.execute('UPDATE import_job SET status=?, notes=?, updated_at=? WHERE id=?', ('mapping_required', 'Parsing for this file type is not automated in local dev. Please provide mapping.', now_iso(), job_id))
            conn.commit()
            raise HTTPException(status_code=202, detail='mapping_required')

        # store preview
        cur.execute('INSERT INTO import_job_preview(import_job_id, preview_json, columns_json, created_at) VALUES (?,?,?,?)', (job_id, json.dumps(preview), json.dumps(columns), now_iso()))
        cur.execute('UPDATE import_job SET status=?, row_count_detected=?, updated_at=? WHERE id=?', ('preview_ready', len(preview), now_iso(), job_id))
        conn.commit()
        return {'import_job_id': job_id, 'preview_rows': len(preview), 'columns': columns}
    finally:
        conn.close()


@router.get('/api/import/{job_id}')
def get_import(job_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM import_job WHERE id=?', (job_id,))
        job = cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail='not found')
        cur.execute('SELECT preview_json, columns_json FROM import_job_preview WHERE import_job_id=? ORDER BY id DESC LIMIT 1', (job_id,))
        p = cur.fetchone()
        preview = json.loads(p['preview_json']) if p else []
        columns = json.loads(p['columns_json']) if p else []
        # fetch logs
        cur.execute('SELECT level, message, row_number, field_name, created_at FROM import_job_log WHERE import_job_id=? ORDER BY id', (job_id,))
        logs = [dict(r) for r in cur.fetchall()]
        return {'job': dict(job), 'preview': preview, 'columns': columns, 'logs': logs}
    finally:
        conn.close()


@router.post('/api/import/{job_id}/map')
def map_job(job_id: int, mapping: Dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        # store mapping template as a quick save
        cur.execute('INSERT INTO import_mapping_template(name, target_domain, mapping_json, created_by, created_at) VALUES (?,?,?,?,?)', (
            mapping.get('name', f'map_{job_id}'), mapping.get('target_domain','generic'), json.dumps(mapping), mapping.get('created_by'), now_iso()
        ))
        # also store mapping JSON on the import_job for commit
        cur.execute('UPDATE import_job SET status=?, target_domain=?, mapping_json=?, updated_at=? WHERE id=?', ('validating', mapping.get('target_domain','generic'), json.dumps(mapping), now_iso(), job_id))
        conn.commit()
        try:
            audit(conn, mapping.get('created_by') if isinstance(mapping, dict) else None, 'import.map', 'import_job', job_id, {'template': mapping.get('name') if isinstance(mapping, dict) else None, 'target_domain': mapping.get('target_domain') if isinstance(mapping, dict) else None})
        except Exception:
            pass
        return {'import_job_id': job_id, 'status': 'validating'}
    finally:
        conn.close()


@router.post('/api/import/{job_id}/validate')
def validate_job(job_id: int, options: Dict = {}, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT preview_json FROM import_job_preview WHERE import_job_id=? ORDER BY id DESC LIMIT 1', (job_id,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(status_code=400, detail='no preview to validate')
        preview = json.loads(p['preview_json'])
        errors = 0
        warnings = 0
        # simple validation: check for empty rows
        for i, r in enumerate(preview):
            if not any([v for v in r.values()]):
                errors += 1
                cur.execute('INSERT INTO import_job_log(import_job_id, level, message, row_number, created_at) VALUES (?,?,?,?,?)', (job_id, 'error', 'empty row', i+1, now_iso()))
        cur.execute('UPDATE import_job SET error_count=?, warnings_count=?, status=?, updated_at=? WHERE id=?', (errors, warnings, ('mapping_required' if errors>0 else 'importing'), now_iso(), job_id))
        conn.commit()
        try:
            audit(conn, None, 'import.validate', 'import_job', job_id, {'errors': errors, 'warnings': warnings})
        except Exception:
            pass
        return {'import_job_id': job_id, 'errors': errors, 'warnings': warnings}
    finally:
        conn.close()


@router.post('/api/import/{job_id}/commit')
def commit_job(job_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT preview_json, mapping_json, target_domain FROM import_job_preview pj JOIN import_job ij ON pj.import_job_id=ij.id WHERE pj.import_job_id=? ORDER BY pj.id DESC LIMIT 1', (job_id,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(status_code=400, detail='no preview to commit')
        preview = json.loads(p['preview_json'])
        mapping_json = p['mapping_json'] if 'mapping_json' in p.keys() else None
        target_domain = p['target_domain'] if 'target_domain' in p.keys() else None

        allowed = set(['funnel_event','cost_benchmark','roi_result','loe','project','task','meeting','agenda_item','minutes','action_item','decision','calendar_event'])

        row_count = 0
        if mapping_json:
            try:
                mapping = json.loads(mapping_json) if isinstance(mapping_json, str) else mapping_json
            except Exception:
                mapping = mapping_json
        else:
            mapping = None

        if mapping and mapping.get('target_table') in allowed:
            target = mapping.get('target_table')
            field_map = mapping.get('field_map', {})
            for r in preview:
                # enforce org scope where possible
                org_val = None
                # check mapped org_unit_id
                if 'org_unit_id' in field_map:
                    org_val = r.get(field_map.get('org_unit_id'))
                # check direct value in row
                if org_val is None:
                    org_val = r.get('org_unit_id') or r.get('org_unit')
                if allowed_orgs is not None and org_val is not None:
                    try:
                        if int(org_val) not in allowed_orgs:
                            raise HTTPException(status_code=403, detail='forbidden')
                    except Exception:
                        # if not an int, compare as string
                        if str(org_val) not in [str(x) for x in allowed_orgs]:
                            raise HTTPException(status_code=403, detail='forbidden')
                # build insert for target
                cols = []
                vals = []
                for tfield, sfield in field_map.items():
                    cols.append(tfield)
                    vals.append(r.get(sfield))
                # add provenance fields if present in table
                cols.extend(['created_at','updated_at','import_job_id'])
                vals.extend([now_iso(), now_iso(), job_id])
                placeholders = ','.join(['?'] * len(vals))
                sql = f"INSERT INTO {target}({','.join(cols)}) VALUES ({placeholders})"
                cur.execute(sql, tuple(vals))
                row_count += 1
            cur.execute('UPDATE import_job SET row_count_imported=?, status=?, updated_at=? WHERE id=?', (row_count, 'completed', now_iso(), job_id))
            conn.commit()
            try:
                audit(conn, None, 'import.commit', 'import_job', job_id, {'imported': row_count, 'target_table': target})
            except Exception:
                pass
            return {'import_job_id': job_id, 'imported': row_count, 'target_table': target}

        # fallback: store into imported_rows for provenance
        for r in preview:
            cur.execute('INSERT INTO imported_rows(import_job_id, target_domain, row_json, created_at) VALUES (?,?,?,?)', (job_id, target_domain or 'generic', json.dumps(r), now_iso()))
            row_count += 1
        cur.execute('UPDATE import_job SET row_count_imported=?, status=?, updated_at=? WHERE id=?', (row_count, 'completed', now_iso(), job_id))
        conn.commit()
        try:
            audit(conn, None, 'import.commit', 'import_job', job_id, {'imported': row_count, 'fallback': True})
        except Exception:
            pass
        return {'import_job_id': job_id, 'imported': row_count}
    finally:
        conn.close()
