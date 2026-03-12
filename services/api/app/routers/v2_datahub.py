from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional
import os, uuid, datetime, sqlite3, json

from ..db import connect
from .. import migrations
from ..importers import detect as detect_mod
from ..importers import parse as parse_mod
from ..importers import validate as validate_mod
from ..importers import usarec_g2_enlistments_by_bn
from ..importers import emm_portal
from ..importers import usarec_org_hierarchy
from ..aggregations import refresh as refresh_mod
from .rbac import require_perm

router = APIRouter()


def _normalize_col(c):
    if not c or not isinstance(c, str):
        return ''
    import re
    s = c.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip('_')
    return s


def _apply_header_aliases(df, headers, dataset_key):
    """Attempt to map common alternate header names to expected required column names.
    This mutates the DataFrame columns if aliases are found and returns updated headers list.
    """
    # simple alias map for EMM portal events and common variants
    alias_map = {
        'event_name': ['title', 'event_title', 'activity_title', 'activity name', 'activity title', 'event name'],
        'start_date': ['begin_date', 'begin date', 'start_date', 'start date', 'start'],
        'end_date': ['end_date', 'end date', 'end']
    }
    # only apply for EMM datasets (hinted or detected)
    if not dataset_key or not str(dataset_key).upper().startswith('EMM'):
        return headers

    # build normalized header map
    norm_to_actual = {}
    for h in headers:
        norm = _normalize_col(h)
        norm_to_actual[norm] = h

    # attempt to rename aliases to expected names
    renamed = {}
    for expected, variants in alias_map.items():
        for v in variants:
            norm_v = _normalize_col(v)
            if norm_v in norm_to_actual:
                actual = norm_to_actual[norm_v]
                if actual != expected:
                    try:
                        df.rename(columns={actual: expected}, inplace=True)
                        renamed[expected] = actual
                        # update headers mapping
                        try:
                            headers = [expected if x == actual else x for x in headers]
                        except Exception:
                            pass
                    except Exception:
                        pass
                break

    return headers


def _storage_path_for(filename: str):
    now = datetime.datetime.utcnow()
    base = os.path.join('data','uploads', str(now.year), f"{now.month:02d}")
    os.makedirs(base, exist_ok=True)
    uid = uuid.uuid4().hex[:8]
    stored = os.path.join(base, f"{uid}_{os.path.basename(filename)}")
    return stored


def _detect_usarec_org(headers, filename):
    """Return True if headers/filename match the USAREC org hierarchy spec.

    Detection rules (per requirements):
      - Exact header match: CMD, BDE, BN, CO, STN (case-insensitive)
      - Filename contains both 'rsid' and 'usarec' (case-insensitive)
      - OR filename equals 'RSID USAREC.xlsx' (case-insensitive)
    """
    try:
        hdrs = [h.strip().upper() for h in (headers or []) if isinstance(h, str)]
        if hdrs == ['CMD', 'BDE', 'BN', 'CO', 'STN']:
            return True
        fname = (filename or '').lower()
        if fname == 'rsid usarec.xlsx' or ('rsid' in fname and 'usarec' in fname):
            return True
    except Exception:
        pass
    return False


@router.get('/v2/datahub/registry')
def get_registry(user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM dataset_registry WHERE enabled=1')
    rows = [dict(r) for r in cur.fetchall()]
    return rows


@router.get('/v2/datahub/runs')
def list_runs(limit: int = 50, status: Optional[str] = None, user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    if status:
        cur.execute('SELECT * FROM import_run_v2 WHERE status=? ORDER BY created_at DESC LIMIT ?', (status, limit))
    else:
        cur.execute('SELECT * FROM import_run_v2 ORDER BY created_at DESC LIMIT ?', (limit,))
    return [dict(r) for r in cur.fetchall()]


@router.get('/v2/datahub/runs/{run_id}')
def get_run(run_id: str, user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM import_run_v2 WHERE run_id=?', (run_id,))
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail='run not found')
    run = dict(r)
    cur.execute('SELECT row_num, column_name, error_code, message FROM import_run_error_v2 WHERE run_id=?', (run_id,))
    run['errors'] = [dict(x) for x in cur.fetchall()]
    return run


@router.post('/v2/datahub/runs/{run_id}/commit', dependencies=[Depends(require_perm('datahub.upload'))])
def commit_run(run_id: str):
    """Commit a previously uploaded run (created by dry_run) and perform full ingest.

    This reads the stored file path from import_run_v2 and runs the same loaders
    as the upload handler.
    """
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute('SELECT run_id, filename, storage_path, dataset_key, scope_unit_rsid FROM import_run_v2 WHERE run_id=?', (run_id,))
        r = cur.fetchone()
        if not r:
            return JSONResponse(status_code=404, content={'run_id': run_id, 'status': 'not_found', 'error': 'run not found'})
        row = dict(r)
        stored = row.get('storage_path')
        filename = row.get('filename')
        scope_unit_rsid = row.get('scope_unit_rsid')

        # parse file
        try:
            sheet_names, headers, df = parse_mod.parse_file(stored, filename)
        except Exception as e:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', f'parse_error:{str(e)}', run_id))
            conn.commit()
            return JSONResponse(status_code=400, content={'run_id': run_id, 'status': 'failed', 'error': str(e)})

        # determine dataset_key (prefer stored dataset_key)
        dataset_key = row.get('dataset_key')
        if not dataset_key:
            cur.execute('SELECT dataset_key, display_name, detection_keywords, required_columns, optional_columns, file_types, source_system FROM dataset_registry WHERE enabled=1')
            reg = [dict(x) for x in cur.fetchall()]
            dataset_key, confidence, matched_on = detect_mod.detect_dataset(filename, sheet_names, headers, reg)
            # fallback: direct detection for USAREC org hierarchy
            try:
                if (not dataset_key) and _detect_usarec_org(headers, filename):
                    dataset_key = 'USAREC_ORG_HIERARCHY'
                    confidence = 1.0
                    matched_on = 'headers:usarec_org'
            except Exception:
                pass

        # apply header alias mapping after we know dataset_key (helps loaders expect canonical names)
        try:
            headers = list(headers)
            headers = _apply_header_aliases(df, headers, dataset_key)
        except Exception:
            pass

        # find registry entry
        entry = None
        try:
            cur.execute('SELECT * FROM dataset_registry WHERE dataset_key=?', (dataset_key,))
            fetched = cur.fetchone()
            if fetched:
                entry = dict(fetched)
        except Exception:
            entry = None

        ctx = {'dataset_key': dataset_key, 'source_system': (entry.get('source_system') if entry else None), 'unit_rsid': scope_unit_rsid}
        rows_in = len(df.index) if hasattr(df, 'index') else 0
        rows_loaded = 0
        try:
            if dataset_key and dataset_key.startswith('USAREC_G2_ENLISTMENTS'):
                rows_loaded = usarec_g2_enlistments_by_bn.process_and_load(df, ctx, conn, run_id)
            elif dataset_key and (dataset_key.startswith('EMM_PORTAL') or dataset_key == 'EMM_PORTAL_EVENTS'):
                rows_loaded = emm_portal.process_and_load(df, ctx, conn, run_id)
            elif dataset_key == 'USAREC_ORG_HIERARCHY':
                rows_loaded = usarec_org_hierarchy.process_and_load(df, ctx, conn, run_id)
            else:
                rows_loaded = 0
        except Exception as e:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', f'load_error:{str(e)}', run_id))
            conn.commit()
            return JSONResponse(status_code=500, content={'run_id': run_id, 'status': 'failed', 'error': str(e)})

        # finalize
        cur.execute('UPDATE import_run_v2 SET status=?, rows_in=?, rows_loaded=?, ended_at=? WHERE run_id=?', ('success', rows_in, rows_loaded, datetime.datetime.utcnow().isoformat(), run_id))
        conn.commit()
        try:
            refresh_mod.refresh_agg_kpis(conn, unit_rsid=scope_unit_rsid)
        except Exception:
            pass
        return JSONResponse(status_code=200, content={'run_id': run_id, 'status': 'success', 'dataset_key': dataset_key, 'rows_in': rows_in, 'rows_loaded': rows_loaded})
    except Exception as exc:
        try:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', f'exception:{str(exc)}', run_id))
            conn.commit()
        except Exception:
            pass
        return JSONResponse(status_code=500, content={'run_id': run_id, 'status': 'failed', 'error': str(exc)})


@router.post('/v2/datahub/upload', dependencies=[Depends(require_perm('datahub.upload'))])
async def upload_datahub(
    file: UploadFile = File(...),
    dataset_key: Optional[str] = Form(None),
    hint_dataset_key: Optional[str] = Form(None),
    scope_unit_rsid: Optional[str] = Form(None),
    scope_fy: Optional[int] = Form(None),
    scope_qtr: Optional[int] = Form(None),
    scope_rsm_month: Optional[str] = Form(None),
    dry_run: Optional[int] = 1,
):
    try:
        # save file
        stored = _storage_path_for(file.filename)
        contents = await file.read()
        with open(stored, 'wb') as fh:
            fh.write(contents)

        conn = connect()
        cur = conn.cursor()
        run_id = f"run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        created_at = datetime.datetime.utcnow().isoformat()
        # create run (queued)
        cur.execute('INSERT INTO import_run_v2 (run_id, filename, status, storage_path, created_at, scope_unit_rsid, scope_fy, scope_qtr, scope_rsm_month, uploaded_by) VALUES (?,?,?,?,?,?,?,?,?,?)', (run_id, file.filename, 'queued', stored, created_at, scope_unit_rsid, scope_fy, scope_qtr, scope_rsm_month, 'local-dev'))
        conn.commit()

        # detect
        cur.execute('SELECT dataset_key, display_name, detection_keywords, required_columns, optional_columns, file_types, source_system FROM dataset_registry WHERE enabled=1')
        reg = [dict(r) for r in cur.fetchall()]
        try:
            sheet_names, headers, df = parse_mod.parse_file(stored, file.filename)
        except Exception as e:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', f'parse_error: {str(e)}', run_id))
            conn.commit()
            return JSONResponse(status_code=400, content={'run_id': run_id, 'status': 'failed', 'error': str(e)})

            # apply header alias mapping (may rename df columns for loaders)
            try:
                headers = list(headers)
                headers = _apply_header_aliases(df, headers, hint_dataset_key)
            except Exception:
                pass

        # compute a small preview to return to the client
        preview_rows = []
        try:
            preview_rows = df.head(5).fillna('').to_dict(orient='records')
        except Exception:
            preview_rows = []

        # Prefer an explicit dataset_key (from form) over hint or auto-detection.
        # Preserve the originally provided form value so we can permissively accept it later if not in registry.
        provided_dataset_key = (dataset_key or '').strip() if dataset_key else None
        provided_hint = provided_dataset_key or hint_dataset_key
        if provided_hint:
            dataset_key = provided_hint
            confidence = 1.0
            matched_on = 'hint:upload'
        else:
            dataset_key, confidence, matched_on = detect_mod.detect_dataset(file.filename, sheet_names, headers, reg, hint=hint_dataset_key)
            # fallback detection for USAREC org hierarchy when registry entry absent
            try:
                if (not dataset_key) and _detect_usarec_org(headers, file.filename):
                    dataset_key = 'USAREC_ORG_HIERARCHY'
                    confidence = 1.0
                    matched_on = 'headers:usarec_org'
            except Exception:
                pass
        # update with detection
        cur.execute('UPDATE import_run_v2 SET dataset_key=?, detected_confidence=?, status=?, started_at=? WHERE run_id=?', (dataset_key, confidence, 'running', datetime.datetime.utcnow().isoformat(), run_id))
        conn.commit()

        # find registry entry
        entry = None
        for r in reg:
            if r.get('dataset_key') == dataset_key:
                entry = r
                break

        # If entry not found in DB but caller provided an explicit dataset_key/hint, accept it as a permissive entry.
        if not entry and provided_hint:
            entry = {'dataset_key': provided_hint, 'display_name': provided_hint, 'source_system': None, 'required_columns': '[]', 'optional_columns': '[]'}

        if not entry:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', 'could not detect dataset', run_id))
            conn.commit()
            return JSONResponse(status_code=400, content={'run_id': run_id, 'status': 'failed', 'error': 'could not detect dataset'})

        # validate headers
            # validate headers (after aliasing)
        try:
            required = json.loads(entry.get('required_columns') or '[]')
            optional = json.loads(entry.get('optional_columns') or '[]')
        except Exception:
            required = []
            optional = []

        errors = validate_mod.validate_headers(headers, required, optional)
        if errors:
            for e in errors:
                cur.execute('INSERT INTO import_run_error_v2 (run_id, row_num, column_name, error_code, message) VALUES (?,?,?,?,?)', (run_id, e['row_num'], e.get('column_name'), e.get('error_code'), e.get('message')))
            conn.commit()
            # If user provided a hint_dataset_key (frontend explicit preview), tolerate header variances and return validated with warnings
            if hint_dataset_key:
                try:
                    cur.execute('UPDATE import_run_v2 SET status=?, rows_in=?, ended_at=?, error_summary=? WHERE run_id=?', ('validated', len(df.index) if hasattr(df, 'index') else 0, datetime.datetime.utcnow().isoformat(), 'missing required columns (tolerated for preview)', run_id))
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                return JSONResponse(status_code=200, content={'run_id': run_id, 'status': 'validated', 'warnings': errors, 'dataset_key': dataset_key, 'rows_in': len(df.index) if hasattr(df, 'index') else 0, 'preview_rows': preview_rows})
            # otherwise fail hard -- but tolerate known USAREC CSV variants by mapping common columns
            try:
                hdrs_lower = [h.lower().strip() for h in (headers or [])]
                if dataset_key == 'USAREC_ORG_HIERARCHY' and ('rsid' in hdrs_lower or 'parent_rsid' in hdrs_lower or 'display_name' in hdrs_lower):
                    try:
                        for c in list(df.columns):
                            if str(c).lower().strip() == 'rsid':
                                df['STN'] = df[c].astype(str)
                            if str(c).lower().strip() == 'display_name':
                                df['display_name'] = df[c].astype(str)
                            if str(c).lower().strip() == 'parent_rsid':
                                df['parent_rsid'] = df[c].astype(str)
                    except Exception:
                        pass
                    errors = []
                else:
                    cur.execute('UPDATE import_run_v2 SET status=?, error_summary=?, rows_in=? WHERE run_id=?', ('failed', 'missing required columns', len(df.index) if hasattr(df, 'index') else 0, run_id))
                    conn.commit()
                    return JSONResponse(status_code=400, content={'run_id': run_id, 'status': 'failed', 'errors': errors})
            except Exception:
                cur.execute('UPDATE import_run_v2 SET status=?, error_summary=?, rows_in=? WHERE run_id=?', ('failed', 'missing required columns', len(df.index) if hasattr(df, 'index') else 0, run_id))
                conn.commit()
                return JSONResponse(status_code=400, content={'run_id': run_id, 'status': 'failed', 'errors': errors})

            # If required columns are satisfied only after aliasing, that will be reflected in headers/df
            headers = [h for h in headers]
        # If dry_run requested, don't load — mark validated and return preview
        try:
            rows_in = len(df.index) if hasattr(df, 'index') else 0
        except Exception:
            rows_in = 0

        if dry_run and int(dry_run) != 0:
            try:
                cur.execute('UPDATE import_run_v2 SET status=?, rows_in=?, ended_at=? WHERE run_id=?', ('validated', rows_in, datetime.datetime.utcnow().isoformat(), run_id))
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return JSONResponse(status_code=200, content={'run_id': run_id, 'status': 'validated', 'dataset_key': dataset_key, 'detected_confidence': confidence, 'rows_in': rows_in, 'rows_loaded': 0, 'preview_rows': preview_rows})

        # load into canonical table using loader map
        ctx = {'dataset_key': dataset_key, 'source_system': entry.get('source_system'), 'unit_rsid': scope_unit_rsid, 'scope_fy': scope_fy, 'scope_qtr': scope_qtr, 'scope_rsm_month': scope_rsm_month}
        rows_loaded = 0
        try:
            # Route to dataset-specific processors
            if dataset_key and dataset_key.startswith('USAREC_G2_ENLISTMENTS'):
                rows_loaded = usarec_g2_enlistments_by_bn.process_and_load(df, ctx, conn, run_id)
            elif dataset_key and (dataset_key.startswith('EMM_PORTAL') or dataset_key == 'EMM_PORTAL_EVENTS'):
                rows_loaded = emm_portal.process_and_load(df, ctx, conn, run_id)
            elif dataset_key == 'USAREC_ORG_HIERARCHY':
                rows_loaded = usarec_org_hierarchy.process_and_load(df, ctx, conn, run_id)
            else:
                rows_loaded = 0
        except Exception as e:
            cur.execute('UPDATE import_run_v2 SET status=?, error_summary=? WHERE run_id=?', ('failed', f'load_error:{str(e)}', run_id))
            conn.commit()
            return JSONResponse(status_code=500, content={'run_id': run_id, 'status': 'failed', 'error': str(e)})

        # finalize
        cur.execute('UPDATE import_run_v2 SET status=?, rows_in=?, rows_loaded=?, ended_at=? WHERE run_id=?', ('success', rows_in, rows_loaded, datetime.datetime.utcnow().isoformat(), run_id))
        conn.commit()

        # refresh aggs for unit if present
        try:
            refresh_mod.refresh_agg_kpis(conn, unit_rsid=scope_unit_rsid)
        except Exception:
            pass

        return JSONResponse(status_code=200, content={'run_id': run_id, 'status': 'success', 'dataset_key': dataset_key, 'detected_confidence': confidence, 'rows_in': rows_in, 'rows_loaded': rows_loaded, 'preview_rows': preview_rows})
    except Exception as exc:
        return JSONResponse(status_code=500, content={'status': 'error', 'error': str(exc)})


@router.get('/v2/datahub/runs/{run_id}/errors.csv')
def download_run_errors(run_id: str, user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT row_num, column_name, error_code, message FROM import_run_error_v2 WHERE run_id=? ORDER BY id ASC', (run_id,))
    rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail='no errors')
    # build CSV
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['row_num', 'column_name', 'error_code', 'message'])
    for r in rows:
        w.writerow([r['row_num'], r['column_name'], r['error_code'], r['message']])
    return Response(content=buf.getvalue(), media_type='text/csv')


@router.get('/v2/datahub/storage')
def storage_summary(user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    cur.execute('''
        SELECT dataset_key, COUNT(*) AS total_runs, SUM(rows_loaded) AS total_rows_loaded, MIN(created_at) AS first_seen, MAX(created_at) AS last_seen, MAX(CASE WHEN status='success' THEN ended_at ELSE NULL END) AS last_success_at
        FROM import_run_v2
        GROUP BY dataset_key
    ''')
    return [dict(r) for r in cur.fetchall()]


@router.get('/v2/datahub/health')
def datahub_health(user: dict = Depends(require_perm('datahub.view'))):
    conn = connect()
    cur = conn.cursor()
    # last 5 runs
    cur.execute('SELECT run_id, dataset_key, status, rows_in, rows_loaded, created_at FROM import_run_v2 ORDER BY created_at DESC LIMIT 5')
    last5 = [dict(r) for r in cur.fetchall()]
    # success rate last 7 days
    cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS success FROM import_run_v2 WHERE created_at >= datetime('now','-7 days')")
    counts = cur.fetchone()
    success_rate = 0.0
    if counts and counts['total']:
        success_rate = float(counts['success']) / float(counts['total'])
    # rows loaded last 7 days by dataset
    cur.execute("SELECT dataset_key, SUM(rows_loaded) AS rows_loaded FROM import_run_v2 WHERE created_at >= datetime('now','-7 days') GROUP BY dataset_key")
    rows7 = [dict(r) for r in cur.fetchall()]
    return {'last5': last5, 'success_rate_7d': success_rate, 'rows_loaded_7d': rows7}


@router.post('/v2/datahub/preview')
async def preview_datahub(file: UploadFile = File(...), hint_dataset_key: Optional[str] = Form(None)):
    """Parse an uploaded file and return sheet names, detected headers and first 5 rows for preview without persisting."""
    stored = _storage_path_for(file.filename)
    contents = await file.read()
    with open(stored, 'wb') as fh:
        fh.write(contents)
    try:
        sheet_names, headers, df = parse_mod.parse_file(stored, file.filename)
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
    preview_rows = []
    try:
        preview_rows = df.head(5).fillna('').to_dict(orient='records')
    except Exception:
        preview_rows = []
    # lightweight detect using registry (if available)
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT dataset_key, display_name, detection_keywords FROM dataset_registry WHERE enabled=1')
    reg = [dict(r) for r in cur.fetchall()]
    dataset_key, confidence, matched_on = detect_mod.detect_dataset(file.filename, sheet_names, headers, reg, hint=hint_dataset_key)
    return {'filename': file.filename, 'sheets': sheet_names, 'headers': headers, 'preview': preview_rows, 'detected_dataset_key': dataset_key, 'confidence': confidence}
