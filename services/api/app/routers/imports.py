from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import Dict, List, Optional
from .. import db
from .rbac import require_scope
import os, hashlib, json, csv, io, datetime, re

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
        conn.commit()
        return {'import_job_id': jid}
    finally:
        conn.close()


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
