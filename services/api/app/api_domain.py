"""© 2026 TAAIP. Copyright pending.
Domain API router implementing Phase 2 endpoints under /api/v2.
All responses are structured as {"status":"ok","data":...}.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from . import auth, database, rbac
from . import crud_domain as crud
from . import models_domain as domain_models
from . import schemas_domain as schemas
from . import models
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    obj = crud.create_marketing_activity(db, payload.dict())
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
    q = crud.marketing_summary(db, None, None, s, e)
    row = q.one_or_none()
    if not row:
        return {"status": "ok", "data": {}}
    impressions = row.impressions or 0
    engagements = row.engagements or 0
    clicks = row.clicks or 0
    conversions = row.conversions or 0
    cost = row.cost or 0.0
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
    try:
        rbac.authorize_create(user, scope_type=payload.scope_type, scope_value=payload.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-loe-{payload.id}", 'actor': user.username, 'action': 'denied_create_loe', 'entity_type': 'loe', 'entity_id': None, 'scope_type': payload.scope_type, 'scope_value': payload.scope_value, 'after_json': {'reason': e.detail}})
        raise
    loe = crud.create_loe(db, payload.dict())
    return {"status": "ok", "data": _format_datetimes({"id": loe.id})}


@router.post('/loes/{id}/metrics')
def create_loe_metric(id: str, payload: schemas.LoeMetricCreate, db: Session = Depends(auth.get_db), user=Depends(require_user)):
    loe = db.query(domain_models.Loe).filter(domain_models.Loe.id == payload.loe_id).one_or_none()
    if not loe:
        raise HTTPException(status_code=404)
    try:
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
    try:
        rbac.authorize_create(user, scope_type=loe.scope_type, scope_value=loe.scope_value)
    except HTTPException as e:
        crud.write_audit(db, {'id': f"audit-deny-loee-{id}", 'actor': user.username, 'action': 'denied_evaluate_loe', 'entity_type': 'loe', 'entity_id': id, 'scope_type': loe.scope_type, 'scope_value': loe.scope_value, 'after_json': {'reason': e.detail}})
        raise
    metrics = crud.evaluate_loe(db, id)
    return {"status": "ok", "data": _format_datetimes({"evaluated": len(metrics)})}


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

    return {"status": "ok", "data": _format_datetimes({
        'leads': leads,
        'conversions': conversions,
        'cost': cost,
        'roi': roi,
        'burden_ratio': burden_ratio,
        'loe_status': loe_status,
        'market_coverage': market_counts,
        'market_potential': mp['data'] if isinstance(mp, dict) and mp.get('status') == 'ok' else None
    })}
