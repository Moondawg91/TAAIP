from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from .. import db
from .. import scope as scope_mod
from .. import org_utils

router = APIRouter(prefix='/v2/analytics', tags=['analytics'])


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
