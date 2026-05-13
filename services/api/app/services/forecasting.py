from typing import Dict, Optional

from services.api.app.services import accountability_engine, execution_quality, market_qma, school_access, targeting_expansion


def project_scope(db, scope_type: str, scope_value: str, assumptions: Optional[Dict] = None) -> Dict:
    assumptions = assumptions or {}

    market = market_qma.summarize_market_qma(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=20,
    )
    access = school_access.summarize_school_access(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=20,
    )
    execq = execution_quality.summarize_execution_quality(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
    )
    acc = accountability_engine.classify_scope(db, scope_type, scope_value)
    tgt = targeting_expansion.recommendations_for_scope(db, scope_type, scope_value, top_n=20)

    market_score = float((market.get("market_qma", {}).get("summary", {}) or {}).get("market_capability_score") or 0.0)
    access_pen = float((access.get("school_access", {}).get("summary", {}) or {}).get("penetration_rate") or 0.0)
    stall_cnt = float((execq.get("execution_quality", {}).get("summary", {}) or {}).get("stall_count") or 0.0)
    rec_count = float(len(tgt.get("recommendations") or []))

    mission_delta = float(assumptions.get("mission_delta", 0.0) or 0.0)
    effort_shift = float(assumptions.get("effort_shift", 0.0) or 0.0)
    access_delta = float(assumptions.get("access_delta", 0.0) or 0.0)
    burden_delta = float(assumptions.get("burden_delta", 0.0) or 0.0)

    projected_feasibility = max(0.0, min(1.0, 0.45 * (market_score / 100.0) + 0.30 * min(1.0, access_pen + access_delta) + 0.20 * max(0.0, 1.0 - stall_cnt / max(1.0, rec_count)) + 0.05 * max(0.0, 1.0 - burden_delta)))

    projected_burden = max(0.0, min(2.5, 1.0 + mission_delta - effort_shift + burden_delta))
    projected_contracts_mid = round(rec_count * projected_feasibility * 0.35, 2)
    projected_contracts_low = round(projected_contracts_mid * 0.8, 2)
    projected_contracts_high = round(projected_contracts_mid * 1.2, 2)

    loe_impact = "neutral"
    if projected_feasibility >= 0.62:
        loe_impact = "improving"
    elif projected_feasibility <= 0.45:
        loe_impact = "degrading"

    return {
        "scope_type": scope_type,
        "scope_value": scope_value,
        "baseline_classification": acc.get("classification"),
        "projected_feasibility": round(projected_feasibility, 4),
        "projected_burden": round(projected_burden, 4),
        "projected_production_range": {
            "low": projected_contracts_low,
            "mid": projected_contracts_mid,
            "high": projected_contracts_high,
        },
        "projected_loe_impact": loe_impact,
        "assumptions": assumptions,
    }
