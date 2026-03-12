import os, json, hashlib, datetime
from typing import List, Dict, Optional
from .column_normalizer import normalize_col_name
from .header_finder import candidate_headers
from .excel_reader import preview_xlsx, preview_csv
from .org_mapper import map_row_to_unit
from . import datasets
from .. import db

def list_importers() -> List[Dict]:
    # dynamically collect importer definitions from datasets module
    out = []
    for name in dir(datasets):
        if name.startswith('g2_') or name.startswith('alrl') or name.startswith('emm'):
            mod = getattr(datasets, name)
            try:
                out.append(mod.IMPORTER)
            except Exception:
                pass
    return out

def detect_importer(path: str, filename: str = None) -> Dict:
    # return detection result with candidates
    filename = filename or os.path.basename(path)
    ext = os.path.splitext(filename)[1].lower()
    previews = {}
    if ext in ('.xlsx', '.xls'):
        previews = preview_xlsx(path)
    elif ext in ('.csv', '.txt'):
        previews = preview_csv(path)
    else:
        raise Exception('unsupported file type')

    candidates = []
    for key in dir(datasets):
        if not key.startswith('_'):
            mod = getattr(datasets, key)
            if hasattr(mod, 'IMPORTER'):
                imp = mod.IMPORTER
                detector = imp.get('detector', {})
                required = detector.get('required_columns', [])
                req_norm = [normalize_col_name(r) for r in required]
                # score against each preview sheet
                best_score = 0.0
                best_sheet = None
                best_header = None
                for sheet_name, rows in previews.items():
                    hdr = candidate_headers(rows, req_norm)
                    if not hdr: continue
                    # compute required match pct
                    if len(req_norm) == 0:
                        pct = 1.0
                    else:
                        pct = hdr['matches'] / float(len(req_norm))
                    score = pct
                    # signature phrases bonus
                    if detector.get('signature_phrases'):
                        text = ' '.join([str(c or '').lower() for c in rows[0][:10]])
                        for p in detector.get('signature_phrases'):
                            if p.lower() in text:
                                score += 0.1
                    if score > best_score:
                        best_score = score
                        best_sheet = sheet_name
                        best_header = hdr
                candidates.append({'dataset_id': imp['id'], 'confidence': best_score, 'header_row_index': best_header['index'] if best_header else None, 'sheet_name': best_sheet, 'required_match_pct': best_score})
    candidates = sorted(candidates, key=lambda x: x['confidence'], reverse=True)
    top = candidates[0] if candidates else None
    return {'dataset_id': top['dataset_id'] if top else None, 'confidence': top['confidence'] if top else 0.0, 'header_row_index': top['header_row_index'] if top else None, 'sheet_name': top['sheet_name'] if top else None, 'candidates': candidates}

def ensure_staging_tables():
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS staging_upload(id TEXT PRIMARY KEY, filename TEXT, content_type TEXT, size_bytes INTEGER, sha256 TEXT, source_system TEXT, detected_dataset_id TEXT, detected_confidence REAL, status TEXT, error_code TEXT, error_message TEXT, created_at TEXT, imported_at TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS staging_reject(id TEXT PRIMARY KEY, upload_id TEXT, dataset_id TEXT, row_number INTEGER, reason_code TEXT, reason_message TEXT, raw_row_json TEXT)''')
        conn.commit()
    finally:
        conn.close()

def run_import(upload_id: str, path: str, filename: str = None, forced_dataset_id: Optional[str] = None, source_system: Optional[str] = None) -> Dict:
    ensure_staging_tables()
    filename = filename or os.path.basename(path)
    detection = detect_importer(path, filename)
    dataset_id = forced_dataset_id or detection.get('dataset_id')
    confidence = detection.get('confidence', 0.0)
    # record detection
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE staging_upload SET detected_dataset_id=?, detected_confidence=?, status=? WHERE id=?', (dataset_id, confidence, 'DETECTED' if dataset_id else 'FAILED', upload_id))
        conn.commit()
    finally:
        conn.close()

    if not dataset_id:
        return {'ok': False, 'error': {'code':'DATASET_NOT_RECOGNIZED', 'message':'Could not match file to a known importer.', 'details': {'candidates': detection.get('candidates', [])}}}

    # dispatch to dataset loader
    loader_mod = getattr(datasets, dataset_id, None)
    if not loader_mod or not hasattr(loader_mod, 'load'):
        # try to import module by expected name
        try:
            mod = __import__(f'services.api.importers.datasets.{dataset_id}', fromlist=['*'])
            loader_mod = mod
        except Exception:
            return {'ok': False, 'error': {'code':'LOADER_NOT_FOUND', 'message':'Loader not implemented for dataset', 'details': {'dataset_id': dataset_id}}}

    # call loader.load(parsed: dict, upload_id, db_conn)
    try:
        result = loader_mod.load(path=path, filename=filename, upload_id=upload_id, source_system=source_system)
        # update staging upload
        conn = db.connect()
        try:
            cur = conn.cursor()
            cur.execute('UPDATE staging_upload SET status=?, imported_at=? WHERE id=?', ('IMPORTED' if result.get('status')=='IMPORTED' else 'FAILED', datetime.datetime.utcnow().isoformat(), upload_id))
            conn.commit()
        finally:
            conn.close()
        return {'ok': True, 'data': {'upload_id': upload_id, 'filename': filename, 'detected': {'dataset_id': dataset_id, 'confidence': confidence}, 'import': result}}
    except Exception as e:
        conn = db.connect()
        try:
            cur = conn.cursor()
            cur.execute('UPDATE staging_upload SET status=?, error_message=? WHERE id=?', ('FAILED', str(e), upload_id))
            conn.commit()
        finally:
            conn.close()
        return {'ok': False, 'error': {'code':'IMPORT_FAILED', 'message': str(e)}}
