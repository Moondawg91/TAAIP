from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from services.api.app.db import connect
from datetime import datetime

router = APIRouter(prefix="/ops/market/compute", tags=["ops-market-compute"])


def _now_iso():
    return datetime.utcnow().isoformat() + 'Z'


def p2p_band(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None
    if v < 0.9:
        return '<0.9'
    if 0.9 <= v <= 1.1:
        return '0.9-1.1'
    return '>1.1'


def classify_category(army_potential: Optional[int], army_share: Optional[float], p2p: Optional[float]) -> str:
    # Simple deterministic rules (configurable thresholds later)
    try:
        ap = int(army_potential or 0)
    except Exception:
        ap = 0
    try:
        share = float(army_share) if army_share is not None else 0.0
    except Exception:
        share = 0.0
    try:
        p = float(p2p) if p2p is not None else 1.0
    except Exception:
        p = 1.0

    if ap >= 500 and share >= 0.4 and p >= 1.0:
        return 'MK'
    if ap >= 300 and share < 0.25:
        return 'MW'
    if 100 <= ap < 300:
        return 'MO'
    return 'SU'


@router.get('/p2p-band')
def get_p2p_band(value: Optional[float] = Query(None)):
    return {'status': 'ok', 'value': value, 'band': p2p_band(value), 'data_as_of': _now_iso()}


@router.get('/classify-zip')
def classify_zip(zip_code: Optional[str] = Query(None), as_of_date: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor()
    where = '1=1'; params: List[Any] = []
    if zip_code:
        where += ' AND (zip_code = ? OR zip = ?)'; params.extend([zip_code, zip_code])
    if as_of_date:
        where += ' AND as_of_date = ?'; params.append(as_of_date)
    try:
        cur.execute(f"SELECT zip_code, army_potential, army_share_of_potential, p2p_value FROM market_sama_zip_fact WHERE {where} LIMIT 1", params)
        r = cur.fetchone() or {}
        ap = r.get('army_potential') or r.get('army_potential') or 0
        share = r.get('army_share_of_potential')
        p2v = r.get('p2p') or r.get('p2p_value')
        cat = classify_category(ap, share, p2v)
        return {'status': 'ok', 'zip': r.get('zip_code') or r.get('zip'), 'army_potential': ap, 'army_share_of_potential': share, 'p2p': p2v, 'category': cat, 'data_as_of': _now_iso()}
    except Exception:
        return {'status': 'ok', 'zip': zip_code, 'category': None, 'data_as_of': None}
