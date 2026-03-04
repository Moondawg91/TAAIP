from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import date

from .. import db

router = APIRouter(prefix='/v2/station/dashboard', tags=['Station'])


def _current_rsm_month() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"


@router.get('/dep-loss')
def station_dep_loss(station_rsid: str = Query(...), period_key: str = Query('CURRENT_MONTH'), rsm_month: Optional[str] = None, fy: Optional[int] = None, qtr_num: Optional[int] = None):
    period_key = (period_key or 'CURRENT_MONTH').upper()
    if period_key == 'CURRENT_MONTH' and not rsm_month:
        rsm_month = _current_rsm_month()

    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, rsid, name, type, parent_id FROM org_unit WHERE rsid=? LIMIT 1', (station_rsid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='station not found')

        station = {'unit_rsid': row['rsid'], 'name': row['name'], 'type': row['type']}
        # build parents chain
        parents = []
        pid = row['parent_id']
        while pid:
            cur.execute('SELECT id, rsid, name, type, parent_id FROM org_unit WHERE id=? LIMIT 1', (pid,))
            prow = cur.fetchone()
            if not prow:
                break
            parents.append({'echelon': prow['type'], 'unit_rsid': prow['rsid'], 'name': prow['name']})
            pid = prow['parent_id']

        # aggregation filters
        filters = ['station_rsid=?', 'period_key=?']
        params = [station_rsid, period_key]
        if period_key == 'CURRENT_MONTH':
            filters.append('rsm_month=?')
            params.append(rsm_month)

        where_clause = ' AND '.join(filters)

        # totals by component
        cur.execute(f"SELECT cmpnt_cd, SUM(loss_count) as total FROM fact_station_dep_loss WHERE {where_clause} GROUP BY cmpnt_cd", tuple(params))
        totals = {}
        total_all = 0
        for r in cur.fetchall():
            c = r['cmpnt_cd']
            v = r['total'] or 0
            totals[c] = v
            total_all += v
        totals['ALL'] = total_all

        # by loss_code
        cur.execute(f"SELECT loss_code, cmpnt_cd, SUM(loss_count) as total FROM fact_station_dep_loss WHERE {where_clause} GROUP BY loss_code, cmpnt_cd ORDER BY loss_code", tuple(params))
        rows = cur.fetchall()
        by_map = {}
        for r in rows:
            lc = r['loss_code']
            cc = r['cmpnt_cd']
            v = r['total'] or 0
            if lc not in by_map:
                by_map[lc] = {'loss_code': lc}
            by_map[lc][cc] = v
            by_map[lc]['ALL'] = by_map[lc].get('ALL', 0) + v

        by_loss_code = list(by_map.values())

        applied_scope = {'station_rsid': station_rsid, 'period_key': period_key, 'rsm_month': rsm_month, 'fy': fy, 'qtr_num': qtr_num}

        return {'applied_scope': applied_scope, 'station': {'unit_rsid': station['unit_rsid'], 'name': station.get('name'), 'parents': parents}, 'totals': totals, 'by_loss_code': by_loss_code}
    finally:
        try:
            conn.close()
        except Exception:
            pass
