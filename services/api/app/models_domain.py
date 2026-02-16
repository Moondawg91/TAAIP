"""© 2025 Maroon Moon, LLC. All rights reserved.
Canonical domain models for Phase 2 (events, marketing, funnel, burden, loes, decisions, audit)
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from .models import Base
from datetime import datetime
from sqlalchemy import func as sa_func


class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    station_rsid = Column(String(4), ForeignKey("stations.rsid"), nullable=True)
    brigade_prefix = Column(String(1), nullable=True)
    battalion_prefix = Column(String(2), nullable=True)
    company_prefix = Column(String(3), nullable=True)
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(String, nullable=False, server_default='planned')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EventMetric(Base):
    __tablename__ = "event_metrics"
    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    metric_date = Column(Date, nullable=False)
    leads_generated = Column(Integer, nullable=True, default=0)
    leads_qualified = Column(Integer, nullable=True, default=0)
    conversions = Column(Integer, nullable=True, default=0)
    cost = Column(Float, nullable=True, default=0.0)
    cost_per_lead = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    engagement_rate = Column(Float, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketingActivity(Base):
    __tablename__ = "marketing_activities"
    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=True)
    station_rsid = Column(String(4), ForeignKey("stations.rsid"), nullable=True)
    brigade_prefix = Column(String(1), nullable=True)
    battalion_prefix = Column(String(2), nullable=True)
    company_prefix = Column(String(3), nullable=True)
    activity_type = Column(String, nullable=False)
    campaign_name = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    data_source = Column(String, nullable=True)
    impressions = Column(Integer, nullable=True, default=0)
    engagements = Column(Integer, nullable=True, default=0)
    clicks = Column(Integer, nullable=True, default=0)
    conversions = Column(Integer, nullable=True, default=0)
    cost = Column(Float, nullable=True, default=0.0)
    reporting_date = Column(Date, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FunnelStage(Base):
    __tablename__ = "funnel_stages"
    id = Column(String, primary_key=True)
    stage_name = Column(String, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FunnelTransition(Base):
    __tablename__ = "funnel_transitions"
    id = Column(String, primary_key=True)
    lead_key = Column(String, nullable=False)
    station_rsid = Column(String(4), ForeignKey("stations.rsid"), nullable=False)
    brigade_prefix = Column(String(1), nullable=True)
    battalion_prefix = Column(String(2), nullable=True)
    company_prefix = Column(String(3), nullable=True)
    from_stage = Column(String, ForeignKey("funnel_stages.id"), nullable=True)
    to_stage = Column(String, ForeignKey("funnel_stages.id"), nullable=True)
    transition_reason = Column(String, nullable=True)
    technician_user = Column(String, nullable=True)
    transitioned_at = Column(DateTime(timezone=True), server_default=func.now())
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BurdenInput(Base):
    __tablename__ = "burden_inputs"
    id = Column(String, primary_key=True)
    scope_type = Column(String, nullable=False)
    scope_value = Column(String, nullable=False)
    mission_requirement = Column(Integer, nullable=False)
    recruiter_strength = Column(Integer, nullable=False)
    reporting_date = Column(Date, nullable=False)
    source_system = Column(String, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BurdenSnapshot(Base):
    __tablename__ = "burden_snapshots"
    id = Column(String, primary_key=True)
    scope_type = Column(String, nullable=False)
    scope_value = Column(String, nullable=False)
    reporting_date = Column(Date, nullable=False)
    mission_requirement = Column(Integer, nullable=False)
    recruiter_strength = Column(Integer, nullable=False)
    burden_ratio = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Loe(Base):
    __tablename__ = "loes"
    id = Column(String, primary_key=True)
    scope_type = Column(String, nullable=False)
    scope_value = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LoeMetric(Base):
    __tablename__ = "loe_metrics"
    id = Column(String, primary_key=True)
    loe_id = Column(String, ForeignKey("loes.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    target_value = Column(Float, nullable=True)
    warn_threshold = Column(Float, nullable=True)
    fail_threshold = Column(Float, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    current_value = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    rationale = Column(String, nullable=True)
    last_evaluated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Decision(Base):
    __tablename__ = "decisions"
    id = Column(String, primary_key=True)
    scope_type = Column(String, nullable=False)
    scope_value = Column(String, nullable=False)
    decision_type = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    details_json = Column(JSON, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    scope_type = Column(String, nullable=True)
    scope_value = Column(String, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
