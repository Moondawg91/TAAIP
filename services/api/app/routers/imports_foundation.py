from fastapi import APIRouter, UploadFile, File, Form
from ..db import connect
from typing import Optional
import csv
import io
import datetime
import sqlite3
import json

router = APIRouter()


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + 'Z'


REQUIRED_COLUMNS = {
    'mi_zip_fact': ['zip5', 'market_category', 'army_potential', 'dod_potential', 'potential_remaining'],
    'mi_cbsa_fact': ['cbsa_code', 'market_category', 'potential_remaining'],
    'mi_mission_category_ref': ['mission_category', 'education_tier'],
    'mi_enlistments_bde': ['bde', 'enlistments'],
    'mi_enlistments_bn': ['rsid_prefix', 'enlistments'],
    'school_program_fact': ['bde','bn','co','rsid_prefix','population','available']
}


@router.post('/imports/foundation/preview')
async def preview_foundation_import(dataset_key: str = Form(...), file: UploadFile = File(...)):
    """Return CSV header detection, required columns, missing, row_count and sample rows."""
    content = await file.read()
    try:
        s = content.decode('utf-8', errors='replace')
    except Exception:
        s = content.decode('latin-1', errors='replace')
    reader = csv.DictReader(io.StringIO(s))
    detected = reader.fieldnames or []
    sample = []
    row_count = 0
    for i, row in enumerate(reader):
        row_count += 1
        if i < 5:
            sample.append(row)
    required = REQUIRED_COLUMNS.get(dataset_key, [])
    missing = [c for c in required if c not in [d.strip() for d in detected]]
    return {
        'dataset_key': dataset_key,
        'required_columns': required,
        'detected_columns': detected,
        'missing_required': missing,
        'row_count': row_count,
        'sample': sample
    }


@router.post('/imports/foundation/commit')
async def commit_foundation_import(dataset_key: str = Form(...), file: UploadFile = File(...), mode: str = Form('replace'), mapping: Optional[str] = Form(None)):
    """Commit CSV into the canonical table. mode=replace|append"""
    content = await file.read()
    try:
        s = content.decode('utf-8', errors='replace')
    except Exception:
        s = content.decode('latin-1', errors='replace')
    reader = csv.DictReader(io.StringIO(s))
    # optional mapping JSON (client may supply mapping of target_field -> source_column)
    # try to pull mapping from dataset_key form if present in the payload (FastAPI passes form fields)
    # Note: when called directly here mapping may not be provided; we'll accept as an env/extra field
    # mapping handled below via Form param (see function signature)
    conn = connect()
    cur = conn.cursor()

    required = REQUIRED_COLUMNS.get(dataset_key, [])

    # helper: normalize column names for fuzzy matching
    def _norm(s):
        if s is None:
            return ''
        return ''.join([c for c in str(s).lower() if c.isalnum()])

    # parse explicit mapping JSON if provided by the client (mapping: JSON string of {target: source})
    mapping_json = None
    if mapping:
        try:
            mapping_json = json.loads(mapping)
        except Exception:
            mapping_json = None

    # detected columns from CSV header
    detected = reader.fieldnames or []

    # attempt to auto-map required columns to detected columns (flexible matching)
    auto_map = {}
    for req in required:
        found = None
        norm_req = _norm(req)
        # exact normalized match
        for c in detected:
            if _norm(c) == norm_req:
                found = c
                break
        if not found:
            # substring
            for c in detected:
                if norm_req in _norm(c) or _norm(c) in norm_req:
                    found = c
                    break
        if not found:
            try:
                from difflib import get_close_matches
                matches = get_close_matches(norm_req, [_norm(c) for c in detected], n=1, cutoff=0.6)
                if matches:
                    idx = [_norm(c) for c in detected].index(matches[0])
                    found = detected[idx]
            except Exception:
                found = None
        if not found and norm_req == 'zip5':
            found = next((c for c in detected if 'zip' in _norm(c)), None)
        auto_map[req] = found

    missing = [k for k, v in auto_map.items() if not v]
    if missing:
        return {'inserted': 0, 'missing_required': missing}

    rows = []
    # gather detected column names from CSV header
    detected_cols = reader.fieldnames or []

    # mapping_json is either parsed from explicit form field or None; use it when applying mapped values

    # target table name
    table = dataset_key

    # determine actual table columns so we only insert into columns that exist
    try:
        cur.execute(f"PRAGMA table_info('{table}')")
        existing_table_cols = [r[1] for r in cur.fetchall()]
    except Exception:
        existing_table_cols = []

    for row in reader:
        # source row with trimmed values
        src = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        # build target row but only include columns that exist in the target table
        r = {}
        for col in existing_table_cols:
            val = None
            # 1) if source had exact same column name as target, use it
            if col in src:
                val = src.get(col)
            # 0) prefer explicit client-provided mapping if present (mapping_json maps target -> source)
            if mapping_json and isinstance(mapping_json, dict) and mapping_json.get(col):
                val = src.get(mapping_json.get(col))
            # 2) if this column is one of required and we have an auto_map entry, use the mapped detected column
            elif col in auto_map and auto_map.get(col):
                val = src.get(auto_map.get(col))
            else:
                # 3) try normalized match from detected columns
                norm_col = _norm(col)
                match = None
                for c in detected_cols:
                    if _norm(c) == norm_col or norm_col in _norm(c) or _norm(c) in norm_col:
                        match = c
                        break
                if not match:
                    try:
                        from difflib import get_close_matches
                        matches = get_close_matches(norm_col, [_norm(c) for c in detected_cols], n=1, cutoff=0.6)
                        if matches:
                            idx = [_norm(c) for c in detected_cols].index(matches[0])
                            match = detected_cols[idx]
                    except Exception:
                        match = None
                if match:
                    val = src.get(match)
            if val is not None:
                r[col] = val
        # zip normalization
        if 'zip' in r and 'zip5' not in r:
            z = r.get('zip') or ''
            r['zip5'] = z[-5:]
        if 'zip5' in r:
            z = (r.get('zip5') or '')
            r['zip5'] = z[-5:]
        if 'market_category' in r and r.get('market_category') is not None:
            r['market_category'] = str(r['market_category']).upper().strip()
        # numeric casts safe
        for numf in ['army_potential','dod_potential','potential_remaining','p2p','contracts_ga','contracts_sa','contracts_vol','enlistments','population','available']:
            if numf in r:
                try:
                    if r[numf] is None or r[numf] == '':
                        r[numf] = None
                    else:
                        # cast to float or int accordingly
                        if '.' in str(r[numf]):
                            r[numf] = float(r[numf])
                        else:
                            r[numf] = int(float(r[numf]))
                except Exception:
                    r[numf] = None
        if 'as_of_date' not in r or not r.get('as_of_date'):
            r['as_of_date'] = _now_iso()
        if 'ingested_at' not in r or not r.get('ingested_at'):
            r['ingested_at'] = _now_iso()
        rows.append(r)

    # perform replace if requested
    try:
        if mode == 'replace':
            cur.execute(f"DELETE FROM {table}")
        # build insert dynamically using keys present in required+detected
        if len(rows) == 0:
            conn.commit()
            return {'inserted': 0}
        cols = list(rows[0].keys())
        placeholders = ','.join(['?'] * len(cols))
        insert_sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        to_insert = []
        for r in rows:
            to_insert.append([r.get(c) for c in cols])
        cur.executemany(insert_sql, to_insert)
        conn.commit()
        inserted = cur.rowcount if hasattr(cur, 'rowcount') and cur.rowcount>=0 else len(to_insert)

        # update registry: ensure columns exist and upsert values
        try:
            cur.execute("PRAGMA table_info('mi_dataset_registry')")
            existing = [r[1] for r in cur.fetchall()]
            # add missing columns if necessary
            if 'loaded' not in existing:
                cur.execute("ALTER TABLE mi_dataset_registry ADD COLUMN loaded INTEGER DEFAULT 0")
            if 'row_count' not in existing:
                cur.execute("ALTER TABLE mi_dataset_registry ADD COLUMN row_count INTEGER DEFAULT 0")
            if 'last_ingested_at' not in existing:
                cur.execute("ALTER TABLE mi_dataset_registry ADD COLUMN last_ingested_at TEXT")
            if 'notes' not in existing:
                cur.execute("ALTER TABLE mi_dataset_registry ADD COLUMN notes TEXT")
        except Exception:
            pass

        try:
            now = _now_iso()
            # Try to upsert using INSERT OR REPLACE while preserving display_name/table_name when present
            cur.execute("SELECT dataset_key FROM mi_dataset_registry WHERE dataset_key=?", (dataset_key,))
            exists = cur.fetchone()
            if exists:
                cur.execute("UPDATE mi_dataset_registry SET loaded=1, row_count=?, last_ingested_at=? WHERE dataset_key=?", (len(rows), now, dataset_key))
            else:
                # provide minimal display_name/table_name
                cur.execute("INSERT OR REPLACE INTO mi_dataset_registry (dataset_key, display_name, table_name, loaded, row_count, last_ingested_at) VALUES (?, ?, ?, 1, ?, ?)", (dataset_key, dataset_key, table, len(rows), now))
            conn.commit()
        except Exception:
            pass

        return {'inserted': inserted}
    except sqlite3.Error as e:
        conn.rollback()
        return {'inserted': 0, 'error': str(e)}
