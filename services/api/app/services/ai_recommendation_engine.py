from typing import Dict, List

from services.api.app.services import (
    accountability_engine,
    execution_quality,
    market_qma,
    school_access,
    targeting_expansion,
)


def generate_recommendation_bundle(db, scope_type: str, scope_value: str) -> Dict:
    market = market_qma.summarize_market_qma(db, scope_type, scope_value, scope_type, scope_value, top_n=10)
    access = school_access.summarize_school_access(db, scope_type, scope_value, scope_type, scope_value, top_n=10)
    execq = execution_quality.summarize_execution_quality(db, scope_type, scope_value, scope_type, scope_value)
    accountability = accountability_engine.classify_scope(db, scope_type, scope_value)
    targeting = targeting_expansion.recommendations_for_scope(db, scope_type, scope_value, top_n=10)

    classif = accountability.get("classification")
    reasons = list(accountability.get("reason_codes") or [])

    actions: List[Dict] = []
    if classif == "access_constrained":
        actions.append({
            "priority": 1,
            "action": "Rebuild school engagement plan for uncovered high-opportunity schools",
            "rationale": "School penetration and access gaps indicate market is present but not being accessed.",
        })
    if classif == "effort_misaligned":
        actions.append({
            "priority": 1,
            "action": "Shift recruiter effort to top market-supportive ZIPs with low execution output",
            "rationale": "Burden/effort mix is not aligned with opportunity and warning signals.",
        })
    if classif == "execution_failure":
        actions.append({
            "priority": 1,
            "action": "Run processing surge on stalled leads and monitor flash-to-bang weekly",
            "rationale": "Execution quality indicates stage aging and processing bottlenecks.",
        })
    if not actions:
        actions.append({
            "priority": 2,
            "action": "Maintain current plan and monitor top indicators",
            "rationale": "Current signals are balanced or insufficient for a major shift.",
        })

    return {
        "scope_type": scope_type,
        "scope_value": scope_value,
        "classification": classif,
        "reason_codes": reasons,
        "actions": actions,
        "evidence": {
            "market": market.get("market_qma", {}).get("summary", {}),
            "school_access": access.get("school_access", {}).get("summary", {}),
            "execution_quality": execq.get("execution_quality", {}).get("summary", {}),
            "targeting_top": (targeting.get("recommendations") or [])[:5],
        },
    }
