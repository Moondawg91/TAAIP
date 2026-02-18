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
