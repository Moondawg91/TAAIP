from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import re
import csv
import io

from .. import db

router = APIRouter(prefix='/v2/station/dep-loss', tags=['Station'])

ALLOWED_PERIODS = {'CURRENT_MONTH', 'YTD'}


def _normalize_row(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'station_rsid': (r.get('station_rsid') or '').strip().upper(),
        'cmpnt_cd': (r.get('cmpnt_cd') or '').strip().upper(),
        'loss_code': (r.get('loss_code') or '').strip().upper().replace(' ', '_'),
        'loss_count': int(r.get('loss_count') or 0)
    }


def _validate_rsm_month(rsm: Optional[str]) -> bool:
    if rsm is None:
        return True
    return bool(re.match(r'^\d{4}-\d{2}$', rsm))


@router.post('/manual')
def manual_ingest(payload: Dict[str, Any]):
    period_key = (payload.get('period_key') or 'CURRENT_MONTH').upper()
    rsm_month = payload.get('rsm_month')
    rows = payload.get('rows') or []

    if period_key not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f'period_key must be one of {list(ALLOWED_PERIODS)}')
    if not _validate_rsm_month(rsm_month):
        raise HTTPException(status_code=400, detail='rsm_month must be in YYYY-MM format')
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=400, detail='rows must be a non-empty list')

    norm = [_normalize_row(r) for r in rows]
    # validate station RSIDs exist and are stations
    station_rsids = list({r['station_rsid'] for r in norm})
    conn = db.connect()
    try:
        cur = conn.cursor()
        placeholders = ','.join('?' for _ in station_rsids) or "''"
        cur.execute(f"SELECT rsid, type FROM org_unit WHERE rsid IN ({placeholders})", tuple(station_rsids))
        found = {r['rsid']: r['type'] for r in cur.fetchall()}
        unknown = [s for s in station_rsids if s not in found or (found.get(s) or '').upper() not in ('STATION', 'STN')]
        if unknown:
            sample = unknown[:5]
            raise HTTPException(status_code=400, detail={'error': 'unknown_stations', 'missing': sample})

        upsert_sql = ("INSERT INTO fact_station_dep_loss (station_rsid, fy, qtr_num, rsm_month, period_key, cmpnt_cd, loss_code, loss_count, source, ingest_run_id, created_at, updated_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now')) "
                      "ON CONFLICT(station_rsid, period_key, rsm_month, cmpnt_cd, loss_code) DO UPDATE SET loss_count=excluded.loss_count, updated_at=datetime('now'), source=excluded.source, ingest_run_id=excluded.ingest_run_id")

        rows_in = len(norm)
        rows_upserted = 0
        for r in norm:
            if r['loss_count'] < 0:
                continue
            cur.execute(upsert_sql, (r['station_rsid'], None, None, rsm_month, period_key, r['cmpnt_cd'], r['loss_code'], r['loss_count'], 'VANTAGE_MANUAL', None))
            rows_upserted += 1
        conn.commit()
        return {'status': 'success', 'period_key': period_key, 'rsm_month': rsm_month, 'rows_in': rows_in, 'rows_upserted': rows_upserted}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.post('/paste')
def paste_ingest(payload: Dict[str, Any]):
    period_key = (payload.get('period_key') or 'CURRENT_MONTH').upper()
    rsm_month = payload.get('rsm_month')
    csv_text = payload.get('csv_text') or ''

    if period_key not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f'period_key must be one of {list(ALLOWED_PERIODS)}')
    if not _validate_rsm_month(rsm_month):
        raise HTTPException(status_code=400, detail='rsm_month must be in YYYY-MM format')
    if not csv_text:
        raise HTTPException(status_code=400, detail='csv_text required')

    f = io.StringIO(csv_text)
    try:
        reader = csv.DictReader(f)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid CSV text')

    rows = []
    for r in reader:
        try:
            rows.append({'station_rsid': r.get('station_rsid'), 'cmpnt_cd': r.get('cmpnt_cd'), 'loss_code': r.get('loss_code'), 'loss_count': int(r.get('loss_count') or 0)})
        except Exception:
            continue

    return manual_ingest({'period_key': period_key, 'rsm_month': rsm_month, 'rows': rows})
