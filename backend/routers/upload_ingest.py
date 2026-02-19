from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import os
import uuid
import sqlite3
import hashlib
import shutil
import csv
from typing import Optional, List
from datetime import datetime

from backend.ingestion.classifier import inspect_file
from backend.ingestion.dataset_registry import classify, detect_dataset

router = APIRouter()
# Resolve DB path: prefer `DB_PATH` then `DB_FILE`, then repo-relative recruiting.db
DB = os.getenv('DB_PATH') or os.getenv('DB_FILE') or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'recruiting.db')
UPLOAD_DIR = '/uploads' if os.path.isdir('/uploads') else '/tmp/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


@router.post('/api/v2/upload/raw')
async def upload_raw(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    source_system: str = Query('USAREC'),
):
    # accept either single `file` or multiple `files[]` form fields
    chosen: UploadFile | None = None
    if files:
        chosen = files[0]
    elif file:
        chosen = file
    if not chosen:
        raise HTTPException(status_code=400, detail='no file provided')

    # read bytes from UploadFile asynchronously
    try:
        data = await chosen.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'read failed: {e}')

    if not data:
        raise HTTPException(status_code=400, detail='empty upload')

    # create safe filename
    ext = os.path.splitext(chosen.filename or '')[1] or ''
    safe_name = f"{uuid.uuid4().hex}_{source_system}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    try:
        with open(dest, 'wb') as out:
            out.write(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'write failed: {e}')
    # inspect (handles CSV and XLSX)
    info = inspect_file(dest)
    cols = info.get('columns') or []
    header_row = info.get('header_row')
    # prefer deterministic detection (expects cols normalized by inspector)
    try:
        detected = detect_dataset({c.upper() for c in cols}, source_system)
    except Exception:
        detected = None
    dataset_key = detected or classify(cols, source_system) or 'unknown'
    # row_count
    try:
        with open(dest, newline='') as fh:
            reader = csv.reader(fh)
            total = sum(1 for _ in reader)
    except Exception:
        total = None

    fhash = file_hash(dest)
    batch_id = uuid.uuid4().hex
    # store batch record (match existing DB schema)
    imported_at = datetime.utcnow().isoformat()
    # ensure DB directory exists so sqlite can create the file if needed
    db_dir = os.path.dirname(DB)
    if db_dir and not os.path.isdir(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception:
            pass
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute('''INSERT OR REPLACE INTO raw_import_batches(batch_id, source_system, filename, stored_path, file_hash, imported_at, detected_profile, status, notes)
                   VALUES(?,?,?,?,?,?,?,?,?)''', (batch_id, source_system, safe_name, dest, fhash, imported_at, dataset_key, 'received', None))
    con.commit()
    con.close()

    # If we deterministically recognized SAMA, attempt immediate load into DB
    low_key = (dataset_key or '').lower()
    if dataset_key == 'USAREC_SAMA' or low_key == 'usarec_sama' or 'sama' in low_key:
        try:
            from backend.ingestion.loaders.sama_loader import load_sama
            con2 = sqlite3.connect(DB)
            load_sama(con2, dest, batch_id)
            con2.close()
            # mark processed
            con3 = sqlite3.connect(DB)
            cur3 = con3.cursor()
            cur3.execute('UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?', ('processed', 'SAMA loaded', batch_id))
            con3.commit()
            con3.close()
        except Exception as e:
            con4 = sqlite3.connect(DB)
            cur4 = con4.cursor()
            cur4.execute('UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?', ('failed', str(e), batch_id))
            con4.commit()
            con4.close()
    # If we detected any contracts/volume dataset, attempt immediate load
    elif 'contract' in low_key or 'contracts' in low_key:
        try:
            from backend.ingestion.loaders.market_share_loader import load_market_share
            con2 = sqlite3.connect(DB)
            load_market_share(con2, dest, batch_id)
            con2.close()
            con3 = sqlite3.connect(DB)
            cur3 = con3.cursor()
            cur3.execute('UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?', ('processed', 'market-share loaded', batch_id))
            con3.commit()
            con3.close()
        except Exception as e:
            con4 = sqlite3.connect(DB)
            cur4 = con4.cursor()
            cur4.execute('UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?', ('failed', str(e), batch_id))
            con4.commit()
            con4.close()

    return {
        'batch_id': batch_id,
        'dataset_key': dataset_key,
        'columns': cols,
        'header_row': header_row,
        'row_count': total,
        'filename': safe_name
    }


@router.post('/api/v2/upload/_test_multipart')
async def _test_multipart(file: UploadFile = File(...)):
    """Smoke-test endpoint to verify multipart handling without running ingestion flow."""
    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'read failed: {e}')
    return {'filename': file.filename, 'bytes': len(data)}
