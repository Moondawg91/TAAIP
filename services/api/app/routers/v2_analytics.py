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
        rsids = [scope['unit_rsid']]
        if scope.get('rollup'):
            try:
                rsids = org_utils.get_descendant_units(conn, scope['unit_rsid'])
            except Exception:
                rsids = [scope['unit_rsid']]

        placeholders = ','.join('?' for _ in rsids)
        sql = f"SELECT mac, activity_type, activity_status, COUNT(1) as cnt FROM fact_emm_activity WHERE rsid IN ({placeholders})"
        params_list = rsids
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
        cur.execute(sql, params_list)
        groups = [dict(r) for r in cur.fetchall()]

        # event list (limited)
        sql2 = f"SELECT activity_id, rsid, unit_name, mac, title, activity_type, activity_status, begin_date, end_date FROM fact_emm_activity WHERE rsid IN ({placeholders})"
        params2 = list(rsids)
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
