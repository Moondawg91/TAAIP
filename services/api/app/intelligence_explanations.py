"""© 2026 TAAIP. Copyright pending.
Intelligence Explanation Schema — canonical WHY / WHAT / HOW explanation objects
used by ALL recommendation engines in the intelligence layer.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import models_intelligence as mi
import uuid


# ─────────────────────────────────────────────────────────────────
# COMPONENT SCHEMAS
# ─────────────────────────────────────────────────────────────────

class ExplanationScope(BaseModel):
    """Identifies the organizational / temporal scope of the recommendation."""

    fy: Optional[str] = Field(None, description="Fiscal year, e.g. 'FY26'")
    quarter: Optional[str] = Field(None, description="Fiscal quarter, e.g. 'Q2'")
    rsm: Optional[str] = Field(None, description="Recruiting Station Mission identifier")
    station_rsid: Optional[str] = Field(None, description="4-char station RSID")
    zip_code: Optional[str] = Field(None, description="5-digit ZIP code")
    school_id: Optional[str] = Field(None, description="School identifier")
    mos: Optional[str] = Field(None, description="Military Occupational Specialty code")


class ExplanationLinks(BaseModel):
    """References to source artifacts that support this recommendation."""

    analytics_snapshot_id: Optional[str] = Field(None, description="ID of the analytics snapshot used")
    rop_version_id: Optional[str] = Field(None, description="ROP plan version ID")
    srp_version_id: Optional[str] = Field(None, description="SRP plan version ID")
    frag_order_id: Optional[str] = Field(None, description="Fragmentary order ID if applicable")


class ExplanationWhy(BaseModel):
    """Data-driven rationale: what the analytics show and why action is warranted."""

    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key metric values that triggered this recommendation"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Ordered list of evidence statements supporting the recommendation"
    )
    trend: Optional[str] = Field(None, description="Trend direction: 'improving', 'declining', 'stable'")
    risk: Optional[str] = Field(None, description="Risk level if no action taken: 'critical', 'high', 'medium', 'low'")


class ExplanationWhat(BaseModel):
    """Describes the specific recommended action."""

    action_type: str = Field(..., description="Category of action: 'rop_change', 'srp_change', 'school_prioritization', 'recruiter_realignment', 'operation_adjustment'")
    action_description: str = Field(..., description="Plain-English description of the recommended action")
    priority: str = Field("medium", description="'critical', 'high', 'medium', 'low'")
    timeframe: str = Field("90_days", description="'immediate', '30_days', '90_days', 'ongoing'")


class ExplanationHow(BaseModel):
    """Expected implementation path and outcome."""

    expected_effect: str = Field(..., description="Measurable outcome expected if the action is implemented")
    mission_link: Optional[str] = Field(None, description="Direct connection to mission metric or goal")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Prerequisites or dependent actions before or alongside this one"
    )


class ExplanationMeta(BaseModel):
    """Provenance and confidence metadata."""

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when this explanation was generated"
    )
    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="0.0–1.0 confidence score derived from data completeness and analytics agreement"
    )
    commander_authority: bool = Field(
        True,
        description="Always True — all recommendations are advisory; commanders retain full decision authority"
    )
    period_analyzed: Optional[Dict[str, str]] = Field(
        None,
        description="{'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}"
    )


# ─────────────────────────────────────────────────────────────────
# ROOT SCHEMA
# ─────────────────────────────────────────────────────────────────

class RecommendationExplanation(BaseModel):
    """
    Complete WHY / WHAT / HOW explanation attached to every intelligence recommendation.
    All fields are JSON-serializable. All sub-models have safe defaults.
    """

    scope: ExplanationScope = Field(default_factory=ExplanationScope)
    links: ExplanationLinks = Field(default_factory=ExplanationLinks)
    why: ExplanationWhy
    what: ExplanationWhat
    how: ExplanationHow
    meta: ExplanationMeta = Field(default_factory=ExplanationMeta)


# ─────────────────────────────────────────────────────────────────
# EXPLANATION BUILDER
# ─────────────────────────────────────────────────────────────────

def build_explanation(
    why: Dict[str, Any],
    what: Dict[str, Any],
    how: Dict[str, Any],
    scope: Optional[Dict[str, Any]] = None,
    links: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    recommendation_record_version_id: Optional[str] = None,
) -> RecommendationExplanation:
    """
    Construct a fully validated RecommendationExplanation from raw dicts.

    Applies safe defaults for every optional field. Missing keys within
    each sub-dict are filled by Pydantic model defaults so callers never
    need to supply a complete structure.

    Args:
        why:   Metrics, evidence, trend, and risk driving the recommendation.
        what:  Action type, description, priority, and timeframe.
        how:   Expected effect, mission link, and dependencies.
        scope: Organizational / temporal scope (all fields optional).
        links: Source artifact references (all fields optional).
        meta:  Provenance and confidence metadata (all fields optional).

    Returns:
        RecommendationExplanation — fully validated and ready for JSON serialization.
    """
    scope_obj = ExplanationScope(**(scope or {}))
    links_obj = ExplanationLinks(**(links or {}))
    meta_obj  = ExplanationMeta(**(meta or {}))

    why_obj  = ExplanationWhy(**why)
    what_obj = ExplanationWhat(**what)
    how_obj  = ExplanationHow(**how)

    explanation = RecommendationExplanation(
        scope=scope_obj,
        links=links_obj,
        why=why_obj,
        what=what_obj,
        how=how_obj,
        meta=meta_obj,
    )

    if db is not None:
        bind = db.get_bind()
        mi.ExplanationArchive.__table__.create(bind=bind, checkfirst=True)
        archive = mi.ExplanationArchive(
            id=f"exp_arc_{uuid.uuid4().hex[:8]}",
            recommendation_record_version_id=recommendation_record_version_id,
            explanation_payload=explanation.model_dump(mode="json"),
        )
        db.add(archive)
        db.flush()

    return explanation
