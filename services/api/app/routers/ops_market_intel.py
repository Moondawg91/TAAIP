from fastapi import APIRouter, Query, Body
from typing import Optional, List
from ..db import connect, row_to_dict
from datetime import datetime

router = APIRouter()


def _table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _build_filters_dict(fy, qtr, month, component, echelon_type, unit_value, rsid_prefix, targeted, market_category, as_of_date):
    return {
        'fy': fy,
        'qtr': qtr,
        'month': month,
        'component': component,
        'echelon_type': echelon_type,
        'unit_value': unit_value,
        'rsid_prefix': rsid_prefix,
        'targeted': targeted,
        'market_category': market_category,
        'as_of_date': as_of_date
    }


def _where_clause_and_params(filters: dict):
    clauses = []
    params = []
    if filters.get('fy') is not None:
        clauses.append('fy = ?')
        params.append(filters['fy'])
    if filters.get('qtr'):
        clauses.append('qtr = ?')
        params.append(filters['qtr'])
    if filters.get('month') is not None:
        clauses.append('month = ?')
        params.append(filters['month'])
    if filters.get('component'):
        clauses.append('component = ?')
        params.append(filters['component'])
    if filters.get('echelon_type'):
        clauses.append('echelon_type = ?')
        params.append(filters['echelon_type'])
    if filters.get('unit_value'):
        clauses.append('unit_value = ?')
        params.append(filters['unit_value'])
    if filters.get('rsid_prefix'):
        clauses.append('rsid_prefix = ?')
        params.append(filters['rsid_prefix'])
    if filters.get('targeted') is not None:
        clauses.append('targeted = ?')
        params.append(1 if str(filters['targeted']).lower() in ('1','true','yes') else 0)
    if filters.get('market_category'):
        clauses.append('zip_category = ?')
        params.append(filters['market_category'])
    where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
    return where, params


@router.get('/ops/market/summary')
def market_summary(
    fy: Optional[int] = Query(None),
    qtr: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    component: Optional[str] = Query(None),
    echelon_type: Optional[str] = Query(None),
    unit_value: Optional[str] = Query(None),
    rsid_prefix: Optional[str] = Query(None),
    targeted: Optional[bool] = Query(None),
    market_category: Optional[str] = Query(None),
    as_of_date: Optional[str] = Query(None)
):
    conn = connect()
    cur = conn.cursor()
    filters = _build_filters_dict(fy, qtr, month, component, echelon_type, unit_value, rsid_prefix, targeted, market_category, as_of_date)
    missing = []
    if not _table_exists(cur, 'market_sama_zip_fact'):
        missing.append('market_sama_zip_fact')

    if missing:
        return {'status': 'ok', 'data_as_of': None, 'filters': filters, 'kpis': { 'total_army_potential': 0, 'total_contracts': 0, 'total_potential_remaining': 0, 'avg_p2p': None, 'mk_count':0,'mw_count':0,'mo_count':0,'su_count':0 }, 'missing_data': missing}

    where, params = _where_clause_and_params(filters)
    # Aggregate KPIs from market_sama_zip_fact
    sql = f"SELECT SUM(army_potential) as total_army_potential, SUM(contracts) as total_contracts, SUM(potential_remaining) as total_potential_remaining, AVG(p2p) as avg_p2p FROM market_sama_zip_fact {where}"
    cur.execute(sql, params)
    row = cur.fetchone() or {}
    row = row_to_dict(cur, row) or {}
    # category counts
    cats = { 'MK':0,'MW':0,'MO':0,'SU':0 }
    cur.execute(f"SELECT zip_category, COUNT(1) as cnt FROM market_sama_zip_fact {where} GROUP BY zip_category", params)
    for r in cur.fetchall() or []:
        k = r.get('zip_category') or r.get('zip') or None
        if k and k.upper() in cats:
            cats[k.upper()] = r.get('cnt',0)

    return {
        'status':'ok',
        'data_as_of': datetime.utcnow().isoformat() + 'Z',
        'filters': filters,
        'kpis': {
            'total_army_potential': row.get('total_army_potential') or 0,
            'total_contracts': row.get('total_contracts') or 0,
            'total_potential_remaining': row.get('total_potential_remaining') or 0,
            'avg_p2p': row.get('avg_p2p'),
            'mk_count': cats['MK'], 'mw_count': cats['MW'], 'mo_count': cats['MO'], 'su_count': cats['SU']
        },
        'missing_data': []
    }


@router.get('/ops/market/sama')
def market_sama(
    fy: Optional[int] = Query(None),
    qtr: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    component: Optional[str] = Query(None),
    echelon_type: Optional[str] = Query(None),
    unit_value: Optional[str] = Query(None),
    rsid_prefix: Optional[str] = Query(None),
    market_category: Optional[str] = Query(None),
    targeted: Optional[bool] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    conn = connect()
    cur = conn.cursor()
    filters = _build_filters_dict(fy, qtr, month, component, echelon_type, unit_value, rsid_prefix, targeted, market_category, None)
    missing = []
    if not _table_exists(cur, 'market_sama_zip_fact'):
        missing.append('market_sama_zip_fact')
        return {'status':'ok','data_as_of':None,'filters':filters,'rows':[],'count':0,'missing_data':missing}

    where, params = _where_clause_and_params(filters)
    sql = f"SELECT * FROM market_sama_zip_fact {where} ORDER BY potential_remaining DESC LIMIT ? OFFSET ?"
    cur.execute(sql, params + [limit, offset])
    raw_rows = cur.fetchall() or []
    rows = [row_to_dict(cur, r) for r in raw_rows]
    # count
    cnt_sql = f"SELECT COUNT(1) as cnt FROM market_sama_zip_fact {where}"
    cur.execute(cnt_sql, params)
    cnt_row = cur.fetchone() or {}
    cnt_row = row_to_dict(cur, cnt_row) or {}
    cnt = cnt_row.get('cnt') or 0
    return {'status':'ok','data_as_of': datetime.utcnow().isoformat() + 'Z','filters':filters,'rows': rows,'count': cnt,'missing_data': []}


@router.get('/ops/market/cbsa')
def market_cbsa(
    fy: Optional[int] = Query(None),
    plot_parameter: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    conn = connect()
    cur = conn.cursor()
    filters = {'fy': fy, 'plot_parameter': plot_parameter}
    missing = []
    if not _table_exists(cur, 'market_cbsa_fact'):
        missing.append('market_cbsa_fact')
        return {'status':'ok','data_as_of':None,'filters':filters,'rows':[],'count':0,'missing_data':missing}

    where = ''
    params = []
    if fy is not None:
        where = 'WHERE fy = ?'
        params = [fy]

    sql = f"SELECT * FROM market_cbsa_fact {where} ORDER BY value DESC LIMIT ? OFFSET ?"
    cur.execute(sql, params + [limit, offset])
    raw_rows = cur.fetchall() or []
    rows = [row_to_dict(cur, r) for r in raw_rows]
    cur.execute(f"SELECT COUNT(1) as cnt FROM market_cbsa_fact {where}", params)
    cnt_row = cur.fetchone() or {}
    cnt_row = row_to_dict(cur, cnt_row) or {}
    cnt = cnt_row.get('cnt') or 0
    return {'status':'ok','data_as_of': datetime.utcnow().isoformat() + 'Z','filters':filters,'rows': rows,'count': cnt,'missing_data': []}


@router.get('/ops/market/demographics')
def market_demographics(
    fy: Optional[int] = Query(None),
    geo_type: Optional[str] = Query(None),
    geo_id: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    conn = connect()
    cur = conn.cursor()
    filters = {'fy': fy, 'geo_type': geo_type, 'geo_id': geo_id}
    if not _table_exists(cur, 'market_demographics_fact'):
        return {'status':'ok','data_as_of':None,'filters':filters,'rows':[],'count':0,'missing_data':['market_demographics_fact']}
    clauses = []
    params = []
    if fy is not None:
        clauses.append('fy = ?'); params.append(fy)
    if geo_type:
        clauses.append('geo_type = ?'); params.append(geo_type)
    if geo_id:
        clauses.append('geo_id = ?'); params.append(geo_id)
    where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
    sql = f"SELECT * FROM market_demographics_fact {where} LIMIT ? OFFSET ?"
    cur.execute(sql, params + [limit, offset])
    raw_rows = cur.fetchall() or []
    rows = [row_to_dict(cur, r) for r in raw_rows]
    cur.execute(f"SELECT COUNT(1) as cnt FROM market_demographics_fact {where}", params)
    cnt_row = cur.fetchone() or {}
    cnt_row = row_to_dict(cur, cnt_row) or {}
    cnt = cnt_row.get('cnt') or 0
    return {'status':'ok','data_as_of': datetime.utcnow().isoformat() + 'Z','filters':filters,'rows': rows,'count': cnt,'missing_data': []}


@router.get('/ops/market/geotargeting/zones')
def list_zones():
    conn = connect(); cur = conn.cursor()
    if not _table_exists(cur, 'market_geotarget_zone'):
        return {'status':'ok','count':0,'zones':[],'missing_data':['market_geotarget_zone']}
    cur.execute('SELECT * FROM market_geotarget_zone ORDER BY created_at DESC')
    zones = cur.fetchall() or []
    return {'status':'ok','count': len(zones),'zones': zones, 'missing_data': []}


@router.post('/ops/market/geotargeting/zones')
def create_zone(payload: dict = Body(...)):
    conn = connect(); cur = conn.cursor()
    now = datetime.utcnow().isoformat() + 'Z'
    zone_id = payload.get('id') or f"zone_{int(datetime.utcnow().timestamp())}"
    cur.execute('INSERT OR REPLACE INTO market_geotarget_zone (id,name,zone_type,rsid_prefix,component,market_category,targeted,geojson,zip_list,cbsa_list,created_by,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
        zone_id,
        payload.get('name'),
        payload.get('zone_type'),
        payload.get('rsid_prefix'),
        payload.get('component'),
        payload.get('market_category'),
        1 if payload.get('targeted') else 0,
        payload.get('geojson'),
        payload.get('zip_list'),
        payload.get('cbsa_list'),
        payload.get('created_by'),
        now,
        now
    ))
    conn.commit()
    return {'status':'ok','id': zone_id}


@router.get('/ops/market/targeting/export')
def export_targeting(
    market_category: Optional[str] = Query(None),
    targeted: Optional[bool] = Query(None),
    limit: int = Query(100)
):
    conn = connect(); cur = conn.cursor()
    if not _table_exists(cur, 'market_sama_zip_fact'):
        return {'status':'ok','data_as_of':None,'filters':{'market_category':market_category,'targeted':targeted},'items':[],'missing_data':['market_sama_zip_fact']}

    clauses = []
    params = []
    if market_category:
        clauses.append('zip_category = ?'); params.append(market_category)
    if targeted is not None:
        clauses.append('targeted = ?'); params.append(1 if targeted else 0)
    where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
    sql = f"SELECT zip_code, station_rsid, zip_category as category, potential_remaining, p2p, army_share_of_potential FROM market_sama_zip_fact {where} ORDER BY potential_remaining DESC, army_share_of_potential ASC LIMIT ?"
    cur.execute(sql, params + [limit])
    rows = cur.fetchall() or []
    items = []
    for r in rows:
        items.append({
            'zip_code': r.get('zip_code') or r.get('zip'),
            'station_rsid': r.get('station_rsid'),
            'category': r.get('category'),
            'potential_remaining': r.get('potential_remaining'),
            'p2p': r.get('p2p'),
            'notes': None
        })
    return {'status':'ok','data_as_of': datetime.utcnow().isoformat() + 'Z','filters':{'market_category':market_category,'targeted':targeted},'items': items,'missing_data': []}
