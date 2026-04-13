from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MissionDecreaseJustificationRequest(BaseModel):
    org_id: str = Field(..., min_length=1)
    period_start: date
    period_end: date
    baseline_start: Optional[date] = None
    baseline_end: Optional[date] = None
    include_evidence: bool = True
    force_refresh: bool = False


class ConfidencePayload(BaseModel):
    score: float
    band: str
    completeness: float
    agreement: float


class CausalFactorPayload(BaseModel):
    factor_id: str
    trace_id: str
    code: str
    label: str
    impact: float
    weighted_score: float
    agreement_score: float
    source: str
    rationale: str


class RecommendationPayload(BaseModel):
    recommendation_id: str
    trace_id: str
    kind: str
    priority: int
    title: str
    rationale: str
    actions: List[str]
    evidence_refs: List[str]


class MissionDecreaseJustificationResponse(BaseModel):
    request_id: str
    traceability_id: str
    generated_at: datetime
    scope: Dict[str, str]
    mission_delta_summary: Dict[str, Any]
    causal_factors: List[CausalFactorPayload]
    recommendations: List[RecommendationPayload]
    accountability_brief: Dict[str, Any]
    loe_summary: Dict[str, Any]
    confidence: ConfidencePayload
    executive_summary: List[str]
    commander_narrative: str
    one_slide_payload: Dict[str, Any]
    assumptions_and_limits: List[str]
    evidence: List[Dict[str, Any]]
    force_refresh_used: bool
