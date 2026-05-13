"""© 2026 TAAIP. Copyright pending.
Data Intelligence Layer: Analytics engines for snapshots, OOA contracts, recruiter effectiveness, vacancy alignment.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from . import models_intelligence as mi
from .models_domain import Event, EventMetric, MarketingActivity, FunnelTransition
from .services.unit_scope import get_unit_scope
from .services.versioning import create_version_event, create_archive_event
import uuid


def _resolve_period_scope(
    period_start: Optional[date],
    period_end: Optional[date],
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
) -> Tuple[date, date, Optional[str], Optional[str], str]:
    """Resolve analysis period from explicit dates or FY/quarter drilldown."""
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
        resolved_start = date(start_year, start_month, 1)
        if end_month == 12:
            resolved_end = date(end_year, 12, 31)
        else:
            resolved_end = date(end_year, end_month + 1, 1) - timedelta(days=1)
    elif resolved_fy:
        fy_year = int(resolved_fy)
        resolved_start = date(fy_year - 1, 10, 1)
        resolved_end = date(fy_year, 9, 30)
    else:
        resolved_start = period_start or (date.today() - timedelta(days=90))
        resolved_end = period_end or date.today()

    period_label = f"{resolved_start.isoformat()} to {resolved_end.isoformat()}"
    return resolved_start, resolved_end, resolved_fy, resolved_quarter, period_label


def _apply_rsm_filter(query: Any, column: Any, rsm: Optional[str]) -> Any:
    """Apply additive RSM filtering using exact or prefix station matching."""
    if not rsm:
        return query
    return query.filter(or_(column == rsm, column.like(f"{rsm}%")))


def _persist_analytics_snapshot(
    db: Session,
    snapshot_type: str,
    payload: Dict[str, Any],
    station_rsid: Optional[str],
    fy: Optional[str],
    quarter: Optional[str],
    rsm: Optional[str],
    period_analyzed: Optional[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    """Persist analytics payload as append-only snapshot version."""
    bind = db.get_bind()
    mi.AnalyticsSnapshot.__table__.create(bind=bind, checkfirst=True)
    mi.AnalyticsSnapshotVersion.__table__.create(bind=bind, checkfirst=True)
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)

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

    period_type = "RSM" if rsm else ("QTR" if quarter else ("FY" if fy else None))
    period_value = rsm or quarter or fy

    version = create_version_event(
        db=db,
        entity_type="analytics_snapshot",
        entity_id=snapshot.id,
        content=payload,
        rsid=station_rsid,
        period_type=period_type,
        period_value=period_value,
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
        period_type=period_type,
        period_value=period_value,
        metadata={
            "snapshot_type": snapshot_type,
            "period_analyzed": period_analyzed,
            "unit_scope": [station_rsid] if station_rsid else [],
        },
    )

    return {
        "analytics_snapshot_id": snapshot.id,
        "analytics_snapshot_version_id": version.id,
    }


class HistoricalSnapshotEngine:
    """Create daily/weekly/monthly snapshots and preserve historical data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_snapshot(
        self,
        snapshot_type: str,  # "daily", "weekly", "monthly", "event_triggered"
        snapshot_date: date,
        scope_type: str,  # "USAREC", "BRIGADE", "BATTALION", "COMPANY", "STATION"
        scope_value: str,
        trigger_event: str = None,
        metrics: Dict[str, float] = None
    ) -> mi.HistoricalSnapshot:
        """Create a historical snapshot."""
        
        snapshot = mi.HistoricalSnapshot(
            id=self._generate_id("snapshot"),
            snapshot_type=snapshot_type,
            snapshot_date=snapshot_date,
            scope_type=scope_type,
            scope_value=scope_value,
            trigger_event=trigger_event,
            data_version=self._get_next_version(snapshot_date, scope_type, scope_value)
        )
        self.db.add(snapshot)
        self.db.flush()
        
        # Store metrics
        if metrics:
            for metric_name, metric_value in metrics.items():
                metric_record = mi.SnapshotMetric(
                    id=self._generate_id("snapshot_metric"),
                    snapshot_id=snapshot.id,
                    metric_name=metric_name,
                    metric_value=metric_value
                )
                self.db.add(metric_record)
        
        self.db.commit()
        return snapshot
    
    def _get_next_version(self, snapshot_date: date, scope_type: str, scope_value: str) -> int:
        """Get next version number for same date/scope."""
        count = self.db.query(mi.HistoricalSnapshot).filter(
            mi.HistoricalSnapshot.snapshot_date == snapshot_date,
            mi.HistoricalSnapshot.scope_type == scope_type,
            mi.HistoricalSnapshot.scope_value == scope_value
        ).count()
        return count + 1
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


class OutOfAreaContractAnalytics:
    """Classify and analyze out-of-area contracts, market leakage, cross-market influence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def classify_contract(
        self,
        contract_id: str,
        applicant_zip: str = None,
        assigned_zip: str = None,
        writing_rsid: str = None,
        assigned_rsid: str = None,
        school_zip: str = None,
        event_zip: str = None,
        originating_operation: str = None
    ) -> mi.ContractClassification:
        """Classify a contract as in-area, out-of-area, imported, exported, or cross-market."""
        
        classification = self._determine_classification(
            applicant_zip, assigned_zip, writing_rsid, assigned_rsid
        )
        
        confidence = self._calculate_confidence(
            applicant_zip, assigned_zip, writing_rsid, assigned_rsid
        )
        
        record = mi.ContractClassification(
            id=self._generate_id("contract_class"),
            contract_id=contract_id,
            applicant_zip=applicant_zip,
            assigned_zip=assigned_zip,
            writing_rsid=writing_rsid,
            assigned_rsid=assigned_rsid,
            school_zip=school_zip,
            event_zip=event_zip,
            originating_operation=originating_operation,
            classification=classification,
            classification_confidence=confidence,
            market_penetration_score=self._calculate_market_penetration(assigned_zip),
            territory_control_score=self._calculate_territory_control(writing_rsid, assigned_rsid),
            operational_influence_score=self._calculate_operational_influence(
                applicant_zip, assigned_zip, writing_rsid, assigned_rsid
            ),
            classified_by='analytics_engine'
        )
        self.db.add(record)
        self.db.commit()
        
        return record
    
    def track_market_leakage(
        self,
        from_zip: str,
        to_zip: str,
        from_rsid: str = None,
        to_rsid: str = None,
        period_start: date = None,
        period_end: date = None
    ) -> mi.MarketLeakage:
        """Track market leakage between territories."""
        
        # Count leakage metrics
        classifications = self.db.query(mi.ContractClassification).filter(
            mi.ContractClassification.applicant_zip == from_zip,
            mi.ContractClassification.assigned_zip == to_zip,
            mi.ContractClassification.classified_at >= period_start if period_start else True,
            mi.ContractClassification.classified_at <= period_end if period_end else True
        ).all()
        
        leak_type = self._determine_leak_type(from_zip, to_zip, from_rsid, to_rsid)
        
        leakage = mi.MarketLeakage(
            id=self._generate_id("leakage"),
            from_zip=from_zip,
            to_zip=to_zip,
            from_rsid=from_rsid,
            to_rsid=to_rsid,
            leak_type=leak_type,
            contract_count=len(classifications),
            lead_count=len([c for c in classifications if c.applicant_zip == from_zip]),
            period_start=period_start or date.today(),
            period_end=period_end or date.today()
        )
        self.db.add(leakage)
        self.db.commit()
        
        return leakage
    
    @staticmethod
    def _determine_classification(applicant_zip: str, assigned_zip: str, 
                                  writing_rsid: str, assigned_rsid: str) -> str:
        """Determine contract classification based on geography and organization."""
        if not assigned_zip or not applicant_zip:
            return "unknown"
        
        if applicant_zip == assigned_zip:
            return "in_area"
        elif writing_rsid and assigned_rsid and writing_rsid != assigned_rsid:
            return "cross_market"
        elif assigned_rsid and applicant_zip:
            # Check if assigned_zip is outside writing_rsid territory
            return "out_of_area"
        else:
            return "imported"
    
    @staticmethod
    def _calculate_confidence(applicant_zip: str, assigned_zip: str,
                             writing_rsid: str, assigned_rsid: str) -> float:
        """Calculate confidence of classification."""
        confidence = 0.0
        if applicant_zip:
            confidence += 0.25
        if assigned_zip:
            confidence += 0.25
        if writing_rsid:
            confidence += 0.25
        if assigned_rsid:
            confidence += 0.25
        return min(confidence, 1.0)
    
    @staticmethod
    def _calculate_market_penetration(assigned_zip: str) -> float:
        """Calculate market penetration score (0.0-1.0)."""
        # Placeholder: would need actual market data
        return 0.5
    
    @staticmethod
    def _calculate_territory_control(writing_rsid: str, assigned_rsid: str) -> float:
        """Calculate territory control score (0.0-1.0)."""
        # Placeholder: would need actual territory data
        return 1.0 if writing_rsid == assigned_rsid else 0.3
    
    @staticmethod
    def _calculate_operational_influence(applicant_zip: str, assigned_zip: str,
                                        writing_rsid: str, assigned_rsid: str) -> float:
        """Calculate operational influence score (0.0-1.0)."""
        # Placeholder: would need actual operational data
        return 0.5
    
    @staticmethod
    def _determine_leak_type(from_zip: str, to_zip: str,
                            from_rsid: str, to_rsid: str) -> str:
        """Determine type of leakage."""
        if from_rsid and to_rsid and from_rsid != to_rsid:
            return "cross_rsid"
        elif from_zip and to_zip and from_zip != to_zip:
            return "out_of_territory"
        else:
            return "territory_loss"
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


class RecruiterEffectivenessAnalytics:
    """Calculate recruiter operational effectiveness metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_effectiveness(
        self,
        recruiter_id: str,
        period_date: date,
        reporting_period: str = "monthly",
        station_rsid: str = None
    ) -> mi.RecruiterEffectiveness:
        """Calculate recruiter effectiveness metrics for a period."""
        
        # Get recruiter activities for period
        if reporting_period == "daily":
            period_start = period_date
            period_end = period_date
        elif reporting_period == "weekly":
            period_start = period_date - timedelta(days=period_date.weekday())
            period_end = period_start + timedelta(days=6)
        else:  # monthly
            period_start = date(period_date.year, period_date.month, 1)
            if period_date.month == 12:
                period_end = date(period_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(period_date.year, period_date.month + 1, 1) - timedelta(days=1)
        
        activities = self.db.query(mi.RecruiterActivity).filter(
            mi.RecruiterActivity.recruiter_id == recruiter_id,
            mi.RecruiterActivity.activity_date >= period_start,
            mi.RecruiterActivity.activity_date <= period_end
        ).all()
        
        # Aggregate metrics
        prospecting_hours = sum(
            a.activity_duration_hours or 0 
            for a in activities if a.activity_type == 'prospecting'
        ) or None
        
        contacts_count = sum(
            a.activity_count or 0
            for a in activities if a.activity_type == 'contact'
        ) or None
        
        appointments_count = sum(
            a.activity_count or 0
            for a in activities if a.activity_type == 'appointment'
        ) or None
        
        attempts_count = sum(
            a.activity_count or 0
            for a in activities if a.activity_type == 'attempt'
        ) or None
        
        contracts_count = sum(
            a.outcome_count or 0
            for a in activities if a.activity_type == 'enlistment'
        ) or None
        
        # Calculate derived metrics
        contacts_per_hour = contacts_count / prospecting_hours if prospecting_hours and prospecting_hours > 0 else None
        appointments_per_hour = appointments_count / prospecting_hours if prospecting_hours and prospecting_hours > 0 else None
        contracts_per_hour = contracts_count / prospecting_hours if prospecting_hours and prospecting_hours > 0 else None
        attempts_per_hour = attempts_count / prospecting_hours if prospecting_hours and prospecting_hours > 0 else None
        attempts_per_appointment = attempts_count / appointments_count if appointments_count and appointments_count > 0 else None
        hours_per_appointment = prospecting_hours / appointments_count if appointments_count and appointments_count > 0 else None
        hours_per_enlistment = prospecting_hours / contracts_count if contracts_count and contracts_count > 0 else None
        
        contact_conversion_rate = appointments_count / contacts_count if contacts_count and contacts_count > 0 else None
        appointment_conversion_rate = contracts_count / appointments_count if appointments_count and appointments_count > 0 else None
        overall_conversion_rate = contracts_count / contacts_count if contacts_count and contacts_count > 0 else None
        
        # Placeholder efficiency scores
        efficiency_index = self._calculate_efficiency_index(
            contacts_per_hour, appointments_per_hour, contracts_per_hour
        )
        effort_index = self._calculate_effort_index(prospecting_hours, contacts_count)
        
        record = mi.RecruiterEffectiveness(
            id=self._generate_id("effectiveness"),
            recruiter_id=recruiter_id,
            station_rsid=station_rsid,
            reporting_period=reporting_period,
            period_date=period_date,
            prospecting_hours=prospecting_hours,
            contacts_count=contacts_count,
            appointments_count=appointments_count,
            attempts_count=attempts_count,
            contracts_count=contracts_count,
            contacts_per_hour=contacts_per_hour,
            appointments_per_hour=appointments_per_hour,
            contracts_per_hour=contracts_per_hour,
            attempts_per_hour=attempts_per_hour,
            attempts_per_appointment=attempts_per_appointment,
            hours_per_appointment=hours_per_appointment,
            hours_per_enlistment=hours_per_enlistment,
            contact_conversion_rate=contact_conversion_rate,
            appointment_conversion_rate=appointment_conversion_rate,
            overall_conversion_rate=overall_conversion_rate,
            efficiency_index=efficiency_index,
            effort_index=effort_index
        )
        self.db.add(record)
        self.db.commit()
        
        return record
    
    @staticmethod
    def _calculate_efficiency_index(contacts_per_hour: float, 
                                   appointments_per_hour: float,
                                   contracts_per_hour: float) -> Optional[float]:
        """Calculate efficiency index (0.0-1.0)."""
        if not any([contacts_per_hour, appointments_per_hour, contracts_per_hour]):
            return None
        # Placeholder: would compare to peer benchmarks
        return 0.5
    
    @staticmethod
    def _calculate_effort_index(prospecting_hours: float, contacts_count: int) -> Optional[float]:
        """Calculate effort index (0.0-1.0)."""
        if not prospecting_hours or prospecting_hours <= 0:
            return None
        # Placeholder: would compare to peer benchmarks
        return min(prospecting_hours / 200.0, 1.0)  # Assume 200 hrs/month is max
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


class PredictiveProductionPacingEngine:
    """Predict recruiter production pacing based on current trends."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def forecast_production(
        self,
        recruiter_id: str,
        forecast_period: str = "monthly",  # "weekly", "monthly", "quarterly"
        as_of_date: date = None,
        station_rsid: str = None
    ) -> mi.PredictiveProductionPace:
        """Forecast recruiter production based on recent effectiveness trends."""
        
        as_of_date = as_of_date or date.today()
        
        # Get recent effectiveness records
        lookback_days = 30 if forecast_period == "weekly" else (90 if forecast_period == "monthly" else 180)
        start_date = as_of_date - timedelta(days=lookback_days)
        
        recent_effectiveness = self.db.query(mi.RecruiterEffectiveness).filter(
            mi.RecruiterEffectiveness.recruiter_id == recruiter_id,
            mi.RecruiterEffectiveness.period_date >= start_date,
            mi.RecruiterEffectiveness.period_date <= as_of_date
        ).all()
        
        if not recent_effectiveness:
            return None
        
        # Calculate average metrics
        avg_contracts_per_hr = sum(
            e.contracts_per_hour or 0 for e in recent_effectiveness
        ) / len(recent_effectiveness) if recent_effectiveness else 0
        
        avg_hours = sum(
            e.prospecting_hours or 0 for e in recent_effectiveness
        ) / len(recent_effectiveness) if recent_effectiveness else 0
        
        # Project forward
        if forecast_period == "weekly":
            projected_hours = avg_hours
        elif forecast_period == "monthly":
            projected_hours = avg_hours * 4
        else:  # quarterly
            projected_hours = avg_hours * 12
        
        predicted_contracts = int(projected_hours * avg_contracts_per_hr) if avg_contracts_per_hr > 0 else 0
        confidence = min(len(recent_effectiveness) / 12.0, 1.0)  # More data = higher confidence
        
        record = mi.PredictiveProductionPace(
            id=self._generate_id("pace"),
            recruiter_id=recruiter_id,
            station_rsid=station_rsid,
            forecast_period=forecast_period,
            as_of_date=as_of_date,
            predicted_contracts=predicted_contracts,
            predicted_contracts_low_bound=int(predicted_contracts * 0.85),
            predicted_contracts_high_bound=int(predicted_contracts * 1.15),
            confidence_level=confidence,
            pacing_vs_goal=self._assess_pacing(predicted_contracts),
            pacing_gap_contracts=self._calculate_pacing_gap(predicted_contracts)
        )
        self.db.add(record)
        self.db.commit()
        
        return record
    
    @staticmethod
    def _assess_pacing(predicted_contracts: int, goal: int = None) -> str:
        """Assess pacing vs goal."""
        goal = goal or 12  # Default monthly goal
        if predicted_contracts >= goal:
            return "on_track" if predicted_contracts <= goal * 1.1 else "ahead"
        else:
            return "behind"
    
    @staticmethod
    def _calculate_pacing_gap(predicted_contracts: int, goal: int = None) -> int:
        """Calculate gap between prediction and goal."""
        goal = goal or 12
        return predicted_contracts - goal
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ============================================================================
# TOP-LEVEL ANALYTICS FUNCTIONS
# ============================================================================

def analyze_contract_roi(
    db: Session,
    station_rsid: str = None,
    event_type: str = None,
    period_start: date = None,
    period_end: date = None,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze event-level and category-level ROI. Calculate cost per lead, cost per conversion,
    conversion rates, and engagement metrics.
    
    Args:
        db: SQLAlchemy session
        station_rsid: Optional filter by station
        event_type: Optional filter by event type
        period_start: Optional start date filter
        period_end: Optional end date filter
    
    Returns:
        Dict with:
        - event_level_roi: List of ROI metrics per event
        - category_roi: Aggregated ROI by event_type
        - summary_metrics: Overall ROI summary
        - confidence: Data completeness score (0.0-1.0)
    """
    
    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )
    
    # Query events and their metrics
    query = db.query(Event, EventMetric).join(
        EventMetric, Event.id == EventMetric.event_id
    ).filter(
        EventMetric.metric_date >= period_start,
        EventMetric.metric_date <= period_end
    )
    
    if station_rsid:
        query = query.filter(Event.station_rsid.in_(get_unit_scope(station_rsid)))
    query = _apply_rsm_filter(query, Event.station_rsid, rsm)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    results = query.all()
    
    if not results:
        response = {
            "event_level_roi": [],
            "category_roi": {},
            "summary_metrics": {
                "total_events": 0,
                "total_cost": 0.0,
                "total_leads": 0,
                "total_conversions": 0,
                "overall_roi": None,
                "overall_cost_per_lead": None,
                "overall_cost_per_conversion": None,
                "overall_conversion_rate": None,
                "average_engagement_rate": None
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="roi",
            payload=response,
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response
    
    # Aggregate by event
    event_roi_map: Dict[str, Dict[str, Any]] = {}
    
    for event, metric in results:
        event_id = event.id
        
        if event_id not in event_roi_map:
            event_roi_map[event_id] = {
                "event_id": event_id,
                "event_name": event.name,
                "event_type": event.event_type,
                "station_rsid": event.station_rsid,
                "total_cost": 0.0,
                "total_leads": 0,
                "total_conversions": 0,
                "metric_count": 0,
                "engagement_rates": []
            }
        
        # Accumulate metrics
        event_roi_map[event_id]["total_cost"] += metric.cost or 0.0
        event_roi_map[event_id]["total_leads"] += metric.leads_generated or 0
        event_roi_map[event_id]["total_conversions"] += metric.conversions or 0
        event_roi_map[event_id]["metric_count"] += 1
        if metric.engagement_rate:
            event_roi_map[event_id]["engagement_rates"].append(metric.engagement_rate)
    
    # Calculate event-level metrics
    event_level_roi = []
    for event_id, data in event_roi_map.items():
        cost_per_lead = (
            data["total_cost"] / data["total_leads"]
            if data["total_leads"] > 0 else None
        )
        cost_per_conversion = (
            data["total_cost"] / data["total_conversions"]
            if data["total_conversions"] > 0 else None
        )
        conversion_rate = (
            data["total_conversions"] / data["total_leads"]
            if data["total_leads"] > 0 else None
        )
        avg_engagement_rate = (
            sum(data["engagement_rates"]) / len(data["engagement_rates"])
            if data["engagement_rates"] else None
        )
        
        # ROI = (Revenue - Cost) / Cost. Without revenue data, we estimate as:
        # ROI = (Conversions * avg_value - Cost) / Cost
        # Using proxy: ROI based on conversion achievement vs cost
        estimated_roi = None
        if conversion_rate and data["total_cost"] > 0:
            # Conservative estimate: each conversion worth 2x average cost per lead
            estimated_revenue = data["total_conversions"] * (cost_per_lead * 2 if cost_per_lead else 100)
            estimated_roi = (estimated_revenue - data["total_cost"]) / data["total_cost"] if data["total_cost"] > 0 else 0
        
        event_level_roi.append({
            "event_id": event_id,
            "event_name": data["event_name"],
            "event_type": data["event_type"],
            "station_rsid": data["station_rsid"],
            "total_cost": round(data["total_cost"], 2),
            "total_leads": data["total_leads"],
            "total_conversions": data["total_conversions"],
            "conversion_rate": round(conversion_rate, 4) if conversion_rate else None,
            "cost_per_lead": round(cost_per_lead, 2) if cost_per_lead else None,
            "cost_per_conversion": round(cost_per_conversion, 2) if cost_per_conversion else None,
            "estimated_roi": round(estimated_roi, 4) if estimated_roi is not None else None,
            "average_engagement_rate": round(avg_engagement_rate, 4) if avg_engagement_rate else None,
            "metric_data_points": data["metric_count"]
        })
    
    # Aggregate by event_type for category ROI
    category_roi: Dict[str, Dict[str, Any]] = {}
    for event_roi in event_level_roi:
        evt_type = event_roi["event_type"]
        if evt_type not in category_roi:
            category_roi[evt_type] = {
                "event_type": evt_type,
                "event_count": 0,
                "total_cost": 0.0,
                "total_leads": 0,
                "total_conversions": 0,
                "cost_per_lead_avg": 0.0,
                "cost_per_conversion_avg": 0.0,
                "estimated_roi": None,
                "engagement_rate_avg": 0.0
            }
        
        category_roi[evt_type]["event_count"] += 1
        category_roi[evt_type]["total_cost"] += event_roi["total_cost"]
        category_roi[evt_type]["total_leads"] += event_roi["total_leads"]
        category_roi[evt_type]["total_conversions"] += event_roi["total_conversions"]
        if event_roi["cost_per_lead"]:
            category_roi[evt_type]["cost_per_lead_avg"] += event_roi["cost_per_lead"]
        if event_roi["cost_per_conversion"]:
            category_roi[evt_type]["cost_per_conversion_avg"] += event_roi["cost_per_conversion"]
        if event_roi["average_engagement_rate"]:
            category_roi[evt_type]["engagement_rate_avg"] += event_roi["average_engagement_rate"]
    
    # Finalize category metrics
    category_roi_final = {}
    for evt_type, data in category_roi.items():
        conversion_rate = (
            data["total_conversions"] / data["total_leads"]
            if data["total_leads"] > 0 else None
        )
        
        # Average the per-event costs
        cost_per_lead_avg = (
            data["cost_per_lead_avg"] / data["event_count"]
            if data["event_count"] > 0 else None
        )
        cost_per_conversion_avg = (
            data["cost_per_conversion_avg"] / data["event_count"]
            if data["event_count"] > 0 else None
        )
        engagement_rate_avg = (
            data["engagement_rate_avg"] / data["event_count"]
            if data["event_count"] > 0 else None
        )
        
        # Category ROI
        estimated_roi = None
        if conversion_rate and data["total_cost"] > 0:
            estimated_revenue = data["total_conversions"] * (cost_per_lead_avg * 2 if cost_per_lead_avg else 100)
            estimated_roi = (estimated_revenue - data["total_cost"]) / data["total_cost"] if data["total_cost"] > 0 else 0
        
        category_roi_final[evt_type] = {
            "event_type": evt_type,
            "event_count": data["event_count"],
            "total_cost": round(data["total_cost"], 2),
            "total_leads": data["total_leads"],
            "total_conversions": data["total_conversions"],
            "conversion_rate": round(conversion_rate, 4) if conversion_rate else None,
            "cost_per_lead": round(cost_per_lead_avg, 2) if cost_per_lead_avg else None,
            "cost_per_conversion": round(cost_per_conversion_avg, 2) if cost_per_conversion_avg else None,
            "estimated_roi": round(estimated_roi, 4) if estimated_roi is not None else None,
            "average_engagement_rate": round(engagement_rate_avg, 4) if engagement_rate_avg else None
        }
    
    # Summary metrics across all events
    total_cost = sum(event_roi["total_cost"] for event_roi in event_level_roi)
    total_leads = sum(event_roi["total_leads"] for event_roi in event_level_roi)
    total_conversions = sum(event_roi["total_conversions"] for event_roi in event_level_roi)
    
    overall_conversion_rate = (
        total_conversions / total_leads if total_leads > 0 else None
    )
    overall_cost_per_lead = (
        total_cost / total_leads if total_leads > 0 else None
    )
    overall_cost_per_conversion = (
        total_cost / total_conversions if total_conversions > 0 else None
    )
    
    overall_roi = None
    if overall_conversion_rate and total_cost > 0:
        estimated_revenue = total_conversions * (overall_cost_per_lead * 2 if overall_cost_per_lead else 100)
        overall_roi = (estimated_revenue - total_cost) / total_cost if total_cost > 0 else 0
    
    overall_engagement_rate = (
        sum(e["average_engagement_rate"] or 0 for e in event_level_roi) / len(event_level_roi)
        if event_level_roi else None
    )
    
    # Data completeness confidence
    # More events and more metric data points = higher confidence
    event_count = len(event_level_roi)
    total_data_points = sum(e["metric_data_points"] for e in event_level_roi)
    confidence = min((event_count / 10.0) * (total_data_points / 30.0), 1.0)
    
    response = {
        "event_level_roi": event_level_roi,
        "category_roi": category_roi_final,
        "summary_metrics": {
            "total_events": event_count,
            "total_cost": round(total_cost, 2),
            "total_leads": total_leads,
            "total_conversions": total_conversions,
            "overall_roi": round(overall_roi, 4) if overall_roi is not None else None,
            "overall_cost_per_lead": round(overall_cost_per_lead, 2) if overall_cost_per_lead else None,
            "overall_cost_per_conversion": round(overall_cost_per_conversion, 2) if overall_cost_per_conversion else None,
            "overall_conversion_rate": round(overall_conversion_rate, 4) if overall_conversion_rate else None,
            "average_engagement_rate": round(overall_engagement_rate, 4) if overall_engagement_rate else None
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat()
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="roi",
        payload=response,
        station_rsid=station_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response


def analyze_out_of_area_contracts(
    db: Session,
    writing_rsid: str = None,
    leak_type: str = None,
    period_start: date = None,
    period_end: date = None,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze out-of-area contracts, market leakage, territory control, and cross-market influence.
    
    Args:
        db: SQLAlchemy session
        writing_rsid: Optional filter by originating station
        leak_type: Optional filter by leakage type (cross_rsid, out_of_territory, territory_loss)
        period_start: Optional start date filter
        period_end: Optional end date filter
    
    Returns:
        Dict with:
        - contract_classifications: Count and breakdown of contract types
        - market_leakage: ZIP-to-ZIP leakage details
        - territory_control: Score by RSID (0.0-1.0)
        - cross_market_influence: RSID-to-RSID influence vectors
        - summary_metrics: Overall leakage %, control score, influence score
        - confidence: Data completeness score (0.0-1.0)
    """
    
    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )
    
    # Query contract classifications
    query = db.query(mi.ContractClassification).filter(
        mi.ContractClassification.classified_at >= period_start,
        mi.ContractClassification.classified_at <= period_end
    )
    
    if writing_rsid:
        query = query.filter(mi.ContractClassification.writing_rsid.in_(get_unit_scope(writing_rsid)))
    query = _apply_rsm_filter(query, mi.ContractClassification.writing_rsid, rsm)
    
    classifications = query.all()
    
    if not classifications:
        response = {
            "contract_classifications": {},
            "market_leakage": [],
            "territory_control": {},
            "cross_market_influence": {},
            "summary_metrics": {
                "total_contracts": 0,
                "in_area_contracts": 0,
                "out_of_area_contracts": 0,
                "leakage_percentage": 0.0,
                "territory_control_score": None,
                "cross_market_influence_score": None
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="ooa",
            payload=response,
            station_rsid=writing_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response
    
    # Analyze contract classifications
    classification_counts = {}
    for c in classifications:
        key = c.classification
        if key not in classification_counts:
            classification_counts[key] = 0
        classification_counts[key] += 1
    
    # Query market leakage
    query_leakage = db.query(mi.MarketLeakage).filter(
        mi.MarketLeakage.period_start <= period_end,
        mi.MarketLeakage.period_end >= period_start
    )
    
    if leak_type:
        query_leakage = query_leakage.filter(mi.MarketLeakage.leak_type == leak_type)
    if writing_rsid:
        query_leakage = query_leakage.filter(mi.MarketLeakage.from_rsid == writing_rsid)
    query_leakage = _apply_rsm_filter(query_leakage, mi.MarketLeakage.from_rsid, rsm)
    
    leakages = query_leakage.all()
    
    # Format leakage data
    leakage_list = []
    total_leaked_contracts = 0
    for leak in leakages:
        total_leaked_contracts += leak.contract_count or 0
        leakage_list.append({
            "from_zip": leak.from_zip,
            "to_zip": leak.to_zip,
            "from_rsid": leak.from_rsid,
            "to_rsid": leak.to_rsid,
            "leak_type": leak.leak_type,
            "contract_count": leak.contract_count,
            "lead_count": leak.lead_count,
            "period": f"{leak.period_start.isoformat()} to {leak.period_end.isoformat()}"
        })
    
    # Calculate territory control scores by RSID
    territory_control = {}
    rsid_map: Dict[str, Dict[str, int]] = {}
    
    for c in classifications:
        rsid = c.writing_rsid or "unknown"
        if rsid not in rsid_map:
            rsid_map[rsid] = {"in_area": 0, "out_of_area": 0, "total": 0}
        
        rsid_map[rsid]["total"] += 1
        if c.classification == "in_area":
            rsid_map[rsid]["in_area"] += 1
        else:
            rsid_map[rsid]["out_of_area"] += 1
    
    for rsid, counts in rsid_map.items():
        control_score = (counts["in_area"] / counts["total"]) if counts["total"] > 0 else 0.0
        territory_control[rsid] = {
            "rsid": rsid,
            "in_area_contracts": counts["in_area"],
            "out_of_area_contracts": counts["out_of_area"],
            "total_contracts": counts["total"],
            "territory_control_score": round(control_score, 4),
            "leakage_percentage": round(100.0 * (1 - control_score), 2)
        }
    
    # Query cross-market influence
    query_influence = db.query(mi.ContractInfluence).filter(
        mi.ContractInfluence.identified_at >= period_start,
        mi.ContractInfluence.identified_at <= period_end
    )

    if writing_rsid:
        query_influence = query_influence.filter(
            mi.ContractInfluence.influencing_rsid == writing_rsid
        )
    query_influence = _apply_rsm_filter(query_influence, mi.ContractInfluence.influencing_rsid, rsm)
    
    influence_data = query_influence.all()
    cross_market_influence = {}
    
    for inf in influence_data:
        from_rsid = inf.influencing_rsid or "unknown"
        to_rsid = inf.influenced_rsid or "unknown"
        key = f"{from_rsid} -> {to_rsid}"
        if key not in cross_market_influence:
            cross_market_influence[key] = {
                "from_rsid": from_rsid,
                "to_rsid": to_rsid,
                "influence_type": inf.influence_type,
                "influenced_contract_count": 0,
                "influence_strength": 0.0,
                "influence_confidence": 0.0
            }
        
        cross_market_influence[key]["influenced_contract_count"] += (inf.contract_count or 0)
        cross_market_influence[key]["influence_strength"] = max(
            cross_market_influence[key]["influence_strength"],
            inf.influence_score or 0.0
        )
        cross_market_influence[key]["influence_confidence"] = max(
            cross_market_influence[key]["influence_confidence"],
            inf.causation_confidence or 0.0
        )
    
    # Calculate summary metrics
    total_contracts = len(classifications)
    in_area_count = classification_counts.get("in_area", 0)
    out_of_area_count = total_contracts - in_area_count
    leakage_pct = (out_of_area_count / total_contracts * 100.0) if total_contracts > 0 else 0.0
    
    avg_control_score = (
        sum(c["territory_control_score"] for c in territory_control.values()) / len(territory_control)
        if territory_control else None
    )
    
    avg_influence_score = (
        sum(c["influence_strength"] for c in cross_market_influence.values()) / len(cross_market_influence)
        if cross_market_influence else None
    )
    
    confidence = min(
        (len(classifications) / 100.0) * ((len(leakage_list) + len(cross_market_influence)) / 10.0),
        1.0
    )
    
    response = {
        "contract_classifications": classification_counts,
        "market_leakage": leakage_list,
        "territory_control": territory_control,
        "cross_market_influence": cross_market_influence,
        "summary_metrics": {
            "total_contracts": total_contracts,
            "in_area_contracts": in_area_count,
            "out_of_area_contracts": out_of_area_count,
            "leakage_percentage": round(leakage_pct, 2),
            "territory_control_score": round(avg_control_score, 4) if avg_control_score else None,
            "cross_market_influence_score": round(avg_influence_score, 4) if avg_influence_score else None
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat()
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="ooa",
        payload=response,
        station_rsid=writing_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response


def analyze_out_of_area_effectiveness(
    db: Session,
    writing_rsid: str = None,
    period_start: date = None,
    period_end: date = None,
    min_contracts_threshold: int = 5,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze out-of-area effectiveness by station with objective scoring.

    Effectiveness is based on retaining contracts in-area, limiting leakage,
    and reducing cross-market exposure.

    Args:
        db: SQLAlchemy session
        writing_rsid: Optional filter for single station RSID
        period_start: Optional start date
        period_end: Optional end date
        min_contracts_threshold: Minimum contracts for stable scoring

    Returns:
        Dict with:
        - station_effectiveness: effectiveness metrics and score per RSID
        - leakage_hotspots: top ZIP leakage routes by contract count
        - summary_metrics: aggregate effectiveness and risk bands
        - confidence: data completeness score (0.0-1.0)
        - period_analyzed: analyzed date range
    """

    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )

    # Reuse core OOA analytics to keep metrics consistent.
    ooa = analyze_out_of_area_contracts(
        db=db,
        writing_rsid=writing_rsid,
        leak_type=None,
        period_start=period_start,
        period_end=period_end,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
    )

    territory_control = ooa.get("territory_control", {})
    leakage_rows = ooa.get("market_leakage", [])
    influence_rows = ooa.get("cross_market_influence", {})

    if not territory_control:
        response = {
            "station_effectiveness": {},
            "leakage_hotspots": [],
            "summary_metrics": {
                "station_count": 0,
                "average_effectiveness_score": None,
                "high_effectiveness_stations": 0,
                "moderate_effectiveness_stations": 0,
                "low_effectiveness_stations": 0,
                "total_leakage_routes": 0,
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="ooa_effectiveness",
            payload=response,
            station_rsid=writing_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response

    # Aggregate outgoing influence by RSID for risk scoring.
    influence_by_from_rsid: Dict[str, Dict[str, float]] = {}
    for rel in influence_rows.values():
        rsid = rel.get("from_rsid") or "unknown"
        if rsid not in influence_by_from_rsid:
            influence_by_from_rsid[rsid] = {
                "route_count": 0,
                "influenced_contracts": 0.0,
                "avg_influence_strength": 0.0,
                "_strength_sum": 0.0,
            }
        influence_by_from_rsid[rsid]["route_count"] += 1
        influence_by_from_rsid[rsid]["influenced_contracts"] += float(rel.get("influenced_contract_count") or 0)
        influence_by_from_rsid[rsid]["_strength_sum"] += float(rel.get("influence_strength") or 0.0)

    for rsid, agg in influence_by_from_rsid.items():
        routes = int(agg["route_count"])
        agg["avg_influence_strength"] = round((agg["_strength_sum"] / routes), 4) if routes > 0 else 0.0
        del agg["_strength_sum"]

    station_effectiveness: Dict[str, Any] = {}
    effectiveness_scores: List[float] = []

    for rsid, tc in territory_control.items():
        total_contracts = int(tc.get("total_contracts") or 0)
        in_area_contracts = int(tc.get("in_area_contracts") or 0)
        out_of_area_contracts = int(tc.get("out_of_area_contracts") or 0)
        control_score = float(tc.get("territory_control_score") or 0.0)
        leakage_percentage = float(tc.get("leakage_percentage") or 0.0)

        influence = influence_by_from_rsid.get(rsid, {
            "route_count": 0,
            "influenced_contracts": 0.0,
            "avg_influence_strength": 0.0,
        })

        # Coverage/stability factor prevents over-weighting very low volume stations.
        sample_stability = min((total_contracts / max(min_contracts_threshold, 1)), 1.0)

        # Effectiveness formula:
        # + territory control (primary), - leakage and influence exposure.
        raw_score = (
            (control_score * 0.65)
            + ((1.0 - (leakage_percentage / 100.0)) * 0.25)
            + ((1.0 - float(influence.get("avg_influence_strength") or 0.0)) * 0.10)
        )
        effectiveness_score = max(min(raw_score * sample_stability, 1.0), 0.0)

        if effectiveness_score >= 0.75:
            band = "high"
        elif effectiveness_score >= 0.50:
            band = "moderate"
        else:
            band = "low"

        station_effectiveness[rsid] = {
            "rsid": rsid,
            "total_contracts": total_contracts,
            "in_area_contracts": in_area_contracts,
            "out_of_area_contracts": out_of_area_contracts,
            "territory_control_score": round(control_score, 4),
            "leakage_percentage": round(leakage_percentage, 2),
            "cross_market_routes": int(influence.get("route_count") or 0),
            "influenced_contracts": int(influence.get("influenced_contracts") or 0),
            "avg_influence_strength": round(float(influence.get("avg_influence_strength") or 0.0), 4),
            "sample_stability": round(sample_stability, 4),
            "effectiveness_score": round(effectiveness_score, 4),
            "effectiveness_band": band,
        }
        effectiveness_scores.append(effectiveness_score)

    leakage_hotspots = sorted(
        leakage_rows,
        key=lambda x: (x.get("contract_count") or 0),
        reverse=True,
    )[:10]

    station_count = len(station_effectiveness)
    high_count = sum(1 for s in station_effectiveness.values() if s["effectiveness_band"] == "high")
    moderate_count = sum(1 for s in station_effectiveness.values() if s["effectiveness_band"] == "moderate")
    low_count = sum(1 for s in station_effectiveness.values() if s["effectiveness_band"] == "low")

    avg_effectiveness = (
        sum(effectiveness_scores) / len(effectiveness_scores)
        if effectiveness_scores else None
    )

    confidence = min(
        ((station_count / 10.0) * ((len(leakage_rows) + len(influence_rows)) / 20.0)),
        1.0,
    )

    response = {
        "station_effectiveness": station_effectiveness,
        "leakage_hotspots": leakage_hotspots,
        "summary_metrics": {
            "station_count": station_count,
            "average_effectiveness_score": round(avg_effectiveness, 4) if avg_effectiveness is not None else None,
            "high_effectiveness_stations": high_count,
            "moderate_effectiveness_stations": moderate_count,
            "low_effectiveness_stations": low_count,
            "total_leakage_routes": len(leakage_rows),
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat(),
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="ooa_effectiveness",
        payload=response,
        station_rsid=writing_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response


def analyze_recruiter_effectiveness(
    db: Session,
    station_rsid: str = None,
    period_start: date = None,
    period_end: date = None,
    reporting_period: str = "monthly",
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze recruiter operational effectiveness. All metrics are objective (hours, contacts, conversions).
    No subjective language.
    
    Args:
        db: SQLAlchemy session
        station_rsid: Optional filter by station
        period_start: Optional start date
        period_end: Optional end date
        reporting_period: "daily", "weekly", or "monthly"
    
    Returns:
        Dict with:
        - recruiter_metrics: List of individual recruiter effectiveness data
        - peer_comparison: Benchmarking metrics vs peers
        - efficiency_distribution: Histogram of efficiency index across recruiters
        - summary_metrics: Aggregate effectiveness across station/brigade
        - confidence: Data completeness score (0.0-1.0)
    """
    
    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )
    
    # Query effectiveness records
    query = db.query(mi.RecruiterEffectiveness).filter(
        mi.RecruiterEffectiveness.period_date >= period_start,
        mi.RecruiterEffectiveness.period_date <= period_end,
        mi.RecruiterEffectiveness.reporting_period == reporting_period
    )
    
    if station_rsid:
        query = query.filter(mi.RecruiterEffectiveness.station_rsid.in_(get_unit_scope(station_rsid)))
    query = _apply_rsm_filter(query, mi.RecruiterEffectiveness.station_rsid, rsm)
    
    effectiveness_records = query.all()
    
    if not effectiveness_records:
        response = {
            "recruiter_metrics": [],
            "peer_comparison": {},
            "efficiency_distribution": {},
            "summary_metrics": {
                "recruiter_count": 0,
                "avg_prospecting_hours": None,
                "avg_contacts_per_hour": None,
                "avg_appointments_per_hour": None,
                "avg_contracts_per_hour": None,
                "avg_contact_conversion_rate": None,
                "avg_appointment_conversion_rate": None,
                "avg_efficiency_index": None,
                "avg_effort_index": None
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="recruiter_effectiveness",
            payload=response,
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response
    
    # Format recruiter metrics
    recruiter_metrics = []
    efficiency_scores = []
    effort_scores = []
    
    for rec in effectiveness_records:
        recruiter_metrics.append({
            "recruiter_id": rec.recruiter_id,
            "station_rsid": rec.station_rsid,
            "period": f"{rec.period_date.isoformat()} ({rec.reporting_period})",
            "prospecting_hours": rec.prospecting_hours,
            "contacts_count": rec.contacts_count,
            "appointments_count": rec.appointments_count,
            "attempts_count": rec.attempts_count,
            "contracts_count": rec.contracts_count,
            "contacts_per_hour": round(rec.contacts_per_hour, 4) if rec.contacts_per_hour else None,
            "appointments_per_hour": round(rec.appointments_per_hour, 4) if rec.appointments_per_hour else None,
            "contracts_per_hour": round(rec.contracts_per_hour, 4) if rec.contracts_per_hour else None,
            "hours_per_appointment": round(rec.hours_per_appointment, 4) if rec.hours_per_appointment else None,
            "hours_per_enlistment": round(rec.hours_per_enlistment, 4) if rec.hours_per_enlistment else None,
            "contact_conversion_rate": round(rec.contact_conversion_rate, 4) if rec.contact_conversion_rate else None,
            "appointment_conversion_rate": round(rec.appointment_conversion_rate, 4) if rec.appointment_conversion_rate else None,
            "efficiency_index": round(rec.efficiency_index, 4) if rec.efficiency_index else None,
            "effort_index": round(rec.effort_index, 4) if rec.effort_index else None
        })
        
        if rec.efficiency_index:
            efficiency_scores.append(rec.efficiency_index)
        if rec.effort_index:
            effort_scores.append(rec.effort_index)
    
    # Peer comparison: calculate percentiles
    efficiency_percentile_map = {}
    if efficiency_scores:
        efficiency_scores_sorted = sorted(efficiency_scores)
        for i, rec in enumerate(recruiter_metrics):
            if rec["efficiency_index"]:
                percentile = (efficiency_scores_sorted.index(rec["efficiency_index"]) / len(efficiency_scores_sorted)) * 100
                efficiency_percentile_map[rec["recruiter_id"]] = {
                    "efficiency_index": rec["efficiency_index"],
                    "percentile": round(percentile, 1),
                    "peer_position": "above_average" if percentile > 50 else "below_average"
                }
    
    # Efficiency distribution histogram
    efficiency_distribution = {
        "0_25_percentile": len([e for e in efficiency_scores if e < 0.25]),
        "25_50_percentile": len([e for e in efficiency_scores if 0.25 <= e < 0.50]),
        "50_75_percentile": len([e for e in efficiency_scores if 0.50 <= e < 0.75]),
        "75_100_percentile": len([e for e in efficiency_scores if e >= 0.75])
    }
    
    # Summary metrics
    avg_prospecting_hours = (
        sum(r["prospecting_hours"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_contacts_per_hour = (
        sum(r["contacts_per_hour"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_appointments_per_hour = (
        sum(r["appointments_per_hour"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_contracts_per_hour = (
        sum(r["contracts_per_hour"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_contact_conversion_rate = (
        sum(r["contact_conversion_rate"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_appointment_conversion_rate = (
        sum(r["appointment_conversion_rate"] or 0 for r in recruiter_metrics) / len(recruiter_metrics)
        if recruiter_metrics else None
    )
    avg_efficiency_index = (
        sum(efficiency_scores) / len(efficiency_scores)
        if efficiency_scores else None
    )
    avg_effort_index = (
        sum(effort_scores) / len(effort_scores)
        if effort_scores else None
    )
    
    confidence = min(len(recruiter_metrics) / 20.0, 1.0)
    
    response = {
        "recruiter_metrics": recruiter_metrics,
        "peer_comparison": efficiency_percentile_map,
        "efficiency_distribution": efficiency_distribution,
        "summary_metrics": {
            "recruiter_count": len(recruiter_metrics),
            "avg_prospecting_hours": round(avg_prospecting_hours, 2) if avg_prospecting_hours else None,
            "avg_contacts_per_hour": round(avg_contacts_per_hour, 4) if avg_contacts_per_hour else None,
            "avg_appointments_per_hour": round(avg_appointments_per_hour, 4) if avg_appointments_per_hour else None,
            "avg_contracts_per_hour": round(avg_contracts_per_hour, 4) if avg_contracts_per_hour else None,
            "avg_contact_conversion_rate": round(avg_contact_conversion_rate, 4) if avg_contact_conversion_rate else None,
            "avg_appointment_conversion_rate": round(avg_appointment_conversion_rate, 4) if avg_appointment_conversion_rate else None,
            "avg_efficiency_index": round(avg_efficiency_index, 4) if avg_efficiency_index else None,
            "avg_effort_index": round(avg_effort_index, 4) if avg_effort_index else None
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat()
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="recruiter_effectiveness",
        payload=response,
        station_rsid=station_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response


def analyze_vacancy_alignment(
    db: Session,
    station_rsid: str = None,
    period_start: date = None,
    period_end: date = None,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze vacancy-to-market alignment. Match vacancy MOS/echelons to demographic opportunities.
    
    Args:
        db: SQLAlchemy session
        station_rsid: Optional filter by station
        period_start: Optional start date
        period_end: Optional end date
    
    Returns:
        Dict with:
        - vacancy_alignments: List of vacancy analysis records
        - alignment_scores: Breakdown of fit scores (demographic, school, industry)
        - target_populations: Identified target demographics
        - messaging_recommendations: Suggested messaging themes and platforms
        - summary_metrics: Aggregate alignment quality and gap analysis
        - confidence: Data completeness score (0.0-1.0)
    """
    
    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )
    
    # Query vacancy alignments using date-cast bounds for DateTime fields.
    query = db.query(mi.VacancyAlignment).filter(
        func.date(mi.VacancyAlignment.created_at) >= period_start,
        func.date(mi.VacancyAlignment.created_at) <= period_end
    )
    
    if station_rsid:
        query = query.filter(mi.VacancyAlignment.station_rsid.in_(get_unit_scope(station_rsid)))
    query = _apply_rsm_filter(query, mi.VacancyAlignment.station_rsid, rsm)
    
    alignments = query.all()
    
    if not alignments:
        response = {
            "vacancy_alignments": [],
            "alignment_scores": {},
            "target_populations": [],
            "messaging_recommendations": [],
            "summary_metrics": {
                "vacancy_count": 0,
                "avg_demographic_fit": None,
                "avg_school_fit": None,
                "avg_industry_fit": None,
                "avg_overall_alignment": None,
                "high_alignment_count": 0,
                "medium_alignment_count": 0,
                "low_alignment_count": 0
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="vacancy_alignment",
            payload=response,
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response
    
    # Format vacancy alignment data
    vacancy_list = []
    fit_scores_demographic = []
    fit_scores_school = []
    fit_scores_industry = []
    fit_scores_overall = []
    
    for va in alignments:
        overall_fit = (
            va.overall_alignment_score
            if va.overall_alignment_score is not None
            else (
                (va.demographic_fit_score or 0.0) * 0.3
                + (va.school_population_fit or 0.0) * 0.4
                + (va.civilian_industry_alignment or 0.0) * 0.3
            )
        )

        vacancy_list.append({
            "vacancy_alignment_id": va.id,
            "vacancy_mos": va.vacancy_mos,
            "vacancy_count": va.vacancy_count,
            "demand_level": va.demand_level,
            "market_zip_primary": va.market_zip_primary,
            "market_zip_secondary": va.market_zip_secondary,
            "station_rsid": va.station_rsid,
            "demographic_fit_score": round(va.demographic_fit_score or 0.0, 4),
            "school_population_fit_score": round(va.school_population_fit or 0.0, 4),
            "civilian_industry_fit_score": round(va.civilian_industry_alignment or 0.0, 4),
            "operational_trend_alignment": round(va.operational_trend_alignment or 0.0, 4),
            "overall_alignment_score": round(overall_fit, 4),
            "alignment_quality": "high" if overall_fit >= 0.75 else ("medium" if overall_fit >= 0.5 else "low"),
            "alignment_rationale": va.alignment_rationale,
            "aligned_at": va.aligned_at.isoformat() if va.aligned_at else None,
            "created_at": va.created_at.isoformat() if va.created_at else None
        })

        fit_scores_demographic.append(va.demographic_fit_score or 0.0)
        fit_scores_school.append(va.school_population_fit or 0.0)
        fit_scores_industry.append(va.civilian_industry_alignment or 0.0)
        fit_scores_overall.append(overall_fit)
    
    # Query target populations linked to selected vacancy alignments.
    alignment_ids = [a.id for a in alignments]
    target_pop_query = db.query(mi.TargetPopulation).filter(
        mi.TargetPopulation.vacancy_alignment_id.in_(alignment_ids)
    )

    target_populations = target_pop_query.all()
    target_pop_list = [
        {
            "target_population_id": tp.id,
            "vacancy_alignment_id": tp.vacancy_alignment_id,
            "target_demographic": tp.target_demographic,
            "population_estimate": tp.population_estimate,
            "geographic_coverage_zips": tp.geographic_coverage_zips or [],
            "schools_to_focus": tp.schools_to_focus or [],
            "industries_to_target": tp.industries_to_target or [],
            "messaging_themes": tp.messaging_themes or [],
            "marketing_platforms": tp.marketing_platforms or [],
            "event_recommendations": tp.event_recommendations or [],
            "partnership_opportunities": tp.partnership_opportunities or [],
            "identified_at": tp.identified_at.isoformat() if tp.identified_at else None
        }
        for tp in target_populations
    ]

    # Query messaging themes linked to selected target populations.
    target_population_ids = [tp.id for tp in target_populations]
    messaging_query = db.query(mi.MessagingTheme)
    if target_population_ids:
        messaging_query = messaging_query.filter(
            mi.MessagingTheme.target_population_id.in_(target_population_ids)
        )
    else:
        messaging_query = messaging_query.filter(mi.MessagingTheme.id == "__none__")

    messaging_themes = messaging_query.all()
    messaging_list = [
        {
            "messaging_theme_id": mt.id,
            "target_population_id": mt.target_population_id,
            "theme_name": mt.theme_name,
            "theme_description": mt.theme_description,
            "target_audience": mt.target_audience,
            "platform": mt.platform,
            "effectiveness_score": round(mt.effectiveness_score or 0.0, 4),
            "historical_ctr": round(mt.historical_ctr or 0.0, 4),
            "historical_conversion": round(mt.historical_conversion or 0.0, 4),
            "created_at": mt.created_at.isoformat() if mt.created_at else None
        }
        for mt in messaging_themes
    ]
    
    # Calculate alignment score breakdown
    alignment_scores = {
        "demographic_fit": {
            "average": round(sum(fit_scores_demographic) / len(fit_scores_demographic), 4) if fit_scores_demographic else 0.0,
            "min": round(min(fit_scores_demographic), 4) if fit_scores_demographic else 0.0,
            "max": round(max(fit_scores_demographic), 4) if fit_scores_demographic else 0.0
        },
        "school_population_fit": {
            "average": round(sum(fit_scores_school) / len(fit_scores_school), 4) if fit_scores_school else 0.0,
            "min": round(min(fit_scores_school), 4) if fit_scores_school else 0.0,
            "max": round(max(fit_scores_school), 4) if fit_scores_school else 0.0
        },
        "civilian_industry_fit": {
            "average": round(sum(fit_scores_industry) / len(fit_scores_industry), 4) if fit_scores_industry else 0.0,
            "min": round(min(fit_scores_industry), 4) if fit_scores_industry else 0.0,
            "max": round(max(fit_scores_industry), 4) if fit_scores_industry else 0.0
        }
    }
    
    # Summary metrics
    high_alignment_count = len([s for s in fit_scores_overall if s >= 0.75])
    medium_alignment_count = len([s for s in fit_scores_overall if 0.5 <= s < 0.75])
    low_alignment_count = len([s for s in fit_scores_overall if s < 0.5])
    
    confidence = min(len(alignments) / 20.0, 1.0)
    
    response = {
        "vacancy_alignments": vacancy_list,
        "alignment_scores": alignment_scores,
        "target_populations": target_pop_list,
        "messaging_recommendations": messaging_list,
        "summary_metrics": {
            "vacancy_count": len(vacancy_list),
            "avg_demographic_fit": alignment_scores["demographic_fit"]["average"],
            "avg_school_fit": alignment_scores["school_population_fit"]["average"],
            "avg_industry_fit": alignment_scores["civilian_industry_fit"]["average"],
            "avg_overall_alignment": round(sum(fit_scores_overall) / len(fit_scores_overall), 4) if fit_scores_overall else None,
            "high_alignment_count": high_alignment_count,
            "medium_alignment_count": medium_alignment_count,
            "low_alignment_count": low_alignment_count
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat()
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="vacancy_alignment",
        payload=response,
        station_rsid=station_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response


def analyze_market_influence(
    db: Session,
    station_rsid: str = None,
    period_start: date = None,
    period_end: date = None,
    min_influence_strength: float = 0.3,
    fy: Optional[str] = None,
    quarter: Optional[str] = None,
    rsm: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze cross-market influence vectors. Identify which RSIDs influence others.

    Args:
        db: SQLAlchemy session
        station_rsid: Optional filter by originating station
        period_start: Optional start date
        period_end: Optional end date
        min_influence_strength: Minimum influence score to include (0.0-1.0)

    Returns:
        Dict with:
        - influence_vectors: Directional influence from one RSID to another
        - influence_network: Network-level analysis of influence propagation
        - influenced_rsids: Which RSIDs are being influenced
        - influencer_rsids: Which RSIDs have the most outbound influence
        - summary_metrics: Aggregate influence patterns and scores
        - confidence: Data completeness score (0.0-1.0)
    """

    period_start, period_end, resolved_fy, resolved_quarter, period_label = _resolve_period_scope(
        period_start=period_start,
        period_end=period_end,
        fy=fy,
        quarter=quarter,
    )

    # Query contract influence using schema-correct fields.
    query = db.query(mi.ContractInfluence).filter(
        func.date(mi.ContractInfluence.identified_at) >= period_start,
        func.date(mi.ContractInfluence.identified_at) <= period_end,
        mi.ContractInfluence.influence_score >= min_influence_strength
    )

    if station_rsid:
        query = query.filter(mi.ContractInfluence.influencing_rsid.in_(get_unit_scope(station_rsid)))
    query = _apply_rsm_filter(query, mi.ContractInfluence.influencing_rsid, rsm)

    influences = query.all()

    if not influences:
        response = {
            "influence_vectors": [],
            "influence_network": {},
            "influenced_rsids": [],
            "influencer_rsids": [],
            "summary_metrics": {
                "total_influence_vectors": 0,
                "rsid_count": 0,
                "avg_influence_strength": None,
                "network_cohesion_score": None,
                "influence_concentration": None
            },
            "confidence": 0.0,
            "period_analyzed": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            },
            "period_analyzed_string": period_label,
            "fy": resolved_fy,
            "quarter": resolved_quarter,
            "rsm": rsm,
        }
        _persist_analytics_snapshot(
            db=db,
            snapshot_type="market_influence",
            payload=response,
            station_rsid=station_rsid,
            fy=resolved_fy,
            quarter=resolved_quarter,
            rsm=rsm,
            period_analyzed=response.get("period_analyzed"),
        )
        return response

    influence_vectors = []
    influencer_map: Dict[str, List[Dict[str, Any]]] = {}
    influenced_map: Dict[str, List[Dict[str, Any]]] = {}

    for inf in influences:
        from_rsid = inf.influencing_rsid or "unknown"
        to_rsid = inf.influenced_rsid or "unknown"
        strength = float(inf.influence_score or 0.0)
        confidence_score = float(inf.causation_confidence or 0.0)
        contracts = int(inf.contract_count or 0)

        vector_record = {
            "from_rsid": from_rsid,
            "to_rsid": to_rsid,
            "from_zip": inf.influencing_zip,
            "to_zip": inf.influenced_zip,
            "influence_type": inf.influence_type,
            "influenced_contract_count": contracts,
            "influence_strength": round(strength, 4),
            "influence_confidence": round(confidence_score, 4),
            "identified_at": inf.identified_at.isoformat() if inf.identified_at else None
        }
        influence_vectors.append(vector_record)

        if from_rsid not in influencer_map:
            influencer_map[from_rsid] = []
        influencer_map[from_rsid].append({
            "target_rsid": to_rsid,
            "strength": strength,
            "contracts": contracts
        })

        if to_rsid not in influenced_map:
            influenced_map[to_rsid] = []
        influenced_map[to_rsid].append({
            "source_rsid": from_rsid,
            "strength": strength,
            "contracts": contracts
        })

    influencer_rsids = []
    for rsid, targets in influencer_map.items():
        total_strength = sum(t["strength"] for t in targets)
        total_contracts = sum(t["contracts"] for t in targets)
        influencer_rsids.append({
            "rsid": rsid,
            "target_count": len(targets),
            "total_influence_strength": round(total_strength, 4),
            "total_influenced_contracts": total_contracts,
            "avg_influence_strength": round(total_strength / len(targets), 4) if targets else 0.0
        })

    influenced_rsids_list = []
    for rsid, sources in influenced_map.items():
        total_strength = sum(s["strength"] for s in sources)
        total_contracts = sum(s["contracts"] for s in sources)
        influenced_rsids_list.append({
            "rsid": rsid,
            "influencer_count": len(sources),
            "total_inbound_influence_strength": round(total_strength, 4),
            "total_contracts_influenced_by_others": total_contracts,
            "avg_inbound_influence_strength": round(total_strength / len(sources), 4) if sources else 0.0
        })

    influencer_rsids.sort(key=lambda x: x["total_influence_strength"], reverse=True)
    influenced_rsids_list.sort(key=lambda x: x["total_inbound_influence_strength"], reverse=True)

    all_rsids = set(influencer_map.keys()) | set(influenced_map.keys())
    network_cohesion = (
        len(influence_vectors) / (len(all_rsids) * (len(all_rsids) - 1))
        if len(all_rsids) > 1 else 0.0
    )

    total_influence_strength = sum(float(inf.influence_score or 0.0) for inf in influences)
    concentration = (
        max(sum(t["strength"] for t in targets) for targets in influencer_map.values()) / total_influence_strength
        if total_influence_strength > 0 and influencer_map else 0.0
    )

    influence_network = {
        "rsid_count": len(all_rsids),
        "vector_count": len(influence_vectors),
        "network_cohesion_score": round(network_cohesion, 4),
        "influence_concentration_score": round(concentration, 4),
        "network_description": "Dense" if network_cohesion > 0.5 else ("Moderate" if network_cohesion > 0.2 else "Sparse")
    }

    avg_influence_strength = total_influence_strength / len(influences) if influences else None
    confidence = min(len(influences) / 30.0, 1.0)

    response = {
        "influence_vectors": influence_vectors,
        "influence_network": influence_network,
        "influenced_rsids": influenced_rsids_list,
        "influencer_rsids": influencer_rsids,
        "summary_metrics": {
            "total_influence_vectors": len(influence_vectors),
            "rsid_count": len(all_rsids),
            "avg_influence_strength": round(avg_influence_strength, 4) if avg_influence_strength is not None else None,
            "network_cohesion_score": round(network_cohesion, 4),
            "influence_concentration": round(concentration, 4)
        },
        "confidence": round(confidence, 4),
        "period_analyzed": {
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat()
        },
        "period_analyzed_string": period_label,
        "fy": resolved_fy,
        "quarter": resolved_quarter,
        "rsm": rsm,
    }
    _persist_analytics_snapshot(
        db=db,
        snapshot_type="market_influence",
        payload=response,
        station_rsid=station_rsid,
        fy=resolved_fy,
        quarter=resolved_quarter,
        rsm=rsm,
        period_analyzed=response.get("period_analyzed"),
    )
    return response
