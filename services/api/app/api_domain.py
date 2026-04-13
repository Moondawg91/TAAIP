"""© 2026 TAAIP. Copyright pending.
Domain API router implementing Phase 2 endpoints under /api/v2.
All responses are structured as {"status":"ok","data":...}.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import os
from . import auth, database, rbac
from . import crud_domain as crud
from . import models_domain as domain_models
from . import schemas_domain as schemas
from . import models
from sqlalchemy.orm import Session
from sqlalchemy import func
from services.api.app.services import (
    accountability_engine,
    ai_recommendation_engine,
    decision_writeback,
    execution_quality,
    forecasting,
    ingest_contracts,
    lms_performance_bridge,
    loe_engine,
    market_qma,
    school_access,
    targeting_expansion,
    what_if,
)

router = APIRouter(prefix="/v2", tags=["domain"])


def require_user(user=Depends(auth.get_current_user)):
    return user


from datetime import datetime, timezone


def _to_iso_z(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    return value


def _format_datetimes(obj):
    if obj is None:
        return None
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out[k] = _format_datetimes(v)
        return out
    if isinstance(obj, list):
        return [_format_datetimes(x) for x in obj]
    if isinstance(obj, datetime):
        return _to_iso_z(obj)
    return obj


@router.post('/events')
def create_event(payload: schemas.EventCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    # debug: record resolved user type and role for CI investigation
    try:
        with open('/tmp/api_domain_user_debug.log', 'a') as f:
            f.write(f"create_event invoked user_type={type(user)} user_repr={repr(getattr(user,'username',user))} role_attr={getattr(getattr(user,'role',None),'name',getattr(user,'role',None))} scope={getattr(user,'scope',None)}\n")
    except Exception:
        pass
    if not payload.station_rsid:
        raise HTTPException(status_code=400, detail='station_rsid is required')
    try:
        rbac.authorize_create(user, station_rsid=payload.station_rsid)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-{payload.id}", 'actor': user.username, 'action': 'denied_create_event', 'entity_type': 'event', 'entity_id': payload.id, 'scope_type': 'STN', 'scope_value': payload.station_rsid, 'after_json': {'reason': e.detail}})
        raise
    ev = crud.create_event(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes(schemas.EventOut.from_orm(ev).dict())}


@router.get('/events')
def list_events(db: Session = Depends(auth.get_db), user=Depends(require_user)):
    q = crud.events_query(db)
    q = rbac.apply_scope_filter(q, domain_models.Event, user.scope)
    rows = q.all()
    data = [schemas.EventOut.from_orm(r).dict() for r in rows]
    return {"status": "ok", "data": _format_datetimes(data)}


@router.get('/events/{id}')
def get_event(id: str, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    ev = crud.get_event(db, id)
    if not ev:
        raise HTTPException(status_code=404)
    if ev.station_rsid and not rbac.is_rsid_in_scope(user.scope, ev.station_rsid):
        raise HTTPException(status_code=403)
    return {"status": "ok", "data": _format_datetimes(schemas.EventOut.from_orm(ev).dict())}


@router.post('/events/{id}/metrics')
def post_event_metric(id: str, payload: schemas.EventMetricCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    ev = crud.get_event(db, id)
    if not ev:
        raise HTTPException(status_code=404)
    try:
        if ev.station_rsid:
            rbac.authorize_create(user, station_rsid=ev.station_rsid)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-{id}", 'actor': user.username, 'action': 'denied_create_event_metric', 'entity_type': 'event_metric', 'entity_id': None, 'scope_type': 'STN', 'scope_value': ev.station_rsid, 'after_json': {'reason': e.detail}})
        raise
    obj = crud.create_event_metric(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": obj.id})}


@router.post('/marketing/activities')
def post_marketing_activity(payload: schemas.MarketingActivityCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    try:
        if payload.station_rsid:
            rbac.authorize_create(user, station_rsid=payload.station_rsid)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-ma-{payload.id}", 'actor': user.username, 'action': 'denied_create_marketing', 'entity_type': 'marketing_activity', 'entity_id': None, 'scope_type': 'STN', 'scope_value': payload.station_rsid, 'after_json': {'reason': e.detail}})
        raise
    # Funding source enforcement (opt-in).
    fs = payload.funding_source or payload.data_source
    enforce = os.environ.get('ENFORCE_FUNDING')
    if enforce and enforce.lower() in ('1', 'true', 'yes') and not fs:
        crud.write_audit(db, {'id': f"audit-deny-ma-{payload.id}", 'actor': user.username, 'action': 'denied_create_marketing', 'entity_type': 'marketing_activity', 'entity_id': None, 'scope_type': 'STN', 'scope_value': payload.station_rsid, 'after_json': {'reason': 'funding_source required'}})
        raise HTTPException(status_code=400, detail='funding_source is required')
    # Remove funding_source before passing to domain CRUD (domain model doesn't include it)
    d = payload.dict()
    d.pop('funding_source', None)
    obj = crud.create_marketing_activity(db, d)
    return {"status": "ok", "data": _format_datetimes({"id": obj.id})}


@router.get('/marketing/activities')
def get_marketing_activities(start: Optional[str] = Query(None), end: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    q = crud.marketing_query(db)
    q = rbac.apply_scope_filter(q, domain_models.MarketingActivity, user.scope)
    rows = q.all()
    out = []
    for r in rows:
        out.append({k: getattr(r, k) for k in r.__dict__ if not k.startswith('_')})
    return {"status": "ok", "data": _format_datetimes(out)}


@router.get('/marketing/summary')
def marketing_summary(start: Optional[str] = Query(None), end: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    from datetime import datetime
    s = datetime.fromisoformat(start).date() if start else None
    e = datetime.fromisoformat(end).date() if end else None
    # Use a direct SQL aggregation grouped by the activity identifier
    # to avoid double-counting rows that may be created by compatibility
    # and domain handlers (some DB variants use `activity_id` while
    # ORM models may reference `id`). Grouping by the physical key
    # (COALESCE(activity_id,id)) ensures each activity contributes once.
    try:
        stmt = """
        SELECT
            SUM(impressions) as impressions,
            SUM(engagement_count) as engagements,
            SUM(COALESCE(clicks,0)) as clicks,
            SUM(activation_conversions) as conversions,
            SUM(COALESCE(cost,0.0)) as cost
        FROM (
                 SELECT COALESCE(activity_id, CAST(id AS TEXT)) as activity_key,
                   MAX(COALESCE(impressions,0)) as impressions,
                   MAX(COALESCE(engagement_count,0)) as engagement_count,
                   MAX(COALESCE(clicks,0)) as clicks,
                   MAX(COALESCE(activation_conversions,0)) as activation_conversions,
                   MAX(COALESCE(cost,0.0)) as cost
            FROM marketing_activities
            GROUP BY activity_key
        ) as dedup
        """
        row = db.execute(text(stmt)).mappings().first()
    except Exception:
        # Fallback: attempt domain query if raw SQL fails
        q = crud.marketing_summary(db, None, None, s, e)
        row = q.one_or_none()
    if not row:
        return {"status": "ok", "data": {}}

    # Normalize SQLAlchemy row/tuple/dict to a mapping for safe access
    if hasattr(row, '_mapping'):
        rmap = row._mapping
    elif isinstance(row, dict):
        rmap = row
    else:
        try:
            rmap = dict(row)
        except Exception:
            rmap = {}

    impressions = int(rmap.get('impressions') or 0)
    engagements = int(rmap.get('engagements') or 0)
    clicks = int(rmap.get('clicks') or 0)
    conversions = int(rmap.get('conversions') or 0)
    cost = float(rmap.get('cost') or 0.0)
    cpl = cost / max(1, conversions) if conversions else None
    return {"status": "ok", "data": _format_datetimes({
        'impressions': impressions,
        'engagements': engagements,
        'clicks': clicks,
        'conversions': conversions,
        'cost': cost,
        'cost_per_conversion': cpl,
    })}


@router.get('/funnel/stages')
def funnel_stages(db: Session = Depends(auth.get_db), user=Depends(require_user)):
    stages = crud.get_funnel_stages(db).all()
    if not stages:
        defaults = [
            ("lead", "lead", 1),
            ("prospect", "prospect", 2),
            ("appointment_made", "appointment_made", 3),
            ("appointment_conducted", "appointment_conducted", 4),
            ("test", "test", 5),
            ("test_pass", "test_pass", 6),
            ("physical", "physical", 7),
            ("enlist", "enlist", 8),
        ]
        for sid, name, order in defaults:
            db.add(domain_models.FunnelStage(id=sid, stage_name=name, sequence_order=order))
        db.commit()
        stages = crud.get_funnel_stages(db).all()
    return {"status": "ok", "data": _format_datetimes([ { 'id': s.id, 'stage_name': s.stage_name, 'sequence_order': s.sequence_order } for s in stages ])}


@router.post('/funnel/transition')
def funnel_transition(payload: schemas.FunnelTransitionCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    try:
        rbac.authorize_create(user, station_rsid=payload.station_rsid)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-tr-{payload.id}", 'actor': user.username, 'action': 'denied_funnel_transition', 'entity_type': 'funnel_transition', 'entity_id': None, 'scope_type': 'STN', 'scope_value': payload.station_rsid, 'after_json': {'reason': e.detail}})
        raise
    obj = crud.create_funnel_transition(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": obj.id})}


@router.post('/burden/input')
def burden_input(payload: schemas.BurdenInputCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    try:
        rbac.authorize_create(user, scope_type=payload.scope_type, scope_value=payload.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-bi-{payload.id}", 'actor': user.username, 'action': 'denied_burden_input', 'entity_type': 'burden_input', 'entity_id': None, 'scope_type': payload.scope_type, 'scope_value': payload.scope_value, 'after_json': {'reason': e.detail}})
        raise
    obj = crud.burden_input_create(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": obj.id})}


@router.get('/burden/latest')
def burden_latest(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and not scope_value.startswith(ns['value']):
        raise HTTPException(status_code=403)
    from .models_domain import BurdenInput
    bi = db.query(BurdenInput).filter(BurdenInput.scope_type == scope_type, BurdenInput.scope_value == scope_value).order_by(BurdenInput.reporting_date.desc()).first()
    if not bi:
        raise HTTPException(status_code=404)
    return {"status": "ok", "data": _format_datetimes({
        'mission_requirement': bi.mission_requirement,
        'recruiter_strength': bi.recruiter_strength,
        'reporting_date': str(bi.reporting_date)
    })}


@router.post('/loes')
def create_loe(payload: schemas.LoeCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    loe_engine.validate_scope(payload.scope_type, payload.scope_value)
    loe_engine.can_user_manage_loe(user, payload.scope_type, payload.scope_value)
    role_name = getattr(getattr(user, 'role', None), 'name', str(getattr(user, 'role', '')))
    company_loe_write_enabled = os.getenv("ALLOW_COMPANY_LOE_WRITE", "0").lower() in {"1", "true", "yes"}
    try:
        if not (role_name == 'COMPANY_CMD' and company_loe_write_enabled):
            rbac.authorize_create(user, scope_type=payload.scope_type, scope_value=payload.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-loe-{payload.id}", 'actor': user.username, 'action': 'denied_create_loe', 'entity_type': 'loe', 'entity_id': None, 'scope_type': payload.scope_type, 'scope_value': payload.scope_value, 'after_json': {'reason': e.detail}})
        raise
    loe = crud.create_loe(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": loe.id})}


@router.get('/loes')
def list_loes(scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    ns = rbac.normalize_scope(user.scope)
    effective_scope_type = (scope_type or ns['type'] or 'USAREC').upper()
    effective_scope_value = (scope_value or ns.get('value') or '')

    loe_engine.validate_scope(effective_scope_type, effective_scope_value if effective_scope_type != 'USAREC' else 'USAREC')

    if ns['type'] != 'USAREC' and effective_scope_type != 'USAREC':
        req_val = effective_scope_value or ''
        if not req_val.startswith(ns.get('value') or ''):
            raise HTTPException(status_code=403, detail='requested scope outside user permissions')

    items = loe_engine.list_loes_for_scope(db, effective_scope_type, effective_scope_value)
    return {"status": "ok", "data": _format_datetimes(items)}


@router.post('/loes/{id}/metrics')
def create_loe_metric(id: str, payload: schemas.LoeMetricCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    loe = db.query(domain_models.Loe).filter(domain_models.Loe.id == payload.loe_id).one_or_none()
    if not loe:
        raise HTTPException(status_code=404)
    loe_engine.validate_scope(loe.scope_type, loe.scope_value)
    loe_engine.can_user_manage_loe(user, loe.scope_type, loe.scope_value)
    role_name = getattr(getattr(user, 'role', None), 'name', str(getattr(user, 'role', '')))
    company_loe_write_enabled = os.getenv("ALLOW_COMPANY_LOE_WRITE", "0").lower() in {"1", "true", "yes"}
    try:
        if not (role_name == 'COMPANY_CMD' and company_loe_write_enabled):
            rbac.authorize_create(user, scope_type=loe.scope_type, scope_value=loe.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-loem-{payload.id}", 'actor': user.username, 'action': 'denied_create_loe_metric', 'entity_type': 'loe_metric', 'entity_id': None, 'scope_type': loe.scope_type, 'scope_value': loe.scope_value, 'after_json': {'reason': e.detail}})
        raise
    obj = crud.create_loe_metric(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": obj.id})}


@router.post('/loes/{id}/evaluate')
def evaluate_loe(id: str, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    loe = db.query(domain_models.Loe).filter(domain_models.Loe.id == id).one_or_none()
    if not loe:
        raise HTTPException(status_code=404)
    loe_engine.validate_scope(loe.scope_type, loe.scope_value)
    loe_engine.can_user_manage_loe(user, loe.scope_type, loe.scope_value)
    role_name = getattr(getattr(user, 'role', None), 'name', str(getattr(user, 'role', '')))
    company_loe_write_enabled = os.getenv("ALLOW_COMPANY_LOE_WRITE", "0").lower() in {"1", "true", "yes"}
    try:
        if not (role_name == 'COMPANY_CMD' and company_loe_write_enabled):
            rbac.authorize_create(user, scope_type=loe.scope_type, scope_value=loe.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-loee-{id}", 'actor': user.username, 'action': 'denied_evaluate_loe', 'entity_type': 'loe', 'entity_id': id, 'scope_type': loe.scope_type, 'scope_value': loe.scope_value, 'after_json': {'reason': e.detail}})
        raise
    result = loe_engine.evaluate_loe(db, id)
    return {"status": "ok", "data": _format_datetimes(result)}


@router.get('/targeting/recommendations')
def targeting_recommendations(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)

    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')

    data = targeting_expansion.recommendations_for_scope(db, st, sv)
    return {"status": "ok", "data": _format_datetimes(data)}


@router.get('/accountability/classification')
def accountability_classification(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)

    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')

    data = accountability_engine.classify_scope(db, st, sv)
    return {"status": "ok", "data": _format_datetimes(data)}


@router.get('/school-access/summary')
def school_access_summary(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')
    payload = school_access.summarize_school_access(db, st, sv, st, sv, top_n=25)
    return _format_datetimes(payload)


@router.get('/execution-quality/summary')
def execution_quality_summary(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')
    payload = execution_quality.summarize_execution_quality(db, st, sv, st, sv)
    return _format_datetimes(payload)


@router.post('/forecasting/scenario')
def forecasting_scenario(payload: dict, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = str(payload.get('scope_type') or '').upper()
    sv = str(payload.get('scope_value') or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')
    out = forecasting.project_scope(db, st, sv, assumptions=payload.get('assumptions') or {})
    return {"status": "ok", "data": _format_datetimes(out)}


@router.post('/what-if/run')
def run_what_if(payload: dict, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = str(payload.get('scope_type') or '').upper()
    sv = str(payload.get('scope_value') or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')
    out = what_if.run_what_if(db, st, sv, payload.get('scenario') or {})
    return {"status": "ok", "data": _format_datetimes(out)}


@router.post('/writeback/decision')
def writeback_decision(payload: dict, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = str(payload.get('scope_type') or '').upper()
    sv = str(payload.get('scope_value') or '').strip()
    loe_engine.validate_scope(st, sv)

    role_name = getattr(getattr(user, 'role', None), 'name', str(getattr(user, 'role', '')))
    company_write_enabled = os.getenv("ALLOW_COMPANY_LOE_WRITE", "0").lower() in {"1", "true", "yes"}
    if role_name == 'STATION_VIEW':
        raise HTTPException(status_code=403, detail='role not permitted to write decisions')
    if role_name == 'COMPANY_CMD' and not company_write_enabled:
        raise HTTPException(status_code=403, detail='company commander writeback disabled by policy')
    if role_name == 'COMPANY_CMD' and not sv.startswith((user.scope or '')[:3]):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')

    rbac.authorize_create(user, scope_type=st, scope_value=sv)

    out = decision_writeback.writeback_change(
        db,
        actor=getattr(user, 'username', 'unknown'),
        scope_type=st,
        scope_value=sv,
        decision_type=str(payload.get('decision_type') or 'targeting_shift'),
        summary=str(payload.get('summary') or 'Operational writeback'),
        before_json=payload.get('before') or {},
        after_json=payload.get('after') or {},
    )
    return {"status": "ok", "data": _format_datetimes(out)}


@router.get('/recommendations/actionable')
def actionable_recommendations(scope_type: str = Query(...), scope_value: str = Query(...), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')
    out = ai_recommendation_engine.generate_recommendation_bundle(db, st, sv)
    return {"status": "ok", "data": _format_datetimes(out)}


@router.get('/lms/performance-correction')
def lms_performance_correction(scope_type: str = Query(...), scope_value: str = Query(...), role: str = Query('commander'), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    st = (scope_type or '').upper()
    sv = (scope_value or '').strip()
    loe_engine.validate_scope(st, sv)
    ns = rbac.normalize_scope(user.scope)
    if ns['type'] != 'USAREC' and st != 'USAREC' and not sv.startswith(ns.get('value') or ''):
        raise HTTPException(status_code=403, detail='requested scope outside user permissions')

    accountability = accountability_engine.classify_scope(db, st, sv)
    modules = lms_performance_bridge.recommendations_for_classification(accountability.get('classification'), role)
    return {"status": "ok", "data": _format_datetimes({
        "scope_type": st,
        "scope_value": sv,
        "classification": accountability.get('classification'),
        "recommended_modules": modules,
    })}


@router.post('/ingest/validate-contract')
def validate_ingest_contract(payload: dict, user=Depends(require_user)):
    dataset_type = str(payload.get('dataset_type') or '')
    columns = payload.get('columns') or []
    ok, data = ingest_contracts.validate_contract(dataset_type, columns)
    return {
        "status": "ok" if ok else "invalid_dataset_schema",
        "data": _format_datetimes(data),
    }


@router.post('/decisions')
def create_decision(payload: schemas.DecisionCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    try:
        rbac.authorize_create(user, scope_type=payload.scope_type, scope_value=payload.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-decision-{payload.id}", 'actor': user.username, 'action': 'denied_create_decision', 'entity_type': 'decision', 'entity_id': None, 'scope_type': payload.scope_type, 'scope_value': payload.scope_value, 'after_json': {'reason': e.detail}})
        raise
    d = crud.create_decision(db, payload.dict())
    crud.write_audit(db, {'id': d.id + '-audit', 'actor': payload.created_by, 'action': 'create_decision', 'entity_type': 'decision', 'entity_id': d.id, 'scope_type': payload.scope_type, 'scope_value': payload.scope_value, 'after_json': payload.details_json})
    return {"status": "ok", "data": _format_datetimes({"id": d.id})}


@router.get('/coverage/summary')
def coverage_summary(scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    StationZipCoverage = models.StationZipCoverage
    sq = db.query(StationZipCoverage.market_category, func.count(StationZipCoverage.id)).group_by(StationZipCoverage.market_category)
    sq = rbac.apply_scope_filter(sq, StationZipCoverage, user.scope)
    rows = sq.all()
    data = { (r[0].name if hasattr(r[0], 'name') else str(r[0])): r[1] for r in rows }
    return {"status": "ok", "data": _format_datetimes(data)}


@router.get('/coverage/market_potential')
def market_potential(scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    StationZipCoverage = models.StationZipCoverage
    MarketCategoryWeights = models.MarketCategoryWeights
    sq = db.query(StationZipCoverage.market_category, func.count(StationZipCoverage.id)).group_by(StationZipCoverage.market_category)
    sq = rbac.apply_scope_filter(sq, StationZipCoverage, user.scope)
    rows = sq.all()
    weights = {mw.category.name: mw.weight for mw in db.query(MarketCategoryWeights).all()}
    score = 0
    for cat, cnt in rows:
        key = cat.name if hasattr(cat, 'name') else str(cat)
        score += weights.get(key, 0) * cnt
    return {"status": "ok", "data": _format_datetimes({"market_potential_score": score})}


@router.get('/command/summary')
def command_summary(scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), db: Session = Depends(auth.get_db), user=Depends(require_user)):
    # aggregate event metrics
    em_q = db.query(domain_models.EventMetric)
    em_q = rbac.apply_scope_filter(em_q, domain_models.EventMetric, user.scope)
    em_row = em_q.with_entities(func.sum(domain_models.EventMetric.leads_generated).label('leads'), func.sum(domain_models.EventMetric.conversions).label('conversions'), func.sum(domain_models.EventMetric.cost).label('cost')).one()
    leads = em_row.leads or 0
    conversions = em_row.conversions or 0
    cost = em_row.cost or 0.0
    roi = (conversions * 1.0 / cost) if cost else None

    # burden snapshot
    bs_q = db.query(domain_models.BurdenSnapshot)
    bs_q = rbac.apply_scope_filter(bs_q, domain_models.BurdenSnapshot, user.scope)
    bs_row = bs_q.order_by(domain_models.BurdenSnapshot.reporting_date.desc()).first()
    burden_ratio = bs_row.burden_ratio if bs_row else None

    # loe statuses
    lm_q = db.query(domain_models.LoeMetric)
    lm_q = rbac.apply_scope_filter(lm_q, domain_models.LoeMetric, user.scope)
    lm_rows = lm_q.with_entities(domain_models.LoeMetric.status, func.count(domain_models.LoeMetric.id)).group_by(domain_models.LoeMetric.status).all()
    loe_status = {r[0]: r[1] for r in lm_rows}

    # market coverage counts
    StationZipCoverage = models.StationZipCoverage
    mz_q = db.query(StationZipCoverage.market_category, func.count(StationZipCoverage.id)).group_by(StationZipCoverage.market_category)
    mz_q = rbac.apply_scope_filter(mz_q, StationZipCoverage, user.scope)
    mz_rows = mz_q.all()
    market_counts = { (r[0].name if hasattr(r[0], 'name') else str(r[0])): r[1] for r in mz_rows }

    mp = market_potential(scope_type, scope_value, db, user)

    effective_scope_type = (scope_type or rbac.normalize_scope(user.scope)['type'] or 'USAREC').upper()
    effective_scope_value = (scope_value or rbac.normalize_scope(user.scope).get('value') or '')

    loe_summary = loe_engine.summarize_loes(db, effective_scope_type, effective_scope_value)
    targeting_summary = targeting_expansion.recommendations_for_scope(db, effective_scope_type, effective_scope_value, top_n=5)
    accountability_summary = accountability_engine.classify_scope(db, effective_scope_type, effective_scope_value)
    school_access_summary = school_access.summarize_school_access(db, effective_scope_type, effective_scope_value, effective_scope_type, effective_scope_value)
    execution_summary = execution_quality.summarize_execution_quality(db, effective_scope_type, effective_scope_value, effective_scope_type, effective_scope_value)
    market_summary = market_qma.summarize_market_qma(db, effective_scope_type, effective_scope_value, effective_scope_type, effective_scope_value)
    loe_blockers = loe_engine.loe_blockers(
        db,
        effective_scope_type,
        effective_scope_value,
        market_summary.get('market_qma', {}).get('summary', {}),
        school_access_summary.get('school_access', {}).get('summary', {}),
        execution_summary.get('execution_quality', {}).get('summary', {}),
    )

    return {"status": "ok", "data": _format_datetimes({
        'leads': leads,
        'conversions': conversions,
        'cost': cost,
        'roi': roi,
        'burden_ratio': burden_ratio,
        'loe_status': loe_status,
        'market_coverage': market_counts,
        'market_potential': mp['data'] if isinstance(mp, dict) and mp.get('status') == 'ok' else None,
        'loe_summary': loe_summary,
        'targeting_recommendations_summary': {
            'top_recommendations': targeting_summary.get('recommendations', [])[:5],
            'formula': targeting_summary.get('formula', {}),
        },
        'accountability_summary': accountability_summary,
        'market_qma_summary': market_summary.get('market_qma', {}).get('summary', {}),
        'school_access_summary': school_access_summary.get('school_access', {}).get('summary', {}),
        'execution_quality_summary': execution_summary.get('execution_quality', {}).get('summary', {}),
        'loe_blockers': loe_blockers,
    })}
