"""© 2026 TAAIP. Copyright pending.
Data Intelligence Layer: Recommendation engines for vacancy alignment, ROP/SRP advisory, school prioritization.
Generates advisory (non-autonomous) recommendations for commander decision-making.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from . import models_intelligence as mi
from .models_domain import Event, FunnelTransition
from .intelligence_explanations import build_explanation
from .services.unit_scope import get_unit_scope
from .services.versioning import create_version_event, create_archive_event
import uuid


def _resolve_recommendation_period(
    fy: Optional[str],
    quarter: Optional[str],
    lookback_days: int,
) -> Dict[str, Any]:
    """Resolve recommendation period from FY/QTR inputs or default lookback."""
    resolved_fy = fy.strip() if fy else None
    resolved_quarter = quarter.strip().upper() if quarter else None

    if resolved_fy and not resolved_fy.isdigit():
        resolved_fy = "".join(ch for ch in resolved_fy if ch.isdigit()) or None

    q_map = {
        "Q1": (10, 12),
        "Q2": (1, 3),
        "Q3": (4, 6),
        "Q4": (7, 9),
    }

    if resolved_fy and resolved_quarter in q_map:
        fy_year = int(resolved_fy)
        start_month, end_month = q_map[resolved_quarter]
        start_year = fy_year - 1 if start_month >= 10 else fy_year
        end_year = fy_year - 1 if end_month >= 10 else fy_year
        start_date = date(start_year, start_month, 1)
        if end_month == 12:
            end_date = date(end_year, 12, 31)
        else:
            end_date = date(end_year, end_month + 1, 1) - timedelta(days=1)
    elif resolved_fy:
        fy_year = int(resolved_fy)
        start_date = date(fy_year - 1, 10, 1)
        end_date = date(fy_year, 9, 30)
    else:
        start_date = date.today() - timedelta(days=lookback_days)
        end_date = date.today()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "period_analyzed": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "analysis_period_days": ((end_date - start_date).days + 1),
    }


def _resolve_period_type_value(
    period_type: Optional[str],
    period_value: Optional[str],
    fy: Optional[str],
    quarter: Optional[str],
    rsm: Optional[str],
) -> Dict[str, Optional[str]]:
    """Resolve FRAGO period metadata with explicit inputs first.

    Priority order:
    1) Explicit period_type + period_value
    2) RSM
    3) Quarter
    4) FY
    """
    if period_type and period_value:
        return {
            "period_type": str(period_type).upper(),
            "period_value": str(period_value),
        }

    if rsm:
        return {"period_type": "RSM", "period_value": rsm}
    if quarter:
        return {"period_type": "QTR", "period_value": quarter}
    if fy:
        return {"period_type": "FY", "period_value": fy}

    return {"period_type": None, "period_value": None}


class VacancyAlignmentEngine:
    """Align vacancies to market demographics, schools, industries, trends."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_vacancy_alignment(
        self,
        vacancy_mos: str,
        vacancy_count: int,
        market_zip_primary: str,
        station_rsid: str = None,
        demographic_data: Dict[str, Any] = None,
        school_data: Dict[str, Any] = None,
        industry_data: Dict[str, Any] = None,
        operational_trends: Dict[str, Any] = None
    ) -> mi.VacancyAlignment:
        """Analyze how well a vacancy aligns to market opportunities."""
        
        demographic_score = self._calculate_demographic_fit(
            vacancy_mos, market_zip_primary, demographic_data or {}
        )
        
        school_score = self._calculate_school_fit(
            vacancy_mos, market_zip_primary, school_data or {}
        )
        
        industry_score = self._calculate_industry_fit(
            vacancy_mos, market_zip_primary, industry_data or {}
        )
        
        trend_score = self._calculate_trend_fit(
            vacancy_mos, market_zip_primary, operational_trends or {}
        )
        
        overall_score = (demographic_score + school_score + industry_score + trend_score) / 4.0
        
        demand_level = self._determine_demand_level(overall_score, vacancy_count)
        
        alignment = mi.VacancyAlignment(
            id=self._generate_id("vacancy_align"),
            vacancy_mos=vacancy_mos,
            vacancy_count=vacancy_count,
            market_zip_primary=market_zip_primary,
            station_rsid=station_rsid,
            demand_level=demand_level,
            demographic_fit_score=demographic_score,
            school_population_fit=school_score,
            civilian_industry_alignment=industry_score,
            operational_trend_alignment=trend_score,
            overall_alignment_score=overall_score,
            alignment_rationale={
                "demographic": "Market demographics support this MOS demand",
                "schools": "School populations align with recruitment needs",
                "industries": "Civilian industries provide transition opportunities",
                "trends": "Operational trends indicate sustained demand"
            }
        )
        self.db.add(alignment)
        self.db.flush()
        
        # Create target populations based on alignment
        self._create_target_populations(alignment)
        
        self.db.commit()
        return alignment
    
    def _create_target_populations(self, alignment: mi.VacancyAlignment) -> None:
        """Create target population recommendations from vacancy alignment."""
        
        target_demographics = []
        messaging_themes = []
        
        # Score-based recommendations
        if alignment.demographic_fit_score > 0.7:
            target_demographics.append("18-25 year olds in urban/suburban areas")
            messaging_themes.append({
                "theme": "Career Opportunity",
                "description": "Emphasize skill development and career growth",
                "platform": "social_media"
            })
        
        if alignment.school_population_fit > 0.7:
            target_demographics.append("High school seniors and junior students")
            messaging_themes.append({
                "theme": "Education Benefits",
                "description": "Highlight GI Bill and education assistance",
                "platform": "school_events"
            })
        
        if alignment.civilian_industry_alignment > 0.7:
            target_demographics.append("Technical/mechanical industry professionals")
            messaging_themes.append({
                "theme": "Technical Skills Transfer",
                "description": "Emphasize military technical training alignment",
                "platform": "digital_ads"
            })
        
        if len(target_demographics) > 0:
            target_pop = mi.TargetPopulation(
                id=self._generate_id("target_pop"),
                vacancy_alignment_id=alignment.id,
                target_demographic=" | ".join(target_demographics),
                population_estimate=self._estimate_population(alignment),
                geographic_coverage_zips=[alignment.market_zip_primary],
                messaging_themes=messaging_themes,
                marketing_platforms=["social_media", "digital_ads", "school_events", "direct"],
                identified_at=datetime.now()
            )
            self.db.add(target_pop)
    
    @staticmethod
    def _calculate_demographic_fit(vacancy_mos: str, market_zip: str, data: Dict) -> float:
        """Calculate demographic fit score (0.0-1.0)."""
        # Placeholder: would use actual demographic data
        return 0.6
    
    @staticmethod
    def _calculate_school_fit(vacancy_mos: str, market_zip: str, data: Dict) -> float:
        """Calculate school population fit score (0.0-1.0)."""
        # Placeholder: would use actual school enrollment data
        return 0.65
    
    @staticmethod
    def _calculate_industry_fit(vacancy_mos: str, market_zip: str, data: Dict) -> float:
        """Calculate civilian industry alignment score (0.0-1.0)."""
        # Placeholder: would use industry employment data
        return 0.55
    
    @staticmethod
    def _calculate_trend_fit(vacancy_mos: str, market_zip: str, data: Dict) -> float:
        """Calculate operational trend alignment score (0.0-1.0)."""
        # Placeholder: would use historical trend data
        return 0.7
    
    @staticmethod
    def _determine_demand_level(score: float, vacancy_count: int) -> str:
        """Determine demand level from score and vacancy count."""
        if score >= 0.8 and vacancy_count >= 10:
            return "critical"
        elif score >= 0.7 and vacancy_count >= 5:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _estimate_population(alignment: mi.VacancyAlignment) -> int:
        """Estimate available population size."""
        # Placeholder: would use census/school enrollment data
        return 5000
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


class RopSrpRecommendationEngine:
    """Generate advisory recommendations for ROP/SRP changes, school prioritization, recruiter realignment."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_school_effectiveness_recommendation(
        self,
        school_name: str,
        school_zip: str,
        station_rsid: str,
        lookback_days: int = 90
    ) -> Optional[mi.AdvisoryRecommendation]:
        """Recommend ROP/SRP changes based on school effectiveness trends."""
        
        # Analyze school performance over lookback period
        period_start = date.today() - timedelta(days=lookback_days)
        
        # Get contracts from this school — expand station_rsid to full unit scope
        unit_scope = get_unit_scope(station_rsid) if station_rsid else []
        school_contracts_q = self.db.query(FunnelTransition).filter(
            FunnelTransition.transitioned_at >= period_start
        )
        if unit_scope:
            school_contracts_q = school_contracts_q.filter(
                FunnelTransition.station_rsid.in_(unit_scope)
            )
        school_contracts = school_contracts_q.all()
        
        if not school_contracts:
            return None
        
        contract_count = len(school_contracts)
        
        # Determine recommendation
        if contract_count == 0:
            recommendation_text = f"School {school_name} is underperforming. Consider reducing ROP engagement or school selection."
            priority = "high"
        elif contract_count < 2:
            recommendation_text = f"School {school_name} shows minimal production. Monitor SRP and adjust engagement strategy."
            priority = "medium"
        else:
            recommendation_text = f"School {school_name} demonstrates consistent production. Maintain current SRP level."
            priority = "low"
        
        rationale = mi.RecommendationRationale(
            id=self._generate_id("rationale"),
            recommendation_id=self._generate_id("recommendation"),
            rationale_type="school_effectiveness",
            why_summary=f"School {school_name} ({school_zip}) in {station_rsid} has generated {contract_count} contracts over {lookback_days} days.",
            supporting_data=[
                {"metric": "contracts", "value": contract_count, "threshold": 3, "trend": "stable"},
                {"metric": "period", "value": f"{lookback_days} days", "threshold": "N/A", "trend": "N/A"}
            ],
            impact_analysis={
                "if_implemented": f"Realign SRP resources to higher-performing schools",
                "financial_impact": f"Potential savings of ~${contract_count * 500}",
                "operational_impact": "Improved resource efficiency and recruiter focus"
            },
            confidence_score=0.75
        )
        self.db.add(rationale)
        self.db.flush()
        
        recommendation = mi.AdvisoryRecommendation(
            id=self._generate_id("recommendation"),
            recommendation_type="school_prioritization",
            recommendation_scope="STATION",
            scope_value=station_rsid,
            recommendation_text=recommendation_text,
            recommendation_detail={
                "school_name": school_name,
                "school_zip": school_zip,
                "contract_count": contract_count,
                "lookback_days": lookback_days,
                "suggested_action": "reduce" if contract_count < 2 else "maintain" if contract_count >= 3 else "monitor"
            },
            rationale_id=rationale.id,
            priority=priority,
            urgency="30_days" if priority == "high" else "90_days"
        )
        self.db.add(recommendation)
        self.db.commit()
        
        return recommendation
    
    def generate_recruiter_realignment_recommendation(
        self,
        recruiter_id: str,
        station_rsid: str,
        lookback_days: int = 90
    ) -> Optional[mi.AdvisoryRecommendation]:
        """Recommend recruiter realignment based on effectiveness metrics."""
        
        period_start = date.today() - timedelta(days=lookback_days)
        
        # Get recruiter effectiveness records
        effectiveness_records = self.db.query(mi.RecruiterEffectiveness).filter(
            mi.RecruiterEffectiveness.recruiter_id == recruiter_id,
            mi.RecruiterEffectiveness.period_date >= period_start
        ).all()
        
        if not effectiveness_records:
            return None
        
        # Calculate average effectiveness
        avg_contracts_per_hour = sum(
            e.contracts_per_hour or 0 for e in effectiveness_records
        ) / len(effectiveness_records) if effectiveness_records else 0
        
        avg_efficiency = sum(
            e.efficiency_index or 0 for e in effectiveness_records
        ) / len(effectiveness_records) if effectiveness_records else 0
        
        # Generate recommendation
        if avg_efficiency < 0.4:
            recommendation_text = f"Recruiter {recruiter_id} is underperforming efficiency benchmarks. Consider additional training or task rebalancing."
            priority = "high"
        elif avg_efficiency < 0.6:
            recommendation_text = f"Recruiter {recruiter_id} shows moderate efficiency. Monitor progress and provide targeted coaching."
            priority = "medium"
        else:
            recommendation_text = f"Recruiter {recruiter_id} meets or exceeds efficiency benchmarks. No action required."
            priority = "low"
        
        rationale = mi.RecommendationRationale(
            id=self._generate_id("rationale"),
            recommendation_id=self._generate_id("recommendation"),
            rationale_type="recruiter_coverage",
            why_summary=f"Recruiter {recruiter_id} in {station_rsid} shows efficiency index of {avg_efficiency:.2f} over {lookback_days} days.",
            supporting_data=[
                {"metric": "efficiency_index", "value": f"{avg_efficiency:.2f}", "threshold": "0.60", "trend": "stable"},
                {"metric": "contracts_per_hour", "value": f"{avg_contracts_per_hour:.2f}", "threshold": "1.5", "trend": "stable"}
            ],
            impact_analysis={
                "if_implemented": "Improve recruiter effectiveness and station production",
                "financial_impact": f"Potential improvement of ${avg_contracts_per_hour * 1000} annually",
                "operational_impact": "Better resource allocation and improved mission readiness"
            },
            confidence_score=0.8
        )
        self.db.add(rationale)
        self.db.flush()
        
        recommendation = mi.AdvisoryRecommendation(
            id=self._generate_id("recommendation"),
            recommendation_type="recruiter_realignment",
            recommendation_scope="STATION",
            scope_value=station_rsid,
            recommendation_text=recommendation_text,
            recommendation_detail={
                "recruiter_id": recruiter_id,
                "efficiency_index": avg_efficiency,
                "contracts_per_hour": avg_contracts_per_hour,
                "suggested_action": "train" if avg_efficiency < 0.4 else "monitor" if avg_efficiency < 0.6 else "maintain"
            },
            rationale_id=rationale.id,
            priority=priority,
            urgency="immediate" if priority == "high" else "30_days"
        )
        self.db.add(recommendation)
        self.db.commit()
        
        return recommendation
    
    def generate_market_leakage_recommendation(
        self,
        from_zip: str,
        to_zip: str,
        from_rsid: str = None,
        lookback_days: int = 90
    ) -> Optional[mi.AdvisoryRecommendation]:
        """Recommend actions to address market leakage."""
        
        # Get leakage data
        period_start = date.today() - timedelta(days=lookback_days)
        
        leakages = self.db.query(mi.MarketLeakage).filter(
            mi.MarketLeakage.from_zip == from_zip,
            mi.MarketLeakage.period_start >= period_start
        ).all()
        
        total_leaked = sum(l.contract_count or 0 for l in leakages)
        
        if total_leaked == 0:
            return None
        
        recommendation_text = f"Market leakage detected: {total_leaked} contracts lost from ZIP {from_zip}. Recommend intensified engagement and market recovery operations."
        
        rationale = mi.RecommendationRationale(
            id=self._generate_id("rationale"),
            recommendation_id=self._generate_id("recommendation"),
            rationale_type="leakage",
            why_summary=f"ZIP {from_zip} has experienced {total_leaked} contract leakage to other territories over {lookback_days} days.",
            supporting_data=[
                {"metric": "contracts_leaked", "value": total_leaked, "threshold": 5, "trend": "increasing"},
                {"metric": "target_zips", "value": to_zip, "threshold": "N/A", "trend": "N/A"}
            ],
            impact_analysis={
                "if_implemented": "Recover market share and strengthen territory control",
                "financial_impact": f"Potential recovery of ${total_leaked * 500}",
                "operational_impact": "Improved market penetration and operational influence"
            },
            confidence_score=0.85
        )
        self.db.add(rationale)
        self.db.flush()
        
        recommendation = mi.AdvisoryRecommendation(
            id=self._generate_id("recommendation"),
            recommendation_type="operation_adjustment",
            recommendation_scope="BRIGADE" if from_rsid else "USAREC",
            scope_value=from_rsid or "USAREC",
            recommendation_text=recommendation_text,
            recommendation_detail={
                "source_zip": from_zip,
                "target_zips": [to_zip],
                "contracts_leaked": total_leaked,
                "suggested_action": "intensify_engagement",
                "recovery_target": total_leaked // 2  # Suggest recovering 50% of leaked contracts
            },
            rationale_id=rationale.id,
            priority="high",
            urgency="immediate"
        )
        self.db.add(recommendation)
        self.db.commit()
        
        return recommendation
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _ensure_rop_srp_versioning_tables(db: Session) -> None:
    """Ensure plan and versioning tables exist for environments without migrations."""
    bind = db.get_bind()
    mi.RopPlan.__table__.create(bind=bind, checkfirst=True)
    mi.RopPlanVersion.__table__.create(bind=bind, checkfirst=True)
    mi.SrpPlan.__table__.create(bind=bind, checkfirst=True)
    mi.SrpPlanVersion.__table__.create(bind=bind, checkfirst=True)


def _ensure_frago_tables(db: Session) -> None:
    """Ensure FRAGO tables exist for environments without migrations."""
    bind = db.get_bind()
    mi.FragoOrder.__table__.create(bind=bind, checkfirst=True)
    mi.FragoOrderVersion.__table__.create(bind=bind, checkfirst=True)
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)


def _ensure_versioning_tables(db: Session) -> None:
    """Ensure Prompt 8 versioning tables exist."""
    bind = db.get_bind()
    mi.AnalyticsSnapshot.__table__.create(bind=bind, checkfirst=True)
    mi.AnalyticsSnapshotVersion.__table__.create(bind=bind, checkfirst=True)
    mi.RecommendationRecord.__table__.create(bind=bind, checkfirst=True)
    mi.RecommendationRecordVersion.__table__.create(bind=bind, checkfirst=True)
    mi.ExplanationArchive.__table__.create(bind=bind, checkfirst=True)
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)


def _persist_analytics_snapshot_version(
    db: Session,
    snapshot_type: str,
    station_rsid: Optional[str],
    fy: Optional[str],
    quarter: Optional[str],
    rsm: Optional[str],
    payload: Dict[str, Any],
    period_analyzed: Optional[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    """Create append-only analytics snapshot version for recommendation context."""
    _ensure_versioning_tables(db)

    snapshot = db.query(mi.AnalyticsSnapshot).filter(
        mi.AnalyticsSnapshot.snapshot_type == snapshot_type,
        mi.AnalyticsSnapshot.station_rsid == station_rsid,
        mi.AnalyticsSnapshot.fy == fy,
        mi.AnalyticsSnapshot.quarter == quarter,
        mi.AnalyticsSnapshot.rsm == rsm,
    ).order_by(mi.AnalyticsSnapshot.created_at.desc()).first()
    if not snapshot:
        snapshot = mi.AnalyticsSnapshot(
            id=f"snapshot_{uuid.uuid4().hex[:8]}",
            snapshot_type=snapshot_type,
            station_rsid=station_rsid,
            fy=fy,
            quarter=quarter,
            rsm=rsm,
        )
        db.add(snapshot)
        db.flush()

    version = create_version_event(
        db=db,
        entity_type="analytics_snapshot",
        entity_id=snapshot.id,
        content=payload,
        rsid=station_rsid,
        period_type="RSM" if rsm else ("QTR" if quarter else ("FY" if fy else None)),
        period_value=rsm or quarter or fy,
        metadata={
            "snapshot_type": snapshot_type,
            "period_analyzed": period_analyzed,
        },
    )

    create_archive_event(
        db=db,
        entity_type="analytics_snapshot",
        entity_id=snapshot.id,
        version_id=version.id,
        version_number=version.version_number,
        content=payload,
        rsid=station_rsid,
        period_type="RSM" if rsm else ("QTR" if quarter else ("FY" if fy else None)),
        period_value=rsm or quarter or fy,
        metadata={
            "snapshot_type": snapshot_type,
            "period_analyzed": period_analyzed,
            "unit_scope": get_unit_scope(station_rsid) if station_rsid else [],
        },
    )

    return {
        "analytics_snapshot_id": snapshot.id,
        "analytics_snapshot_version_id": version.id,
    }


def _persist_recommendation_record_version(
    db: Session,
    recommendation_type: str,
    station_rsid: Optional[str],
    fy: Optional[str],
    quarter: Optional[str],
    rsm: Optional[str],
    payload: Dict[str, Any],
    explanation_objects: Optional[Dict[str, Any]],
    analytics_snapshot_id: Optional[str],
) -> Dict[str, str]:
    """Create append-only recommendation record version."""
    _ensure_versioning_tables(db)

    record = db.query(mi.RecommendationRecord).filter(
        mi.RecommendationRecord.recommendation_type == recommendation_type,
        mi.RecommendationRecord.station_rsid == station_rsid,
        mi.RecommendationRecord.fy == fy,
        mi.RecommendationRecord.quarter == quarter,
        mi.RecommendationRecord.rsm == rsm,
    ).order_by(mi.RecommendationRecord.created_at.desc()).first()

    if not record:
        record = mi.RecommendationRecord(
            id=f"rec_record_{uuid.uuid4().hex[:8]}",
            recommendation_type=recommendation_type,
            station_rsid=station_rsid,
            fy=fy,
            quarter=quarter,
            rsm=rsm,
        )
        db.add(record)
        db.flush()

    version = create_version_event(
        db=db,
        entity_type="recommendation_record",
        entity_id=record.id,
        content=payload,
        rsid=station_rsid,
        period_type="RSM" if rsm else ("QTR" if quarter else ("FY" if fy else None)),
        period_value=rsm or quarter or fy,
        metadata={
            "recommendation_type": recommendation_type,
            "analytics_snapshot_id": analytics_snapshot_id,
            "explanation_objects": explanation_objects or {},
        },
    )

    create_archive_event(
        db=db,
        entity_type="recommendation_record",
        entity_id=record.id,
        version_id=version.id,
        version_number=version.version_number,
        content=payload,
        rsid=station_rsid,
        period_type="RSM" if rsm else ("QTR" if quarter else ("FY" if fy else None)),
        period_value=rsm or quarter or fy,
        metadata={
            "recommendation_type": recommendation_type,
            "analytics_snapshot_id": analytics_snapshot_id,
            "explanation_objects": explanation_objects or {},
            "unit_scope": get_unit_scope(station_rsid) if station_rsid else [],
        },
    )

    return {
        "record_id": record.id,
        "record_version_id": version.id,
    }


def _resolve_current_plan_versions(db: Session, station_rsid: Optional[str]) -> Dict[str, Optional[str]]:
    """Get or create baseline ROP/SRP plans and return current version IDs."""
    if not station_rsid:
        return {
            "rop_version_id": None,
            "srp_version_id": None,
        }

    _ensure_rop_srp_versioning_tables(db)

    rop_plan = db.query(mi.RopPlan).filter(
        mi.RopPlan.station_rsid == station_rsid,
        mi.RopPlan.status == "active",
    ).order_by(mi.RopPlan.created_at.desc()).first()
    if not rop_plan:
        rop_plan = mi.RopPlan(
            id=f"rop_plan_{uuid.uuid4().hex[:8]}",
            station_rsid=station_rsid,
            plan_name=f"ROP Baseline {station_rsid}",
            plan_scope="STATION",
            status="active",
        )
        db.add(rop_plan)
        db.flush()

    rop_version = db.query(mi.RopPlanVersion).filter(
        mi.RopPlanVersion.rop_plan_id == rop_plan.id,
        mi.RopPlanVersion.is_current == True,  # noqa: E712
    ).order_by(mi.RopPlanVersion.version_number.desc()).first()
    if not rop_version:
        rop_version = mi.RopPlanVersion(
            id=f"rop_ver_{uuid.uuid4().hex[:8]}",
            rop_plan_id=rop_plan.id,
            version_number=1,
            version_notes="Initial baseline",
            plan_payload={
                "station_rsid": station_rsid,
                "focus_schools": [],
                "weekly_school_hours_target": 40,
            },
            effective_start=date.today(),
            is_current=True,
        )
        db.add(rop_version)
        db.flush()

    srp_plan = db.query(mi.SrpPlan).filter(
        mi.SrpPlan.station_rsid == station_rsid,
        mi.SrpPlan.status == "active",
    ).order_by(mi.SrpPlan.created_at.desc()).first()
    if not srp_plan:
        srp_plan = mi.SrpPlan(
            id=f"srp_plan_{uuid.uuid4().hex[:8]}",
            station_rsid=station_rsid,
            plan_name=f"SRP Baseline {station_rsid}",
            plan_scope="STATION",
            status="active",
        )
        db.add(srp_plan)
        db.flush()

    srp_version = db.query(mi.SrpPlanVersion).filter(
        mi.SrpPlanVersion.srp_plan_id == srp_plan.id,
        mi.SrpPlanVersion.is_current == True,  # noqa: E712
    ).order_by(mi.SrpPlanVersion.version_number.desc()).first()
    if not srp_version:
        srp_version = mi.SrpPlanVersion(
            id=f"srp_ver_{uuid.uuid4().hex[:8]}",
            srp_plan_id=srp_plan.id,
            version_number=1,
            version_notes="Initial baseline",
            plan_payload={
                "station_rsid": station_rsid,
                "priority_recruiter_ids": [],
                "priority_zips": [],
            },
            effective_start=date.today(),
            is_current=True,
        )
        db.add(srp_version)
        db.flush()

    db.commit()
    return {
        "rop_version_id": rop_version.id,
        "srp_version_id": srp_version.id,
    }


def _build_linkage_analysis(all_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute adherence scores, deviations, and COA options against current baseline plans."""
    deviations: List[Dict[str, Any]] = []

    for rec in all_recommendations:
        detail = rec.get("detail") or {}
        suggested_action = str(detail.get("suggested_action") or "").lower()
        deviation_detected = suggested_action not in ("", "maintain")
        if deviation_detected:
            deviations.append({
                "recommendation_id": rec.get("recommendation_id"),
                "recommendation_type": rec.get("recommendation_type"),
                "suggested_action": suggested_action,
                "priority": rec.get("priority"),
            })

    def _score(rec_types: List[str]) -> float:
        scoped = [r for r in all_recommendations if (r.get("recommendation_type") in rec_types)]
        if not scoped:
            return 1.0
        scoped_devs = [
            r for r in scoped
            if str((r.get("detail") or {}).get("suggested_action") or "").lower() not in ("", "maintain")
        ]
        return round(max(0.0, 1.0 - (len(scoped_devs) / len(scoped))), 4)

    rop_adherence_score = _score(["school_prioritization", "rop_change"])
    srp_adherence_score = _score(["recruiter_realignment", "srp_change", "operation_adjustment"])

    coas: List[Dict[str, Any]] = []
    if rop_adherence_score < 1.0:
        coas.append({
            "coa_type": "rop_change",
            "coa_title": "ROP realignment to match current production variance",
            "expected_effect": "Improve school-level resource efficiency",
            "trigger": "ROP deviations detected",
        })
    if srp_adherence_score < 1.0:
        coas.append({
            "coa_type": "srp_change",
            "coa_title": "SRP shift for recruiter and market recovery focus",
            "expected_effect": "Increase recruiter efficiency and reduce leakage",
            "trigger": "SRP deviations detected",
        })
    if not coas:
        coas.append({
            "coa_type": "maintain",
            "coa_title": "Maintain baseline ROP/SRP posture",
            "expected_effect": "Sustain current production levels",
            "trigger": "No meaningful deviations detected",
        })

    return {
        "adherence_scoring": {
            "rop_adherence_score": rop_adherence_score,
            "srp_adherence_score": srp_adherence_score,
            "overall_adherence_score": round((rop_adherence_score + srp_adherence_score) / 2.0, 4),
        },
        "deviation_detection": deviations,
        "coa_generation": coas,
    }


def _build_frago_from_recommendation(
    db: Session,
    recommendation: Dict[str, Any],
    rop_version_id: Optional[str],
    srp_version_id: Optional[str],
    analytics_snapshot_id: Optional[str],
    recommendation_record_version_id: Optional[str] = None,
    analytics_snapshot_version_id: Optional[str] = None,
    rsid: Optional[str] = None,
    period_type: Optional[str] = None,
    period_value: Optional[str] = None,
) -> mi.FragoOrderVersion:
    """Create a new FRAGO version from a recommendation payload."""
    _ensure_frago_tables(db)

    scope = recommendation.get("scope") or {}
    station_rsid = (
        rsid
        or recommendation.get("rsid")
        or recommendation.get("station_rsid")
        or scope.get("station_rsid")
        or recommendation.get("scope_value")
        or "UNKNOWN"
    )
    period_meta = _resolve_period_type_value(
        period_type=period_type or recommendation.get("period_type"),
        period_value=period_value or recommendation.get("period_value"),
        fy=recommendation.get("fy") or scope.get("fy"),
        quarter=recommendation.get("quarter") or scope.get("quarter"),
        rsm=recommendation.get("rsm") or scope.get("rsm"),
    )
    unit_scope = get_unit_scope(station_rsid) if station_rsid and station_rsid != "UNKNOWN" else []

    frago_order = db.query(mi.FragoOrder).filter(
        mi.FragoOrder.station_rsid == station_rsid,
        mi.FragoOrder.status.in_(["draft", "issued", "active"]),
    ).order_by(mi.FragoOrder.created_at.desc()).first()

    if not frago_order:
        frago_order = mi.FragoOrder(
            id=f"frago_{uuid.uuid4().hex[:8]}",
            station_rsid=station_rsid,
            title=f"FRAGO for {station_rsid}",
            status="draft",
        )
        db.add(frago_order)
        db.flush()

    linkage_metadata = {
        "rop_version_id": rop_version_id,
        "srp_version_id": srp_version_id,
        "analytics_snapshot_id": analytics_snapshot_id,
        "recommendation_record_version_id": recommendation_record_version_id,
        "analytics_snapshot_version_id": analytics_snapshot_version_id,
    }
    period_analyzed = recommendation.get("period_analyzed")
    if not period_analyzed:
        period_analyzed = (recommendation.get("meta") or {}).get("period_analyzed")

    scope_with_drilldown = dict(scope)
    scope_with_drilldown["rsid"] = station_rsid
    scope_with_drilldown["unit_scope"] = unit_scope
    scope_with_drilldown["period_type"] = period_meta["period_type"]
    scope_with_drilldown["period_value"] = period_meta["period_value"]
    scope_with_drilldown["fy"] = recommendation.get("fy") or scope.get("fy")
    scope_with_drilldown["quarter"] = recommendation.get("quarter") or scope.get("quarter")
    scope_with_drilldown["rsm"] = recommendation.get("rsm") or scope.get("rsm")

    content = {
        "recommendation": recommendation,
        "explanation": recommendation.get("explanation") or {},
        "scope": scope_with_drilldown,
        "rsid": station_rsid,
        "unit_scope": unit_scope,
        "period_type": period_meta["period_type"],
        "period_value": period_meta["period_value"],
        "fy": scope_with_drilldown.get("fy"),
        "quarter": scope_with_drilldown.get("quarter"),
        "rsm": scope_with_drilldown.get("rsm"),
        "period_analyzed": period_analyzed,
        "linkage": linkage_metadata,
        "generated_at": datetime.now().isoformat(),
    }

    frago_version = create_version_event(
        db=db,
        entity_type="frago_order",
        entity_id=frago_order.id,
        content=content,
        rsid=station_rsid,
        period_type=period_meta["period_type"],
        period_value=period_meta["period_value"],
        metadata={
            "generated_from_recommendation_id": recommendation.get("id"),
            "rop_version_id": rop_version_id,
            "srp_version_id": srp_version_id,
            "analytics_snapshot_id": analytics_snapshot_id,
            "recommendation_record_version_id": recommendation_record_version_id,
            "analytics_snapshot_version_id": analytics_snapshot_version_id,
            "effective_start": None,
            "effective_end": None,
            "period_analyzed": period_analyzed,
        },
    )

    create_archive_event(
        db=db,
        entity_type="frago_order",
        entity_id=frago_order.id,
        version_id=frago_version.id,
        version_number=frago_version.version_number,
        content=content,
        rsid=station_rsid,
        period_type=period_meta["period_type"],
        period_value=period_meta["period_value"],
        metadata={
            "generated_from_recommendation_id": recommendation.get("id"),
            "rop_version_id": rop_version_id,
            "srp_version_id": srp_version_id,
            "analytics_snapshot_id": analytics_snapshot_id,
            "recommendation_record_version_id": recommendation_record_version_id,
            "analytics_snapshot_version_id": analytics_snapshot_version_id,
            "period_analyzed": period_analyzed,
            "unit_scope": unit_scope,
            "summary": content.get("scope", {}).get("summary") or content.get("recommendation", {}).get("summary"),
        },
    )
    return frago_version


# ============================================================================
# TOP-LEVEL RECOMMENDATION FUNCTIONS
# ============================================================================

def recommend_vacancy_alignment(
    db: Session,
    vacancy_mos: str,
    vacancy_count: int,
    market_zip_primary: str,
    station_rsid: str = None,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
    demographic_data: Dict[str, Any] = None,
    school_data: Dict[str, Any] = None,
    industry_data: Dict[str, Any] = None,
    operational_trends: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate vacancy alignment recommendations with target populations and messaging strategies.
    
    Returns structured advisory with WHY (data), WHAT (action), HOW (implementation).
    
    Args:
        db: SQLAlchemy session
        vacancy_mos: Military Occupational Specialty (e.g., "68W", "13B")
        vacancy_count: Number of open vacancies
        market_zip_primary: Primary market ZIP code
        station_rsid: Optional RSID of recruiting station
        demographic_data: Optional demographic context
        school_data: Optional school enrollment data
        industry_data: Optional civilian industry employment data
        operational_trends: Optional historical trend data
    
    Returns:
        Dict with:
        - recommendation_id: Unique recommendation identifier
        - recommendation_type: "vacancy_alignment"
        - priority: critical/high/medium/low
        - urgency: immediate/30_days/90_days/ongoing
        - data_support: WHY - supporting data and metrics
        - action_summary: WHAT - recommended actions
        - implementation_plan: HOW - detailed steps to implement
        - target_populations: Identified demographic targets
        - messaging_themes: Recommended messaging and platforms
        - commander_authority: True (advisory, commander decides)
        - confidence_score: 0.0-1.0
        - created_at: Recommendation timestamp
    """
    
    bind = db.get_bind()
    mi.VacancyAlignment.__table__.create(bind=bind, checkfirst=True)
    mi.TargetPopulation.__table__.create(bind=bind, checkfirst=True)
    _ensure_versioning_tables(db)

    engine = VacancyAlignmentEngine(db)

    try:
        alignment = engine.analyze_vacancy_alignment(
            vacancy_mos=vacancy_mos,
            vacancy_count=vacancy_count,
            market_zip_primary=market_zip_primary,
            station_rsid=station_rsid,
            demographic_data=demographic_data,
            school_data=school_data,
            industry_data=industry_data,
            operational_trends=operational_trends
        )
        
        # Determine priority and urgency
        if alignment.overall_alignment_score >= 0.8 and vacancy_count >= 10:
            priority = "critical"
            urgency = "immediate"
        elif alignment.overall_alignment_score >= 0.7 and vacancy_count >= 5:
            priority = "high"
            urgency = "30_days"
        else:
            priority = "medium"
            urgency = "90_days"
        
        # Traceability metadata
        period_context = _resolve_recommendation_period(fy=fy, quarter=quarter, lookback_days=90)
        period_analyzed = period_context["period_analyzed"]
        resolved_fy = period_context["fy"]
        resolved_quarter = period_context["quarter"]
        analytics_meta = _persist_analytics_snapshot_version(
            db=db,
            snapshot_type="vacancy_alignment",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload={
                "recommendation_type": "vacancy_alignment",
                "station_rsid": station_rsid,
                "fy": resolved_fy,
                "quarter": resolved_quarter,
                "rsm": rsm,
            },
            period_analyzed=period_analyzed,
        )
        analytics_snapshot_id = analytics_meta["analytics_snapshot_id"]
        analytics_snapshot_version_id = analytics_meta["analytics_snapshot_version_id"]
        confidence_score = round(
            0.5 + sum(
                0.1 for d in [demographic_data, school_data, industry_data, operational_trends]
                if d is not None
            ),
            2,
        )
        version_links = _resolve_current_plan_versions(db, station_rsid)
        rop_version_id = version_links["rop_version_id"]
        srp_version_id = version_links["srp_version_id"]
        frago_version_ids: List[str] = []

        # Build structured explanation via canonical builder
        explanation = build_explanation(
            why={
                "metrics": {
                    "overall_alignment_score": round(alignment.overall_alignment_score, 4),
                    "demographic_fit_score": round(alignment.demographic_fit_score, 4),
                    "school_population_fit": round(alignment.school_population_fit, 4),
                    "civilian_industry_alignment": round(alignment.civilian_industry_alignment, 4),
                    "operational_trend_alignment": round(alignment.operational_trend_alignment, 4),
                    "vacancy_count": vacancy_count,
                },
                "evidence": [
                    f"Overall alignment score: {alignment.overall_alignment_score:.1%}",
                    f"Demographic fit: {alignment.demographic_fit_score:.1%}",
                    f"School population fit: {alignment.school_population_fit:.1%}",
                    f"Civilian industry alignment: {alignment.civilian_industry_alignment:.1%}",
                    f"Operational trend alignment: {alignment.operational_trend_alignment:.1%}",
                ],
                "trend": "stable",
                "risk": "high" if alignment.demand_level in ("critical", "high") else "medium",
            },
            what={
                "action_type": "operation_adjustment",
                "action_description": (
                    f"Target identified populations for MOS {vacancy_mos} in market "
                    f"{market_zip_primary}. Demand level: {alignment.demand_level}. "
                    f"{vacancy_count} open vacancies."
                ),
                "priority": priority,
                "timeframe": urgency,
            },
            how={
                "expected_effect": (
                    "Improved vacancy fill rate through market-aligned targeting "
                    "and messaging campaign on recommended platforms."
                ),
                "mission_link": f"MOS {vacancy_mos} vacancy fill for station {station_rsid or 'N/A'}",
                "dependencies": [
                    "Commander approval",
                    "Messaging campaign activation",
                    "Recruiter briefing on target demographics",
                ],
            },
            scope={
                "station_rsid": station_rsid,
                "zip_code": market_zip_primary,
                "mos": vacancy_mos,
                "fy": resolved_fy,
                "quarter": resolved_quarter,
                "rsm": rsm,
            },
            links={
                "analytics_snapshot_id": analytics_snapshot_id,
                "rop_version_id": rop_version_id,
                "srp_version_id": srp_version_id,
            },
            meta={"confidence_score": confidence_score, "period_analyzed": period_analyzed},
            db=db,
        )
        
        # Get target populations
        target_populations = db.query(mi.TargetPopulation).filter(
            mi.TargetPopulation.vacancy_alignment_id == alignment.id
        ).all()
        
        target_pop_list = [
            {
                "demographic": tp.target_demographic,
                "population_estimate": tp.population_estimate,
                "geographic_coverage": tp.geographic_coverage_zips,
                "messaging_themes": tp.messaging_themes,
                "marketing_platforms": tp.marketing_platforms
            }
            for tp in target_populations
        ]

        draft_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="vacancy_alignment",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload={
                "recommendation_type": "vacancy_alignment",
                "recommendation_id": alignment.id,
                "status": "draft",
            },
            explanation_objects={"explanation": explanation.model_dump(mode='json')},
            analytics_snapshot_id=analytics_snapshot_id,
        )

        # Optional advisory FRAGO creation for high-impact vacancy recommendations.
        if priority in ("critical", "high"):
            frago_input = {
                "id": alignment.id,
                "recommendation_id": alignment.id,
                "recommendation_type": "vacancy_alignment",
                "priority": priority,
                "summary": f"Vacancy alignment advisory for MOS {vacancy_mos}",
                "scope": {"station_rsid": station_rsid, "zip_code": market_zip_primary, "mos": vacancy_mos},
                "station_rsid": station_rsid,
                "fy": resolved_fy,
                "quarter": resolved_quarter,
                "rsm": rsm,
                "period_analyzed": period_analyzed,
                "explanation": explanation.model_dump(mode='json'),
                "links": {
                    "analytics_snapshot_id": analytics_snapshot_id,
                    "rop_version_id": rop_version_id,
                    "srp_version_id": srp_version_id,
                },
                "meta": explanation.meta.model_dump(mode='json'),
                "detail": {
                    "overall_alignment_score": round(alignment.overall_alignment_score, 4),
                    "demand_level": alignment.demand_level,
                    "vacancy_count": vacancy_count,
                },
            }
            frago_version = _build_frago_from_recommendation(
                db,
                frago_input,
                rop_version_id,
                srp_version_id,
                analytics_snapshot_id,
                recommendation_record_version_id=draft_record_meta["record_version_id"],
                analytics_snapshot_version_id=analytics_snapshot_version_id,
                rsid=station_rsid,
                period_type="RSM" if rsm else ("QTR" if resolved_quarter else ("FY" if resolved_fy else None)),
                period_value=rsm or resolved_quarter or resolved_fy,
            )
            frago_version_ids.append(frago_version.id)
            db.commit()

        response = {
            "recommendation_id": alignment.id,
            "recommendation_type": "vacancy_alignment",
            "vacancy_mos": vacancy_mos,
            "market_zip": market_zip_primary,
            "station_rsid": station_rsid,
            "priority": priority,
            "urgency": urgency,
            "data_support": {
                "overall_alignment_score": round(alignment.overall_alignment_score, 4),
                "demand_level": alignment.demand_level,
                "demographic_fit_score": round(alignment.demographic_fit_score, 4),
                "school_fit_score": round(alignment.school_population_fit, 4),
                "industry_fit_score": round(alignment.civilian_industry_alignment, 4),
                "trend_fit_score": round(alignment.operational_trend_alignment, 4),
                "vacancy_count": vacancy_count
            },
            "explanation": explanation.model_dump(mode='json'),
            "scope": explanation.scope.model_dump(mode='json'),
            "links": explanation.links.model_dump(mode='json'),
            "meta": explanation.meta.model_dump(mode='json'),
            "target_populations": target_pop_list,
            "commander_authority": True,
            "analytics_snapshot_id": analytics_snapshot_id,
            "rop_version_id": rop_version_id,
            "srp_version_id": srp_version_id,
            "frag_order_id": None,
            "frago_version_ids": frago_version_ids,
            "period_analyzed": period_analyzed,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
            "confidence_score": confidence_score,
            "created_at": datetime.now().isoformat(),
            "status": "advisory"
        }

        final_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="vacancy_alignment",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload=response,
            explanation_objects={"explanation": response.get("explanation")},
            analytics_snapshot_id=analytics_snapshot_id,
        )
        response["recommendation_record_id"] = final_record_meta["record_id"]
        response["recommendation_record_version_id"] = final_record_meta["record_version_id"]
        db.commit()
        return response
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }


def recommend_rop_srp(
    db: Session,
    station_rsid: str,
    lookback_days: int = 90,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate ROP/SRP advisory recommendations based on school effectiveness and recruiter performance.
    
    Returns multiple advisory recommendations with WHY/WHAT/HOW structure for commander decision.
    
    Args:
        db: SQLAlchemy session
        station_rsid: Station RSID
        lookback_days: Analysis lookback period (default 90 days)
    
    Returns:
        Dict with:
        - recommendations: List of ROP/SRP advisory recommendations
        - summary: Executive summary of recommended changes
        - school_effectiveness: School-level analysis and recommendations
        - recruiter_realignment: Recruiter-level analysis and recommendations
        - market_recovery: Market leakage recovery recommendations
        - total_recommendations: Count of recommendations generated
        - commander_authority: True (all advisory, commander decides)
    """
    
    engine = RopSrpRecommendationEngine(db)
    recommendations = []

    # Traceability metadata
    period_context = _resolve_recommendation_period(fy=fy, quarter=quarter, lookback_days=lookback_days)
    period_analyzed = period_context["period_analyzed"]
    resolved_fy = period_context["fy"]
    resolved_quarter = period_context["quarter"]
    effective_lookback_days = period_context["analysis_period_days"]
    analytics_meta = _persist_analytics_snapshot_version(
        db=db,
        snapshot_type="rop_srp",
        station_rsid=station_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        payload={
            "recommendation_type": "rop_srp",
            "station_rsid": station_rsid,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        },
        period_analyzed=period_analyzed,
    )
    analytics_snapshot_id = analytics_meta["analytics_snapshot_id"]
    analytics_snapshot_version_id = analytics_meta["analytics_snapshot_version_id"]
    version_links = _resolve_current_plan_versions(db, station_rsid)
    rop_version_id = version_links["rop_version_id"]
    srp_version_id = version_links["srp_version_id"]
    frago_version_ids: List[str] = []

    try:
        # Generate school effectiveness recommendations
        school_recommendations = []
        _rop_scope = get_unit_scope(station_rsid) if station_rsid else []
        _school_q = db.query(mi.ContractClassification).filter(
            mi.ContractClassification.school_zip != None
        )
        if _rop_scope:
            _school_q = _school_q.filter(
                mi.ContractClassification.writing_rsid.in_(_rop_scope)
            )
        contracts_by_school = _school_q.all()
        
        school_map: Dict[str, int] = {}
        for contract in contracts_by_school:
            key = contract.school_zip
            if key not in school_map:
                school_map[key] = 0
            school_map[key] += 1
        
        for school_zip, contract_count in sorted(school_map.items(), key=lambda x: x[1]):
            recommendation = engine.generate_school_effectiveness_recommendation(
                school_name=f"School-{school_zip}",
                school_zip=school_zip,
                station_rsid=station_rsid,
                lookback_days=effective_lookback_days
            )
            if recommendation:
                school_recommendations.append(recommendation)
        
        # Generate recruiter realignment recommendations
        recruiter_recommendations = []
        recruiters = db.query(mi.RecruiterEffectiveness.recruiter_id).filter(
            mi.RecruiterEffectiveness.station_rsid.in_(_rop_scope) if _rop_scope else True
        ).distinct().all()
        
        for (recruiter_id,) in recruiters:
            recommendation = engine.generate_recruiter_realignment_recommendation(
                recruiter_id=recruiter_id,
                station_rsid=station_rsid,
                lookback_days=effective_lookback_days
            )
            if recommendation:
                recruiter_recommendations.append(recommendation)
        
        # Generate market leakage recovery recommendations
        leakage_recommendations = []
        leakages = db.query(mi.MarketLeakage).filter(
            mi.MarketLeakage.from_rsid.in_(_rop_scope) if _rop_scope else True
        ).all()
        
        for leakage in leakages[:3]:  # Top 3 leakage vectors
            recommendation = engine.generate_market_leakage_recommendation(
                from_zip=leakage.from_zip,
                to_zip=leakage.to_zip,
                from_rsid=station_rsid,
                lookback_days=effective_lookback_days
            )
            if recommendation:
                leakage_recommendations.append(recommendation)
        
        # Format all recommendations
        all_recommendations = []
        for rec in school_recommendations + recruiter_recommendations + leakage_recommendations:
            rationale = db.query(mi.RecommendationRationale).filter_by(id=rec.rationale_id).first()
            rec_explanation = build_explanation(
                why={
                    "metrics": {
                        k: v for k, v in (rec.recommendation_detail or {}).items()
                        if isinstance(v, (int, float))
                    },
                    "evidence": [rationale.why_summary] if rationale else [],
                    "trend": "stable",
                    "risk": rec.priority if rec.priority in ("critical", "high", "medium", "low") else "medium",
                },
                what={
                    "action_type": rec.recommendation_type,
                    "action_description": rec.recommendation_text,
                    "priority": rec.priority,
                    "timeframe": rec.urgency or "90_days",
                },
                how={
                    "expected_effect": (
                        (rationale.impact_analysis or {}).get(
                            "if_implemented", "Improve operational performance"
                        ) if rationale else "Improve operational performance"
                    ),
                    "mission_link": f"Station {station_rsid} ROP/SRP optimization",
                    "dependencies": ["Commander approval"],
                },
                scope={"station_rsid": station_rsid, "fy": resolved_fy, "quarter": resolved_quarter, "rsm": rsm},
                links={
                    "analytics_snapshot_id": analytics_snapshot_id,
                    "rop_version_id": rop_version_id,
                    "srp_version_id": srp_version_id,
                },
                meta={
                    "confidence_score": float(rationale.confidence_score)
                    if rationale and rationale.confidence_score else 0.75,
                    "period_analyzed": period_analyzed,
                },
                db=db,
            )
            all_recommendations.append({
                "recommendation_id": rec.id,
                "recommendation_type": rec.recommendation_type,
                "priority": rec.priority,
                "urgency": rec.urgency,
                "summary": rec.recommendation_text,
                "explanation": rec_explanation.model_dump(mode='json'),
                "scope": rec_explanation.scope.model_dump(mode='json'),
                "links": rec_explanation.links.model_dump(mode='json'),
                "meta": rec_explanation.meta.model_dump(mode='json'),
                "data": rationale.supporting_data if rationale else [],
                "impact": rationale.impact_analysis if rationale else {},
                "detail": rec.recommendation_detail,
                "rop_version_id": rop_version_id,
                "srp_version_id": srp_version_id,
                "commander_authority": True,
                "status": "advisory"
            })

        linkage_analysis = _build_linkage_analysis(all_recommendations)

        draft_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="rop_srp",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload={
                "recommendation_type": "rop_srp",
                "station_rsid": station_rsid,
                "recommendation_count": len(all_recommendations),
                "status": "draft",
            },
            explanation_objects={
                "recommendations": [r.get("explanation") for r in all_recommendations],
            },
            analytics_snapshot_id=analytics_snapshot_id,
        )

        deviation_ids = {
            d.get("recommendation_id")
            for d in linkage_analysis.get("deviation_detection", [])
            if d.get("recommendation_id")
        }
        for rec_payload in all_recommendations:
            should_create_frago = (
                rec_payload.get("priority") in ("critical", "high")
                or rec_payload.get("recommendation_id") in deviation_ids
            )
            if not should_create_frago:
                continue

            frago_input = dict(rec_payload)
            frago_input["id"] = rec_payload.get("recommendation_id")
            frago_input["station_rsid"] = station_rsid
            frago_input["fy"] = resolved_fy
            frago_input["quarter"] = resolved_quarter
            frago_input["rsm"] = rsm
            frago_input["period_analyzed"] = period_analyzed
            frago_version = _build_frago_from_recommendation(
                db,
                frago_input,
                rop_version_id,
                srp_version_id,
                analytics_snapshot_id,
                recommendation_record_version_id=draft_record_meta["record_version_id"],
                analytics_snapshot_version_id=analytics_snapshot_version_id,
                rsid=station_rsid,
                period_type="RSM" if rsm else ("QTR" if resolved_quarter else ("FY" if resolved_fy else None)),
                period_value=rsm or resolved_quarter or resolved_fy,
            )
            frago_version_ids.append(frago_version.id)
        db.commit()
        
        # Build executive summary
        summary_text = f"""
ROP/SRP Analysis for {station_rsid} ({lookback_days} day lookback):

Schools Analyzed: {len(school_map)}
Underperforming Schools: {len([r for r in school_recommendations if 'underperforming' in r.recommendation_text.lower()])}
Recruiters Reviewed: {len(recruiters)}
Recruiters Below Efficiency Target: {len([r for r in recruiter_recommendations if 'underperforming' in r.recommendation_text.lower()])}
Market Leakage Vectors: {len(leakage_recommendations)}

Key Recommendations:
- Reduce ROP engagement at {len([r for r in school_recommendations if 'underperforming' in r.recommendation_text.lower()])} underperforming schools
- Provide coaching to {len([r for r in recruiter_recommendations if 'training' in r.recommendation_detail.get('suggested_action', '').lower()])} recruiters
- Implement market recovery operations in {len(leakage_recommendations)} leakage hotspots

All recommendations are ADVISORY. Final decisions remain with commanding officer.
"""
        
        response = {
            "station_rsid": station_rsid,
            "recommendations": all_recommendations,
            "summary": summary_text,
            "school_effectiveness_count": len(school_recommendations),
            "recruiter_realignment_count": len(recruiter_recommendations),
            "market_recovery_count": len(leakage_recommendations),
            "total_recommendations": len(all_recommendations),
            "adherence_scoring": linkage_analysis["adherence_scoring"],
            "deviation_detection": linkage_analysis["deviation_detection"],
            "coa_generation": linkage_analysis["coa_generation"],
            "commander_authority": True,
            "analytics_snapshot_id": analytics_snapshot_id,
            "rop_version_id": rop_version_id,
            "srp_version_id": srp_version_id,
            "frag_order_id": None,
            "frago_version_ids": frago_version_ids,
            "period_analyzed": period_analyzed,
            "analysis_period_days": effective_lookback_days,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
            "generated_at": datetime.now().isoformat(),
            "status": "complete"
        }

        final_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="rop_srp",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload=response,
            explanation_objects={
                "recommendations": [r.get("explanation") for r in all_recommendations],
            },
            analytics_snapshot_id=analytics_snapshot_id,
        )
        response["recommendation_record_id"] = final_record_meta["record_id"]
        response["recommendation_record_version_id"] = final_record_meta["record_version_id"]
        db.commit()
        return response
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }


def recommend_school_prioritization(
    db: Session,
    station_rsid: str,
    lookback_days: int = 180,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate school prioritization recommendations based on production trends.
    
    Returns advisory with WHY/WHAT/HOW for school ROP allocation decisions.
    
    Args:
        db: SQLAlchemy session
        station_rsid: Station RSID
        lookback_days: Analysis lookback period (default 180 days)
    
    Returns:
        Dict with:
        - school_rankings: Schools ranked by effectiveness
        - rop_allocation_current: Current ROP allocation per school
        - rop_allocation_recommended: Recommended ROP allocation per school
        - why: Data supporting recommendations
        - what: Recommended actions
        - how: Implementation steps
        - commander_authority: True (advisory, commander decides)
        - confidence_score: 0.0-1.0
    """
    
    try:
        period_context = _resolve_recommendation_period(fy=fy, quarter=quarter, lookback_days=lookback_days)
        period_start = period_context["start_date"]
        period_end = period_context["end_date"]
        period_analyzed = period_context["period_analyzed"]
        resolved_fy = period_context["fy"]
        resolved_quarter = period_context["quarter"]
        effective_lookback_days = period_context["analysis_period_days"]
        
        # Get school contracts — expand station_rsid to full unit scope
        _sp_scope = get_unit_scope(station_rsid) if station_rsid else []
        _contracts_q = db.query(mi.ContractClassification).filter(
            mi.ContractClassification.school_zip != None,
            mi.ContractClassification.classified_at >= period_start,
            mi.ContractClassification.classified_at <= period_end,
        )
        if _sp_scope:
            _contracts_q = _contracts_q.filter(
                mi.ContractClassification.writing_rsid.in_(_sp_scope)
            )
        contracts = _contracts_q.all()
        
        # Score schools by production
        school_scores: Dict[str, Dict[str, Any]] = {}
        for contract in contracts:
            school_zip = contract.school_zip
            if school_zip not in school_scores:
                school_scores[school_zip] = {
                    "total_contracts": 0,
                    "average_quality": 0.0,
                    "rop_allocation_current": 5.0  # Placeholder: hours per week
                }
            school_scores[school_zip]["total_contracts"] += 1
        
        # Rank schools
        school_rankings = sorted(
            [
                {
                    "school_zip": zip_code,
                    "contracts_generated": data["total_contracts"],
                    "effectiveness_score": min(data["total_contracts"] / 5.0, 1.0),
                    "priority_tier": "high" if data["total_contracts"] >= 5 else ("medium" if data["total_contracts"] >= 2 else "low"),
                    "rop_current_hours_per_week": data["rop_allocation_current"]
                }
                for zip_code, data in school_scores.items()
            ],
            key=lambda x: x["contracts_generated"],
            reverse=True
        )
        
        # Calculate recommended allocation
        total_rop_hours = sum(s["rop_current_hours_per_week"] for s in school_rankings)
        recommended_allocation = [
            {
                "school_zip": school["school_zip"],
                "priority_tier": school["priority_tier"],
                "rop_recommended_hours_per_week": (school["effectiveness_score"] * total_rop_hours * 0.7) if school["priority_tier"] == "high" else (school["effectiveness_score"] * total_rop_hours * 0.2) if school["priority_tier"] == "medium" else (school["effectiveness_score"] * total_rop_hours * 0.1),
                "action": "maintain" if school["effectiveness_score"] > 0.7 else ("increase" if school["effectiveness_score"] > 0.4 else "decrease")
            }
            for school in school_rankings
        ]
        
        _high = [s for s in school_rankings if s['priority_tier'] == 'high']
        _med  = [s for s in school_rankings if s['priority_tier'] == 'medium']
        _low  = [s for s in school_rankings if s['priority_tier'] == 'low']
        _total_contracts = sum(s['contracts_generated'] for s in school_rankings)
        _avg_contracts = round(_total_contracts / len(school_rankings), 2) if school_rankings else 0.0
        _increase_count = len([r for r in recommended_allocation if r['action'] == 'increase'])
        _decrease_count = len([r for r in recommended_allocation if r['action'] == 'decrease'])

        # Traceability metadata
        analytics_meta = _persist_analytics_snapshot_version(
            db=db,
            snapshot_type="school_prioritization",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload={
                "recommendation_type": "school_prioritization",
                "station_rsid": station_rsid,
                "fy": resolved_fy,
                "quarter": resolved_quarter,
                "rsm": rsm,
            },
            period_analyzed=period_analyzed,
        )
        analytics_snapshot_id = analytics_meta["analytics_snapshot_id"]
        analytics_snapshot_version_id = analytics_meta["analytics_snapshot_version_id"]
        version_links = _resolve_current_plan_versions(db, station_rsid)
        rop_version_id = version_links["rop_version_id"]
        srp_version_id = version_links["srp_version_id"]
        frago_version_ids: List[str] = []

        explanation = build_explanation(
            why={
                "metrics": {
                    "total_schools": len(school_rankings),
                    "high_performers": len(_high),
                    "medium_performers": len(_med),
                    "low_performers": len(_low),
                    "total_contracts": _total_contracts,
                    "avg_contracts_per_school": _avg_contracts,
                },
                "evidence": [
                    f"{len(_high)} high-performing schools identified",
                    f"{len(_med)} medium-performing schools",
                    f"{len(_low)} low-performing schools requiring reduced ROP",
                    f"Total contracts generated: {_total_contracts} over {lookback_days} days",
                    f"FY/QTR scope: {resolved_fy or 'N/A'} {resolved_quarter or ''}".strip(),
                ],
                "trend": "stable",
                "risk": "high" if _low else "medium",
            },
            what={
                "action_type": "school_prioritization",
                "action_description": (
                    f"Realign ROP allocation across {len(school_rankings)} schools. "
                    f"Increase engagement at {_increase_count} high-performing schools; "
                    f"decrease at {_decrease_count} underperforming schools."
                ),
                "priority": "high" if _low else "medium",
                "timeframe": "30_days",
            },
            how={
                "expected_effect": (
                    "Optimized ROP hours allocation improves per-school production "
                    "and reduces wasted recruiter effort at low-yield schools."
                ),
                "mission_link": f"Station {station_rsid} school engagement plan",
                "dependencies": [
                    "Commander approval",
                    "Updated ROP schedule issuance",
                    "Recruiter briefing on new school priorities",
                ],
            },
            scope={"station_rsid": station_rsid, "fy": resolved_fy, "quarter": resolved_quarter, "rsm": rsm},
            links={
                "analytics_snapshot_id": analytics_snapshot_id,
                "rop_version_id": rop_version_id,
                "srp_version_id": srp_version_id,
            },
            meta={
                "confidence_score": 0.80,
                "period_analyzed": {
                    "start_date": period_start.isoformat(),
                    "end_date": period_end.isoformat(),
                },
            },
            db=db,
        )

        draft_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="school_prioritization",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload={
                "recommendation_type": "school_prioritization",
                "station_rsid": station_rsid,
                "school_count": len(school_rankings),
                "status": "draft",
            },
            explanation_objects={"explanation": explanation.model_dump(mode='json')},
            analytics_snapshot_id=analytics_snapshot_id,
        )

        school_priority = "high" if _low else "medium"
        if school_priority in ("critical", "high"):
            frago_input = {
                "id": f"school_prio_{station_rsid}_{date.today().isoformat()}",
                "recommendation_id": None,
                "recommendation_type": "school_prioritization",
                "priority": school_priority,
                "summary": f"School prioritization advisory for {station_rsid}",
                "scope": {"station_rsid": station_rsid},
                "station_rsid": station_rsid,
                "fy": resolved_fy,
                "quarter": resolved_quarter,
                "rsm": rsm,
                "period_analyzed": period_analyzed,
                "explanation": explanation.model_dump(mode='json'),
                "links": {
                    "analytics_snapshot_id": analytics_snapshot_id,
                    "rop_version_id": rop_version_id,
                    "srp_version_id": srp_version_id,
                },
                "meta": explanation.meta.model_dump(mode='json'),
                "detail": {
                    "high_priority_count": len(_high),
                    "medium_priority_count": len(_med),
                    "low_priority_count": len(_low),
                    "lookback_days": lookback_days,
                },
            }
            frago_version = _build_frago_from_recommendation(
                db,
                frago_input,
                rop_version_id,
                srp_version_id,
                analytics_snapshot_id,
                recommendation_record_version_id=draft_record_meta["record_version_id"],
                analytics_snapshot_version_id=analytics_snapshot_version_id,
                rsid=station_rsid,
                period_type="RSM" if rsm else ("QTR" if resolved_quarter else ("FY" if resolved_fy else None)),
                period_value=rsm or resolved_quarter or resolved_fy,
            )
            frago_version_ids.append(frago_version.id)
            db.commit()

        response = {
            "station_rsid": station_rsid,
            "analysis_period_days": effective_lookback_days,
            "school_rankings": school_rankings,
            "rop_allocation_recommended": recommended_allocation,
            "explanation": explanation.model_dump(mode='json'),
            "scope": explanation.scope.model_dump(mode='json'),
            "links": explanation.links.model_dump(mode='json'),
            "meta": explanation.meta.model_dump(mode='json'),
            "summary": {
                "high_priority_count": len([s for s in school_rankings if s['priority_tier'] == 'high']),
                "medium_priority_count": len([s for s in school_rankings if s['priority_tier'] == 'medium']),
                "low_priority_count": len([s for s in school_rankings if s['priority_tier'] == 'low']),
                "total_contracts": sum(s['contracts_generated'] for s in school_rankings),
                "average_effectiveness": sum(s['effectiveness_score'] for s in school_rankings) / len(school_rankings) if school_rankings else 0.0,
                "rop_plan_alignment_score": round(
                    1.0 - (
                        len([r for r in recommended_allocation if r["action"] in ("decrease", "increase")]) / max(1, len(recommended_allocation))
                    ),
                    4,
                ),
            },
            "commander_authority": True,
            "analytics_snapshot_id": analytics_snapshot_id,
            "rop_version_id": rop_version_id,
            "srp_version_id": srp_version_id,
            "frag_order_id": None,
            "frago_version_ids": frago_version_ids,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
            },
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
            "confidence_score": 0.80,
            "generated_at": datetime.now().isoformat(),
            "status": "complete"
        }

        final_record_meta = _persist_recommendation_record_version(
            db=db,
            recommendation_type="school_prioritization",
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            payload=response,
            explanation_objects={"explanation": response.get("explanation")},
            analytics_snapshot_id=analytics_snapshot_id,
        )
        response["recommendation_record_id"] = final_record_meta["record_id"]
        response["recommendation_record_version_id"] = final_record_meta["record_version_id"]
        db.commit()
        return response
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }
