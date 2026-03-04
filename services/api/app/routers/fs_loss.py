from fastapi import APIRouter, Depends
from typing import Optional
from .. import db
from .rbac import require_perm

router = APIRouter(prefix='/v2/fs-loss', tags=['fs-loss'])


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


@router.get('/station/{station_rsid}/dep-loss-by-bucket')
def station_dep_loss_by_bucket(station_rsid: str, time_period: str):
    """Aggregate dep_loss by loss_bucket and component code for a station and time period.

    SQL equivalent:
      select dl.loss_bucket, dl.cmpnt_cd, sum(dl.dep_losses) as dep_losses
      from fact_dep_loss dl
      where dl.station_rsid = ? and dl.time_period = ?
      group by dl.loss_bucket, dl.cmpnt_cd
      order by dl.cmpnt_cd, dl.loss_bucket;
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT loss_bucket, cmpnt_cd, SUM(dep_losses) as dep_losses FROM fact_dep_loss WHERE station_rsid=? AND time_period=? GROUP BY loss_bucket, cmpnt_cd ORDER BY cmpnt_cd, loss_bucket",
                (station_rsid, time_period),
            )
            rows = cur.fetchall()
            out = []
            for r in rows:
                try:
                    lb = r['loss_bucket']
                    cc = r['cmpnt_cd']
                    val = r['dep_losses']
                except Exception:
                    lb, cc, val = r[0], r[1], r[2]
                out.append({'loss_bucket': lb, 'cmpnt_cd': cc, 'dep_losses': val})
            return {'status': 'ok', 'rows': out}
        except Exception:
            return {'status': 'ok', 'rows': []}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/unit/{unit_code}/ancestors')
def unit_ancestors(unit_code: str):
    """Return ancestor chain for a unit using a recursive CTE.

    SQL equivalent:
      with recursive tree as (
        select u.unit_code, u.unit_name, u.echelon, u.parent_code
        from unit u
        where u.unit_code = ?
        union all
        select p.unit_code, p.unit_name, p.echelon, p.parent_code
        from unit p
        join tree t on t.parent_code = p.unit_code
      )
      select * from tree;
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "WITH RECURSIVE tree(unit_code, unit_name, echelon, parent_code) AS (SELECT unit_code, unit_name, echelon, parent_code FROM unit WHERE unit_code = ? UNION ALL SELECT p.unit_code, p.unit_name, p.echelon, p.parent_code FROM unit p JOIN tree t ON t.parent_code = p.unit_code) SELECT unit_code, unit_name, echelon, parent_code FROM tree",
                (unit_code,)
            )
            rows = cur.fetchall()
            out = []
            for r in rows:
                try:
                    out.append({'unit_code': r['unit_code'], 'unit_name': r['unit_name'], 'echelon': r['echelon'], 'parent_code': r['parent_code']})
                except Exception:
                    out.append({'unit_code': r[0], 'unit_name': r[1], 'echelon': r[2], 'parent_code': r[3]})
            return {'status': 'ok', 'tree': out}
        except Exception:
            return {'status': 'ok', 'tree': []}
    finally:
        try:
            conn.close()
        except Exception:
            pass
