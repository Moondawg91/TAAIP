"""© 2026 TAAIP. Copyright pending.
Data Intelligence Layer models: ingestion, normalization, snapshots, analytics, recommendations.
Preserves raw sources, maintains historical lineage, enables decision support.
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from .models import Base
from datetime import datetime


# ========================================================
# DATA INGESTION & NORMALIZATION
# ========================================================

class DataSource(Base):
    """Track data source systems (RID, Vantage, PowerBI, EMM, custom imports)."""
    __tablename__ = "data_sources"
    id = Column(String, primary_key=True)
    source_name = Column(String, nullable=False, unique=True)  # e.g., "RID", "Vantage", "PowerBI", "EMM"
    source_type = Column(String, nullable=False)  # "SYSTEM" or "IMPORT"
    description = Column(Text, nullable=True)
    schema_version = Column(String, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DataIngestionLog(Base):
    """Log all data ingestions for audit trail and historical lineage."""
    __tablename__ = "data_ingestion_logs"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    source_file = Column(String, nullable=False)  # filename/identifier
    source_hash = Column(String, nullable=True)  # MD5/SHA256 of source file
    record_count = Column(Integer, nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    ingested_by = Column(String, nullable=True)  # user/system that initiated ingest
    status = Column(String, nullable=False, server_default='pending')  # pending, success, partial, failed
    error_message = Column(Text, nullable=True)
    source_metadata = Column(JSON, nullable=True)  # source metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ColumnMapping(Base):
    """Schema auto-detection: map source columns to normalized fields."""
    __tablename__ = "column_mappings"
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    source_column_name = Column(String, nullable=False)
    source_data_type = Column(String, nullable=False)
    normalized_field_name = Column(String, nullable=False)
    normalized_data_type = Column(String, nullable=False)
    transformation_rule = Column(JSON, nullable=True)  # e.g., {"type": "date_parse", "format": "MM/DD/YYYY"}
    confidence = Column(Float, nullable=True)  # 0.0-1.0 confidence of mapping
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NormalizedValue(Base):
    """Normalization rules for categorical values (ZIP codes, RSIDs, schools, companies, etc)."""
    __tablename__ = "normalized_values"
    id = Column(String, primary_key=True)
    field_type = Column(String, nullable=False)  # "ZIP", "RSID", "SCHOOL", "COMPANY", "STATUS", etc
    source_value = Column(String, nullable=False)
    normalized_value = Column(String, nullable=False)
    source_system = Column(String, nullable=True)
    mapping_confidence = Column(Float, nullable=True)  # 0.0-1.0
    is_approved = Column(Boolean, nullable=False, server_default='0')
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ========================================================
# HISTORICAL SNAPSHOTS
# ========================================================

class HistoricalSnapshot(Base):
    """Track daily/weekly/monthly snapshots for trend analysis and predictive modeling."""
    __tablename__ = "historical_snapshots"
    id = Column(String, primary_key=True)
    snapshot_type = Column(String, nullable=False)  # "daily", "weekly", "monthly", "event_triggered"
    snapshot_date = Column(Date, nullable=False)
    scope_type = Column(String, nullable=False)  # "USAREC", "BRIGADE", "BATTALION", "COMPANY", "STATION"
    scope_value = Column(String, nullable=False)  # brigade_prefix, battalion_prefix, company_prefix, station_rsid, or "USAREC"
    trigger_event = Column(String, nullable=True)  # "operation_start", "operation_end", "board_decision", "performance_threshold"
    data_version = Column(Integer, nullable=False)  # allows multiple snapshots on same date for different triggers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SnapshotMetric(Base):
    """Snapshot contents: KPIs, funnel data, production metrics at point in time."""
    __tablename__ = "snapshot_metrics"
    id = Column(String, primary_key=True)
    snapshot_id = Column(String, ForeignKey("historical_snapshots.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # "leads", "engagements", "contracts", "cost", "roi", etc
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)  # "count", "dollars", "percentage", "ratio"
    dimension = Column(String, nullable=True)  # "event_type", "channel", "school", "company", etc
    dimension_value = Column(String, nullable=True)
    context = Column(JSON, nullable=True)  # additional context as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# OUT-OF-AREA CONTRACT ANALYTICS
# ========================================================

class ContractClassification(Base):
    """Classify contracts as in-area, out-of-area, imported, exported, cross-market."""
    __tablename__ = "contract_classifications"
    id = Column(String, primary_key=True)
    contract_id = Column(String, nullable=False)  # reference to source contract
    applicant_zip = Column(String(5), nullable=True)
    assigned_zip = Column(String(5), nullable=True)
    writing_rsid = Column(String(4), nullable=True)
    assigned_rsid = Column(String(4), nullable=True)
    school_zip = Column(String(5), nullable=True)
    event_zip = Column(String(5), nullable=True)
    originating_operation = Column(String, nullable=True)
    classification = Column(String, nullable=False)  # "in_area", "out_of_area", "imported", "exported", "cross_market"
    classification_confidence = Column(Float, nullable=True)  # 0.0-1.0
    market_penetration_score = Column(Float, nullable=True)  # 0.0-1.0
    territory_control_score = Column(Float, nullable=True)  # 0.0-1.0
    operational_influence_score = Column(Float, nullable=True)  # 0.0-1.0
    classified_at = Column(DateTime(timezone=True), server_default=func.now())
    classified_by = Column(String, nullable=True)  # algorithm or user
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarketLeakage(Base):
    """Track market leakage: ZIP ownership, loss, cross-market influence."""
    __tablename__ = "market_leakage"
    id = Column(String, primary_key=True)
    from_zip = Column(String(5), nullable=False)
    to_zip = Column(String(5), nullable=False)
    from_rsid = Column(String(4), nullable=True)
    to_rsid = Column(String(4), nullable=True)
    leak_type = Column(String, nullable=False)  # "out_of_territory", "cross_rsid", "territory_loss", "influence_gain"
    contract_count = Column(Integer, nullable=True)
    lead_count = Column(Integer, nullable=True)
    engagement_count = Column(Integer, nullable=True)
    leak_value_dollars = Column(Float, nullable=True)
    leak_value_contracts = Column(Integer, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    identified_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ContractInfluence(Base):
    """Track cross-market influence: which RSIDs/ZIPs influence success of other territories."""
    __tablename__ = "contract_influence"
    id = Column(String, primary_key=True)
    influencing_rsid = Column(String(4), nullable=True)
    influencing_zip = Column(String(5), nullable=True)
    influenced_rsid = Column(String(4), nullable=True)
    influenced_zip = Column(String(5), nullable=True)
    influence_type = Column(String, nullable=False)  # "positive", "negative", "neutral"
    contract_count = Column(Integer, nullable=True)
    influence_score = Column(Float, nullable=True)  # 0.0-1.0
    causation_confidence = Column(Float, nullable=True)  # 0.0-1.0
    identified_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# RECRUITER OPERATIONAL EFFECTIVENESS
# ========================================================

class RecruiterActivity(Base):
    """Track recruiter activities: prospecting hours, contacts, appointments, attempts, enlistments."""
    __tablename__ = "recruiter_activity"
    id = Column(String, primary_key=True)
    recruiter_id = Column(String, nullable=False)
    recruiter_name = Column(String, nullable=True)
    station_rsid = Column(String(4), nullable=True)
    brigade_prefix = Column(String(1), nullable=True)
    battalion_prefix = Column(String(2), nullable=True)
    company_prefix = Column(String(3), nullable=True)
    activity_date = Column(Date, nullable=False)
    activity_type = Column(String, nullable=False)  # "prospecting", "contact", "appointment", "attempt", "enlistment"
    activity_count = Column(Integer, nullable=True)
    activity_duration_hours = Column(Float, nullable=True)
    outcome_count = Column(Integer, nullable=True)
    outcome_type = Column(String, nullable=True)  # "contract", "referral", "rejection", "no_show"
    reporting_period = Column(String, nullable=True)  # "daily", "weekly", "monthly"
    source_system = Column(String, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecruiterEffectiveness(Base):
    """Recruiter effectiveness metrics: derived operational analytics (objective, non-judgmental)."""
    __tablename__ = "recruiter_effectiveness"
    id = Column(String, primary_key=True)
    recruiter_id = Column(String, nullable=False)
    station_rsid = Column(String(4), nullable=True)
    reporting_period = Column(String, nullable=False)  # "daily", "weekly", "monthly"
    period_date = Column(Date, nullable=False)
    prospecting_hours = Column(Float, nullable=True)
    contacts_count = Column(Integer, nullable=True)
    appointments_count = Column(Integer, nullable=True)
    attempts_count = Column(Integer, nullable=True)
    contracts_count = Column(Integer, nullable=True)
    contacts_per_hour = Column(Float, nullable=True)
    appointments_per_hour = Column(Float, nullable=True)
    contracts_per_hour = Column(Float, nullable=True)
    attempts_per_hour = Column(Float, nullable=True)
    attempts_per_appointment = Column(Float, nullable=True)
    hours_per_appointment = Column(Float, nullable=True)
    hours_per_enlistment = Column(Float, nullable=True)
    contact_conversion_rate = Column(Float, nullable=True)  # contacts → appointments
    appointment_conversion_rate = Column(Float, nullable=True)  # appointments → contracts
    overall_conversion_rate = Column(Float, nullable=True)  # prospecting → contracts
    workload_pct_of_station = Column(Float, nullable=True)  # % of station workload
    efficiency_index = Column(Float, nullable=True)  # 0.0-1.0 relative to peers
    effort_index = Column(Float, nullable=True)  # 0.0-1.0 relative to peers
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PredictiveProductionPace(Base):
    """Predict recruiter production pacing based on current activity trends."""
    __tablename__ = "predictive_production_pace"
    id = Column(String, primary_key=True)
    recruiter_id = Column(String, nullable=False)
    station_rsid = Column(String(4), nullable=True)
    forecast_period = Column(String, nullable=False)  # "weekly", "monthly", "quarterly"
    as_of_date = Column(Date, nullable=False)
    predicted_contracts = Column(Integer, nullable=True)
    predicted_contracts_low_bound = Column(Integer, nullable=True)
    predicted_contracts_high_bound = Column(Integer, nullable=True)
    confidence_level = Column(Float, nullable=True)  # 0.0-1.0
    pacing_vs_goal = Column(String, nullable=True)  # "on_track", "ahead", "behind"
    pacing_gap_contracts = Column(Integer, nullable=True)  # +/- contracts to meet goal
    recommended_actions = Column(JSON, nullable=True)  # array of action recommendations
    forecasted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# VACANCY ALIGNMENT ENGINE
# ========================================================

class VacancyAlignment(Base):
    """Align vacancies to market demographics, school populations, civilian industries, trends."""
    __tablename__ = "vacancy_alignment"
    id = Column(String, primary_key=True)
    vacancy_mos = Column(String, nullable=False)  # MOS code
    vacancy_count = Column(Integer, nullable=False)
    market_zip_primary = Column(String(5), nullable=False)
    market_zip_secondary = Column(String(5), nullable=True)
    station_rsid = Column(String(4), nullable=True)
    demand_level = Column(String, nullable=False)  # "critical", "high", "medium", "low"
    demographic_fit_score = Column(Float, nullable=True)  # 0.0-1.0
    school_population_fit = Column(Float, nullable=True)  # 0.0-1.0
    civilian_industry_alignment = Column(Float, nullable=True)  # 0.0-1.0
    operational_trend_alignment = Column(Float, nullable=True)  # 0.0-1.0
    overall_alignment_score = Column(Float, nullable=True)  # 0.0-1.0
    alignment_rationale = Column(JSON, nullable=True)  # {"why": "...", "data_sources": [...], "impact": "..."}
    aligned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TargetPopulation(Base):
    """Identified target populations for vacancy alignment and operations."""
    __tablename__ = "target_populations"
    id = Column(String, primary_key=True)
    vacancy_alignment_id = Column(String, ForeignKey("vacancy_alignment.id"), nullable=False)
    target_demographic = Column(String, nullable=False)  # "18-25yr HS seniors", "college students", "technical industry", etc
    population_estimate = Column(Integer, nullable=True)
    geographic_coverage_zips = Column(JSON, nullable=True)  # list of ZIPs
    schools_to_focus = Column(JSON, nullable=True)  # list of school names/IDs
    industries_to_target = Column(JSON, nullable=True)  # civilian industries
    messaging_themes = Column(JSON, nullable=True)  # array of messaging recommendations
    marketing_platforms = Column(JSON, nullable=True)  # "social_media", "radio", "digital_ads", "school_events", etc
    event_recommendations = Column(JSON, nullable=True)  # array of event types
    partnership_opportunities = Column(JSON, nullable=True)  # potential partners
    identified_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MessagingTheme(Base):
    """Messaging theme recommendations for target populations."""
    __tablename__ = "messaging_themes"
    id = Column(String, primary_key=True)
    target_population_id = Column(String, ForeignKey("target_populations.id"), nullable=False)
    theme_name = Column(String, nullable=False)
    theme_description = Column(Text, nullable=True)
    target_audience = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # "social_media", "radio", "digital", "direct", "school", "event"
    effectiveness_score = Column(Float, nullable=True)  # 0.0-1.0
    historical_ctr = Column(Float, nullable=True)  # click-through rate
    historical_conversion = Column(Float, nullable=True)  # conversion rate
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# ROP/SRP RECOMMENDATION ENGINE
# ========================================================

class RecommendationRationale(Base):
    """Structured rationale for recommendations: WHY, WHAT DATA, HOW IMPACTS."""
    __tablename__ = "recommendation_rationale"
    id = Column(String, primary_key=True)
    recommendation_id = Column(String, nullable=False)  # links to advisory recommendation
    rationale_type = Column(String, nullable=False)  # "school_effectiveness", "market_penetration", "recruiter_coverage", "leakage", "conversion_trend"
    why_summary = Column(Text, nullable=False)  # Plain English why this recommendation exists
    supporting_data = Column(JSON, nullable=False)  # array of {"metric": "...", "value": "...", "threshold": "...", "trend": "..."}
    impact_analysis = Column(JSON, nullable=False)  # {"if_implemented": "...", "financial_impact": "...", "operational_impact": "..."}
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdvisoryRecommendation(Base):
    """Advisory recommendations for ROP/SRP changes, school prioritization, recruiter realignment, etc."""
    __tablename__ = "advisory_recommendations"
    id = Column(String, primary_key=True)
    recommendation_type = Column(String, nullable=False)  # "rop_change", "srp_change", "school_prioritization", "recruiter_realignment", "engagement_frequency", "operation_adjustment"
    recommendation_scope = Column(String, nullable=False)  # "USAREC", "BRIGADE", "BATTALION", "COMPANY", "STATION", "INDIVIDUAL"
    scope_value = Column(String, nullable=False)  # brigade_prefix, battalion_prefix, company_prefix, station_rsid, recruiter_id, or "USAREC"
    recommendation_text = Column(Text, nullable=False)
    recommendation_detail = Column(JSON, nullable=False)  # detailed parameters/configuration
    rationale_id = Column(String, ForeignKey("recommendation_rationale.id"), nullable=False)
    priority = Column(String, nullable=False)  # "critical", "high", "medium", "low"
    urgency = Column(String, nullable=False)  # "immediate", "30_days", "90_days", "ongoing"
    status = Column(String, nullable=False, server_default='advisory')  # "advisory", "acknowledged", "implemented", "rejected", "deferred"
    commander_acknowledgement = Column(String, nullable=True)  # user who acknowledged
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    commander_decision = Column(String, nullable=True)  # "accepted", "modified", "rejected"
    decision_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    implementation_start = Column(DateTime(timezone=True), nullable=True)
    implementation_end = Column(DateTime(timezone=True), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# ROP/SRP PLAN LINKAGE + VERSIONING
# ========================================================

class RopPlan(Base):
    """Baseline ROP plan container by station/scope."""
    __tablename__ = "rop_plans"
    id = Column(String, primary_key=True)
    station_rsid = Column(String(4), nullable=False)
    plan_name = Column(String, nullable=False)
    plan_scope = Column(String, nullable=False, server_default='STATION')
    status = Column(String, nullable=False, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RopPlanVersion(Base):
    """Append-only version table for ROP plans."""
    __tablename__ = "rop_plan_versions"
    id = Column(String, primary_key=True)
    rop_plan_id = Column(String, ForeignKey("rop_plans.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_notes = Column(Text, nullable=True)
    plan_payload = Column(JSON, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, server_default='1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SrpPlan(Base):
    """Baseline SRP plan container by station/scope."""
    __tablename__ = "srp_plans"
    id = Column(String, primary_key=True)
    station_rsid = Column(String(4), nullable=False)
    plan_name = Column(String, nullable=False)
    plan_scope = Column(String, nullable=False, server_default='STATION')
    status = Column(String, nullable=False, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SrpPlanVersion(Base):
    """Append-only version table for SRP plans."""
    __tablename__ = "srp_plan_versions"
    id = Column(String, primary_key=True)
    srp_plan_id = Column(String, ForeignKey("srp_plans.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_notes = Column(Text, nullable=True)
    plan_payload = Column(JSON, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, server_default='1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# FRAGO GENERATION LAYER
# ========================================================

class FragoOrder(Base):
    """FRAGO order container by station/scope."""
    __tablename__ = "frago_orders"
    id = Column(String, primary_key=True)
    station_rsid = Column(String(8), nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default='draft')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FragoOrderVersion(Base):
    """Append-only version table for FRAGO order content."""
    __tablename__ = "frago_order_versions"
    id = Column(String, primary_key=True)
    frago_id = Column(String, ForeignKey("frago_orders.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(JSON, nullable=False)
    generated_from_recommendation_id = Column(String, nullable=True)
    rop_version_id = Column(String, nullable=True)
    srp_version_id = Column(String, nullable=True)
    analytics_snapshot_id = Column(String, nullable=True)
    recommendation_record_version_id = Column(String, ForeignKey("recommendation_record_versions.id"), nullable=True)
    analytics_snapshot_version_id = Column(String, ForeignKey("analytics_snapshot_versions.id"), nullable=True)
    effective_start = Column(DateTime(timezone=True), nullable=True)
    effective_end = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, nullable=False, server_default='1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================================
# VERSIONING + ARCHIVAL LAYER
# ========================================================

class AnalyticsSnapshot(Base):
    """Root analytics snapshot record by type/scope."""
    __tablename__ = "analytics_snapshots"
    id = Column(String, primary_key=True)
    snapshot_type = Column(String, nullable=False)
    station_rsid = Column(String(8), nullable=True, index=True)
    fy = Column(String, nullable=True)
    quarter = Column(String, nullable=True)
    rsm = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalyticsSnapshotVersion(Base):
    """Append-only analytics snapshot versions preserving payload history."""
    __tablename__ = "analytics_snapshot_versions"
    id = Column(String, primary_key=True)
    snapshot_id = Column(String, ForeignKey("analytics_snapshots.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    period_analyzed = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_current = Column(Boolean, nullable=False, server_default='1')


class RecommendationRecord(Base):
    """Root recommendation record by recommendation type and scope."""
    __tablename__ = "recommendation_records"
    id = Column(String, primary_key=True)
    recommendation_type = Column(String, nullable=False)
    station_rsid = Column(String(8), nullable=True, index=True)
    fy = Column(String, nullable=True)
    quarter = Column(String, nullable=True)
    rsm = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecommendationRecordVersion(Base):
    """Append-only recommendation payload versions."""
    __tablename__ = "recommendation_record_versions"
    id = Column(String, primary_key=True)
    record_id = Column(String, ForeignKey("recommendation_records.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    explanation_objects = Column(JSON, nullable=True)
    analytics_snapshot_id = Column(String, ForeignKey("analytics_snapshots.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_current = Column(Boolean, nullable=False, server_default='1')


class ExplanationArchive(Base):
    """Append-only archive of explanation objects."""
    __tablename__ = "explanation_archives"
    id = Column(String, primary_key=True)
    recommendation_record_version_id = Column(String, ForeignKey("recommendation_record_versions.id"), nullable=True)
    explanation_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VersionArchiveEvent(Base):
    """Append-only version archive ledger for all intelligence version writes."""
    __tablename__ = "version_archive_events"
    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)  # analytics_snapshot | recommendation_record | frago_order
    entity_id = Column(String, nullable=False)
    version_id = Column(String, nullable=False)
    version_number = Column(Integer, nullable=False)
    station_rsid = Column(String(8), nullable=True, index=True)
    fy = Column(String, nullable=True)
    quarter = Column(String, nullable=True)
    rsm = Column(String, nullable=True)
    event_type = Column(String, nullable=False, server_default='version_created')
    payload_hash = Column(String(64), nullable=True)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
