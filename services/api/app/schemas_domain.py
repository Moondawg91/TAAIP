"""© 2026 TAAIP. Copyright pending.
Pydantic schemas for Phase 2 domain APIs
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date


class EventCreate(BaseModel):
    id: str
    station_rsid: Optional[str]
    name: str
    event_type: str
    location: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    budget: Optional[float]
    status: Optional[str] = "planned"


class EventOut(BaseModel):
    id: str
    station_rsid: Optional[str]
    name: str
    event_type: str
    location: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    budget: Optional[float]
    status: str

    class Config:
        orm_mode = True


class EventMetricCreate(BaseModel):
    id: str
    event_id: str
    metric_date: date
    leads_generated: Optional[int] = 0
    leads_qualified: Optional[int] = 0
    conversions: Optional[int] = 0
    cost: Optional[float] = 0.0


class MarketingActivityCreate(BaseModel):
    id: str
    event_id: Optional[str]
    station_rsid: Optional[str]
    activity_type: str
    campaign_name: Optional[str]
    channel: Optional[str]
    data_source: Optional[str]
    funding_source: Optional[str]
    impressions: Optional[int] = 0
    engagements: Optional[int] = 0
    clicks: Optional[int] = 0
    conversions: Optional[int] = 0
    cost: Optional[float] = 0.0
    reporting_date: Optional[date]
    metadata_json: Optional[Any]


class FunnelTransitionCreate(BaseModel):
    id: str
    lead_key: str
    station_rsid: str
    from_stage: Optional[str]
    to_stage: str
    transition_reason: Optional[str]
    technician_user: Optional[str]


class BurdenInputCreate(BaseModel):
    id: str
    scope_type: str
    scope_value: str
    mission_requirement: int
    recruiter_strength: int
    reporting_date: date
    source_system: Optional[str]


class LoeCreate(BaseModel):
    id: str
    scope_type: str
    scope_value: str
    title: str
    description: Optional[str]
    created_by: str


class LoeMetricCreate(BaseModel):
    id: str
    loe_id: str
    metric_name: str
    target_value: Optional[float]
    warn_threshold: Optional[float]
    fail_threshold: Optional[float]


class DecisionCreate(BaseModel):
    id: str
    scope_type: str
    scope_value: str
    decision_type: str
    summary: str
    details_json: Optional[Any]
    created_by: str
