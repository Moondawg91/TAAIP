from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from services.api.app.db import connect, row_to_dict, table_has_cols
from datetime import datetime

router = APIRouter(prefix="/api/ops/market", tags=["ops-market"])


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters_dict(as_of_date, component, echelon_type, unit_value, zip_category, cbsa_code):
    return {"as_of_date": as_of_date, "component": component, "echelon_type": echelon_type, "unit_value": unit_value, "zip_category": zip_category, "cbsa_code": cbsa_code}


@router.get('/summary')
def summary(as_of_date: Optional[str] = None, component: Optional[str] = None, echelon_type: Optional[str] = None, unit_value: Optional[str] = Query(None, alias='rsid_prefix'), zip_category: Optional[str] = None, cbsa_code: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(as_of_date, component, echelon_type, unit_value, zip_category, cbsa_code)
    missing = []
    try:
        # Build where clause
        where = ['1=1']
        params: List[Any] = []
        if as_of_date:
            where.append('as_of_date = ?')
            params.append(as_of_date)
        if component:
            where.append('component = ?'); params.append(component)
        if echelon_type:
            where.append('echelon_type = ?'); params.append(echelon_type)
        if unit_value:
            where.append('unit_value LIKE ?'); params.append(f"{unit_value}%")
        if zip_category:
            where.append('zip_category = ?'); params.append(zip_category)
        if cbsa_code:
            where.append('cbsa_code = ?'); params.append(cbsa_code)

        where_sql = ' AND '.join(where)
        # Check table presence
        try:
            cur.execute('SELECT COUNT(1) FROM market_zip_metrics WHERE ' + where_sql, params)
            cnt = cur.fetchone()[0] or 0
        except Exception:
            cnt = 0
        if cnt == 0:
            missing.append('market_zip_metrics empty')
            kpis = {'zips': 0, 'total_army_potential': 0, 'total_dod_potential': 0, 'total_potential_remaining': 0, 'army_share_of_potential': None, 'contracts_total': 0, 'contracts_ga': 0, 'contracts_sa': 0, 'contracts_vol': 0}
            by_zip_category = []
            data_as_of = None
        else:
            # aggregates
            cur.execute(f"SELECT COALESCE(SUM(army_potential),0), COALESCE(SUM(dod_potential),0), COALESCE(SUM(potential_remaining),0), COALESCE(SUM(contracts_ga+contracts_sa+contracts_vol),0), COALESCE(SUM(contracts_ga),0), COALESCE(SUM(contracts_sa),0), COALESCE(SUM(contracts_vol),0) FROM market_zip_metrics WHERE {where_sql}", params)
            agg = cur.fetchone() or [0]*7
            total_army = agg[0] or 0
            total_dod = agg[1] or 0
            total_pot_rem = agg[2] or 0
            contracts_total = agg[3] or 0
            contracts_ga = agg[4] or 0
            contracts_sa = agg[5] or 0
            contracts_vol = agg[6] or 0
            # army share weighted if possible
            army_share = None
            try:
                cur.execute(f"SELECT SUM(army_share_of_potential * COALESCE(army_potential,0)) FROM market_zip_metrics WHERE {where_sql}", params)
                num = cur.fetchone()[0]
                cur.execute(f"SELECT SUM(COALESCE(army_potential,0)) FROM market_zip_metrics WHERE {where_sql}", params)
                den = cur.fetchone()[0]
                if den and den > 0 and num is not None:
                    army_share = float(num) / float(den)
            except Exception:
                army_share = None
            kpis = {'zips': cnt, 'total_army_potential': int(total_army), 'total_dod_potential': int(total_dod), 'total_potential_remaining': int(total_pot_rem), 'army_share_of_potential': army_share, 'contracts_total': int(contracts_total), 'contracts_ga': int(contracts_ga), 'contracts_sa': int(contracts_sa), 'contracts_vol': int(contracts_vol)}
            # by zip_category
            cur.execute(f"SELECT zip_category, COALESCE(SUM(army_potential),0), COALESCE(SUM(potential_remaining),0), COALESCE(SUM(contracts_ga+contracts_sa+contracts_vol),0) FROM market_zip_metrics WHERE {where_sql} GROUP BY zip_category", params)
            by_zip_category = []
            for r in cur.fetchall():
                rr = row_to_dict(cur, r)
                by_zip_category.append({'zip_category': rr.get('zip_category'), 'army_potential': int(rr.get('COALESCE(SUM(army_potential),0)') if isinstance(rr.get('COALESCE(SUM(army_potential),0)'), int) else rr.get(1,0)), 'potential_remaining': int(rr.get(2,0)), 'contracts_total': int(rr.get(3,0)), 'army_share_of_potential': None})
            # data_as_of
            cur.execute(f"SELECT MAX(ingested_at) FROM market_zip_metrics WHERE {where_sql}", params)
            data_as_of = cur.fetchone()[0]

        return {"status": "ok", "data_as_of": data_as_of, "filters": filters, "kpis": kpis, "by_zip_category": by_zip_category, "missing_data": missing}
    except Exception:
        return {"status": "ok", "data_as_of": None, "filters": filters, "kpis": {"zips":0}, "by_zip_category": [], "missing_data": ["query_error"]}


@router.get('/zips')
def list_zips(as_of_date: Optional[str] = None, component: Optional[str] = None, echelon_type: Optional[str] = None, unit_value: Optional[str] = Query(None, alias='rsid_prefix'), zip_category: Optional[str] = None, cbsa_code: Optional[str] = None, limit: int = 500):
    conn = connect(); cur = conn.cursor()
    where = ['1=1']; params = []
    if as_of_date: where.append('as_of_date = ?'); params.append(as_of_date)
    if component: where.append('component = ?'); params.append(component)
    if echelon_type: where.append('echelon_type = ?'); params.append(echelon_type)
    if unit_value: where.append('unit_value LIKE ?'); params.append(f"{unit_value}%")
    if zip_category: where.append('zip_category = ?'); params.append(zip_category)
    if cbsa_code: where.append('cbsa_code = ?'); params.append(cbsa_code)
    where_sql = ' AND '.join(where)
    try:
        cur.execute(f"SELECT station_rsid, zip, zip_category, army_potential, dod_potential, dod_wtd_avg, army_share_of_potential, contracts_ga, contracts_sa, contracts_vol, potential_remaining, p2p_band, cbsa_code, dma_name FROM market_zip_metrics WHERE {where_sql} ORDER BY potential_remaining DESC LIMIT ?", params + [limit])
        rows = cur.fetchall()
        out = [row_to_dict(cur, r) for r in rows]
        return {"status":"ok", "count": len(out), "rows": out}
    except Exception:
        return {"status":"ok", "count":0, "rows": []}


@router.get('/cbsa')
def list_cbsa(as_of_date: Optional[str] = None, component: Optional[str] = None, echelon_type: Optional[str] = None, unit_value: Optional[str] = Query(None, alias='rsid_prefix'), cbsa_code: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    where = ['1=1']; params = []
    if as_of_date: where.append('as_of_date = ?'); params.append(as_of_date)
    if component: where.append('component = ?'); params.append(component)
    if echelon_type: where.append('echelon_type = ?'); params.append(echelon_type)
    if unit_value: where.append('unit_value LIKE ?'); params.append(f"{unit_value}%")
    where_sql = ' AND '.join(where)
    try:
        # prefer market_cbsa_metrics
        try:
            cur.execute('PRAGMA table_info(market_cbsa_metrics)')
            cur.execute(f"SELECT cbsa_code, cbsa_name, total_population, total_potential, potential_remaining, contracts_total, army_share_of_potential FROM market_cbsa_metrics WHERE 1=1 {(' AND cbsa_code=?' if cbsa_code else '')} LIMIT 500", ([cbsa_code] if cbsa_code else []))
            rows = cur.fetchall()
            out = [row_to_dict(cur,r) for r in rows]
            return {"status":"ok","count": len(out), "rows": out}
        except Exception:
            # aggregate from zip metrics
            sql = f"SELECT cbsa_code, COALESCE(COUNT(DISTINCT zip),0), COALESCE(SUM(army_potential),0), COALESCE(SUM(potential_remaining),0), COALESCE(SUM(contracts_ga+contracts_sa+contracts_vol),0) FROM market_zip_metrics WHERE {where_sql} GROUP BY cbsa_code LIMIT 500"
            cur.execute(sql, params)
            rows = cur.fetchall()
            out = []
            for r in rows:
                rr = row_to_dict(cur, r)
                out.append({'cbsa_code': rr.get(0) or rr.get('cbsa_code'), 'zips': int(rr.get(1,0)), 'total_army_potential': int(rr.get(2,0)), 'potential_remaining': int(rr.get(3,0)), 'contracts_total': int(rr.get(4,0))})
            return {"status":"ok","count": len(out), "rows": out}
    except Exception:
        return {"status":"ok","count":0,"rows": []}


@router.get('/demographics')
def list_demographics(as_of_date: Optional[str] = None, component: Optional[str] = None, echelon_type: Optional[str] = None, unit_value: Optional[str] = Query(None, alias='rsid_prefix'), geo_level: Optional[str] = None, geo_value: Optional[str] = None, limit: int = 500):
    conn = connect(); cur = conn.cursor()
    where = ['1=1']; params = []
    if as_of_date: where.append('as_of_date = ?'); params.append(as_of_date)
    if component: where.append('component = ?'); params.append(component)
    if echelon_type: where.append('echelon_type = ?'); params.append(echelon_type)
    if unit_value: where.append('unit_value LIKE ?'); params.append(f"{unit_value}%")
    if geo_level: where.append('geo_level = ?'); params.append(geo_level)
    if geo_value: where.append('geo_value = ?'); params.append(geo_value)
    where_sql = ' AND '.join(where)
    try:
        cur.execute(f"SELECT id, as_of_date, component, echelon_type, unit_value, geo_level, geo_value, race_ethnicity, gender, fqma_population, youth_population, enlistments, p2p_value FROM market_demographics WHERE {where_sql} LIMIT ?", params + [limit])
        rows = cur.fetchall(); out = [row_to_dict(cur, r) for r in rows]
        return {"status":"ok","count": len(out), "rows": out}
    except Exception:
        return {"status":"ok","count":0,"rows": []}


@router.get('/geotargeting/zones')
def list_zones(limit: int = 500):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('SELECT id, name, description, zone_type, echelon_type, unit_value, component, status, geometry_json, created_at, updated_at FROM geo_target_zones LIMIT ?',(limit,))
        rows = cur.fetchall(); zones = []
        for r in rows:
            z = row_to_dict(cur, r)
            # member counts
            cur.execute('SELECT COUNT(1) FROM geo_target_zone_members WHERE zone_id=?',(z.get('id'),))
            cnt = cur.fetchone()[0] or 0
            z['member_count'] = cnt
            zones.append(z)
        return {"status":"ok","count": len(zones), "zones": zones}
    except Exception:
        return {"status":"ok","count":0,"zones": []}


@router.post('/geotargeting/zones')
def create_zone(payload: Dict[str, Any]):
    conn = connect(); cur = conn.cursor(); now = _now_iso()
    # validate minimal
    zone_id = payload.get('id') or payload.get('name')
    if not zone_id:
        raise HTTPException(status_code=400, detail='id or name required')
    try:
        cur.execute('INSERT OR REPLACE INTO geo_target_zones(id, name, description, zone_type, echelon_type, unit_value, component, status, geometry_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (zone_id, payload.get('name'), payload.get('description'), payload.get('zone_type'), payload.get('echelon_type'), payload.get('unit_value'), payload.get('component'), payload.get('status') or 'draft', payload.get('geometry_json'), now, now))
        # members
        members = payload.get('members') or []
        for m in members:
            mid = m.get('id') or f"{zone_id}:{m.get('member_type')}:{m.get('member_value')}"
            cur.execute('INSERT OR REPLACE INTO geo_target_zone_members(id, zone_id, member_type, member_value, created_at) VALUES (?,?,?,?,?)', (mid, zone_id, m.get('member_type'), m.get('member_value'), now))
        conn.commit()
        return {"status":"ok"}
    except Exception:
        return {"status":"ok"}


@router.put('/geotargeting/zones/{zone_id}')
def update_zone(zone_id: str, payload: Dict[str, Any]):
    conn = connect(); cur = conn.cursor(); now = _now_iso()
    try:
        cur.execute('UPDATE geo_target_zones SET name=?, description=?, zone_type=?, echelon_type=?, unit_value=?, component=?, status=?, geometry_json=?, updated_at=? WHERE id=?', (payload.get('name'), payload.get('description'), payload.get('zone_type'), payload.get('echelon_type'), payload.get('unit_value'), payload.get('component'), payload.get('status'), payload.get('geometry_json'), now, zone_id))
        members = payload.get('members')
        if members is not None:
            # replace members
            cur.execute('DELETE FROM geo_target_zone_members WHERE zone_id=?',(zone_id,))
            for m in members:
                mid = m.get('id') or f"{zone_id}:{m.get('member_type')}:{m.get('member_value')}"
                cur.execute('INSERT OR REPLACE INTO geo_target_zone_members(id, zone_id, member_type, member_value, created_at) VALUES (?,?,?,?,?)', (mid, zone_id, m.get('member_type'), m.get('member_value'), now))
        conn.commit()
        return {"status":"ok"}
    except Exception:
        return {"status":"ok"}


@router.delete('/geotargeting/zones/{zone_id}')
def delete_zone(zone_id: str):
    conn = connect(); cur = conn.cursor(); now = _now_iso()
    try:
        cur.execute('UPDATE geo_target_zones SET status=? , updated_at=? WHERE id=?', ('inactive', now, zone_id))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


@router.get('/import/templates')
def import_templates():
    templates = [
        {"dataset_key":"market_zip_metrics","required_columns":["id","zip"],"optional_columns":["army_potential","dod_potential","zip_category","cbsa_code","dma_name","p2p_band","p2p_value"],"notes":"SAMA ZIP extract mapping; supports MK/MW/MO/SU and P2P fields"},
        {"dataset_key":"market_cbsa_metrics","required_columns":["id","cbsa_code"],"optional_columns":["cbsa_name","total_population","total_potential"],"notes":"CBSA aggregated metrics"},
        {"dataset_key":"market_demographics","required_columns":["id","geo_level","geo_value"],"optional_columns":["race_ethnicity","gender","fqma_population"],"notes":"Demographics by geo level"},
        {"dataset_key":"geo_target_zones","required_columns":["id","name","zone_type"],"optional_columns":["geometry_json","members"],"notes":"Geofencing registry; members optional"}
    ]
    return {"status":"ok","templates": templates}
