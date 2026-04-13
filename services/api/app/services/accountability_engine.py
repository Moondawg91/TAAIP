from typing import Dict, List

from services.api.app.services import execution_quality, loe_engine, market_qma, school_access
from services.api.app.services import targeting_expansion


def classify_scope(db, scope_type: str, scope_value: str) -> Dict:
    market = market_qma.summarize_market_qma(db, scope_type, scope_value, scope_type, scope_value, top_n=20)
    access = school_access.summarize_school_access(db, scope_type, scope_value, scope_type, scope_value, top_n=20)
    execq = execution_quality.summarize_execution_quality(db, scope_type, scope_value, scope_type, scope_value)
    loe = loe_engine.summarize_loes(db, scope_type, scope_value)

    rec = targeting_expansion.recommendations_for_scope(db, scope_type, scope_value, top_n=20)
    items = rec.get("recommendations") or []

    if not items:
        return {
            "scope_type": scope_type,
            "scope_value": scope_value,
            "classification": "insufficient_data",
            "confidence": "low",
            "reason_codes": ["no_targeting_rows_available"],
            "supporting_metrics": {},
        }

    burden_vals: List[float] = []
    effort_vals: List[float] = []
    production_vals: List[float] = []
    warning_vals: List[float] = []
    opportunity_vals: List[float] = []

    for i in items:
        if i.get("entity_type") != "zip":
            continue
        burden = float(i.get("burden_ratio") or 1.0)
        burden_pressure = max(0.0, min(1.0, (burden - 1.0) / 1.5))
        burden_vals.append(burden_pressure)
        effort_vals.append(float(i.get("effort_signal") or 0.0))
        production_vals.append(float(i.get("production_signal") or 0.0))
        warning_vals.append(float(i.get("warning_severity") or 0.0))
        opportunity_vals.append(float(i.get("market_potential_score") or 0.0) / 100.0)

    if not opportunity_vals:
        return {
            "scope_type": scope_type,
            "scope_value": scope_value,
            "classification": "insufficient_data",
            "confidence": "low",
            "reason_codes": ["insufficient_supporting_fields"],
            "supporting_metrics": {},
        }

    avg_burden = sum(burden_vals) / len(burden_vals) if burden_vals else 0.0
    avg_effort = sum(effort_vals) / len(effort_vals) if effort_vals else 0.0
    avg_production = sum(production_vals) / len(production_vals) if production_vals else 0.0
    avg_warning = sum(warning_vals) / len(warning_vals) if warning_vals else 0.0
    avg_opportunity = sum(opportunity_vals) / len(opportunity_vals) if opportunity_vals else 0.0

    market_summary = (market.get("market_qma", {}).get("summary", {}) or {})
    access_summary = (access.get("school_access", {}).get("summary", {}) or {})
    exec_summary = (execq.get("execution_quality", {}).get("summary", {}) or {})

    market_supports_mission = bool(market_summary.get("market_supports_mission")) if market.get("status") == "ok" else False
    access_penetration = float(access_summary.get("penetration_rate") or 0.0)
    stall_count = float(exec_summary.get("stall_count") or 0.0)
    processing_bottleneck_count = float(exec_summary.get("processing_bottleneck_count") or 0.0)
    loe_at_risk = int((loe.get("status_counts") or {}).get("at_risk") or 0)
    loe_not_met = int((loe.get("status_counts") or {}).get("not_met") or 0)

    reason_codes = []
    classification = "balanced"
    recommended_next_action = "Maintain current plan and monitor indicators"

    # Explicit rules (ordered by diagnostic priority).
    if avg_opportunity <= 0.35 and avg_burden >= 0.50 and not market_supports_mission:
        classification = "market_constrained"
        reason_codes.append("market_weak_burden_high")
        recommended_next_action = "Re-segment market and shift mission assumptions before reallocating effort"
    elif access_penetration < 0.50 and market_supports_mission:
        classification = "access_constrained"
        reason_codes.append("low_school_penetration_with_market_support")
        recommended_next_action = "Prioritize school and community access actions in top uncovered markets"
    elif avg_burden >= 0.60 and avg_effort <= 0.40:
        classification = "effort_misaligned"
        reason_codes.append("burden_high_effort_low")
        recommended_next_action = "Rebalance recruiter effort toward top prioritized ZIPs and channels"
    elif avg_opportunity >= 0.60 and avg_production <= 0.35 and (stall_count > 0 or processing_bottleneck_count > 0):
        classification = "execution_failure"
        reason_codes.append("strong_market_low_output_normal_burden")
        recommended_next_action = "Execute processing recovery plan and weekly flash-to-bang review"
    elif loe_not_met + loe_at_risk >= 3 and avg_effort >= 0.45 and avg_production <= 0.40:
        classification = "leadership_or_training_issue"
        reason_codes.append("loe_underperformance_with_sustained_effort")
        recommended_next_action = "Initiate leader coaching and focused LMS training tied to failing LOE metrics"
    elif avg_opportunity >= 0.45 and avg_production >= 0.45 and avg_effort >= 0.45 and avg_burden <= 0.55:
        classification = "balanced"
        reason_codes.append("healthy_market_effort_execution_balance")
        recommended_next_action = "Scale proven actions while preserving current LOE thresholds"
    else:
        classification = "insufficient_data"
        reason_codes.append("mixed_or_partial_signals")
        recommended_next_action = "Improve data completeness for access, execution, and production before major decisions"

    confidence_score = 0.35
    confidence_score += 0.15 if len(opportunity_vals) >= 5 else 0.0
    confidence_score += 0.15 if avg_warning > 0 or avg_effort > 0 or avg_production > 0 else 0.0
    confidence_score += 0.25 if classification != "insufficient_data" else 0.0
    confidence_score = min(1.0, confidence_score)

    if confidence_score >= 0.75:
        confidence = "high"
    elif confidence_score >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "scope_type": scope_type,
        "scope_value": scope_value,
        "classification": classification,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "supporting_metrics": {
            "avg_burden_pressure": round(avg_burden, 4),
            "avg_effort_signal": round(avg_effort, 4),
            "avg_warning_severity": round(avg_warning, 4),
            "avg_opportunity": round(avg_opportunity, 4),
            "avg_production_signal": round(avg_production, 4),
            "market_supports_mission": market_supports_mission,
            "school_penetration_rate": round(access_penetration, 4),
            "execution_stall_count": int(stall_count),
            "processing_bottleneck_count": int(processing_bottleneck_count),
            "loe_at_risk": loe_at_risk,
            "loe_not_met": loe_not_met,
            "sample_size": len(opportunity_vals),
        },
        "recommended_next_action": recommended_next_action,
    }
