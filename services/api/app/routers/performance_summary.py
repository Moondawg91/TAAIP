from fastapi import APIRouter
from ..db import connect, row_to_dict

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get('/mission-assessment')
def mission_assessment_summary():
    conn = connect()
    try:
        cur = conn.cursor()
        # return latest mission assessment snapshot and a tiny comparison rollup
        cur.execute("SELECT * FROM mission_assessments ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        latest = row_to_dict(cur, row) if row else {}

        # simple KPIs: sum of production metrics for most recent date_key
        kpis = {}
        try:
            cur.execute('SELECT date_key, SUM(metric_value) as total FROM fact_production GROUP BY date_key ORDER BY date_key DESC LIMIT 1')
            r = cur.fetchone()
            kpis['latest_date'] = r['date_key'] if r and 'date_key' in r else None
            kpis['latest_total'] = float(r['total']) if r and r['total'] is not None else 0.0
        except Exception:
            kpis['latest_date'] = None
            kpis['latest_total'] = 0.0

        return {'latest_assessment': latest, 'kpis': kpis}
    finally:
        try:
            conn.close()
        except Exception:
            pass
