from fastapi import APIRouter, Header, HTTPException
from ..db import connect
from io import StringIO
import csv
import os

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/activities.csv")
def export_activities(x_api_key: str = Header(None)):
    token = os.environ.get("EXPORT_API_TOKEN", "devtoken123")
    if x_api_key != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT activity_id,event_id,activity_type,campaign_name,channel,impressions,engagement_count,awareness_metric,activation_conversions,cost FROM marketing_activities")
        rows = cur.fetchall()
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(["activity_id", "event_id", "activity_type", "campaign_name", "channel", "impressions", "engagement_count", "awareness_metric", "activation_conversions", "cost"])
        for r in rows:
            writer.writerow(list(r))
        return (sio.getvalue(), 200, {"Content-Type": "text/csv"})
    finally:
        conn.close()


@router.get("/facts/metric")
def export_fact_metric():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, metric_key, metric_value, unit, org_unit_id, recorded_at, source, import_job_id FROM fact_metric")
        rows = cur.fetchall()
        return {"rows": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.get('/dashboard')
def export_dashboard(type: str = None, format: str = 'csv', fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit_value: str = None, funding_line: str = None):
    """Export tactical/dashboard data as CSV or JSON. type=events-roi|marketing|funnel|budget"""
    conn = connect()
    try:
        cur = conn.cursor()
        filters = {'fy': fy, 'qtr': qtr, 'month': month, 'echelon_type': echelon_type, 'unit_value': unit_value, 'funding_line': funding_line}
        if type == 'events-roi':
            # reuse simple query: list events with costs and marketing sums
            cur.execute("SELECT id, COALESCE(name,''), COALESCE(planned_cost,0), COALESCE(actual_cost,0), start_dt, end_dt FROM event ORDER BY start_dt DESC LIMIT 100")
            rows = cur.fetchall()
            items = []
            for r in rows:
                eid = str(r[0])
                cur.execute('SELECT COALESCE(SUM(cost),0) FROM marketing_activities WHERE event_id=?', (eid,))
                mcost = (cur.fetchone() or [0])[0] or 0
                items.append({'event_id': eid, 'name': r[1], 'planned_cost': r[2] or 0, 'actual_cost': r[3] or 0, 'marketing_cost': mcost, 'start_date': r[4], 'end_date': r[5]})
            if format == 'json':
                return {'status': 'ok', 'items': items, 'filters': filters}
            # csv
            import csv, io
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(['event_id','name','planned_cost','actual_cost','marketing_cost','start_date','end_date'])
            for it in items:
                w.writerow([it['event_id'], it['name'], it['planned_cost'], it['actual_cost'], it['marketing_cost'], it.get('start_date'), it.get('end_date')])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'marketing':
            cur.execute('SELECT channel, COALESCE(SUM(cost),0) as cost, COALESCE(SUM(impressions),0) as impressions, COALESCE(SUM(activation_conversions),0) as activations FROM marketing_activities GROUP BY channel')
            rows = cur.fetchall()
            items = [{'channel': r[0], 'cost': r[1], 'impressions': r[2], 'activations': r[3]} for r in rows]
            if format == 'json':
                return {'status':'ok','by_channel': items, 'filters': filters}
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['channel','cost','impressions','activations'])
            for it in items:
                w.writerow([it['channel'], it['cost'], it['impressions'], it['activations']])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'funnel':
            cur.execute('SELECT from_stage, to_stage, COUNT(1) as cnt FROM funnel_transitions GROUP BY from_stage, to_stage')
            rows = cur.fetchall()
            items = [{'from_stage': r[0], 'to_stage': r[1], 'count': r[2]} for r in rows]
            if format == 'json':
                return {'status':'ok','conversions': items, 'filters': filters}
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['from_stage','to_stage','count'])
            for it in items:
                w.writerow([it['from_stage'], it['to_stage'], it['count']])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'budget':
            # delegate to budget dashboard router function if available
            try:
                from .budget_dashboard import budget_dashboard
                data = budget_dashboard(None, fy=fy, qtr=qtr, org_unit_id=None, station_id=None, funding_line=funding_line, funding_source=None, eor_code=None)
            except Exception:
                data = {'status':'ok','totals':{},'by_funding_source':[], 'by_event':[], 'filters': filters}
            if format == 'json':
                return data
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            # write kpis
            kpis = data.get('kpis') or {}
            w.writerow(['metric','value'])
            for k,v in kpis.items():
                w.writerow([k,v])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        # unknown type
        return {'status':'error','message':'unknown export type'}
    finally:
        try:
            conn.close()
        except Exception:
            pass
