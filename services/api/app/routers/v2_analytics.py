from fastapi import APIRouter, Request
from typing import Optional
from datetime import date, datetime
from .. import db
from .. import scope as scope_mod
from .. import org_utils

router = APIRouter(prefix='/v2/analytics', tags=['analytics'])


def _table_exists(conn, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None


def _month_label(yyyymm: str) -> str:
    try:
        dt = datetime.strptime(yyyymm + '-01', '%Y-%m-%d')
        return dt.strftime('%b %Y')
    except Exception:
        return yyyymm


@router.get('/enlistments/bn')
def enlistments_by_bn(request: Request, unit_rsid: Optional[str] = None, fy: Optional[int] = None, qtr_num: Optional[int] = None, rsm_month: Optional[str] = None, rollup: Optional[int] = None):
    params = dict(request.query_params)
    # merge explicit args into params for parse
    if unit_rsid is not None:
        params['unit_rsid'] = unit_rsid
    if fy is not None:
        params['fy'] = str(fy)
    if qtr_num is not None:
        params['qtr_num'] = str(qtr_num)
    if rsm_month is not None:
        params['rsm_month'] = rsm_month
    if rollup is not None:
        params['rollup'] = str(rollup)

    scope = scope_mod.parse_scope_params(params)
    conn = db.connect()
    try:
        cur = conn.cursor()
        # resolve unit list
        rsids = [scope['unit_rsid']]
        # sanitize rsids: ensure non-empty list of valid ids; if none, return empty-safe result
        rsids = [r for r in rsids if r]
        if not rsids:
            return {'applied_scope': scope, 'groups': [], 'events': [], 'total_events': 0}
        if scope.get('rollup'):
            try:
                rsids = org_utils.get_descendant_units(conn, scope['unit_rsid'])
            except Exception:
                rsids = [scope['unit_rsid']]

        sql = 'SELECT bn_name, rsid, SUM(enlistments) as total_enlistments, COUNT(1) as row_count FROM fact_enlistments_bn WHERE rsid IN ({})'
        placeholders = ','.join('?' for _ in rsids)
        sql = sql.format(placeholders)
        params_list = rsids
        # filter by fy/qtr/rsm
        if scope.get('fy') is not None:
            sql += ' AND fy = ?'
            params_list.append(scope['fy'])
        if scope.get('qtr_num') is not None:
            sql += ' AND qtr_num = ?'
            params_list.append(scope['qtr_num'])
        if scope.get('rsm_month') is not None:
            sql += ' AND rsm_month = ?'
            params_list.append(scope['rsm_month'])

        sql += ' GROUP BY bn_name, rsid ORDER BY total_enlistments DESC'
        cur.execute(sql, params_list)
        rows = [dict(r) for r in cur.fetchall()]
        return {'applied_scope': scope, 'rows': rows, 'total_rows': len(rows)}
    finally:
        conn.close()


@router.get('/emm/events')
def emm_events(request: Request, unit_rsid: Optional[str] = None, fy: Optional[int] = None, qtr_num: Optional[int] = None, rsm_month: Optional[str] = None, rollup: Optional[int] = None, limit: int = 100):
    params = dict(request.query_params)
    if unit_rsid is not None:
        params['unit_rsid'] = unit_rsid
    if fy is not None:
        params['fy'] = str(fy)
    if qtr_num is not None:
        params['qtr_num'] = str(qtr_num)
    if rsm_month is not None:
        params['rsm_month'] = rsm_month
    if rollup is not None:
        params['rollup'] = str(rollup)

    scope = scope_mod.parse_scope_params(params)
    conn = db.connect()
    try:
        cur = conn.cursor()
        # Resolve rsids list; allow rollup expansion but do it safely.
        rsids = [scope['unit_rsid']]
        if scope.get('rollup'):
            try:
                # Resolve descendants using an explicit recursive CTE here
                try:
                    cur2 = conn.cursor()
                    cur2.execute('SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE LIMIT 1', (scope['unit_rsid'],))
                    r = cur2.fetchone()
                    if r and (r[0] is not None or (isinstance(r, dict) and r.get('id') is not None)):
                        oid = r[0] if not isinstance(r, dict) else r.get('id')
                        cte = '''WITH RECURSIVE subs(id, rsid, depth) AS (
                            SELECT id, rsid, 0 FROM org_unit WHERE id = ?
                            UNION ALL
                            SELECT o.id, o.rsid, subs.depth+1 FROM org_unit o JOIN subs ON o.parent_id = subs.id WHERE subs.depth < 50
                        ) SELECT rsid FROM subs WHERE rsid IS NOT NULL;'''
                        cur2.execute(cte, (oid,))
                        fetched = cur2.fetchall()
                        expanded = []
                        for row in fetched:
                            try:
                                expanded.append(row['rsid'])
                            except Exception:
                                try:
                                    expanded.append(row[0])
                                except Exception:
                                    pass
                        if expanded:
                            rsids = expanded
                except Exception:
                    rsids = [scope['unit_rsid']]
            except Exception:
                rsids = [scope['unit_rsid']]

        # Instrumentation for debugging rollup inclusion
        try:
            print('EMM_DEBUG: requested_unit_rsid=', scope.get('unit_rsid'))
            # resolve org_unit id for debugging
            try:
                cur.execute('SELECT id FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (scope.get('unit_rsid'), str(scope.get('unit_rsid')).upper()))
                found = cur.fetchone()
                print('EMM_DEBUG: resolved_org_unit_row=', dict(found) if found else None)
            except Exception as _:
                print('EMM_DEBUG: resolved_org_unit_row=ERROR')
            print('EMM_DEBUG: expanded_rsids_count=', len(rsids), 'expanded_rsids=', rsids)
        except Exception:
            pass

        # Create a temporary table to hold rsids and join against it. This
        # avoids sqlite placeholder binding mismatches when the rsid list is
        # large or dynamically generated.
        try:
            cur.execute('CREATE TEMP TABLE IF NOT EXISTS tmp_rsids (rsid TEXT)')
            cur.execute('DELETE FROM tmp_rsids')
            for r in rsids:
                cur.execute('INSERT INTO tmp_rsids(rsid) VALUES (?)', (r,))
            # log contents of tmp_rsids
            try:
                cur.execute('SELECT COUNT(1) as c FROM tmp_rsids')
                cc = cur.fetchone()
                print('EMM_DEBUG: tmp_rsids_count=', dict(cc) if cc else None)
                cur.execute('SELECT rsid FROM tmp_rsids')
                allr = [row[0] for row in cur.fetchall()]
                print('EMM_DEBUG: tmp_rsids_rows=', allr)
            except Exception:
                print('EMM_DEBUG: tmp_rsids_inspect_failed')
        except Exception:
            # fallback: if temp table operations fail, ensure rsids is non-empty
            if not rsids:
                return {'applied_scope': scope, 'groups': [], 'events': [], 'total_events': 0}

        # aggregated groups
        sql = "SELECT mac, activity_type, activity_status, COUNT(1) as cnt FROM fact_emm_activity WHERE rsid IN (SELECT rsid FROM tmp_rsids)"
        params_list = []
        if scope.get('fy') is not None:
            sql += ' AND fy = ?'
            params_list.append(scope['fy'])
        if scope.get('qtr_num') is not None:
            sql += ' AND qtr_num = ?'
            params_list.append(scope['qtr_num'])
        if scope.get('rsm_month') is not None:
            sql += ' AND rsm_month = ?'
            params_list.append(scope['rsm_month'])
        sql += ' GROUP BY mac, activity_type, activity_status ORDER BY cnt DESC'
        # For debugging: show matched rows before aggregation
        try:
            debug_sql = "SELECT activity_id, rsid, title, begin_date FROM fact_emm_activity WHERE rsid IN (SELECT rsid FROM tmp_rsids)"
            cur.execute(debug_sql)
            dbg = cur.fetchall()
            print('EMM_DEBUG: matched_rows_before_agg_count=', len(dbg))
            for r in dbg[:20]:
                print('EMM_DEBUG: matched_row=', tuple(r))
        except Exception:
            print('EMM_DEBUG: matched_rows_before_agg_failed')
        cur.execute(sql, params_list)
        groups = [dict(r) for r in cur.fetchall()]

        # event list (limited)
        sql2 = "SELECT activity_id, rsid, unit_name, mac, title, activity_type, activity_status, begin_date, end_date FROM fact_emm_activity WHERE rsid IN (SELECT rsid FROM tmp_rsids)"
        params2 = []
        if scope.get('fy') is not None:
            sql2 += ' AND fy = ?'
            params2.append(scope['fy'])
        if scope.get('qtr_num') is not None:
            sql2 += ' AND qtr_num = ?'
            params2.append(scope['qtr_num'])
        if scope.get('rsm_month') is not None:
            sql2 += ' AND rsm_month = ?'
            params2.append(scope['rsm_month'])
        sql2 += ' ORDER BY begin_date DESC LIMIT ?'
        params2.append(limit)
        cur.execute(sql2, params2)
        events = [dict(r) for r in cur.fetchall()]
        return {'applied_scope': scope, 'groups': groups, 'events': events, 'total_events': len(events)}
    finally:
        conn.close()


@router.get('/cbsa')
def analytics_cbsa(limit: int = 10, cbsa: Optional[str] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()
        rows = []

        if _table_exists(conn, 'market_cbsa_metrics'):
            sql = '''
                SELECT
                  cbsa_code,
                  COALESCE(cbsa_name, cbsa_code) as cbsa_name,
                  COALESCE(MAX(total_potential), 0) as lead_count,
                  COALESCE(MAX(p2p_value), 0) as avg_score,
                  COALESCE(MAX(contracts_total), 0) as high_quality_count,
                  COALESCE(MAX(army_share_of_potential), 0) as market_share,
                  COALESCE(MAX(potential_remaining), 0) as conversion_potential
                FROM market_cbsa_metrics
                WHERE (? IS NULL OR cbsa_code = ?)
                GROUP BY cbsa_code, cbsa_name
                ORDER BY lead_count DESC
                LIMIT ?
            '''
            cur.execute(sql, (cbsa, cbsa, max(1, limit)))
            rows = [dict(r) for r in cur.fetchall()]
        elif _table_exists(conn, 'mi_cbsa_fact'):
            sql = '''
                SELECT
                  cbsa_code,
                  COALESCE(cbsa_name, cbsa_code) as cbsa_name,
                  COALESCE(SUM(dod_potential), 0) as lead_count,
                  COALESCE(AVG(p2p), 0) as avg_score,
                  COALESCE(SUM(COALESCE(contracts_ga,0)+COALESCE(contracts_sa,0)+COALESCE(contracts_vol,0)), 0) as high_quality_count,
                  COALESCE(AVG(army_share_of_potential), 0) as market_share,
                  COALESCE(SUM(potential_remaining), 0) as conversion_potential
                FROM mi_cbsa_fact
                WHERE (? IS NULL OR cbsa_code = ?)
                GROUP BY cbsa_code, cbsa_name
                ORDER BY lead_count DESC
                LIMIT ?
            '''
            cur.execute(sql, (cbsa, cbsa, max(1, limit)))
            rows = [dict(r) for r in cur.fetchall()]

        return {'status': 'ok', 'cbsas': rows}
    finally:
        conn.close()


@router.get('/schools')
def analytics_schools(limit: int = 15, rsid: Optional[str] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()

        if _table_exists(conn, 'school_fact'):
            sql = '''
                SELECT
                  sf.school_name as name,
                  COALESCE(s.city, '') as city,
                  COALESCE(sf.school_type, s.school_type, 'Unknown') as type,
                  COALESCE(SUM(sf.leads_ytd), 0) as leads,
                  COALESCE(SUM(sf.contracts_ytd), 0) as conversions,
                  COALESCE(SUM(sf.visits_ytd), 0) as events,
                  CASE
                    WHEN COALESCE(SUM(sf.contracts_ytd),0) >= 10 THEN 'high'
                    WHEN COALESCE(SUM(sf.contracts_ytd),0) >= 3 THEN 'medium'
                    ELSE 'low'
                  END as priority,
                  CASE WHEN COALESCE(SUM(sf.leads_ytd),0) > 0
                    THEN ROUND((SUM(sf.contracts_ytd) * 100.0) / SUM(sf.leads_ytd), 2)
                    ELSE 0
                  END as conversion_rate,
                  0 as cost_per_lead
                FROM school_fact sf
                LEFT JOIN schools s ON s.id = sf.school_id
                WHERE (? IS NULL OR sf.rsid_prefix = ?)
                GROUP BY sf.school_name, COALESCE(s.city, ''), COALESCE(sf.school_type, s.school_type, 'Unknown')
                ORDER BY leads DESC
                LIMIT ?
            '''
            cur.execute(sql, (rsid, rsid, max(1, limit)))
            return {'status': 'ok', 'schools': [dict(r) for r in cur.fetchall()]}

        if _table_exists(conn, 'schools'):
            sql = '''
                SELECT
                  school_name as name,
                  COALESCE(city, '') as city,
                  COALESCE(school_type, 'Unknown') as type,
                  0 as leads,
                  0 as conversions,
                  0 as events,
                  'low' as priority,
                  0 as conversion_rate,
                  0 as cost_per_lead
                FROM schools
                ORDER BY school_name ASC
                LIMIT ?
            '''
            cur.execute(sql, (max(1, limit),))
            return {'status': 'ok', 'schools': [dict(r) for r in cur.fetchall()]}

        return {'status': 'ok', 'schools': []}
    finally:
        conn.close()


@router.get('/segments')
def analytics_segments(rsid: Optional[str] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()
        rows = []

        if _table_exists(conn, 'mi_cbsa_fact'):
            sql = '''
                SELECT
                  COALESCE(market_category, 'unknown') as segment_name,
                  COALESCE(SUM(dod_potential), 0) as size,
                  COALESCE(SUM(army_potential), 0) as leads_generated,
                  COALESCE(SUM(COALESCE(contracts_ga,0)+COALESCE(contracts_sa,0)+COALESCE(contracts_vol,0)), 0) as conversions,
                  COALESCE(SUM(potential_remaining), 0) as remaining_potential,
                  COALESCE(AVG(p2p), 0) as avg_propensity
                FROM mi_cbsa_fact
                WHERE (? IS NULL OR rsid_prefix = ?)
                GROUP BY COALESCE(market_category, 'unknown')
                ORDER BY remaining_potential DESC
            '''
            cur.execute(sql, (rsid, rsid))
            rows = [dict(r) for r in cur.fetchall()]

        segments = []
        for r in rows:
            name = str(r.get('segment_name') or 'unknown')
            size = float(r.get('size') or 0)
            leads = float(r.get('leads_generated') or 0)
            conversions = float(r.get('conversions') or 0)
            remaining = float(r.get('remaining_potential') or 0)
            penetration = round((leads * 100.0 / size), 2) if size > 0 else 0
            conversion_rate = round((conversions * 100.0 / leads), 2) if leads > 0 else 0
            if remaining >= 1000:
                priority = 'high'
            elif remaining >= 250:
                priority = 'medium'
            else:
                priority = 'low'

            segments.append({
                'segment_name': name.replace('_', ' ').title(),
                'segment_code': name.upper().replace(' ', '_'),
                'size': int(size),
                'leads_generated': int(leads),
                'penetration_rate': penetration,
                'avg_propensity': float(r.get('avg_propensity') or 0),
                'conversions': int(conversions),
                'priority': priority,
                'remaining_potential': int(remaining),
                'conversion_rate': conversion_rate,
            })

        return {'status': 'ok', 'segments': segments}
    finally:
        conn.close()


@router.get('/contracts')
def analytics_contracts(fy: Optional[int] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()
        today = date.today()
        target_fy = fy or (today.year + (1 if today.month >= 10 else 0))

        mission_goal = 0
        if _table_exists(conn, 'mission_target'):
            cur.execute('SELECT COALESCE(SUM(annual_contract_mission),0) as mission_goal FROM mission_target WHERE fy = ?', (target_fy,))
            row = cur.fetchone()
            mission_goal = int((row['mission_goal'] if row else 0) or 0)

        contracts_achieved = 0
        by_month = []
        by_component = []
        if _table_exists(conn, 'fact_production'):
            cur.execute('''
                SELECT COALESCE(SUM(metric_value),0) as total
                FROM fact_production
                WHERE fy = ? AND lower(metric_key) IN ('contracts','contract','net_contracts')
            ''', (target_fy,))
            row = cur.fetchone()
            contracts_achieved = int((row['total'] if row else 0) or 0)

            cur.execute('''
                SELECT substr(date_key,1,7) as month_key,
                       COALESCE(SUM(CASE WHEN lower(metric_key) IN ('contracts','contract','net_contracts') THEN metric_value ELSE 0 END),0) as achieved
                FROM fact_production
                WHERE fy = ?
                GROUP BY substr(date_key,1,7)
                ORDER BY month_key
                LIMIT 12
            ''', (target_fy,))
            month_rows = [dict(r) for r in cur.fetchall()]

            monthly_goal = int(round(mission_goal / 12.0)) if mission_goal else 0
            by_month = [
                {
                    'month': _month_label(str(r.get('month_key') or '')),
                    'goal': monthly_goal,
                    'achieved': int(r.get('achieved') or 0),
                    'variance': int((r.get('achieved') or 0) - monthly_goal),
                }
                for r in month_rows
            ]

            cur.execute('''
                SELECT
                  COALESCE(NULLIF(scope_value,''), NULLIF(scope_type,''), 'USAREC') as component,
                  COALESCE(SUM(CASE WHEN lower(metric_key) IN ('contracts','contract','net_contracts') THEN metric_value ELSE 0 END),0) as achieved
                FROM fact_production
                WHERE fy = ?
                GROUP BY COALESCE(NULLIF(scope_value,''), NULLIF(scope_type,''), 'USAREC')
                ORDER BY achieved DESC
                LIMIT 8
            ''', (target_fy,))
            comp_rows = [dict(r) for r in cur.fetchall()]
            component_goal = int(round(mission_goal / len(comp_rows))) if mission_goal and comp_rows else 0
            by_component = [
                {
                    'component': str(r.get('component') or 'USAREC'),
                    'goal': component_goal,
                    'achieved': int(r.get('achieved') or 0),
                    'percent': round((int(r.get('achieved') or 0) * 100.0 / component_goal), 1) if component_goal > 0 else 0,
                }
                for r in comp_rows
            ]

        if mission_goal <= 0:
            mission_goal = max(contracts_achieved, 1)

        remaining = max(mission_goal - contracts_achieved, 0)
        percent_complete = round((contracts_achieved * 100.0 / mission_goal), 1) if mission_goal > 0 else 0

        fy_end = date(target_fy, 9, 30)
        days_remaining = max((fy_end - today).days, 0)
        elapsed_days = max(365 - days_remaining, 1)
        daily_rate_needed = round((remaining / days_remaining), 2) if days_remaining > 0 else 0
        current_daily_rate = round((contracts_achieved / elapsed_days), 2)

        return {
            'status': 'ok',
            'metrics': {
                'fiscal_year': target_fy,
                'mission_goal': mission_goal,
                'contracts_achieved': contracts_achieved,
                'remaining': remaining,
                'percent_complete': percent_complete,
                'days_remaining': days_remaining,
                'daily_rate_needed': daily_rate_needed,
                'current_daily_rate': current_daily_rate,
                'on_track': current_daily_rate >= daily_rate_needed if daily_rate_needed > 0 else True,
                'by_month': by_month,
                'by_component': by_component,
            }
        }
    finally:
        conn.close()
