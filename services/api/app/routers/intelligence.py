"""© 2026 TAAIP. Copyright pending.
Data Intelligence Layer API endpoints: ingestion, analytics, recommendations.
Non-breaking additions to existing API. No changes to existing endpoints or signatures.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import time

from ..database import get_db
from ..intelligence_ingestion import (
    IngestionPipeline,
    ingest_rid_pipeline,
    ingest_vantage_pipeline,
    ingest_powerbi_pipeline,
    ingest_emm_pipeline,
)
from ..intelligence_analytics import (
    HistoricalSnapshotEngine,
    OutOfAreaContractAnalytics,
    RecruiterEffectivenessAnalytics,
    PredictiveProductionPacingEngine
)
from ..intelligence_recommendations import (
    VacancyAlignmentEngine,
    recommend_vacancy_alignment,
    recommend_rop_srp,
    recommend_school_prioritization,
)
from ..services.versioning import list_versions, get_version, get_archive_event
from ..services.runtime_cache import bucket
from ..services.intelligence_observability import timed_event, error_payload
from .. import models_intelligence as mi


router = APIRouter(prefix="/api/v2/intelligence", tags=["Data Intelligence"])


def _error_response(status_code: int, message: str, context: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_payload(message, context=context))


def _extract_frago_scope_metadata(content: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize FRAGO scope/period metadata from content payload."""
    content = content or {}
    scope = content.get("scope") or {}
    return {
        "rsid": content.get("rsid") or scope.get("rsid") or scope.get("station_rsid"),
        "unit_scope": content.get("unit_scope") or scope.get("unit_scope") or [],
        "period_type": content.get("period_type") or scope.get("period_type"),
        "period_value": content.get("period_value") or scope.get("period_value"),
    }


def _archive_event_payload(db: Session, entity_type: str, entity_id: str, version_number: int) -> Dict[str, Any]:
    row = get_archive_event(db, entity_type, entity_id, version_number)
    if not row:
        return {}
    return {
        "archive_event_id": row.id,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "version_id": row.version_id,
        "version_number": row.version_number,
        "station_rsid": row.station_rsid,
        "fy": row.fy,
        "quarter": row.quarter,
        "rsm": row.rsm,
        "event_type": row.event_type,
        "payload_hash": row.payload_hash,
        "metadata": row.event_metadata,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _sectioned_diff(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    left = left or {}
    right = right or {}
    keys_left = set(left.keys())
    keys_right = set(right.keys())

    added = sorted(list(keys_right - keys_left))
    removed = sorted(list(keys_left - keys_right))
    changed = []
    for key in sorted(list(keys_left & keys_right)):
        if left.get(key) != right.get(key):
            changed.append({
                "field": key,
                "before": left.get(key),
                "after": right.get(key),
            })

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def _build_structured_version_diff(
    entity_type: str,
    left_content: Dict[str, Any],
    right_content: Dict[str, Any],
    left_explanation: Dict[str, Any],
    right_explanation: Dict[str, Any],
) -> Dict[str, Any]:
    analytics_diff = {"added": [], "removed": [], "changed": []}
    recommendation_diff = {"added": [], "removed": [], "changed": []}
    frago_diff = {"added": [], "removed": [], "changed": []}

    if entity_type == "analytics_snapshot":
        analytics_diff = _sectioned_diff(left_content, right_content)
    elif entity_type == "recommendation_record":
        recommendation_diff = _sectioned_diff(left_content, right_content)
    elif entity_type == "frago_order":
        frago_diff = _sectioned_diff(left_content, right_content)

    return {
        "analytics": analytics_diff,
        "recommendations": recommendation_diff,
        "frago": frago_diff,
        "explanation": _sectioned_diff(left_explanation, right_explanation),
    }


# ========================================================
# Pydantic Models for Requests/Responses
# ========================================================

class IngestionRequest(BaseModel):
    source_name: str
    ingested_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContractClassificationRequest(BaseModel):
    contract_id: str
    applicant_zip: Optional[str] = None
    assigned_zip: Optional[str] = None
    writing_rsid: Optional[str] = None
    assigned_rsid: Optional[str] = None
    school_zip: Optional[str] = None
    event_zip: Optional[str] = None
    originating_operation: Optional[str] = None


class RecruiterActivityRequest(BaseModel):
    recruiter_id: str
    activity_date: date
    activity_type: str
    activity_count: Optional[int] = None
    activity_duration_hours: Optional[float] = None
    outcome_count: Optional[int] = None
    outcome_type: Optional[str] = None
    station_rsid: Optional[str] = None
    source_system: Optional[str] = None


class EffectivenessCalculationRequest(BaseModel):
    recruiter_id: str
    period_date: date
    reporting_period: str = "monthly"  # "daily", "weekly", "monthly"
    station_rsid: Optional[str] = None


class VacancyAlignmentRequest(BaseModel):
    vacancy_mos: str
    vacancy_count: int
    market_zip_primary: str
    station_rsid: Optional[str] = None


class RecommendationQueryResponse(BaseModel):
    id: str
    recommendation_type: str
    recommendation_scope: str
    scope_value: str
    recommendation_text: str
    priority: str
    urgency: str
    status: str
    generated_at: datetime


class VersionCompareRequest(BaseModel):
    version_id_a: str
    version_id_b: str


class EntityVersionCompareRequest(BaseModel):
    entity_type: str
    entity_id: str
    left_version: int
    right_version: int


def _flatten_payload(data: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten nested payloads into dotted-path keys for diff output."""
    flat: Dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            flat.update(_flatten_payload(value, next_prefix))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            next_prefix = f"{prefix}[{idx}]"
            flat.update(_flatten_payload(value, next_prefix))
    else:
        flat[prefix] = data
    return flat


def _diff_payloads(payload_a: Dict[str, Any], payload_b: Dict[str, Any]) -> Dict[str, Any]:
    """Compute added/removed/changed field diff between two JSON payloads."""
    flat_a = _flatten_payload(payload_a or {})
    flat_b = _flatten_payload(payload_b or {})

    keys_a = set(flat_a.keys())
    keys_b = set(flat_b.keys())

    fields_added = sorted(list(keys_b - keys_a))
    fields_removed = sorted(list(keys_a - keys_b))

    changed: Dict[str, Any] = {}
    for key in sorted(list(keys_a & keys_b)):
        if flat_a[key] != flat_b[key]:
            changed[key] = {
                "before": flat_a[key],
                "after": flat_b[key],
            }

    return {
        "fields_added": fields_added,
        "fields_removed": fields_removed,
        "fields_changed": changed,
    }


# ========================================================
# INGESTION ENDPOINTS
# ========================================================

@router.post("/ingest/file", summary="Ingest data file (CSV/XLSX)")
def ingest_data_file(
    source_name: str,
    file: UploadFile = File(...),
    ingested_by: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest a data file from RID, Vantage, PowerBI, EMM, or custom source.
    Auto-detects schema, normalizes values, preserves raw source.
    
    Returns: Ingestion log with record count and status.
    """
    try:
        content = file.file.read()
        source = source_name.strip().lower()

        if source == "rid":
            result = ingest_rid_pipeline(
                db=db,
                file_path=file.filename,
                file_content=content,
                ingested_by=ingested_by,
            )
        elif source == "vantage":
            result = ingest_vantage_pipeline(
                db=db,
                file_path=file.filename,
                file_content=content,
                ingested_by=ingested_by,
            )
        elif source in ["powerbi", "power_bi", "power-bi"]:
            result = ingest_powerbi_pipeline(
                db=db,
                file_path=file.filename,
                file_content=content,
                ingested_by=ingested_by,
            )
        elif source == "emm":
            result = ingest_emm_pipeline(
                db=db,
                file_path=file.filename,
                file_content=content,
                ingested_by=ingested_by,
            )
        else:
            pipeline = IngestionPipeline(db)
            log = pipeline.ingest_file(
                source_name=source_name,
                file_path=file.filename,
                file_content=content,
                ingested_by=ingested_by,
            )
            result = {
                "ingestion_log_id": log.id,
                "source": source_name,
                "status": log.status,
                "record_count": log.record_count,
                "ingested_at": log.ingested_at.isoformat() if log.ingested_at else None,
                "file_hash": log.source_hash,
                "error_message": log.error_message,
            }

        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result.get("error_message", "Ingestion failed"))

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ingestion-logs", summary="Get ingestion history")
def get_ingestion_logs(
    source_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retrieve ingestion logs (audit trail) for data quality and lineage tracking."""
    query = db.query(mi.DataIngestionLog)
    source_lookup: Dict[str, str] = {
        s.id: s.source_name for s in db.query(mi.DataSource).all()
    }
    if source_name:
        source = db.query(mi.DataSource).filter_by(source_name=source_name).first()
        if source:
            query = query.filter_by(source_id=source.id)
    
    logs = query.order_by(mi.DataIngestionLog.ingested_at.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "source": source_lookup.get(log.source_id, log.source_id),
            "file": log.source_file,
            "record_count": log.record_count,
            "status": log.status,
            "ingested_at": log.ingested_at.isoformat(),
            "error": log.error_message
        }
        for log in logs
    ]


# ========================================================
# HISTORICAL SNAPSHOT ENDPOINTS
# ========================================================

@router.post("/snapshots", summary="Create historical snapshot")
def create_snapshot(
    snapshot_type: str,  # "daily", "weekly", "monthly", "event_triggered"
    snapshot_date: date,
    scope_type: str,
    scope_value: str,
    trigger_event: Optional[str] = None,
    metrics: Optional[Dict[str, float]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a historical snapshot of operational metrics.
    Snapshots are never overwritten and support trend analysis.
    """
    try:
        engine = HistoricalSnapshotEngine(db)
        snapshot = engine.create_snapshot(
            snapshot_type=snapshot_type,
            snapshot_date=snapshot_date,
            scope_type=scope_type,
            scope_value=scope_value,
            trigger_event=trigger_event,
            metrics=metrics or {}
        )
        return {
            "id": snapshot.id,
            "type": snapshot.snapshot_type,
            "date": snapshot.snapshot_date.isoformat(),
            "scope": f"{snapshot.scope_type}/{snapshot.scope_value}",
            "trigger": snapshot.trigger_event,
            "version": snapshot.data_version,
            "created_at": snapshot.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/snapshots", summary="Query historical snapshots")
def get_snapshots(
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Query historical snapshots for trend analysis."""
    query = db.query(mi.HistoricalSnapshot)
    
    if scope_type:
        query = query.filter_by(scope_type=scope_type)
    if scope_value:
        query = query.filter_by(scope_value=scope_value)
    if start_date:
        query = query.filter(mi.HistoricalSnapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(mi.HistoricalSnapshot.snapshot_date <= end_date)
    
    snapshots = query.order_by(mi.HistoricalSnapshot.snapshot_date.desc()).limit(limit).all()
    return [
        {
            "id": s.id,
            "type": s.snapshot_type,
            "date": s.snapshot_date.isoformat(),
            "scope": f"{s.scope_type}/{s.scope_value}",
            "trigger": s.trigger_event,
            "version": s.data_version,
            "created_at": s.created_at.isoformat()
        }
        for s in snapshots
    ]


# ========================================================
# OUT-OF-AREA CONTRACT ANALYTICS ENDPOINTS
# ========================================================

@router.post("/contracts/classify", summary="Classify contract (OOA analysis)")
def classify_contract(
    req: ContractClassificationRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Classify a contract as in-area, out-of-area, imported, exported, or cross-market."""
    try:
        analytics = OutOfAreaContractAnalytics(db)
        classification = analytics.classify_contract(
            contract_id=req.contract_id,
            applicant_zip=req.applicant_zip,
            assigned_zip=req.assigned_zip,
            writing_rsid=req.writing_rsid,
            assigned_rsid=req.assigned_rsid,
            school_zip=req.school_zip,
            event_zip=req.event_zip,
            originating_operation=req.originating_operation
        )
        return {
            "contract_id": classification.contract_id,
            "classification": classification.classification,
            "confidence": classification.classification_confidence,
            "market_penetration": classification.market_penetration_score,
            "territory_control": classification.territory_control_score,
            "operational_influence": classification.operational_influence_score,
            "classified_at": classification.classified_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/market-leakage", summary="Query market leakage analysis")
def get_market_leakage(
    from_zip: Optional[str] = None,
    from_rsid: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Query market leakage analysis for territory control insights."""
    query = db.query(mi.MarketLeakage)
    
    if from_zip:
        query = query.filter_by(from_zip=from_zip)
    if from_rsid:
        query = query.filter_by(from_rsid=from_rsid)
    if start_date:
        query = query.filter(mi.MarketLeakage.period_start >= start_date)
    if end_date:
        query = query.filter(mi.MarketLeakage.period_end <= end_date)
    
    leakages = query.order_by(mi.MarketLeakage.identified_at.desc()).limit(limit).all()
    return [
        {
            "from_zip": l.from_zip,
            "to_zip": l.to_zip,
            "from_rsid": l.from_rsid,
            "to_rsid": l.to_rsid,
            "leak_type": l.leak_type,
            "contract_count": l.contract_count,
            "leak_value": l.leak_value_dollars,
            "period": f"{l.period_start.isoformat()} to {l.period_end.isoformat()}"
        }
        for l in leakages
    ]


# ========================================================
# RECRUITER EFFECTIVENESS ENDPOINTS
# ========================================================

@router.post("/recruiter-activity", summary="Record recruiter activity")
def record_recruiter_activity(
    req: RecruiterActivityRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Record recruiter activity (contacts, appointments, prospecting hours, etc)."""
    try:
        activity = mi.RecruiterActivity(
            id=f"activity_{datetime.now().timestamp()}_{req.recruiter_id}",
            recruiter_id=req.recruiter_id,
            station_rsid=req.station_rsid,
            activity_date=req.activity_date,
            activity_type=req.activity_type,
            activity_count=req.activity_count,
            activity_duration_hours=req.activity_duration_hours,
            outcome_count=req.outcome_count,
            outcome_type=req.outcome_type,
            source_system=req.source_system
        )
        db.add(activity)
        db.commit()
        return {
            "id": activity.id,
            "recruiter_id": activity.recruiter_id,
            "activity_type": activity.activity_type,
            "activity_date": activity.activity_date.isoformat(),
            "created_at": activity.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recruiter-effectiveness", summary="Calculate recruiter effectiveness")
def calculate_effectiveness(
    req: EffectivenessCalculationRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Calculate recruiter operational effectiveness metrics (objective, non-judgmental)."""
    try:
        analytics = RecruiterEffectivenessAnalytics(db)
        effectiveness = analytics.calculate_effectiveness(
            recruiter_id=req.recruiter_id,
            period_date=req.period_date,
            reporting_period=req.reporting_period,
            station_rsid=req.station_rsid
        )
        return {
            "recruiter_id": effectiveness.recruiter_id,
            "period": f"{effectiveness.reporting_period}/{effectiveness.period_date.isoformat()}",
            "prospecting_hours": effectiveness.prospecting_hours,
            "contacts": effectiveness.contacts_count,
            "appointments": effectiveness.appointments_count,
            "contracts": effectiveness.contracts_count,
            "contacts_per_hour": effectiveness.contacts_per_hour,
            "appointments_per_hour": effectiveness.appointments_per_hour,
            "contracts_per_hour": effectiveness.contracts_per_hour,
            "contact_conversion_rate": effectiveness.contact_conversion_rate,
            "appointment_conversion_rate": effectiveness.appointment_conversion_rate,
            "efficiency_index": effectiveness.efficiency_index,
            "effort_index": effectiveness.effort_index,
            "calculated_at": effectiveness.calculated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recruiter-effectiveness/{recruiter_id}", summary="Get recruiter effectiveness history")
def get_effectiveness_history(
    recruiter_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 12,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get historical effectiveness records for a recruiter (trend analysis)."""
    query = db.query(mi.RecruiterEffectiveness).filter_by(recruiter_id=recruiter_id)
    
    if start_date:
        query = query.filter(mi.RecruiterEffectiveness.period_date >= start_date)
    if end_date:
        query = query.filter(mi.RecruiterEffectiveness.period_date <= end_date)
    
    records = query.order_by(mi.RecruiterEffectiveness.period_date.desc()).limit(limit).all()
    return [
        {
            "period": f"{r.reporting_period}/{r.period_date.isoformat()}",
            "contracts": r.contracts_count,
            "contracts_per_hour": r.contracts_per_hour,
            "efficiency_index": r.efficiency_index,
            "effort_index": r.effort_index
        }
        for r in records
    ]


@router.post("/recruiter-production-forecast", summary="Forecast recruiter production")
def forecast_production(
    recruiter_id: str,
    forecast_period: str = "monthly",
    station_rsid: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Predict recruiter production pacing based on recent trends."""
    try:
        engine = PredictiveProductionPacingEngine(db)
        forecast = engine.forecast_production(
            recruiter_id=recruiter_id,
            forecast_period=forecast_period,
            station_rsid=station_rsid
        )
        if not forecast:
            raise HTTPException(status_code=404, detail="Insufficient history to forecast")
        
        return {
            "recruiter_id": forecast.recruiter_id,
            "forecast_period": forecast.forecast_period,
            "predicted_contracts": forecast.predicted_contracts,
            "confidence": forecast.confidence_level,
            "pacing_vs_goal": forecast.pacing_vs_goal,
            "pacing_gap": forecast.pacing_gap_contracts,
            "forecasted_at": forecast.forecasted_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========================================================
# VACANCY ALIGNMENT & RECOMMENDATIONS ENDPOINTS
# ========================================================

@router.post("/vacancy-alignment", summary="Analyze vacancy alignment")
def analyze_vacancy_alignment(
    req: VacancyAlignmentRequest,
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    rsm: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Analyze how well a vacancy aligns to market opportunities."""
    with timed_event("analytics.fetch", rsid=req.station_rsid, period=f"{fy or quarter or rsm or ''}", endpoint="vacancy_alignment"):
        try:
            result = recommend_vacancy_alignment(
                db=db,
                vacancy_mos=req.vacancy_mos,
                vacancy_count=req.vacancy_count,
                market_zip_primary=req.market_zip_primary,
                station_rsid=req.station_rsid,
                fy=fy,
                quarter=quarter,
                rsm=rsm,
            )
            if result.get("status") == "failed":
                return _error_response(
                    400,
                    result.get("error_message", "Vacancy alignment failed"),
                    context={"operation": "vacancy_alignment", "rsid": req.station_rsid},
                )
            return result
        except Exception:
            return _error_response(400, "Vacancy alignment failed", context={"operation": "vacancy_alignment"})


@router.post("/recommendations/rop-srp", summary="Generate ROP/SRP recommendations")
def generate_rop_srp_recommendations(
    station_rsid: str,
    lookback_days: int = 90,
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    rsm: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate advisory ROP/SRP recommendations for commander decision support."""
    with timed_event("recommendations.fetch", rsid=station_rsid, period=f"{fy or quarter or rsm or ''}", endpoint="recommend_rop_srp"):
        try:
            result = recommend_rop_srp(
                db=db,
                station_rsid=station_rsid,
                lookback_days=lookback_days,
                fy=fy,
                quarter=quarter,
                rsm=rsm,
            )
            if result.get("status") == "failed":
                return _error_response(
                    400,
                    result.get("error_message", "Recommendation generation failed"),
                    context={"operation": "recommend_rop_srp", "rsid": station_rsid},
                )
            return result
        except Exception:
            return _error_response(400, "Recommendation generation failed", context={"operation": "recommend_rop_srp"})


@router.post("/recommendations/school-prioritization", summary="Generate school prioritization recommendations")
def generate_school_prioritization_recommendations(
    station_rsid: str,
    lookback_days: int = 180,
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    rsm: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate school prioritization recommendations for ROP allocation planning."""
    with timed_event("recommendations.fetch", rsid=station_rsid, period=f"{fy or quarter or rsm or ''}", endpoint="recommend_school_prioritization"):
        try:
            result = recommend_school_prioritization(
                db=db,
                station_rsid=station_rsid,
                lookback_days=lookback_days,
                fy=fy,
                quarter=quarter,
                rsm=rsm,
            )
            if result.get("status") == "failed":
                return _error_response(
                    400,
                    result.get("error_message", "School prioritization failed"),
                    context={"operation": "recommend_school_prioritization", "rsid": station_rsid},
                )
            return result
        except Exception:
            return _error_response(400, "School prioritization failed", context={"operation": "recommend_school_prioritization"})


@router.get("/fragos/{frago_version_id}", summary="Download FRAGO version content")
def get_frago_version(
    frago_version_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Download FRAGO version payload and linkage metadata."""
    cache_key = f"frago_snapshot:{frago_version_id}"
    cached = bucket("frago_snapshot").get(cache_key)
    if cached is not None:
        return cached

    with timed_event("frago.fetch", endpoint="frago_version"):
        frago_version = db.query(mi.FragoOrderVersion).filter_by(id=frago_version_id).first()
        if not frago_version:
            return _error_response(404, "FRAGO version not found", context={"frago_version_id": frago_version_id})

        meta = _extract_frago_scope_metadata(frago_version.content)
        archive_event = _archive_event_payload(
            db,
            "frago_order",
            frago_version.frago_id,
            int(frago_version.version_number or 0),
        )
        explanation = (archive_event.get("metadata") or {}).get("explanation") or {}

        payload = {
            "frago_version_id": frago_version.id,
            "frago_id": frago_version.frago_id,
            "version_number": frago_version.version_number,
            "timestamp": frago_version.created_at.isoformat() if frago_version.created_at else None,
            "rsid": meta["rsid"],
            "unit_scope": meta["unit_scope"],
            "period_type": meta["period_type"],
            "period_value": meta["period_value"],
            "content": frago_version.content,
            "explanation": explanation,
            "archive_event": archive_event,
            "rop_version_id": frago_version.rop_version_id,
            "srp_version_id": frago_version.srp_version_id,
            "analytics_snapshot_id": frago_version.analytics_snapshot_id,
            "recommendation_record_version_id": frago_version.recommendation_record_version_id,
            "analytics_snapshot_version_id": frago_version.analytics_snapshot_version_id,
            "created_at": frago_version.created_at.isoformat() if frago_version.created_at else None,
            "effective_start": frago_version.effective_start.isoformat() if frago_version.effective_start else None,
            "effective_end": frago_version.effective_end.isoformat() if frago_version.effective_end else None,
        }
        bucket("frago_snapshot").set(cache_key, payload)
        return payload


@router.get("/recommendations", summary="Get advisory recommendations")
def get_recommendations(
    recommendation_type: Optional[str] = None,
    status: Optional[str] = None,
    scope_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[RecommendationQueryResponse]:
    """
    Query advisory recommendations (ROP/SRP, school prioritization, recruiter realignment, etc).
    All recommendations are advisory only - commanders retain authority.
    """
    query = db.query(mi.AdvisoryRecommendation)
    
    if recommendation_type:
        query = query.filter_by(recommendation_type=recommendation_type)
    if status:
        query = query.filter_by(status=status)
    if scope_type:
        query = query.filter_by(recommendation_scope=scope_type)
    if priority:
        query = query.filter_by(priority=priority)
    
    recommendations = query.order_by(mi.AdvisoryRecommendation.generated_at.desc()).limit(limit).all()
    return [
        RecommendationQueryResponse(
            id=r.id,
            recommendation_type=r.recommendation_type,
            recommendation_scope=r.recommendation_scope,
            scope_value=r.scope_value,
            recommendation_text=r.recommendation_text,
            priority=r.priority,
            urgency=r.urgency,
            status=r.status,
            generated_at=r.generated_at
        )
        for r in recommendations
    ]


@router.post("/recommendations/{recommendation_id}/acknowledge", summary="Acknowledge recommendation")
def acknowledge_recommendation(
    recommendation_id: str,
    commander_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Commander acknowledges a recommendation."""
    rec = db.query(mi.AdvisoryRecommendation).filter_by(id=recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.status = "acknowledged"
    rec.commander_acknowledgement = commander_id
    rec.acknowledged_at = datetime.now()
    db.commit()
    
    return {"id": rec.id, "status": rec.status, "acknowledged_at": rec.acknowledged_at.isoformat()}


@router.post("/recommendations/{recommendation_id}/decision", summary="Commander decision on recommendation")
def record_recommendation_decision(
    recommendation_id: str,
    decision: str,  # "accepted", "modified", "rejected"
    decision_notes: str = None,
    commander_id: str = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Record commander decision on a recommendation."""
    rec = db.query(mi.AdvisoryRecommendation).filter_by(id=recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    rec.status = decision
    rec.commander_decision = decision
    rec.decision_notes = decision_notes
    rec.decided_at = datetime.now()
    db.commit()
    
    return {
        "id": rec.id,
        "decision": rec.commander_decision,
        "status": rec.status,
        "decided_at": rec.decided_at.isoformat()
    }


@router.get("/analytics/{snapshot_id}/versions", summary="Get analytics snapshot version history")
def get_analytics_versions(
    snapshot_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    cache_key = f"analytics_snapshot:{snapshot_id}"
    cached = bucket("analytics_snapshot").get(cache_key)
    if cached is not None:
        return cached
    with timed_event("analytics.fetch", endpoint="analytics_versions"):
        versions = list_versions(db, "analytics_snapshot", snapshot_id)
        payload = {
            "snapshot_id": snapshot_id,
            "versions": [
                {
                    "version_id": v.id,
                    "version_number": v.version_number,
                    "timestamp": v.created_at.isoformat() if v.created_at else None,
                    "content": v.payload,
                    "payload": v.payload,
                    "period_analyzed": v.period_analyzed,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "explanation": (_archive_event_payload(db, "analytics_snapshot", snapshot_id, int(v.version_number or 0)).get("metadata") or {}).get("explanation") or {},
                    "archive_event": _archive_event_payload(db, "analytics_snapshot", snapshot_id, int(v.version_number or 0)),
                }
                for v in versions
            ],
        }
        bucket("analytics_snapshot").set(cache_key, payload)
        return payload


@router.get("/recommendations/{record_id}/versions", summary="Get recommendation version history")
def get_recommendation_versions(
    record_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    cache_key = f"recommendation_snapshot:{record_id}"
    cached = bucket("recommendation_snapshot").get(cache_key)
    if cached is not None:
        return cached
    with timed_event("recommendations.fetch", endpoint="recommendation_versions"):
        versions = list_versions(db, "recommendation_record", record_id)
        payload = {
            "record_id": record_id,
            "versions": [
                {
                    "version_id": v.id,
                    "version_number": v.version_number,
                    "timestamp": v.created_at.isoformat() if v.created_at else None,
                    "content": v.payload,
                    "payload": v.payload,
                    "explanation_objects": v.explanation_objects,
                    "analytics_snapshot_id": v.analytics_snapshot_id,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "explanation": (_archive_event_payload(db, "recommendation_record", record_id, int(v.version_number or 0)).get("metadata") or {}).get("explanation") or {},
                    "archive_event": _archive_event_payload(db, "recommendation_record", record_id, int(v.version_number or 0)),
                }
                for v in versions
            ],
        }
        bucket("recommendation_snapshot").set(cache_key, payload)
        return payload


@router.get("/explanations/{record_version_id}", summary="Get explanation archives for recommendation version")
def get_explanation_archives(
    record_version_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    record_version = db.query(mi.RecommendationRecordVersion).filter_by(id=record_version_id).first()
    archives = db.query(mi.ExplanationArchive).filter_by(
        recommendation_record_version_id=record_version_id
    ).order_by(mi.ExplanationArchive.created_at.asc()).all()
    return {
        "record_version_id": record_version_id,
        "archives": [
            {
                "archive_id": a.id,
                "explanation_payload": a.explanation_payload,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in archives
        ],
    }


@router.get("/fragos/{frago_id}/versions", summary="Get FRAGO version history")
def get_frago_versions(
    frago_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    cache_key = f"frago_snapshot:list:{frago_id}"
    cached = bucket("frago_snapshot").get(cache_key)
    if cached is not None:
        return cached
    with timed_event("frago.fetch", endpoint="frago_versions"):
        versions = list_versions(db, "frago_order", frago_id)
        payload = {
            "frago_id": frago_id,
            "versions": [
                {
                    "version_id": v.id,
                    "version_number": v.version_number,
                    "timestamp": v.created_at.isoformat() if v.created_at else None,
                    "rsid": _extract_frago_scope_metadata(v.content)["rsid"],
                    "unit_scope": _extract_frago_scope_metadata(v.content)["unit_scope"],
                    "period_type": _extract_frago_scope_metadata(v.content)["period_type"],
                    "period_value": _extract_frago_scope_metadata(v.content)["period_value"],
                    "content": v.content,
                    "recommendation_record_version_id": v.recommendation_record_version_id,
                    "analytics_snapshot_version_id": v.analytics_snapshot_version_id,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "explanation": (_archive_event_payload(db, "frago_order", frago_id, int(v.version_number or 0)).get("metadata") or {}).get("explanation") or {},
                    "archive_event": _archive_event_payload(db, "frago_order", frago_id, int(v.version_number or 0)),
                }
                for v in versions
            ],
        }
        bucket("frago_snapshot").set(cache_key, payload)
        return payload


@router.get("/archive/events", summary="Get append-only intelligence archive events")
def get_archive_events(
    entity_type: Optional[str] = Query(None),
    station_rsid: Optional[str] = Query(None),
    fy: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    rsm: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    bind = db.get_bind()
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)

    def _normalize_optional(value: Any) -> Optional[str]:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        if value is None:
            return None
        return None

    entity_type_value = _normalize_optional(entity_type)
    station_rsid_value = _normalize_optional(station_rsid)
    fy_value = _normalize_optional(fy)
    quarter_value = _normalize_optional(quarter)
    rsm_value = _normalize_optional(rsm)

    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 200
    if limit_value < 1:
        limit_value = 1
    if limit_value > 1000:
        limit_value = 1000

    cache_key = f"archive_events:{entity_type_value}:{station_rsid_value}:{fy_value}:{quarter_value}:{rsm_value}:{limit_value}"
    cached = bucket("archive_event").get(cache_key)
    if cached is not None:
        return cached

    q = db.query(mi.VersionArchiveEvent)
    if entity_type_value:
        q = q.filter(mi.VersionArchiveEvent.entity_type == entity_type_value)
    if station_rsid_value:
        q = q.filter(mi.VersionArchiveEvent.station_rsid == station_rsid_value)
    if fy_value:
        q = q.filter(mi.VersionArchiveEvent.fy == fy_value)
    if quarter_value:
        q = q.filter(mi.VersionArchiveEvent.quarter == quarter_value)
    if rsm_value:
        q = q.filter(mi.VersionArchiveEvent.rsm == rsm_value)

    with timed_event("archive.fetch", rsid=station_rsid_value, period=f"{fy_value or quarter_value or rsm_value or ''}", endpoint="archive_events"):
        rows = q.order_by(mi.VersionArchiveEvent.created_at.desc()).limit(limit_value).all()
    payload = {
        "count": len(rows),
        "events": [
            {
                "archive_event_id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "version_id": r.version_id,
                "version_number": r.version_number,
                "station_rsid": r.station_rsid,
                "fy": r.fy,
                "quarter": r.quarter,
                "rsm": r.rsm,
                "event_type": r.event_type,
                "payload_hash": r.payload_hash,
                "metadata": r.event_metadata,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
    bucket("archive_event").set(cache_key, payload)
    return payload


@router.post("/compare/analytics", summary="Compare two analytics snapshot versions")
def compare_analytics_versions(
    req: VersionCompareRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    a = db.query(mi.AnalyticsSnapshotVersion).filter_by(id=req.version_id_a).first()
    b = db.query(mi.AnalyticsSnapshotVersion).filter_by(id=req.version_id_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both analytics versions not found")

    archive_a = _archive_event_payload(db, "analytics_snapshot", a.snapshot_id, int(a.version_number or 0))
    archive_b = _archive_event_payload(db, "analytics_snapshot", b.snapshot_id, int(b.version_number or 0))
    explanation_a = (archive_a.get("metadata") or {}).get("explanation") or {}
    explanation_b = (archive_b.get("metadata") or {}).get("explanation") or {}
    diff = _build_structured_version_diff("analytics_snapshot", a.payload or {}, b.payload or {}, explanation_a, explanation_b)
    return {
        "entity_type": "analytics_snapshot",
        "entity_id": a.snapshot_id,
        "left_version": int(a.version_number or 0),
        "right_version": int(b.version_number or 0),
        "diff": diff,
        "left_archive_event": archive_a,
        "right_archive_event": archive_b,
        "left_explanation": explanation_a,
        "right_explanation": explanation_b,
    }


@router.post("/compare/recommendations", summary="Compare two recommendation versions")
def compare_recommendation_versions(
    req: VersionCompareRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    a = db.query(mi.RecommendationRecordVersion).filter_by(id=req.version_id_a).first()
    b = db.query(mi.RecommendationRecordVersion).filter_by(id=req.version_id_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both recommendation versions not found")

    archive_a = _archive_event_payload(db, "recommendation_record", a.record_id, int(a.version_number or 0))
    archive_b = _archive_event_payload(db, "recommendation_record", b.record_id, int(b.version_number or 0))
    explanation_a = (archive_a.get("metadata") or {}).get("explanation") or {}
    explanation_b = (archive_b.get("metadata") or {}).get("explanation") or {}
    diff = _build_structured_version_diff("recommendation_record", a.payload or {}, b.payload or {}, explanation_a, explanation_b)
    return {
        "entity_type": "recommendation_record",
        "entity_id": a.record_id,
        "left_version": int(a.version_number or 0),
        "right_version": int(b.version_number or 0),
        "diff": diff,
        "left_archive_event": archive_a,
        "right_archive_event": archive_b,
        "left_explanation": explanation_a,
        "right_explanation": explanation_b,
    }


@router.post("/compare/fragos", summary="Compare two FRAGO versions")
def compare_frago_versions(
    req: VersionCompareRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    a = db.query(mi.FragoOrderVersion).filter_by(id=req.version_id_a).first()
    b = db.query(mi.FragoOrderVersion).filter_by(id=req.version_id_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both FRAGO versions not found")

    archive_a = _archive_event_payload(db, "frago_order", a.frago_id, int(a.version_number or 0))
    archive_b = _archive_event_payload(db, "frago_order", b.frago_id, int(b.version_number or 0))
    explanation_a = (archive_a.get("metadata") or {}).get("explanation") or {}
    explanation_b = (archive_b.get("metadata") or {}).get("explanation") or {}
    diff = _build_structured_version_diff("frago_order", a.content or {}, b.content or {}, explanation_a, explanation_b)
    return {
        "entity_type": "frago_order",
        "entity_id": a.frago_id,
        "left_version": int(a.version_number or 0),
        "right_version": int(b.version_number or 0),
        "diff": diff,
        "left_archive_event": archive_a,
        "right_archive_event": archive_b,
        "left_explanation": explanation_a,
        "right_explanation": explanation_b,
    }


@router.get("/versions/detail", summary="Get deterministic version detail with archive + explanation")
def get_version_detail(
    entity_type: str,
    entity_id: str,
    version_number: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    row = get_version(db, entity_type, entity_id, version_number)
    if not row:
        return _error_response(404, "Version not found", context={"entity_type": entity_type, "entity_id": entity_id, "version_number": version_number})

    if entity_type == "analytics_snapshot":
        content = row.payload
    elif entity_type == "recommendation_record":
        content = row.payload
    elif entity_type == "frago_order":
        content = row.content
    else:
        return _error_response(400, "Unsupported entity_type", context={"entity_type": entity_type})

    archive_event = _archive_event_payload(db, entity_type, entity_id, version_number)
    explanation = (archive_event.get("metadata") or {}).get("explanation") or {}
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "version_number": int(version_number),
        "timestamp": row.created_at.isoformat() if row.created_at else None,
        "content": content,
        "explanation": explanation,
        "archive_event": archive_event,
    }


@router.post("/compare/versions", summary="Compare two versions with archive + explanation context")
def compare_versions(
    req: EntityVersionCompareRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    started = time.perf_counter()
    left = get_version(db, req.entity_type, req.entity_id, int(req.left_version))
    right = get_version(db, req.entity_type, req.entity_id, int(req.right_version))
    if not left or not right:
        return _error_response(
            404,
            "One or both versions not found",
            context={"entity_type": req.entity_type, "entity_id": req.entity_id, "left_version": req.left_version, "right_version": req.right_version},
        )

    if req.entity_type == "analytics_snapshot":
        left_content = left.payload or {}
        right_content = right.payload or {}
    elif req.entity_type == "recommendation_record":
        left_content = left.payload or {}
        right_content = right.payload or {}
    elif req.entity_type == "frago_order":
        left_content = left.content or {}
        right_content = right.content or {}
    else:
        return _error_response(400, "Unsupported entity_type", context={"entity_type": req.entity_type})

    left_archive = _archive_event_payload(db, req.entity_type, req.entity_id, int(req.left_version))
    right_archive = _archive_event_payload(db, req.entity_type, req.entity_id, int(req.right_version))
    left_explanation = (left_archive.get("metadata") or {}).get("explanation") or {}
    right_explanation = (right_archive.get("metadata") or {}).get("explanation") or {}

    duration_ms = int((time.perf_counter() - started) * 1000)
    with timed_event("compare.request", endpoint="compare_versions", entity_type=req.entity_type, entity_id=req.entity_id):
        pass

    return {
        "entity_type": req.entity_type,
        "entity_id": req.entity_id,
        "left_version": int(req.left_version),
        "right_version": int(req.right_version),
        "diff": _build_structured_version_diff(
            req.entity_type,
            left_content,
            right_content,
            left_explanation,
            right_explanation,
        ),
        "left_archive_event": left_archive,
        "right_archive_event": right_archive,
        "left_explanation": left_explanation,
        "right_explanation": right_explanation,
    }
