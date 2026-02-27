from fastapi import APIRouter, Depends
from typing import Optional
from .. import db
from .rbac import require_perm

router = APIRouter(prefix='/api/v2/fs-loss', tags=['fs-loss'])


@router.get('/summary')
def fs_loss_summary(unit_rsid: Optional[str] = None, fy: Optional[int] = None, qtr: Optional[str] = None, user: dict = Depends(require_perm('dashboards.view'))):
    """Return a minimal FS loss summary placeholder until Data Hub imports exist."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        # Aggregate by code if table exists, otherwise return empty
        try:
            sql = 'SELECT loss_code, COUNT(1) as count FROM fs_loss_event'
            where = []
            params = []
            if unit_rsid:
                where.append('unit_rsid = ?')
                params.append(unit_rsid)
            if fy:
                where.append("substr(event_date,1,4) = ?")
                params.append(str(fy))
            if qtr:
                # crude qtr filter: translate Q1..Q4 to months
                qmap = {'Q1': ('01','03'), 'Q2':('04','06'), 'Q3':('07','09'), 'Q4':('10','12')}
                if qtr in qmap:
                    start, end = qmap[qtr]
                    where.append("substr(event_date,6,2) BETWEEN ? AND ?")
                    params.extend([start, end])
            if where:
                sql = sql + ' WHERE ' + ' AND '.join(where)
            sql = sql + ' GROUP BY loss_code ORDER BY count DESC'
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            out = [{'loss_code': r['loss_code'] if 'loss_code' in r.keys() else r[0], 'count': r['count'] if 'count' in r.keys() else r[1]} for r in rows]
            return {'status': 'ok', 'summary': out}
        except Exception:
            return {'status': 'ok', 'summary': []}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/codes')
def fs_loss_codes():
    # Return a small static list of loss codes for now
    codes = [
        {'code': 'L01', 'label': 'Medical Disqualification'},
        {'code': 'L02', 'label': 'Failure to Ship'},
        {'code': 'L03', 'label': 'Administrative Separation'},
        {'code': 'L99', 'label': 'Other'}
    ]
    return {'status': 'ok', 'codes': codes}
