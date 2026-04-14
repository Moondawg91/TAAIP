from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from starlette.exceptions import HTTPException

from services.api.app.services import accountability_engine, execution_quality, funnel_engine


STALL_STAGE_AGE_DAYS = 21.0
WATCH_STAGE_AGE_DAYS = 14.0
OVERDUE_FLASH_TO_BANG_DAYS = 90.0
BOARD_ESCALATION_CLASSIFICATIONS = {"execution_failure", "leadership_or_training_issue"}


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join([prefix] + [str(part or "") for part in parts])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def _status_for_scope(
    avg_flash_to_bang: float,
    avg_stage_age_days: float,
    stall_count: int,
    processing_bottleneck_count: int,
    funnel_gap_stage: Optional[str],
) -> str:
    if avg_flash_to_bang >= OVERDUE_FLASH_TO_BANG_DAYS or avg_stage_age_days >= STALL_STAGE_AGE_DAYS:
        return "overdue"
    if stall_count > 0 or processing_bottleneck_count > 0:
        return "stalled"
    if avg_stage_age_days >= WATCH_STAGE_AGE_DAYS or bool(funnel_gap_stage):
        return "watch"
    return "on_track"


def _processing_posture(item_count: int, stalled_count: int, overdue_count: int) -> str:
    if item_count <= 0:
        return "unknown"
    stalled_rate = stalled_count / float(item_count)
    overdue_rate = overdue_count / float(item_count)
    if overdue_rate >= 0.3 or stalled_rate >= 0.45:
        return "failing"
    if overdue_rate >= 0.15 or stalled_rate >= 0.2:
        return "watch"
    return "on_track"


def _constraint(constraint_type: str, description: str, severity: str, *parts: str) -> Dict:
    return {
        "constraint_id": _stable_id("PROC-CONST", constraint_type, *parts),
        "constraint_type": constraint_type,
        "description": description,
        "severity": severity,
    }


def summarize_flash_to_bang_processing_engine(
    db,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    actor_scope_type: Optional[str] = None,
    actor_scope_value: Optional[str] = None,
    top_n: int = 25,
    execution_signal: Optional[Dict] = None,
    funnel_signal: Optional[Dict] = None,
    accountability_signal: Optional[Dict] = None,
) -> Dict:
    st = scope_type or "USAREC"
    sv = scope_value or "USAREC"
    ast = actor_scope_type or st
    asv = actor_scope_value or sv

    try:
        execution_quality.enforce_scope(ast, asv, st, sv)
    except HTTPException:
        return {
            "status": "invalid",
            "flash_to_bang_processing_engine": {
                "summary": {
                    "total_leads": 0,
                    "total_processing_items": 0,
                    "authoritative_flash_to_bang_days": 0.0,
                    "stalled": 0,
                    "overdue": 0,
                    "processing_posture": "unknown",
                },
                "processing_items": [],
                "stalled_items": [],
                "overdue_items": [],
                "escalations": [],
                "processing_scorecard": {
                    "on_track_rate": 0.0,
                    "stalled_rate": 0.0,
                    "overdue_rate": 0.0,
                    "processing_bottleneck_rate": 0.0,
                },
                "data_sources": {
                    "execution_quality": "invalid_scope",
                    "funnel": "invalid_scope",
                    "accountability": "invalid_scope",
                },
                "processing_constraints": [
                    _constraint(
                        "invalid_scope",
                        "Requested scope is outside actor permissions.",
                        "high",
                        st,
                        sv,
                    )
                ],
            },
        }

    execution_signal = execution_signal or execution_quality.summarize_execution_quality(db, st, sv, ast, asv)
    funnel_signal = funnel_signal or funnel_engine.summarize_funnel_engine(db, st, sv, ast, asv, top_n=top_n)
    accountability_signal = accountability_signal or accountability_engine.classify_scope(db, st, sv)

    execution_payload = execution_signal.get("execution_quality") or {}
    execution_summary = execution_payload.get("summary") or {}
    station_rows = list(((execution_payload.get("by_scope") or {}).get("station") or []))
    root_causes = list(execution_payload.get("root_cause_breakdown") or [])
    funnel_payload = funnel_signal.get("funnel_engine") or {}
    funnel_summary = funnel_payload.get("summary") or {}
    funnel_gaps = list(funnel_payload.get("prioritized_funnel_gaps") or [])

    processing_constraints: List[Dict] = []

    if execution_signal.get("status") != "ok":
        processing_constraints.append(
            _constraint(
                execution_signal.get("status") or "no_active_dataset",
                "Execution quality dataset is unavailable for processing tracking.",
                "high",
                st,
                sv,
            )
        )
        return {
            "status": "no_data" if execution_signal.get("status") == "no_active_dataset" else (execution_signal.get("status") or "invalid"),
            "flash_to_bang_processing_engine": {
                "summary": {
                    "total_leads": 0,
                    "total_processing_items": 0,
                    "authoritative_flash_to_bang_days": 0.0,
                    "stalled": 0,
                    "overdue": 0,
                    "processing_posture": "unknown",
                },
                "processing_items": [],
                "stalled_items": [],
                "overdue_items": [],
                "escalations": [],
                "processing_scorecard": {
                    "on_track_rate": 0.0,
                    "stalled_rate": 0.0,
                    "overdue_rate": 0.0,
                    "processing_bottleneck_rate": 0.0,
                },
                "data_sources": {
                    "execution_quality": execution_signal.get("status") or "unknown",
                    "funnel": funnel_signal.get("status") or "unknown",
                    "accountability": "accountability_engine.classify_scope()",
                },
                "processing_constraints": processing_constraints,
            },
        }

    if funnel_signal.get("status") != "ok":
        processing_constraints.append(
            _constraint(
                "partial_data",
                "Funnel dataset is unavailable; processing engine is using execution quality outputs only.",
                "medium",
                st,
                sv,
            )
        )

    if not station_rows:
        processing_constraints.append(
            _constraint(
                "no_processing_items",
                "No station-level execution quality rows were available for processing tracking.",
                "medium",
                st,
                sv,
            )
        )
        return {
            "status": "no_data",
            "flash_to_bang_processing_engine": {
                "summary": {
                    "total_leads": 0,
                    "total_processing_items": 0,
                    "authoritative_flash_to_bang_days": float(execution_summary.get("avg_flash_to_bang") or 0.0),
                    "stalled": 0,
                    "overdue": 0,
                    "processing_posture": "unknown",
                },
                "processing_items": [],
                "stalled_items": [],
                "overdue_items": [],
                "escalations": [],
                "processing_scorecard": {
                    "on_track_rate": 0.0,
                    "stalled_rate": 0.0,
                    "overdue_rate": 0.0,
                    "processing_bottleneck_rate": 0.0,
                },
                "data_sources": {
                    "execution_quality": "execution_quality.summarize_execution_quality()",
                    "funnel": "funnel_engine.summarize_funnel_engine()" if funnel_signal.get("status") == "ok" else funnel_signal.get("status") or "unknown",
                    "accountability": "accountability_engine.classify_scope()",
                },
                "processing_constraints": processing_constraints,
            },
        }

    root_cause_by_name = {str(item.get("cause") or ""): int(item.get("count") or 0) for item in root_causes}

    processing_items: List[Dict] = []
    for row in sorted(station_rows, key=lambda item: str(item.get("station_rsid") or ""))[:top_n]:
        station_rsid = str(row.get("station_rsid") or "")
        matching_gap = None
        for gap in funnel_gaps:
            if str(gap.get("scope_type") or "") == "STN" and str(gap.get("scope_value") or "") == station_rsid:
                matching_gap = gap
                break

        avg_flash_to_bang = round(float(row.get("avg_flash_to_bang") or execution_summary.get("avg_flash_to_bang") or 0.0), 2)
        avg_stage_age_days = round(float(row.get("avg_stage_age_days") or 0.0), 2)
        stall_count = int(row.get("stall_count") or 0)
        processing_bottleneck_count = int(row.get("processing_bottleneck_count") or 0)
        lead_count = int(row.get("lead_count") or 0)

        bottleneck_category = "processing_problem" if root_cause_by_name.get("processing_problem") else "mixed"
        if root_cause_by_name.get("future_soldier_management_problem") and not processing_bottleneck_count:
            bottleneck_category = "future_soldier_management_problem"
        elif root_cause_by_name.get("engagement_problem") and processing_bottleneck_count == 0 and stall_count == 0:
            bottleneck_category = "engagement_problem"
        elif root_cause_by_name.get("prospecting_problem") and processing_bottleneck_count == 0 and stall_count == 0:
            bottleneck_category = "prospecting_problem"

        funnel_gap_stage = str((matching_gap or {}).get("stage") or "") or None
        status = _status_for_scope(
            avg_flash_to_bang=avg_flash_to_bang,
            avg_stage_age_days=avg_stage_age_days,
            stall_count=stall_count,
            processing_bottleneck_count=processing_bottleneck_count,
            funnel_gap_stage=funnel_gap_stage,
        )

        processing_items.append(
            {
                "processing_item_id": _stable_id("PROC", station_rsid, status),
                "station_rsid": station_rsid,
                "lead_count": lead_count,
                "authoritative_flash_to_bang_days": avg_flash_to_bang,
                "avg_stage_age_days": avg_stage_age_days,
                "stall_count": stall_count,
                "processing_bottleneck_count": processing_bottleneck_count,
                "status": status,
                "bottleneck_category": bottleneck_category,
                "funnel_gap_stage": funnel_gap_stage,
                "accountability_classification": accountability_signal.get("classification"),
                "recommended_next_action": accountability_signal.get("recommended_next_action"),
                "trace_id": _stable_id("TRACE", station_rsid, str(funnel_gap_stage or "none")),
            }
        )

    stalled_items = [item for item in processing_items if item.get("status") == "stalled"]
    overdue_items = [item for item in processing_items if item.get("status") == "overdue"]
    on_track_items = [item for item in processing_items if item.get("status") == "on_track"]

    escalations: List[Dict] = []
    accountability_classification = str(accountability_signal.get("classification") or "")
    for item in [*stalled_items, *overdue_items]:
        escalate_to = "TWG"
        if accountability_classification in BOARD_ESCALATION_CLASSIFICATIONS or int(item.get("processing_bottleneck_count") or 0) > 0:
            escalate_to = "BOARD"

        reason_parts = []
        if item.get("status") == "overdue":
            reason_parts.append("overdue_processing")
        if int(item.get("stall_count") or 0) > 0:
            reason_parts.append("stalled_pipeline")
        if int(item.get("processing_bottleneck_count") or 0) > 0:
            reason_parts.append("processing_bottleneck")
        if item.get("funnel_gap_stage"):
            reason_parts.append(str(item.get("funnel_gap_stage")))

        escalations.append(
            {
                "escalation_id": _stable_id("PROC-ESC", str(item.get("station_rsid") or ""), escalate_to),
                "processing_item_id": str(item.get("processing_item_id") or ""),
                "station_rsid": str(item.get("station_rsid") or ""),
                "escalate_to": escalate_to,
                "reason": ",".join(reason_parts) if reason_parts else "processing_risk",
                "recommended_action": accountability_signal.get("recommended_next_action") or "Review flash-to-bang delays and republish corrective action.",
                "trace_id": _stable_id("TRACE", "PROC-ESC", str(item.get("station_rsid") or "")),
            }
        )

    total_leads = sum(int(item.get("lead_count") or 0) for item in processing_items)
    processing_posture = _processing_posture(len(processing_items), len(stalled_items), len(overdue_items))
    bottleneck_items = [item for item in processing_items if int(item.get("processing_bottleneck_count") or 0) > 0]

    return {
        "status": "ok",
        "flash_to_bang_processing_engine": {
            "summary": {
                "total_leads": total_leads,
                "total_processing_items": len(processing_items),
                "authoritative_flash_to_bang_days": round(float(execution_summary.get("avg_flash_to_bang") or 0.0), 2),
                "stalled": len(stalled_items),
                "overdue": len(overdue_items),
                "processing_posture": processing_posture,
            },
            "processing_items": processing_items,
            "stalled_items": stalled_items,
            "overdue_items": overdue_items,
            "escalations": sorted(escalations, key=lambda item: (str(item.get("station_rsid") or ""), str(item.get("escalate_to") or ""))),
            "processing_scorecard": {
                "on_track_rate": round((len(on_track_items) / float(len(processing_items))) if processing_items else 0.0, 6),
                "stalled_rate": round((len(stalled_items) / float(len(processing_items))) if processing_items else 0.0, 6),
                "overdue_rate": round((len(overdue_items) / float(len(processing_items))) if processing_items else 0.0, 6),
                "processing_bottleneck_rate": round((len(bottleneck_items) / float(len(processing_items))) if processing_items else 0.0, 6),
            },
            "data_sources": {
                "execution_quality": "execution_quality.summarize_execution_quality()",
                "funnel": "funnel_engine.summarize_funnel_engine()" if funnel_signal.get("status") == "ok" else funnel_signal.get("status") or "unknown",
                "accountability": "accountability_engine.classify_scope()",
            },
            "processing_constraints": processing_constraints,
        },
    }