from fastapi import APIRouter, Request, HTTPException
from typing import Any, Dict, List
from ..db import connect

router = APIRouter(prefix="/budget", tags=["budget"])


def _safe_sum(cur, sql, params=()):
    try:
        cur.execute(sql, params)
        r = cur.fetchone()
        if not r:
            return 0.0
        val = list(r.values())[0] if hasattr(r, 'values') else (r[0] if isinstance(r, (list, tuple)) else r)
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


@router.get('/comptroller/ledger')
def comptroller_ledger(fy: int = None, org_unit_id: int = None, funding_source: str = None) -> Dict[str, Any]:
    conn = connect()
    try:
        cur = conn.cursor()

        totals = {'allocated': 0.0, 'obligated': 0.0, 'executed': 0.0, 'remaining': 0.0}
        rows: List[Dict[str, Any]] = []

        # Allocate per funding account (funding_source)
        try:
            sql = "SELECT COALESCE(bli.funding_source,'unassigned') as account, SUM(COALESCE(bli.amount,0)) as allocated FROM budget_line_item bli LEFT JOIN fy_budget fb ON fb.id = bli.fy_budget_id WHERE 1=1"
            params = []
            if fy is not None:
                sql += ' AND fb.fy=?'; params.append(fy)
            if org_unit_id is not None:
                sql += ' AND fb.org_unit_id=?'; params.append(org_unit_id)
            if funding_source is not None:
                sql += ' AND bli.funding_source=?'; params.append(funding_source)
            sql += ' GROUP BY bli.funding_source'
            cur.execute(sql, tuple(params))
            for r in cur.fetchall():
                acct = r.get('account') or 'unassigned'
                alloc = float(r.get('allocated') or 0)
                # obligated: approximate via budget_line_item.status
                cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM budget_line_item WHERE funding_source=? AND (status IN ("committed","obligated") OR status IS NOT NULL)', (acct,))
                ro = cur.fetchone(); ob = float(ro['s']) if ro and ro['s'] is not None else 0.0
                # executed from expenses
                cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses WHERE funding_source=?', (acct,))
                rx = cur.fetchone(); ex = float(rx['s']) if rx and rx['s'] is not None else 0.0
                rem = alloc - ob - ex
                totals['allocated'] += alloc
                totals['obligated'] += ob
                totals['executed'] += ex
                rows.append({'account': acct, 'allocated': round(alloc,2), 'obligated': round(ob,2), 'executed': round(ex,2), 'remaining': round(rem,2)})
        except Exception:
            # if grouping fails, return empty ledger
            rows = []

        totals['remaining'] = round(totals['allocated'] - totals['obligated'] - totals['executed'], 2)
        totals['allocated'] = round(totals['allocated'], 2)
        totals['obligated'] = round(totals['obligated'], 2)
        totals['executed'] = round(totals['executed'], 2)

        return {'totals': totals, 'rows': rows}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/comptroller/ledger/export.csv')
def comptroller_ledger_export(fy: int = None, org_unit_id: int = None, funding_source: str = None):
    import csv, io
    data = comptroller_ledger(fy=fy, org_unit_id=org_unit_id, funding_source=funding_source)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['account','allocated','obligated','executed','remaining'])
    for r in data.get('rows', []):
        w.writerow([r.get('account'), r.get('allocated'), r.get('obligated'), r.get('executed'), r.get('remaining')])
    from fastapi.responses import Response
    return Response(content=buf.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="comptroller_ledger.csv"'})
