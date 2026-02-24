from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ..db import connect
import csv
import io
import datetime
import json

router = APIRouter(prefix="/imports/mi", tags=["imports_mi"])

REQUIRED_COLUMNS = {
    'mi_zip_fact': ['zip5','market_category','potential_remaining'],
    'mi_cbsa_fact': ['cbsa_code','market_category','potential_remaining']
}

def _now_iso():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def _safe_int(v):
    try:
        if v is None or v == '':
            return None
        return int(float(v))
    except Exception:
        return None


def _safe_float(v):
    try:
        if v is None or v == '':
            return None
        return float(v)
    except Exception:
        return None


@router.post('/preview')
async def preview(dataset_key: str = Form(...), file: UploadFile = File(...)):
    if dataset_key not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail='unknown dataset_key')
    content = (await file.read()).decode('utf-8', errors='replace')
    f = io.StringIO(content)
    try:
        reader = csv.DictReader(f)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid CSV')
    detected = reader.fieldnames or []
    rows = []
    errors = []
    sample = []
    for i, r in enumerate(reader):
        if i < 20:
            sample.append(r)
        rows.append(r)
    row_count = len(rows)
    missing_required = [c for c in REQUIRED_COLUMNS[dataset_key] if c not in [d.lower() for d in detected]]
    return JSONResponse({'detected_columns': detected, 'required_columns': REQUIRED_COLUMNS[dataset_key], 'missing_required': missing_required, 'row_count': row_count, 'sample': sample, 'errors': errors})


@router.post('/commit')
async def commit(dataset_key: str = Form(...), file: UploadFile = File(...), mode: str = Form('replace')):
    if dataset_key not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail='unknown dataset_key')
    if mode != 'replace':
        raise HTTPException(status_code=400, detail='only replace mode supported')
    content = (await file.read()).decode('utf-8', errors='replace')
    f = io.StringIO(content)
    try:
        reader = csv.DictReader(f)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid CSV')
    detected = reader.fieldnames or []
    missing_required = [c for c in REQUIRED_COLUMNS[dataset_key] if c not in [d.lower() for d in detected]]
    if missing_required:
        raise HTTPException(status_code=400, detail=f'missing required columns: {missing_required}')

    conn = connect()
    cur = conn.cursor()
    # replace mode: delete existing rows
    try:
        cur.execute(f"DELETE FROM {dataset_key}")
    except Exception:
        pass
    inserted = 0
    now = _now_iso()
    for r in reader:
        # normalize fields
        if dataset_key == 'mi_zip_fact':
            zip5 = (r.get('zip5') or r.get('zip') or '').strip()
            if len(zip5) > 5: zip5 = zip5[:5]
            if len(zip5) < 5: zip5 = zip5.zfill(5)
            cbsa_code = (r.get('cbsa_code') or '').strip()
            cbsa_name = (r.get('cbsa_name') or '').strip()
            station_name = (r.get('station_name') or '').strip()
            component = (r.get('component') or '').strip().upper()
            market_category = (r.get('market_category') or '').strip().upper()
            army_potential = _safe_int(r.get('army_potential') or r.get('army_potential'))
            dod_potential = _safe_int(r.get('dod_potential') or r.get('dod_potential'))
            army_share_of_potential = _safe_float(r.get('army_share_of_potential') or r.get('army_share'))
            potential_remaining = _safe_int(r.get('potential_remaining'))
            contracts_ga = _safe_int(r.get('contracts_ga') or r.get('contracts'))
            contracts_sa = _safe_int(r.get('contracts_sa'))
            contracts_vol = _safe_int(r.get('contracts_vol'))
            p2p = _safe_float(r.get('p2p'))
            as_of_date = r.get('as_of_date') or now
            created_at = r.get('created_at') or now
            updated_at = r.get('updated_at') or now
            # insert
            try:
                cur.execute("INSERT INTO mi_zip_fact(id, fy, qtr, rsid_prefix, zip5, cbsa_code, cbsa_name, station_name, component, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, created_at, updated_at, demo_json, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            ((r.get('id') or None), _safe_int(r.get('fy')), r.get('qtr'), r.get('rsid_prefix'), zip5, cbsa_code, cbsa_name, station_name, component, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, created_at, updated_at, json.dumps({}), now))
                inserted += 1
            except Exception as e:
                # ignore row but continue
                continue
        elif dataset_key == 'mi_cbsa_fact':
            cbsa_code = (r.get('cbsa_code') or '').strip()
            cbsa_name = (r.get('cbsa_name') or '').strip()
            station_name = (r.get('station_name') or '').strip()
            component = (r.get('component') or '').strip().upper()
            market_category = (r.get('market_category') or '').strip().upper()
            army_potential = _safe_int(r.get('army_potential'))
            dod_potential = _safe_int(r.get('dod_potential'))
            army_share_of_potential = _safe_float(r.get('army_share_of_potential') or r.get('army_share'))
            potential_remaining = _safe_int(r.get('potential_remaining'))
            contracts_ga = _safe_int(r.get('contracts_ga') or r.get('contracts'))
            contracts_sa = _safe_int(r.get('contracts_sa'))
            contracts_vol = _safe_int(r.get('contracts_vol'))
            p2p = _safe_float(r.get('p2p'))
            as_of_date = r.get('as_of_date') or now
            created_at = r.get('created_at') or now
            updated_at = r.get('updated_at') or now
            try:
                cur.execute("INSERT INTO mi_cbsa_fact(id, fy, qtr, rsid_prefix, cbsa_code, cbsa_name, station_name, component, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, created_at, updated_at, demo_json, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            ((r.get('id') or None), _safe_int(r.get('fy')), r.get('qtr'), r.get('rsid_prefix'), cbsa_code, cbsa_name, station_name, component, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, created_at, updated_at, json.dumps({}), now))
                inserted += 1
            except Exception:
                continue
    try:
        conn.commit()
    except Exception:
        pass
    # update registry
    try:
        cur.execute("INSERT OR REPLACE INTO mi_dataset_registry(dataset_key, display_name, table_name, required_columns_json, optional_columns_json, last_seen_at) VALUES (?,?,?,?,?,?)",
                    (dataset_key, dataset_key, dataset_key, json.dumps(REQUIRED_COLUMNS.get(dataset_key,[])), json.dumps([]), _now_iso()))
        # also update row_count in registry table if exists
        try:
            cur.execute("UPDATE mi_dataset_registry SET last_seen_at=?, required_columns_json=?, optional_columns_json=? WHERE dataset_key=?", (_now_iso(), json.dumps(REQUIRED_COLUMNS.get(dataset_key,[])), json.dumps([]), dataset_key))
        except Exception:
            pass
        conn.commit()
    except Exception:
        pass
    return JSONResponse({'inserted': inserted, 'dataset_key': dataset_key})
