from fastapi import APIRouter, Query
from typing import Optional
from ..db import connect, execute_with_retry, table_has_cols
from datetime import datetime

router = APIRouter()


def _table_exists(conn, name: str) -> bool:
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False


def _build_filters(qs):
    # Normalize known filters
    return {
        'fy': qs.get('fy'),
        'qtr': qs.get('qtr'),
        'month': qs.get('month'),
        'rsid_prefix': qs.get('rsid_prefix'),
        'component': qs.get('component'),
        'market_category': qs.get('market_category')
    }


def _rsid_where(prefix_param):
    if not prefix_param:
        return "", {}
    return " AND rsid_prefix LIKE :rsid_prefix ", {'rsid_prefix': f"{prefix_param}%"}


def _data_as_of_from(conn, table):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT MAX(ingested_at) as as_of FROM {table}")
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return None


# Market intelligence summary (both new and legacy paths)
@router.get("/operations/market-intel/summary")
@router.get("/ops/market/summary")
def market_intel_summary(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), month: Optional[int] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    missing = []
    # Ensure table exists
    if not _table_exists(conn, 'market_zip_fact'):
        missing.append('market_zip_fact')
    if not _table_exists(conn, 'market_cbsa_fact'):
        missing.append('market_cbsa_fact')

    filters = {'fy': fy, 'qtr': qtr, 'month': month, 'rsid_prefix': rsid_prefix}

    resp = {'status': 'ok', 'data_as_of': None, 'filters': filters, 'kpis': {}, 'series': {}, 'tables': {}, 'missing_data': missing}

    if missing:
        return resp

    # build WHERE clauses
    where = []
    params = {}
    if fy is not None:
        where.append('fy = :fy')
        params['fy'] = fy
    if qtr is not None:
        where.append('qtr = :qtr')
        params['qtr'] = qtr
    if month is not None:
        where.append('month = :month')
        params['month'] = month
    rsid_clause, rsid_params = _rsid_where(rsid_prefix)
    if rsid_clause:
        where.append('rsid_prefix LIKE :rsid_prefix')
        params.update(rsid_params)

    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

    try:
        # KPIs from zip-level aggregated
        sql = f"SELECT SUM(fqma) as total_fqma, SUM(youth_pop) as total_youth_pop, SUM(army_accessions) as army_accessions, AVG(army_share) as army_share_avg, SUM(potential_remaining) as potential_remaining_total, AVG(p2p) as p2p_avg FROM market_zip_fact {where_sql}"
        cur.execute(sql, params)
        r = cur.fetchone()
        resp['kpis'] = {
            'total_fqma': r[0] or 0,
            'total_youth_pop': r[1] or 0,
            'army_accessions': r[2] or 0,
            'army_share_avg': float(r[3]) if r[3] is not None else None,
            'potential_remaining_total': r[4] or 0,
            'p2p_avg': float(r[5]) if r[5] is not None else None
        }

        # counts by market_category
        sql = f"SELECT market_category, COUNT(1) as cnt FROM market_zip_fact {where_sql} GROUP BY market_category"
        cur.execute(sql, params)
        counts = {row[0]: row[1] for row in cur.fetchall()}
        resp['kpis']['counts_by_market_category'] = counts

        # flags counts
        sql = f"SELECT SUM(must_keep), SUM(must_win), SUM(market_of_opportunity), SUM(supplemental_market) FROM market_zip_fact {where_sql}"
        cur.execute(sql, params)
        fr = cur.fetchone()
        resp['kpis'].update({
            'must_keep_count': int(fr[0] or 0),
            'must_win_count': int(fr[1] or 0),
            'moo_count': int(fr[2] or 0),
            'supplemental_count': int(fr[3] or 0)
        })

        # top zips
        tz_sql = f"SELECT zip5, cbsa_code, market_category, potential_remaining, p2p FROM market_zip_fact {where_sql} ORDER BY potential_remaining DESC, p2p DESC LIMIT 50"
        cur.execute(tz_sql, params)
        resp['tables']['top_zip_opportunities'] = [dict(zip(['zip5','cbsa_code','market_category','potential_remaining','p2p'], row)) for row in cur.fetchall()]

        # top cbsas
        tc_sql = f"SELECT cbsa_code, cbsa_name, SUM(potential_remaining) as potential_remaining, AVG(p2p) as p2p_avg FROM market_cbsa_fact {where_sql} GROUP BY cbsa_code, cbsa_name ORDER BY potential_remaining DESC LIMIT 50"
        cur.execute(tc_sql, params)
        resp['tables']['top_cbsa_opportunities'] = [dict(zip(['cbsa_code','cbsa_name','potential_remaining','p2p_avg'], row)) for row in cur.fetchall()]

        # series: p2p trend by month (if month available)
        s_sql = f"SELECT month, AVG(p2p) as p2p_avg, AVG(army_share) as share_avg FROM market_zip_fact {where_sql} GROUP BY month ORDER BY month"
        cur.execute(s_sql, params)
        resp['series']['p2p_trend'] = [{'month': row[0], 'p2p_avg': row[1], 'share_avg': row[2]} for row in cur.fetchall()]

        resp['data_as_of'] = _data_as_of_from(conn, 'market_zip_fact') or _data_as_of_from(conn, 'market_cbsa_fact')
    except Exception:
        # safe failure -> mark missing_data
        resp['missing_data'].append('aggregation_failed')
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return resp


@router.get("/operations/market-intel/sama")
@router.get("/ops/market/zips")
def market_sama(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), month: Optional[int] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    missing = []
    if not _table_exists(conn, 'market_zip_fact'):
        missing.append('market_zip_fact')
    resp = {'status': 'ok', 'data_as_of': None, 'filters': {'fy': fy, 'qtr': qtr, 'month': month, 'rsid_prefix': rsid_prefix}, 'kpis': {}, 'series': {}, 'tables': {}, 'missing_data': missing}
    if missing:
        return resp
    where = []
    params = {}
    if fy is not None:
        where.append('fy = :fy'); params['fy'] = fy
    if qtr is not None:
        where.append('qtr = :qtr'); params['qtr'] = qtr
    if month is not None:
        where.append('month = :month'); params['month'] = month
    if rsid_prefix:
        where.append('rsid_prefix LIKE :rsid_prefix'); params['rsid_prefix'] = f"{rsid_prefix}%"
    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
    try:
        sql = f"SELECT zip5, cbsa_code, market_category, fqma, youth_pop, army_share, potential_remaining, p2p, must_keep, must_win, market_of_opportunity, supplemental_market FROM market_zip_fact {where_sql} ORDER BY potential_remaining DESC LIMIT 1000"
        cur.execute(sql, params)
        rows = [dict(zip(['zip5','cbsa_code','market_category','fqma','youth_pop','army_share','potential_remaining','p2p','must_keep','must_win','market_of_opportunity','supplemental_market'], r)) for r in cur.fetchall()]
        resp['tables']['sama_zip_table'] = rows
        resp['data_as_of'] = _data_as_of_from(conn, 'market_zip_fact')
    except Exception:
        resp['missing_data'].append('sama_query_failed')
    finally:
        try: conn.close()
        except Exception: pass
    return resp


@router.get("/operations/market-intel/cbsa")
@router.get("/ops/market/cbsa")
def market_cbsa(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor(); missing = []
    if not _table_exists(conn, 'market_cbsa_fact'):
        missing.append('market_cbsa_fact')
    resp = {'status':'ok','data_as_of':None,'filters':{'fy':fy,'qtr':qtr,'rsid_prefix':rsid_prefix},'kpis':{},'series':{},'tables':{},'missing_data':missing}
    if missing:
        return resp
    where = []; params={}
    if fy is not None: where.append('fy = :fy'); params['fy']=fy
    if qtr is not None: where.append('qtr = :qtr'); params['qtr']=qtr
    if rsid_prefix: where.append('rsid_prefix LIKE :rsid_prefix'); params['rsid_prefix']=f"{rsid_prefix}%"
    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
    try:
        sql = f"SELECT cbsa_code, cbsa_name, SUM(youth_pop) as total_youth, SUM(fqma) as total_fqma, SUM(army_accessions) as army_accessions, AVG(army_share) as army_share_avg, SUM(potential_remaining) as potential_remaining, AVG(p2p) as p2p_avg FROM market_cbsa_fact {where_sql} GROUP BY cbsa_code, cbsa_name ORDER BY potential_remaining DESC LIMIT 200"
        cur.execute(sql, params)
        resp['tables']['cbsa_rollups'] = [dict(zip(['cbsa_code','cbsa_name','total_youth','total_fqma','army_accessions','army_share_avg','potential_remaining','p2p_avg'], r)) for r in cur.fetchall()]
        resp['data_as_of'] = _data_as_of_from(conn, 'market_cbsa_fact')
    except Exception:
        resp['missing_data'].append('cbsa_query_failed')
    finally:
        try: conn.close()
        except Exception: pass
    return resp


@router.get("/operations/schools/summary")
def schools_summary(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor(); missing = []
    if not _table_exists(conn, 'school_fact'):
        missing.append('school_fact')
    resp = {'status':'ok','data_as_of':None,'filters':{'fy':fy,'qtr':qtr,'rsid_prefix':rsid_prefix},'kpis':{},'tables':{},'missing_data':missing}
    if missing:
        return resp
    where = []; params={}
    if fy is not None: where.append('fy = :fy'); params['fy']=fy
    if qtr is not None: where.append('qtr = :qtr'); params['qtr']=qtr
    if rsid_prefix: where.append('rsid_prefix LIKE :rsid_prefix'); params['rsid_prefix']=f"{rsid_prefix}%"
    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
    try:
        sql = f"SELECT COUNT(1) as total_schools, SUM(CASE WHEN access_level='full' THEN 1 ELSE 0 END) as schools_with_access_full, SUM(CASE WHEN access_level='denied' THEN 1 ELSE 0 END) as access_denied_count, SUM(visits_ytd) as visits_ytd_total, SUM(engagements_ytd) as engagements_ytd_total, SUM(leads_ytd) as leads_ytd_total, SUM(contracts_ytd) as contracts_ytd_total FROM school_fact {where_sql}"
        cur.execute(sql, params)
        r = cur.fetchone()
        resp['kpis'] = {
            'total_schools': int(r[0] or 0),
            'schools_with_access_full': int(r[1] or 0),
            'access_denied_count': int(r[2] or 0),
            'visits_ytd_total': int(r[3] or 0),
            'engagements_ytd_total': int(r[4] or 0),
            'leads_ytd_total': int(r[5] or 0),
            'contracts_ytd_total': int(r[6] or 0)
        }

        # at_risk_schools: high enrollment but low engagements/contracts
        ar_sql = f"SELECT school_id, school_name, enrollment, fqma_est, engagements_ytd, contracts_ytd, last_visit_at FROM school_fact {where_sql} ORDER BY (enrollment+COALESCE(fqma_est,0)) DESC LIMIT 200"
        cur.execute(ar_sql, params)
        resp['tables']['at_risk_schools'] = [dict(zip(['school_id','school_name','enrollment','fqma_est','engagements_ytd','contracts_ytd','last_visit_at'], r)) for r in cur.fetchall()]

        # top_opportunity_schools: high enrollment + low penetration
        to_sql = f"SELECT school_id, school_name, enrollment, fqma_est, visits_ytd, engagements_ytd FROM school_fact {where_sql} ORDER BY (fqma_est - COALESCE(engagements_ytd,0)) DESC LIMIT 200"
        cur.execute(to_sql, params)
        resp['tables']['top_opportunity_schools'] = [dict(zip(['school_id','school_name','enrollment','fqma_est','visits_ytd','engagements_ytd'], r)) for r in cur.fetchall()]

        resp['data_as_of'] = _data_as_of_from(conn, 'school_fact')
    except Exception:
        resp['missing_data'].append('schools_query_failed')
    finally:
        try: conn.close()
        except Exception: pass
    return resp


@router.get("/operations/cep/summary")
def cep_summary(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor(); missing = []
    if not _table_exists(conn, 'cep_fact'):
        missing.append('cep_fact')
    resp = {'status':'ok','data_as_of':None,'filters':{'fy':fy,'qtr':qtr,'rsid_prefix':rsid_prefix},'kpis':{},'series':{},'tables':{},'missing_data':missing}
    if missing:
        return resp
    where = []; params={}
    if fy is not None: where.append('fy = :fy'); params['fy']=fy
    if qtr is not None: where.append('qtr = :qtr'); params['qtr']=qtr
    if rsid_prefix: where.append('rsid_prefix LIKE :rsid_prefix'); params['rsid_prefix']=f"{rsid_prefix}%"
    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
    try:
        sql = f"SELECT SUM(asvab_tests) as asvab_tests_total, SUM(cep_events) as cep_events_total, SUM(cep_participants) as participants_total, SUM(leads_from_cep) as leads_from_cep_total, SUM(contracts_from_cep) as contracts_from_cep_total FROM cep_fact {where_sql}"
        cur.execute(sql, params)
        r = cur.fetchone()
        leads = int(r[3] or 0)
        contracts = int(r[4] or 0)
        conv = (contracts / leads) if leads > 0 else None
        resp['kpis'] = {
            'asvab_tests_total': int(r[0] or 0),
            'cep_events_total': int(r[1] or 0),
            'participants_total': int(r[2] or 0),
            'leads_from_cep_total': leads,
            'contracts_from_cep_total': contracts,
            'conversion_rate': conv
        }

        # gap schools
        gap_sql = f"SELECT school_id, SUM(cep_participants) as participants, SUM(asvab_tests) as asvab_tests, SUM(leads_from_cep) as leads, SUM(contracts_from_cep) as contracts FROM cep_fact {where_sql} GROUP BY school_id ORDER BY (COALESCE(SUM(asvab_tests),0)) ASC LIMIT 200"
        cur.execute(gap_sql, params)
        resp['tables']['cep_gap_schools'] = [dict(zip(['school_id','participants','asvab_tests','leads','contracts'], r)) for r in cur.fetchall()]

        resp['data_as_of'] = _data_as_of_from(conn, 'cep_fact')
    except Exception:
        resp['missing_data'].append('cep_query_failed')
    finally:
        try: conn.close()
        except Exception: pass
    return resp


@router.get("/operations/geo/summary")
def geo_summary(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor(); missing = []
    if not _table_exists(conn, 'geo_campaign_fact'):
        missing.append('geo_campaign_fact')
    resp = {'status':'ok','data_as_of':None,'filters':{'fy':fy,'qtr':qtr,'rsid_prefix':rsid_prefix},'kpis':{},'tables':{},'missing_data':missing}
    if missing:
        return resp
    where = []; params={}
    if fy is not None: where.append('fy = :fy'); params['fy']=fy
    if qtr is not None: where.append('qtr = :qtr'); params['qtr']=qtr
    if rsid_prefix: where.append('rsid_prefix LIKE :rsid_prefix'); params['rsid_prefix']=f"{rsid_prefix}%"
    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
    try:
        sql = f"SELECT SUM(spend) as spend_total, SUM(impressions) as impressions_total, SUM(engagements) as engagements_total, SUM(leads) as leads_total, SUM(contracts) as contracts_total FROM geo_campaign_fact {where_sql}"
        cur.execute(sql, params)
        r = cur.fetchone()
        spend = float(r[0] or 0)
        leads = int(r[3] or 0)
        contracts = int(r[4] or 0)
        cpl = (spend / leads) if leads>0 else None
        cpa = (spend / contracts) if contracts>0 else None
        resp['kpis'] = {
            'spend_total': spend,
            'impressions_total': int(r[1] or 0),
            'engagements_total': int(r[2] or 0),
            'leads_total': leads,
            'contracts_total': contracts,
            'cpl': cpl,
            'cpa': cpa
        }
        campaigns_sql = f"SELECT campaign_id, campaign_name, geo_type, area_label, SUM(spend) as spend, SUM(impressions) as impressions, SUM(engagements) as engagements, SUM(leads) as leads, SUM(contracts) as contracts FROM geo_campaign_fact {where_sql} GROUP BY campaign_id, campaign_name, geo_type, area_label ORDER BY spend DESC LIMIT 200"
        cur.execute(campaigns_sql, params)
        resp['tables']['campaigns'] = [dict(zip(['campaign_id','campaign_name','geo_type','area_label','spend','impressions','engagements','leads','contracts'], r)) for r in cur.fetchall()]
        resp['data_as_of'] = _data_as_of_from(conn, 'geo_campaign_fact')
    except Exception:
        resp['missing_data'].append('geo_query_failed')
    finally:
        try: conn.close()
        except Exception: pass
    return resp
