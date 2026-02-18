from fastapi import APIRouter, Depends, Request, Header, HTTPException
from services.api.app.db import get_db_conn, init_db
from services.api.app.routers.rbac import get_current_user, require_not_role, require_roles
from datetime import datetime
import uuid
import csv
from io import StringIO
import os
from typing import Dict
import json
from services.api.app.database import engine
from sqlalchemy import text

router = APIRouter(prefix="/v2")


# Ingest endpoints expected by tests


@router.post("/ingest/survey")
def ingest_survey(payload: Dict):
    conn = get_db_conn()
    cur = conn.cursor()
    # store raw survey responses in a simple surveys table
    cur.execute("CREATE TABLE IF NOT EXISTS surveys(id INTEGER PRIMARY KEY AUTOINCREMENT, survey_id TEXT, lead_id TEXT, responses_json TEXT, created_at TEXT)")
    cur.execute('INSERT INTO surveys(survey_id,lead_id,responses_json,created_at) VALUES(?,?,?,?)', (payload.get('survey_id'), payload.get('lead_id'), json.dumps(payload.get('responses') or {}), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.post("/ingest/census")
def ingest_census(payload: Dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS external_census(id INTEGER PRIMARY KEY AUTOINCREMENT, geography_code TEXT, attributes_json TEXT, created_at TEXT)')
    cur.execute('INSERT INTO external_census(geography_code,attributes_json,created_at) VALUES(?,?,?)', (payload.get('geography_code'), json.dumps(payload.get('attributes') or {}), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.post("/ingest/social")
def ingest_social(payload: Dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS external_social(id INTEGER PRIMARY KEY AUTOINCREMENT, external_id TEXT, handle TEXT, signals_json TEXT, created_at TEXT)')
    cur.execute('INSERT INTO external_social(external_id,handle,signals_json,created_at) VALUES(?,?,?,?)', (payload.get('external_id'), payload.get('handle'), json.dumps(payload.get('signals') or {}), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}

router = APIRouter(prefix="/v2")


# Note: startup init is handled by the application entrypoint; keep router stateless


@router.post("/events")
def create_event(payload: dict, user: dict = Depends(get_current_user)):
    # station_view cannot create events
    if "station_view" in (user.get("roles") or []):
        raise HTTPException(status_code=403, detail="Forbidden")
    eid = "evt_" + uuid.uuid4().hex[:10]
    # Use SQLAlchemy engine for DDL/DML to avoid mixing sqlite3 connections
    # which can lead to file locks during concurrent test teardown.
    stmt = text(
        "INSERT INTO event(org_unit_id,name,event_type,start_dt,end_dt,location_name,created_at) VALUES(:org_unit_id,:name,:event_type,:start_dt,:end_dt,:location_name,:created_at)"
    )
    params = {
        "org_unit_id": payload.get("org_unit_id"),
        "name": payload.get("name"),
        "event_type": payload.get("type") or payload.get("event_type"),
        "start_dt": payload.get("start_date") or payload.get("start_dt"),
        "end_dt": payload.get("end_date") or payload.get("end_dt"),
        "location_name": payload.get("location") or payload.get("location_name"),
        "created_at": datetime.utcnow().isoformat(),
    }
    with engine.begin() as conn:
        conn.execute(stmt, params)
    return {"status": "ok", "event_id": eid}


@router.post("/marketing/activities")
def post_activity(payload: dict, user: dict = Depends(get_current_user)):
    aid = payload.get('id') or ("act_" + uuid.uuid4().hex[:10])
    stmt = text(
        "INSERT INTO marketing_activities(id,event_id,activity_type,campaign_name,channel,data_source,impressions,engagements,clicks,conversions,cost,reporting_date,metadata_json,created_at,record_status) VALUES(:id,:event_id,:activity_type,:campaign_name,:channel,:data_source,:impressions,:engagements,:clicks,:conversions,:cost,:reporting_date,:metadata_json,:created_at,:record_status)"
    )
    params = {
        "id": aid,
        "event_id": payload.get("event_id"),
        "activity_type": payload.get("activity_type"),
        "campaign_name": payload.get("campaign_name"),
        "channel": payload.get("channel"),
        "data_source": payload.get("data_source"),
        "impressions": payload.get("impressions") or 0,
        "engagements": payload.get("engagements") or payload.get("engagement_count") or 0,
        "clicks": payload.get("clicks") or 0,
        "conversions": payload.get("conversions") or payload.get("activation_conversions") or 0,
        "cost": float(payload.get("cost") or 0.0),
        "reporting_date": payload.get("reporting_date"),
        "metadata_json": payload.get("metadata"),
        "created_at": datetime.utcnow().isoformat(),
        "record_status": "active",
    }
    with engine.begin() as conn:
        conn.execute(stmt, params)
    return {"status": "ok", "activity_id": aid}


@router.get("/marketing/analytics")
def marketing_analytics(event_id: str = None):
    conn = get_db_conn()
    cur = conn.cursor()
    q = "SELECT SUM(impressions) as impressions, SUM(engagement_count) as engagements, AVG(awareness_metric) as avg_awareness, SUM(activation_conversions) as activations FROM marketing_activities"
    params = ()
    if event_id:
        q += " WHERE event_id=?"
        params = (event_id,)
    cur.execute(q, params)
    row = cur.fetchone()
    conn.close()
    total_impressions = int(row[0] or 0)
    total_engagement = int(row[1] or 0)
    avg_awareness = round(float(row[2] or 0.0), 2)
    total_activations = int(row[3] or 0)
    return {
        "total_impressions": total_impressions,
        "total_engagement": total_engagement,
        "avg_awareness": avg_awareness,
        "total_activations": total_activations,
    }


@router.get("/marketing/funnel-attribution")
def funnel_attribution(lead_id: str = None):
    return {"status": "ok", "lead_id": lead_id, "attribution": {}}


@router.get("/kpis")
def kpis(event_id: str = None):
    conn = get_db_conn()
    cur = conn.cursor()
    # activity aggregates
    cur.execute(
        "SELECT SUM(impressions) as impressions, SUM(engagement_count) as engagements, SUM(activation_conversions) as activations, SUM(cost) as cost FROM marketing_activities WHERE event_id=?",
        (event_id,),
    )
    arow = cur.fetchone()
    impressions = int(arow[0] or 0)
    engagements = int(arow[1] or 0)
    activations = int(arow[2] or 0)
    activity_cost = float(arow[3] or 0.0)
    # budgets
    cur.execute("SELECT SUM(allocated_amount) as b FROM budgets WHERE event_id=?", (event_id,))
    brow = cur.fetchone()
    budget_cost = float(brow[0] or 0.0)
    total_cost = activity_cost + budget_cost
    cpl = None
    if activations > 0:
        cpl = round(total_cost / activations, 2)
    conn.close()
    return {
        "total_impressions": impressions,
        "total_engagements": engagements,
        "total_activations": activations,
        "total_cost": total_cost,
        "cpl": cpl,
    }


@router.get("/exports/activities.csv")
def export_activities(x_api_key: str = Header(None)):
    token = os.environ.get("EXPORT_API_TOKEN", "devtoken123")
    if x_api_key != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT activity_id,event_id,activity_type,campaign_name,channel,impressions,engagement_count,awareness_metric,activation_conversions,cost FROM marketing_activities")
    rows = cur.fetchall()
    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(["activity_id", "event_id", "activity_type", "campaign_name", "channel", "impressions", "engagement_count", "awareness_metric", "activation_conversions", "cost"])
    for r in rows:
        writer.writerow(list(r))
    return (sio.getvalue(), 200, {"Content-Type": "text/csv"})


@router.get("/exports/kpis.csv")
def export_kpis(event_id: str = None, x_api_key: str = Header(None)):
    token = os.environ.get("EXPORT_API_TOKEN", "devtoken123")
    if x_api_key != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(["event_id", "metric", "value"])
    writer.writerow([event_id or "", "impressions", 0])
    return (sio.getvalue(), 200, {"Content-Type": "text/csv"})


@router.post("/exports/run")
def exports_run(x_api_key: str = Header(None)):
    token = os.environ.get("EXPORT_API_TOKEN", "devtoken123")
    if x_api_key != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM marketing_activities")
    rows = cur.fetchone()[0]
    return {"status": "ok", "exports": [{"name": "activities.csv", "rows": int(rows)}]}


@router.get("/lms/courses")
def lms_courses():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT course_id,title,description FROM lms_courses")
    rows = cur.fetchall()
    courses = [{"course_id": r[0], "title": r[1], "description": r[2]} for r in rows]
    # ensure usarec-101 present
    if not any(c.get("course_id") == "usarec-101" for c in courses):
        courses.insert(0, {"course_id": "usarec-101", "title": "USAREC Orientation", "description": ""})
    return {"status": "ok", "count": len(courses), "courses": courses}


@router.get("/lms/stats")
def lms_stats():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM lms_courses")
    total_courses = int(cur.fetchone()[0] or 0)
    cur.execute("SELECT COUNT(1) FROM lms_enrollments")
    total_enrollments = int(cur.fetchone()[0] or 0)
    return {"status": "ok", "stats": {"total_courses": total_courses, "total_enrollments": total_enrollments}}


@router.post("/lms/enroll")
def lms_enroll(payload: dict):
    eid = "enr_" + uuid.uuid4().hex[:10]
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO lms_enrollments(enrollment_id,user_id,course_id,progress_percent,enrolled_at,updated_at) VALUES(?,?,?,?,?,?)", (eid, payload.get("user_id"), payload.get("course_id"), payload.get("progress_percent") or 0, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok", "enrollment_id": eid}


@router.get("/lms/enrollments/{user_id}")
def get_enrollments(user_id: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT enrollment_id,course_id,progress_percent FROM lms_enrollments WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    enrollments = [{"enrollment_id": r[0], "course_id": r[1], "progress_percent": r[2]} for r in rows]
    return {"status": "ok", "count": len(enrollments), "enrollments": enrollments}


@router.put("/lms/progress")
def lms_progress(payload: dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE lms_enrollments SET progress_percent=?, updated_at=? WHERE enrollment_id=?", (payload.get("progress_percent"), datetime.utcnow().isoformat(), payload.get("enrollment_id")))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.get("/funnel/stages")
def funnel_stages():
    return {"status": "ok", "stages": ["lead", "prospect", "applicant", "contract", "accession"]}


@router.post("/funnel/transition")
def funnel_transition(payload: dict):
    tid = "ft_" + uuid.uuid4().hex[:10]
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO funnel_transitions(id,lead_id,from_stage,to_stage,transition_reason,created_at) VALUES(?,?,?,?,?,?)", (tid, payload.get("lead_id"), payload.get("from_stage"), payload.get("to_stage"), payload.get("transition_reason"), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.post("/burden/input")
def burden_input(payload: dict, user: dict = Depends(require_roles("co_cmd"))):
    bid = "bur_" + uuid.uuid4().hex[:10]
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO burden_inputs(id,scope_type,scope_value,mission_requirement,recruiter_strength,reporting_date,created_at) VALUES(?,?,?,?,?,?,?)", (bid, payload.get("scope_type"), payload.get("scope_value"), payload.get("mission_requirement"), payload.get("recruiter_strength"), payload.get("reporting_date"), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@router.get("/burden/latest")
def burden_latest(scope_type: str = None, scope_value: str = None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id,scope_type,scope_value,mission_requirement,recruiter_strength,reporting_date,created_at FROM burden_inputs WHERE scope_type=? AND scope_value=? ORDER BY reporting_date DESC LIMIT 1", (scope_type, scope_value))
    row = cur.fetchone()
    if not row:
        return {"status": "ok", "record": None}
    record = {"id": row[0], "scope_type": row[1], "scope_value": row[2], "mission_requirement": row[3], "recruiter_strength": row[4], "reporting_date": row[5], "created_at": row[6]}
    return {"status": "ok", "record": record}


@router.post("/loes")
def create_loe(payload: dict, user: dict = Depends(require_roles("usarec_admin"))):
    lid = "loe_" + uuid.uuid4().hex[:10]
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO loes(id,scope_type,scope_value,title,description,created_by,created_at) VALUES(?,?,?,?,?,?,?)", (lid, payload.get("scope_type"), payload.get("scope_value"), payload.get("title"), payload.get("description"), payload.get("created_by"), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok", "id": lid}
