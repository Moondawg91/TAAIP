"""© 2025 Maroon Moon, LLC. All rights reserved.
CRUD helpers for Phase 2 canonical domain models. Queries are composable so RBAC filters can be applied before materialization.
"""

"""© 2025 Maroon Moon, LLC. All rights reserved.
CRUD helpers for Phase 2 canonical domain models. Queries are composable so RBAC filters can be applied before materialization.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models_domain as domain
from . import rbac
from typing import Optional, Dict
from datetime import date, datetime, timezone


def _prefixes_from_rsid(rsid: Optional[str]) -> Dict[str, Optional[str]]:
    if not rsid:
        return {'brigade_prefix': None, 'battalion_prefix': None, 'company_prefix': None}
    return {
        'brigade_prefix': rsid[0:1],
        'battalion_prefix': rsid[0:2],
        'company_prefix': rsid[0:3]
    }


def create_event(db: Session, payload: dict):
    # enforce server-side timestamps: ignore created_at/updated_at from payload
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    payload.pop('reported_at', None)
    payload.pop('ingested_at', None)
    pfx = _prefixes_from_rsid(payload.get('station_rsid'))
    ev = domain.Event(**payload, **pfx)
    db.add(ev)
    db.commit()
    return ev


def events_query(db: Session):
    return db.query(domain.Event)


def get_event(db: Session, event_id: str):
    return db.query(domain.Event).filter(domain.Event.id == event_id).one_or_none()


def create_event_metric(db: Session, payload: dict):
    # compute cost_per_lead if possible
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    # set ingested_at server-side
    payload.pop('ingested_at', None)
    payload['ingested_at'] = datetime.now(timezone.utc)
    if payload.get('leads_generated') and payload.get('cost'):
        payload['cost_per_lead'] = payload['cost'] / max(1, payload['leads_generated'])
    em = domain.EventMetric(**payload)
    db.add(em)
    db.commit()
    return em


def event_metrics_query(db: Session, event_id: Optional[str] = None):
    q = db.query(domain.EventMetric)
    if event_id:
        q = q.filter(domain.EventMetric.event_id == event_id)
    return q


def create_marketing_activity(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    payload.pop('ingested_at', None)
    payload['ingested_at'] = datetime.now(timezone.utc)
    pfx = _prefixes_from_rsid(payload.get('station_rsid'))
    ma = domain.MarketingActivity(**payload, **pfx)
    db.add(ma)
    db.commit()
    return ma


def marketing_query(db: Session):
    return db.query(domain.MarketingActivity)


def marketing_summary(db: Session, scope_type: str, scope_value: str, start: date = None, end: date = None):
    q = db.query(
        func.sum(domain.MarketingActivity.impressions).label('impressions'),
        func.sum(domain.MarketingActivity.engagements).label('engagements'),
        func.sum(domain.MarketingActivity.clicks).label('clicks'),
        func.sum(domain.MarketingActivity.conversions).label('conversions'),
        func.sum(domain.MarketingActivity.cost).label('cost')
    )
    # apply date filter
    if start:
        q = q.filter(domain.MarketingActivity.reporting_date >= start)
    if end:
        q = q.filter(domain.MarketingActivity.reporting_date <= end)
    return q


def get_funnel_stages(db: Session):
    return db.query(domain.FunnelStage).order_by(domain.FunnelStage.sequence_order)


def create_funnel_transition(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    payload.pop('ingested_at', None)
    payload['ingested_at'] = datetime.now(timezone.utc)
    pfx = _prefixes_from_rsid(payload.get('station_rsid'))
    ft = domain.FunnelTransition(**payload, **pfx)
    db.add(ft)
    db.commit()
    return ft


def burden_input_create(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    payload.pop('ingested_at', None)
    payload['ingested_at'] = datetime.now(timezone.utc)
    bi = domain.BurdenInput(**payload)
    db.add(bi)
    db.commit()
    return bi


def compute_burden_snapshot(db: Session, scope_type: str, scope_value: str):
    # find latest input for the scope
    src = db.query(domain.BurdenInput).filter(domain.BurdenInput.scope_type == scope_type, domain.BurdenInput.scope_value == scope_value).order_by(domain.BurdenInput.reporting_date.desc()).first()
    if not src:
        return None
    ratio = src.mission_requirement / max(1, src.recruiter_strength)
    snap = domain.BurdenSnapshot(id=src.id + "-snap", scope_type=src.scope_type, scope_value=src.scope_value, reporting_date=src.reporting_date, mission_requirement=src.mission_requirement, recruiter_strength=src.recruiter_strength, burden_ratio=ratio)
    db.add(snap)
    db.commit()
    return snap


def create_loe(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    loe = domain.Loe(**payload)
    db.add(loe)
    db.commit()
    return loe


def create_loe_metric(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    payload.pop('ingested_at', None)
    payload['ingested_at'] = datetime.now(timezone.utc)
    lm = domain.LoeMetric(**payload)
    db.add(lm)
    db.commit()
    return lm


def evaluate_loe(db: Session, loe_id: str):
    metrics = db.query(domain.LoeMetric).filter(domain.LoeMetric.loe_id == loe_id).all()
    from datetime import datetime
    for m in metrics:
        if m.current_value is None:
            m.status = 'unknown'
        else:
            if m.fail_threshold is not None and m.current_value <= m.fail_threshold:
                m.status = 'not_met'
            elif m.warn_threshold is not None and m.current_value <= m.warn_threshold:
                m.status = 'at_risk'
            else:
                m.status = 'met'
        m.last_evaluated_at = datetime.utcnow()
    db.commit()
    return metrics


def create_decision(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    d = domain.Decision(**payload)
    db.add(d)
    db.commit()
    return d


def write_audit(db: Session, payload: dict):
    payload.pop('created_at', None)
    payload.pop('updated_at', None)
    a = domain.AuditLog(**payload)
    db.add(a)
    db.commit()
    return a
