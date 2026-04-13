from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from starlette.exceptions import HTTPException

from services.api.app.services import (
    market_engine,
    funnel_engine,
    targeting_engine,
    school_plan_engine,
    roi_engine,
    twg_engine,
)

# Board priority score weights
WEIGHT_TWG_PRIORITY = 0.40
WEIGHT_MISSION_IMPACT = 0.20
WEIGHT_ROI_IMPACT = 0.15
WEIGHT_TARGETING_ALIGNMENT = 0.15
WEIGHT_RESOURCE_PRESSURE = 0.10

# Board decision thresholds
HIGH_PRIORITY_THRESHOLD = 70.0
MEDIUM_PRIORITY_THRESHOLD = 40.0

# Decision rules
APPROVE_THRESHOLD = 65.0
MODIFY_THRESHOLD = 35.0
REJECT_THRESHOLD = 0.0

# Resource shift triggers
SHIFT_HIGH_PRIORITY = 75.0
SHIFT_TARGETING_GAP = 60.0
SHIFT_ROI_CONCERN = 45.0


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip().upper()
    if st == "USAREC":
        return ""
    if st == "BDE":
        return sv[:1]
    if st == "BN":
        return sv[:2]
    if st == "CO":
        return sv[:3]
    if st == "STN":
        return sv[:4]
    return sv


def enforce_scope(
    actor_scope_type: str,
    actor_scope_value: str,
    request_scope_type: str,
    request_scope_value: str,
) -> None:
    a_type = (actor_scope_type or "USAREC").upper().strip()
    r_type = (request_scope_type or "USAREC").upper().strip()
    a_val = (actor_scope_value or "USAREC").strip().upper()
    r_val = (request_scope_value or "USAREC").strip().upper()

    if a_type == "USAREC":
        return
    if r_type == "USAREC":
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")

    a_prefix = _scope_prefix(a_type, a_val)
    r_prefix = _scope_prefix(r_type, r_val)
    if a_prefix and not r_prefix.startswith(a_prefix):
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")


def _clamp100(v: Optional[float]) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
    except Exception:
        return 0.0
    if f < 0:
        return 0.0
    if f > 100:
        return 100.0
    return f


def _clamp_ratio(v: Optional[float]) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
    except Exception:
        return 0.0
    if f < 0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def _mission_impact(twg_item: Dict) -> float:
    """
    Evaluate mission impact of a TWG item.
    Higher if item addresses mission feasibility risk.
    Inferred from TWG category and priority signals.
    """
    category = str(twg_item.get("category") or "").lower()
    priority_score = float(twg_item.get("priority_score") or 0.0)
    
    # Mission-direct items have highest mission impact
    if category == "mission":
        return 80.0
    
    # Market and funnel directly affect mission via pipeline
    if category in ["market", "funnel"] and priority_score >= 70:
        return 70.0
    
    # ROI items with low-ROI addressing help mission by removing drag
    if category == "roi" and priority_score >= 70:
        return 65.0
    
    # Targeting and school items help but less direct mission impact
    if category in ["targeting", "school"] and priority_score >= 70:
        return 55.0
    
    return 40.0


def _roi_impact(twg_item: Dict, roi_signal: Optional[Dict]) -> float:
    """
    Evaluate ROI impact of addressing this TWG item.
    """
    if not roi_signal or roi_signal.get("status") == "no_data":
        return 0.0
    
    category = str(twg_item.get("category") or "")
    priority_score = float(twg_item.get("priority_score") or 0.0)
    
    # Low-ROI addressing items have direct ROI impact
    if category == "roi":
        return 70.0
    
    # High-priority funnel/targeting items improve overall ROI
    if category in ["funnel", "targeting"] and priority_score >= 70:
        return 60.0
    
    # Medium priority items have moderate ROI benefit
    if priority_score >= 40:
        return 40.0
    
    return 20.0


def _targeting_alignment(twg_item: Dict, targeting_signal: Optional[Dict]) -> float:
    """
    Evaluate targeting alignment of this TWG item.
    """
    if not targeting_signal or targeting_signal.get("status") == "no_data":
        return 0.0
    
    category = str(twg_item.get("category") or "")
    
    # Direct targeting items well-aligned
    if category == "targeting":
        return 75.0
    
    # Funnel and school items improve targeting effectiveness  
    if category in ["funnel", "school"]:
        return 60.0
    
    # Market items provide context for targeting
    if category == "market":
        return 50.0
    
    return 30.0


def _resource_pressure(twg_signal: Optional[Dict]) -> float:
    """
    Calculate resource pressure based on TWG item volume and priority concentration.
    Higher = more resource-constrained (less available for discretionary items).
    """
    if not twg_signal or twg_signal.get("status") == "no_data":
        return 0.0
    
    summary = twg_signal.get("summary") or {}
    total_items = int(summary.get("total_items") or 0)
    high_priority_count = int(summary.get("high_priority_count") or 0)
    
    # Resource pressure = concentration of high-priority items (0..1) scaled to 0..100
    if total_items == 0:
        return 0.0
    
    concentration = float(high_priority_count) / float(total_items)
    return concentration * 100.0


def _board_priority_score(
    twg_priority: float,
    mission_impact: float,
    roi_impact: float,
    targeting_alignment: float,
    resource_pressure: float,
) -> float:
    """
    Calculate board priority score from multi-engine inputs.
    """
    return round(
        WEIGHT_TWG_PRIORITY * _clamp100(twg_priority)
        + WEIGHT_MISSION_IMPACT * _clamp100(mission_impact)
        + WEIGHT_ROI_IMPACT * _clamp100(roi_impact)
        + WEIGHT_TARGETING_ALIGNMENT * _clamp100(targeting_alignment)
        + WEIGHT_RESOURCE_PRESSURE * _clamp100(resource_pressure),
        4,
    )


def _priority_band(score: float) -> str:
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "high"
    if score >= MEDIUM_PRIORITY_THRESHOLD:
        return "medium"
    return "low"


def _impact_level(score: float) -> str:
    if score >= 75.0:
        return "high"
    if score >= 50.0:
        return "medium"
    return "low"


def _decision_type(board_priority_score: float, twg_item: Dict) -> str:
    """
    Determine approval decision based on board priority score and item characteristics.
    """
    if board_priority_score >= APPROVE_THRESHOLD:
        return "approve"
    elif board_priority_score >= MODIFY_THRESHOLD:
        return "modify"
    else:
        return "reject"


def _decision_rationale(
    twg_item: Dict,
    board_priority_score: float,
    decision_type: str,
    mission_impact: float,
    roi_impact: float,
    targeting_alignment: float,
) -> str:
    """
    Generate human-readable rationale for board decision.
    """
    category = str(twg_item.get("category") or "").upper()
    priority_band = _priority_band(board_priority_score)
    
    base = f"{category} item ({priority_band} board priority: {board_priority_score:.1f})"
    
    if decision_type == "approve":
        impacts = []
        if mission_impact >= 50:
            impacts.append("critical mission impact")
        if roi_impact >= 50:
            impacts.append("significant ROI benefit")
        if targeting_alignment >= 50:
            impacts.append("strong targeting alignment")
        
        if impacts:
            return f"Approve: {base}. {', '.join(impacts).capitalize()}."
        return f"Approve: {base}. Multi-signal priority supports action."
    
    elif decision_type == "modify":
        constraints = []
        if mission_impact < 50:
            constraints.append("moderate mission impact")
        if roi_impact < 50:
            constraints.append("limited ROI benefit")
        
        if constraints:
            return f"Modify scope/timeline: {base}. {', '.join(constraints).capitalize()}."
        return f"Modify: {base}. Requires scope adjustment for resource efficiency."
    
    else:
        return f"Reject: {base}. Insufficient cross-engine impact justifies action."


def _owner_level_for_decision(
    twg_item: Dict,
    decision_type: str,
    board_priority_score: float,
) -> str:
    """
    Determine command-level owner for board decision execution.
    """
    twg_owner = str(twg_item.get("owner_level") or "CO").upper()
    
    # Enforce board escalation for approve decisions
    if decision_type == "approve":
        if board_priority_score >= 85:
            return "BN"  # Battalion level for critical items
        if board_priority_score >= 75:
            return "CO" if twg_owner != "BN" else "BN"
        return twg_owner
    
    # Modify decisions stay at TWG owner level
    return twg_owner


def _due_out_for_decision(
    decision_type: str,
    board_priority_score: float,
) -> str:
    """
    Assign due-out timeline based on decision type and priority.
    """
    if decision_type == "reject":
        return "(no action)"
    
    days_out = 7
    if board_priority_score >= 80:
        days_out = 3
    elif board_priority_score >= 70:
        days_out = 5
    elif board_priority_score >= 50:
        days_out = 10
    elif board_priority_score >= 40:
        days_out = 14
    else:
        days_out = 21
    
    due_date = datetime.utcnow() + timedelta(days=days_out)
    return due_date.date().isoformat()


def _expected_effect(
    decision_type: str,
    twg_item: Dict,
    mission_impact: float,
    roi_impact: float,
) -> str:
    """
    Describe expected operational effect of board decision.
    """
    category = str(twg_item.get("category") or "").upper()
    
    if decision_type == "reject":
        return "No operational change; item does not warrant resource allocation."
    
    effects = []
    
    if mission_impact >= 60:
        effects.append("improve mission feasibility")
    
    if roi_impact >= 60:
        effects.append("increase event ROI")
    
    if category == "funnel":
        effects.append("improve funnel progression")
    elif category == "targeting":
        effects.append("strengthen ZIP targeting")
    elif category == "school":
        effects.append("enhance school engagement")
    elif category == "market":
        effects.append("strengthen market footprint")
    
    if effects:
        return "Expect to " + ", ".join(effects) + "."
    
    return "Expect incremental operational improvement."


def _resource_shift_generated(
    board_item: Dict,
    decision_type: str,
    board_priority_score: float,
) -> List[Dict]:
    """
    Generate resource shift directives for approved decisions requiring shifts.
    """
    shifts = []
    
    # Only approved items with high priority generate mandatory shifts
    if decision_type != "approve" or board_priority_score < SHIFT_HIGH_PRIORITY:
        return shifts
    
    category = str(board_item.get("category") or "").upper()
    
    # Funnel dropoff addressing requires recruiter reallocation
    if category == "FUNNEL":
        shifts.append({
            "shift_type": "effort",
            "from": "retention_optimization",
            "to": "funnel_acceleration",
            "justification": "Address critical funnel gaps identified in TWG review.",
            "expected_effect": "Improve lead-to-accession conversion.",
        })
    
    # Targeting gaps require resource concentration
    elif category == "TARGETING":
        shifts.append({
            "shift_type": "targeting",
            "from": "low_opportunity_zips",
            "to": "high_opportunity_zips",
            "justification": "Concentrate effort on high-opportunity ZIPs per board directive.",
            "expected_effect": "Maximize targeting efficiency and school reach.",
        })
    
    # ROI issues require event reallocation
    elif category == "ROI":
        shifts.append({
            "shift_type": "event",
            "from": "low_value_events",
            "to": "high_roi_events",
            "justification": "Redirect event effort from low-ROI to high-ROI activities.",
            "expected_effect": "Improve accession-per-event ratio.",
        })
    
    # School gaps require school-level effort shift
    elif category == "SCHOOL":
        shifts.append({
            "shift_type": "school",
            "from": "low_engagement_schools",
            "to": "high_opportunity_schools",
            "justification": "Intensify engagement at high-opportunity schools.",
            "expected_effect": "Increase school-level participation rates.",
        })
    
    return shifts


def _downstream_task_for_decision(
    board_item: Dict,
    board_decision: Dict,
    shifts: List[Dict],
) -> Optional[Dict]:
    """
    Generate TWG-executable task for board decision.
    Each decision creates exactly one downstream task for execution tracking.
    """
    decision_type = str(board_decision.get("decision_type") or "")
    decision_id = str(board_decision.get("decision_id") or "")
    
    if decision_type == "reject":
        return None  # Rejected items don't create tasks
    
    task_id = f"TASK-{uuid4().hex[:12].upper()}"
    source_twg_id = str(board_item.get("source_twg_item_id") or "")
    owner_level = str(board_decision.get("owner_level") or "CO")
    due_out = str(board_decision.get("due_out") or "")
    category = str(board_item.get("category") or "").upper()
    
    # Determine action based on decision type and shifts
    if decision_type == "approve":
        if shifts:
            action = f"Execute {category} shift: {shifts[0].get('justification', 'per board directive')}"
        else:
            action = f"Implement approved {category} action per board guidance."
    else:  # modify
        action = f"Develop modified {category} approach per board guidance and resource constraints."
    
    return {
        "task_id": task_id,
        "source_board_decision_id": decision_id,
        "owner_level": owner_level,
        "action": action,
        "due_out": due_out,
        "expected_effect": str(board_decision.get("expected_effect") or ""),
        "trace_id": f"TASK-{uuid4().hex[:12].upper()}",
    }


def _overall_board_posture(approved: int, modified: int, rejected: int, total: int) -> str:
    """
    Determine overall board posture based on decision distribution.
    """
    if total == 0:
        return "unknown"
    
    approval_rate = float(approved) / float(total)
    
    if approval_rate >= 0.65:
        return "aggressive"
    elif approval_rate >= 0.40:
        return "balanced"
    else:
        return "constrained"


def summarize_targeting_board_engine(
    db,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    actor_scope_type: Optional[str] = None,
    actor_scope_value: Optional[str] = None,
    top_n: int = 20,
) -> Dict:
    """
    Authoritative Targeting Board decision-output engine.
    
    Consumes TWG board_candidates and produces board decisions, resource shifts,
    and downstream execution tasks.
    
    Board evaluates each candidate against:
    - Mission impact
    - ROI impact
    - Targeting alignment
    - Resource pressure
    
    Produces:
    - approve / modify / reject decisions
    - resource shift directives
    - downstream TWG execution tasks
    """
    
    # Enforce scope
    enforce_scope(
        actor_scope_type,
        actor_scope_value,
        scope_type,
        scope_value,
    )
    
    # Collect upstream signals
    twg_signal = twg_engine.summarize_twg_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=top_n
    )
    
    roi_signal = roi_engine.summarize_roi_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=30
    )
    
    targeting_signal = targeting_engine.summarize_targeting_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=30
    )
    
    # No board candidates = no_data
    if twg_signal.get("status") != "ok":
        return {
            "status": "no_data",
            "targeting_board_engine": {
                "summary": {
                    "total_items": 0,
                    "approved_count": 0,
                    "modified_count": 0,
                    "rejected_count": 0,
                    "resource_shift_count": 0,
                    "overall_board_posture": "unknown",
                },
                "prioritized_board_items": [],
                "board_decisions": [],
                "directed_shifts": [],
                "downstream_twg_tasks": [],
                "data_sources": {
                    "twg": "twg_engine.summarize_twg_engine()",
                    "roi": roi_signal.get("status"),
                    "targeting": targeting_signal.get("status"),
                },
            },
        }
    
    board_candidates = twg_signal.get("twg_engine", {}).get("board_candidates") or []
    
    if not board_candidates:
        return {
            "status": "no_data",
            "targeting_board_engine": {
                "summary": {
                    "total_items": 0,
                    "approved_count": 0,
                    "modified_count": 0,
                    "rejected_count": 0,
                    "resource_shift_count": 0,
                    "overall_board_posture": "unknown",
                },
                "prioritized_board_items": [],
                "board_decisions": [],
                "directed_shifts": [],
                "downstream_twg_tasks": [],
                "data_sources": {
                    "twg": "ok (no board candidates)",
                    "roi": roi_signal.get("status"),
                    "targeting": targeting_signal.get("status"),
                },
            },
        }
    
    # Evaluate each board candidate
    board_items = []
    approved_count = 0
    modified_count = 0
    rejected_count = 0
    all_shifts = []
    all_tasks = []
    
    for idx, twg_item in enumerate(board_candidates[:top_n]):
        # Calculate impacts
        m_impact = _mission_impact(twg_item)
        r_impact = _roi_impact(twg_item, roi_signal)
        t_align = _targeting_alignment(twg_item, targeting_signal)
        resource_p = _resource_pressure(twg_signal.get("twg_engine"))
        
        # Board priority score
        twg_priority = float(twg_item.get("priority_score") or 0.0)
        board_priority = _board_priority_score(twg_priority, m_impact, r_impact, t_align, resource_p)
        
        # Decision
        decision_type = _decision_type(board_priority, twg_item)
        rationale = _decision_rationale(twg_item, board_priority, decision_type, m_impact, r_impact, t_align)
        owner_level = _owner_level_for_decision(twg_item, decision_type, board_priority)
        due_out = _due_out_for_decision(decision_type, board_priority)
        expected_effect = _expected_effect(decision_type, twg_item, m_impact, r_impact)
        
        # Count decisions
        if decision_type == "approve":
            approved_count += 1
        elif decision_type == "modify":
            modified_count += 1
        else:
            rejected_count += 1
        
        # Build board item
        board_item_id = f"BI-{uuid4().hex[:12].upper()}"
        board_trace_id = f"BD-{uuid4().hex[:12].upper()}"
        
        board_item = {
            "board_item_id": board_item_id,
            "source_twg_item_id": str(twg_item.get("item_id") or ""),
            "category": str(twg_item.get("category") or ""),
            "decision_type": decision_type,
            "decision_rationale": rationale,
            "priority_score": board_priority,
            "impact_level": _impact_level(board_priority),
            "resource_implication": decision_type == "approve" and board_priority >= SHIFT_HIGH_PRIORITY,
            "trace_id": board_trace_id,
        }
        board_items.append(board_item)
        
        # Build decision record
        decision_id = f"DEC-{uuid4().hex[:12].upper()}"
        board_decision = {
            "decision_id": decision_id,
            "action": str(twg_item.get("recommended_action") or ""),
            "decision_type": decision_type,
            "owner_level": owner_level,
            "expected_effect": expected_effect,
            "time_horizon": due_out,
            "rationale": rationale,
            "trace_id": board_trace_id,
        }
        
        # Generate shifts if approved with high priority
        shifts = _resource_shift_generated(board_item, decision_type, board_priority)
        for shift in shifts:
            shift["trace_id"] = f"SFT-{uuid4().hex[:12].upper()}"
            all_shifts.append(shift)
        
        # Generate downstream task
        task = _downstream_task_for_decision(board_item, board_decision, shifts)
        if task:
            all_tasks.append(task)
    
    # Build data sources
    data_sources = {
        "twg": "twg_engine.summarize_twg_engine()",
        "market": "market_engine.summarize_market_engine()",
        "funnel": "funnel_engine.summarize_funnel_engine()",
        "targeting": "targeting_engine.summarize_targeting_engine()",
        "school_plan": "school_plan_engine.summarize_school_plan_engine()",
        "roi": "roi_engine.summarize_roi_engine()",
        "mission_adjustment": "mission_decrease_justification.summarize_mission_decrease_justification()",
    }
    
    return {
        "status": "ok",
        "targeting_board_engine": {
            "summary": {
                "total_items": len(board_items),
                "approved_count": approved_count,
                "modified_count": modified_count,
                "rejected_count": rejected_count,
                "resource_shift_count": len(all_shifts),
                "overall_board_posture": _overall_board_posture(
                    approved_count, modified_count, rejected_count, len(board_items)
                ),
            },
            "prioritized_board_items": board_items,
            "board_decisions": [
                {
                    "decision_id": str(board_items[idx].get("board_item_id", "")).replace("BI-", "DEC-"),
                    "action": str(board_candidates[idx].get("recommended_action") or ""),
                    "decision_type": str(board_items[idx].get("decision_type") or ""),
                    "owner_level": str(board_items[idx].get("trace_id", ""))[:2]
                    or "CO",
                    "expected_effect": str(board_items[idx].get("resource_implication") or ""),
                    "time_horizon": "(pending)",
                    "rationale": str(board_items[idx].get("decision_rationale") or ""),
                    "trace_id": str(board_items[idx].get("trace_id") or ""),
                }
                for idx in range(len(board_items))
            ],
            "directed_shifts": all_shifts,
            "downstream_twg_tasks": all_tasks,
            "data_sources": data_sources,
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }
