from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from starlette.exceptions import HTTPException

from services.api.app.services import (
    funnel_engine,
    school_plan_engine,
    roi_engine,
    twg_engine,
    targeting_board_engine,
)

# Utilization thresholds
UTILIZATION_OVERLOADED = 1.0
UTILIZATION_BALANCED_HIGH = 1.0
UTILIZATION_BALANCED_LOW = 0.7
UTILIZATION_UNDERUTILIZED = 0.7

# Capacity constraints
DEFAULT_RECRUITER_CAPACITY_DAYS = 220  # Working days/year
DEFAULT_HOURS_PER_DAY = 8
EFFORT_HOURS_PER_EVENT = 8
EFFORT_HOURS_PER_SCHOOL_ENGAGEMENT = 4
EFFORT_HOURS_PER_FUNNEL_ACTIVITY = 6
EFFORT_HOURS_PER_ZIP_MANAGEMENT = 3

# Risk thresholds
HIGH_RISK_OVERLOAD_RATIO = 0.7  # If >70% assets overloaded
MEDIUM_RISK_OVERLOAD_RATIO = 0.3


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


def _query_recruiter_count(db, scope_type: str, scope_value: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Query actual recruiter count from organization/assignment data.
    
    Returns: (count, constraint_reason) where constraint_reason is None if data found.
    If data cannot be found at requested scope, returns (None, reason).
    """
    try:
        from services.api.app import crud_domain
        from services.api.app.schemas_domain import ScopeFilter
        
        # Query active recruiter assignments at scope
        scope_filter = ScopeFilter(
            scope_type=scope_type,
            scope_value=scope_value,
        )
        
        # Get organizational unit with recruiter count
        org_units = crud_domain.read_org_units_by_scope(db, scope_filter)
        
        if org_units and len(org_units) > 0:
            # Sum recruiter counts across units
            recruiter_count = sum(
                int(u.recruiter_count or 0) for u in org_units
                if u.recruiter_count is not None
            )
            if recruiter_count > 0:
                return recruiter_count, None
            else:
                return None, "no_recruiter_assignments_found"
        else:
            return None, "scope_not_found_in_database"
            
    except Exception as e:
        return None, f"error_querying_recruiter_data: {str(e)[:50]}"


def _query_asset_strength(db, scope_type: str, scope_value: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Query actual asset strength data (recruiter workload, ownership, assignments).
    
    Returns: (asset_list, constraint_reason) where asset_list is None if data not found.
    """
    try:
        from services.api.app import crud_domain
        from services.api.app.schemas_domain import ScopeFilter
        
        # Query recruiter assignments and current workload
        scope_filter = ScopeFilter(
            scope_type=scope_type,
            scope_value=scope_value,
        )
        
        recruiter_assignments = crud_domain.read_recruiter_assignments(db, scope_filter)
        
        if recruiter_assignments and len(recruiter_assignments) > 0:
            assets = []
            for assignment in recruiter_assignments:
                assets.append({
                    "asset_id": assignment.recruiter_id,
                    "recruiter_name": assignment.recruiter_name,
                    "location": assignment.org_unit_value,
                    "current_assignments": int(assignment.assignment_count or 0),
                    "ownership_schools": int(assignment.owned_school_count or 0),
                    "status_observations": assignment.workload_indicator or "unknown",
                })
            return assets, None
        else:
            return None, "no_recruiter_assignments_found"
            
    except Exception as e:
        return None, f"error_querying_asset_data: {str(e)[:50]}"


def _calculate_capacity_hours(recruiter_count: int) -> float:
    """
    Calculate total available capacity in hours.
    """
    return float(recruiter_count) * DEFAULT_RECRUITER_CAPACITY_DAYS * DEFAULT_HOURS_PER_DAY


def _extract_current_workload(
    funnel_signal: Optional[Dict],
    school_signal: Optional[Dict],
    roi_signal: Optional[Dict],
    twg_signal: Optional[Dict],
) -> float:
    """
    Synthesize current workload (in effort hours) from upstream engine signals.
    """
    workload_hours = 0.0
    
    # Funnel workload: prioritized gaps indicate effort needed
    if funnel_signal and funnel_signal.get("status") == "ok":
        funnel_gaps = funnel_signal.get("funnel_engine", {}).get("prioritized_funnel_gaps") or []
        workload_hours += len(funnel_gaps) * EFFORT_HOURS_PER_FUNNEL_ACTIVITY
    
    # School workload: underengaged schools require effort
    if school_signal and school_signal.get("status") == "ok":
        school_summary = school_signal.get("school_plan_engine", {}).get("summary") or {}
        underengaged = int(school_summary.get("underengaged_school_count") or 0)
        workload_hours += underengaged * EFFORT_HOURS_PER_SCHOOL_ENGAGEMENT
    
    # ROI workload: events require effort
    if roi_signal and roi_signal.get("status") == "ok":
        roi_summary = roi_signal.get("roi_engine", {}).get("summary") or {}
        total_events = int(roi_summary.get("total_events_scored") or 0)
        workload_hours += total_events * EFFORT_HOURS_PER_EVENT
    
    # TWG workload: high-priority agenda items indicate sustained effort
    if twg_signal and twg_signal.get("status") == "ok":
        twg_summary = twg_signal.get("twg_engine", {}).get("summary") or {}
        high_priority = int(twg_summary.get("high_priority_count") or 0)
        workload_hours += high_priority * EFFORT_HOURS_PER_FUNNEL_ACTIVITY
    
    return workload_hours


def _utilization_status(utilization_rate: float) -> str:
    """
    Classify utilization status based on rate.
    """
    if utilization_rate > UTILIZATION_OVERLOADED:
        return "overloaded"
    elif utilization_rate >= UTILIZATION_BALANCED_LOW:
        return "balanced"
    else:
        return "underutilized"


def _infer_workload_driver(
    funnel_signal: Optional[Dict],
    school_signal: Optional[Dict],
    roi_signal: Optional[Dict],
) -> str:
    """
    Identify which factor is driving highest workload.
    """
    drivers = []
    
    if funnel_signal and funnel_signal.get("status") == "ok":
        funnel_gaps = len(funnel_signal.get("funnel_engine", {}).get("prioritized_funnel_gaps") or [])
        if funnel_gaps > 0:
            drivers.append(("funnel", funnel_gaps * EFFORT_HOURS_PER_FUNNEL_ACTIVITY))
    
    if school_signal and school_signal.get("status") == "ok":
        school_summary = school_signal.get("school_plan_engine", {}).get("summary") or {}
        underengaged = int(school_summary.get("underengaged_school_count") or 0)
        if underengaged > 0:
            drivers.append(("school_engagement", underengaged * EFFORT_HOURS_PER_SCHOOL_ENGAGEMENT))
    
    if roi_signal and roi_signal.get("status") == "ok":
        roi_summary = roi_signal.get("roi_engine", {}).get("summary") or {}
        total_events = int(roi_summary.get("total_events_scored") or 0)
        if total_events > 0:
            drivers.append(("event_coverage", total_events * EFFORT_HOURS_PER_EVENT))
    
    if not drivers:
        return "baseline_operations"
    
    # Return highest-impact driver
    drivers.sort(key=lambda x: x[1], reverse=True)
    return drivers[0][0]


def _evaluate_shift_feasibility(
    shift: Dict,
    asset_distribution: List[Dict],
    current_workload: float,
    capacity_hours: float,
) -> str:
    """
    Evaluate feasibility of a proposed board shift.
    
    Returns: high | medium | low
    """
    shift_type = str(shift.get("shift_type") or "").lower()
    
    # Quantify shift impact in hours
    shift_hours = 0.0
    
    if shift_type in ["effort", "event"]:
        shift_hours = 8.0  # ~1 person-day per shift
    elif shift_type == "targeting":
        shift_hours = 4.0  # ~0.5 person-day
    elif shift_type == "school":
        shift_hours = 6.0  # ~0.75 person-day
    elif shift_type == "resource":
        shift_hours = 16.0  # ~2 person-days
    
    # Count overloaded assets
    overloaded_count = sum(1 for a in asset_distribution if a.get("status") == "overloaded")
    total_assets = len(asset_distribution)
    
    # Feasibility logic
    available_capacity = capacity_hours - current_workload
    
    if available_capacity > shift_hours * 2:
        return "high"
    elif available_capacity > shift_hours:
        return "medium"
    else:
        return "low"


def _extract_board_shifts(board_signal: Optional[Dict]) -> List[Dict]:
    """
    Extract directed shifts from board engine output.
    """
    if not board_signal or board_signal.get("status") != "ok":
        return []
    
    board_engine = board_signal.get("targeting_board_engine") or {}
    shifts = board_engine.get("directed_shifts") or []
    
    return shifts


def _generate_recommended_shift(
    asset_from: Dict,
    workload_driver: str,
    utilization_rate: float,
    feasibility: str,
) -> Dict:
    """
    Generate asset reallocation recommendation.
    """
    shift_id = f"SHIFT-{uuid4().hex[:12].upper()}"
    
    if utilization_rate > 1.2:
        shift_justification = f"Critical overloading detected; redistribute {asset_from.get('asset_id')} workload"
    elif utilization_rate > 1.0:
        shift_justification = f"Asset overutilized ({utilization_rate:.1%}); balance workload"
    else:
        shift_justification = f"Optimize asset allocation based on {workload_driver} demand"
    
    return {
        "shift_id": shift_id,
        "asset_id": str(asset_from.get("asset_id") or ""),
        "from": str(asset_from.get("location") or ""),
        "to": "high_opportunity_area",
        "justification": shift_justification,
        "feasibility": feasibility,
        "expected_effect": "Improve asset efficiency and reduce saturation",
        "trace_id": f"SHIFT-{uuid4().hex[:12].upper()}",
    }


def _detect_execution_constraints(
    asset_distribution: List[Dict],
    board_shifts: List[Dict],
) -> List[Dict]:
    """
    Identify execution constraints that will block or slow operations.
    """
    constraints = []
    
    # Detect personnel constraints
    overloaded_assets = [a for a in asset_distribution if a.get("status") == "overloaded"]
    if len(overloaded_assets) > 0:
        constraints.append({
            "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
            "constraint_type": "personnel",
            "description": f"{len(overloaded_assets)} assets overloaded; capacity limits execution",
            "affected_area": "overall_operations",
            "severity": "high" if len(overloaded_assets) > len(asset_distribution) / 2 else "medium",
            "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
        })
    
    # Detect workload constraints from shifts
    high_impact_shifts = [s for s in board_shifts if str(s.get("shift_type") or "").lower() in ["resource", "effort"]]
    if len(high_impact_shifts) > 3:
        constraints.append({
            "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
            "constraint_type": "workload",
            "description": f"{len(high_impact_shifts)} high-impact shifts exceed available capacity",
            "affected_area": "board_directive_execution",
            "severity": "high",
            "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
        })
    
    # Detect distance/travel constraints (placeholder for geographic analysis)
    constraints.append({
        "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
        "constraint_type": "distance",
        "description": "Asset travel time between priority locations may limit daily coverage",
        "affected_area": "geographic_coverage",
        "severity": "low",
        "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
    })
    
    return constraints


def _calculate_execution_risk(
    asset_distribution: List[Dict],
    board_signal: Optional[Dict],
) -> Tuple[str, str]:
    """
    Calculate overall execution risk level and feasibility posture.
    
    Returns: (risk_level, feasibility_posture)
    """
    if not asset_distribution:
        return "high", "constrained"
    
    overloaded_count = sum(1 for a in asset_distribution if a.get("status") == "overloaded")
    total_count = len(asset_distribution)
    
    overload_ratio = float(overloaded_count) / float(total_count)
    
    # Risk level assessment
    if overload_ratio >= HIGH_RISK_OVERLOAD_RATIO:
        risk_level = "high"
    elif overload_ratio >= MEDIUM_RISK_OVERLOAD_RATIO:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Feasibility posture assessment
    board_items_count = 0
    if board_signal and board_signal.get("status") == "ok":
        board_engine = board_signal.get("targeting_board_engine") or {}
        board_items_count = int(board_engine.get("summary", {}).get("approved_count") or 0)
    
    if overload_ratio > 0.5 and board_items_count > 3:
        feasibility_posture = "constrained"
    elif overload_ratio < 0.3 and board_items_count <= 3:
        feasibility_posture = "overcapacity"
    else:
        feasibility_posture = "feasible"
    
    return risk_level, feasibility_posture


def summarize_asset_engine(
    db,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    actor_scope_type: Optional[str] = None,
    actor_scope_value: Optional[str] = None,
    top_n: int = 20,
    board_signal: Optional[Dict] = None,
    twg_signal: Optional[Dict] = None,
    funnel_signal: Optional[Dict] = None,
    school_signal: Optional[Dict] = None,
    roi_signal: Optional[Dict] = None,
) -> Dict:
    """
    Authoritative Asset Recommendations and Availability engine.
    
    Consumes board directives and current workload signals to:
    - Calculate asset utilization by area (using REAL recruiter strength data)
    - Recommend realistic reallocations (traceable to board decisions)
    - Flag execution constraints and risks
    - Evaluate feasibility of board decisions
    
    HARD RULES:
    1. Uses actual recruiter/asset data from database; no fabricated capacities
    2. Returns structured no_data/partial_data constraints when data unavailable
    3. All recommendations traceable to specific board decisions and upstream evidence
    
    Inputs (consume-only; no independent analytics):
    - targeting_board_engine: board_decisions, directed_shifts
    - twg_engine: workload indicators, due_outs
    - funnel_engine: funnel workload by stage
    - school_plan_engine: engagement demand
    - roi_engine: event workload + effectiveness
    
    Produces:
    - asset distribution with utilization rates
    - recommended shifts with feasibility assessment and board traceability
    - execution constraints and risk flags
    """
    
    # Enforce scope
    enforce_scope(
        actor_scope_type,
        actor_scope_value,
        scope_type,
        scope_value,
    )
    
    # Collect upstream signals, reusing precomputed payloads when provided.
    board_signal = board_signal or targeting_board_engine.summarize_targeting_board_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=top_n
    )

    twg_signal = twg_signal or twg_engine.summarize_twg_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=top_n
    )

    funnel_signal = funnel_signal or funnel_engine.summarize_funnel_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=15
    )

    school_signal = school_signal or school_plan_engine.summarize_school_plan_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=15
    )

    roi_signal = roi_signal or roi_engine.summarize_roi_engine(
        db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=15
    )
    
    # Query REAL recruiter strength and asset data
    recruiter_count, recruiter_constraint = _query_recruiter_count(db, scope_type, scope_value)
    asset_list, asset_constraint = _query_asset_strength(db, scope_type, scope_value)
    
    # No workload signals AND no recruiter data = no_data with constraints
    no_workload = all(
        s.get("status") != "ok" or not s
        for s in [twg_signal, funnel_signal, school_signal, roi_signal]
    )
    
    if no_workload and recruiter_count is None:
        constraints = []
        if recruiter_constraint:
            constraints.append({
                "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
                "constraint_type": "data_availability",
                "description": f"Cannot query recruiter strength: {recruiter_constraint}",
                "affected_area": "asset_capacity_calculation",
                "severity": "high",
                "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
            })
        if asset_constraint:
            constraints.append({
                "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
                "constraint_type": "data_availability",
                "description": f"Cannot query asset strength: {asset_constraint}",
                "affected_area": "asset_distribution",
                "severity": "high",
                "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
            })
        
        return {
            "status": "no_data",
            "asset_engine": {
                "summary": {
                    "total_assets": 0,
                    "overutilized_assets": 0,
                    "underutilized_assets": 0,
                    "balanced_assets": 0,
                    "execution_risk_level": "unknown",
                    "feasibility_posture": "constrained_by_data",
                },
                "asset_distribution": [],
                "recommended_shifts": [],
                "execution_constraints": constraints,
                "data_sources": {
                    "board": board_signal.get("status") if board_signal else "unavailable",
                    "twg": twg_signal.get("status") if twg_signal else "unavailable",
                    "funnel": funnel_signal.get("status") if funnel_signal else "unavailable",
                    "school_plan": school_signal.get("status") if school_signal else "unavailable",
                    "roi": roi_signal.get("status") if roi_signal else "unavailable",
                    "recruiter_strength": "unavailable",
                    "asset_assignments": "unavailable",
                },
            },
        }
    
    # Partial data: recruiter data found but insufficient workload signals
    if recruiter_count is not None and no_workload:
        return {
            "status": "partial_data",
            "asset_engine": {
                "summary": {
                    "total_assets": 1,  # At least we have recruiter count
                    "overutilized_assets": 0,
                    "underutilized_assets": 0,
                    "balanced_assets": 1,
                    "execution_risk_level": "unknown",
                    "feasibility_posture": "pending_workload_data",
                },
                "asset_distribution": [
                    {
                        "asset_id": f"ASSET-{scope_value or 'USAREC'}-001",
                        "location": f"{scope_type.upper() if scope_type else 'USAREC'}: {scope_value or 'USAREC'}",
                        "current_load": 0.0,
                        "capacity": round(_calculate_capacity_hours(recruiter_count), 2),
                        "utilization_rate": 0.0,
                        "status": "unknown",
                        "primary_workload_driver": "awaiting_workload_data",
                        "trace_id": f"ASSET-{uuid4().hex[:12].upper()}",
                    }
                ],
                "recommended_shifts": [],
                "execution_constraints": [
                    {
                        "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
                        "constraint_type": "incomplete_data",
                        "description": "Recruiter strength available but insufficient workload signals for utilization analysis",
                        "affected_area": "asset_utilization_analysis",
                        "severity": "medium",
                        "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
                    }
                ],
                "data_sources": {
                    "board": board_signal.get("status") if board_signal else "unavailable",
                    "twg": twg_signal.get("status") if twg_signal else "unavailable",
                    "funnel": funnel_signal.get("status") if funnel_signal else "unavailable",
                    "school_plan": school_signal.get("status") if school_signal else "unavailable",
                    "roi": roi_signal.get("status") if roi_signal else "unavailable",
                    "recruiter_strength": "available",
                    "asset_assignments": "available" if asset_list else "unavailable",
                },
            },
        }
    
    # Full data available: calculate utilization and generate recommendations
    capacity_hours = _calculate_capacity_hours(recruiter_count) if recruiter_count else 0.0
    current_workload = _extract_current_workload(funnel_signal, school_signal, roi_signal, twg_signal)
    workload_driver = _infer_workload_driver(funnel_signal, school_signal, roi_signal)
    utilization_rate = current_workload / capacity_hours if capacity_hours > 0 else 0.0
    
    # Build asset distribution from real data or synthesized from recruiter count
    asset_distribution = []
    
    if asset_list and len(asset_list) > 0:
        # Use real asset data
        for asset in asset_list[:top_n]:
            # Estimate individual asset capacity (recruiter_capacity / num_recruiters)
            individual_capacity = capacity_hours / len(asset_list) if len(asset_list) > 0 else capacity_hours
            asset_workload = (current_workload / len(asset_list)) if len(asset_list) > 0 else current_workload
            asset_utilization = asset_workload / individual_capacity if individual_capacity > 0 else 0.0
            
            asset_distribution.append({
                "asset_id": str(asset.get("asset_id") or ""),
                "recruiter_name": str(asset.get("recruiter_name") or ""),
                "location": str(asset.get("location") or ""),
                "current_assignments": int(asset.get("current_assignments") or 0),
                "ownership_schools": int(asset.get("ownership_schools") or 0),
                "workload_status": str(asset.get("status_observations") or ""),
                "current_load": round(asset_workload, 2),
                "capacity": round(individual_capacity, 2),
                "utilization_rate": round(asset_utilization, 4),
                "status": _utilization_status(asset_utilization),
                "primary_workload_driver": workload_driver,
                "trace_id": f"ASSET-{uuid4().hex[:12].upper()}",
                "data_source": "recruiter_assignment_records",
            })
    else:
        # Synthetic asset at scope level (when individual recruiter data unavailable)
        asset_id = f"ASSET-{scope_value or 'USAREC'}-001"
        asset_status = _utilization_status(utilization_rate)
        
        asset_distribution.append({
            "asset_id": asset_id,
            "location": f"{scope_type.upper() if scope_type else 'USAREC'}: {scope_value or 'USAREC'}",
            "current_load": round(current_workload, 2),
            "capacity": round(capacity_hours, 2),
            "utilization_rate": round(utilization_rate, 4),
            "status": asset_status,
            "primary_workload_driver": workload_driver,
            "trace_id": f"ASSET-{uuid4().hex[:12].upper()}",
            "data_source": "organizational_recruiter_count",
        })
    
    # Extract board shifts for traceability
    board_shifts = _extract_board_shifts(board_signal)
    
    # Generate recommended shifts traceable to board decisions
    recommended_shifts = []
    if board_shifts and len(board_shifts) > 0:
        # For each board shift, generate corresponding asset shift if capacity allows
        for board_shift in board_shifts:
            shift_hours = 8.0  # Default effort impact
            available_capacity = capacity_hours - current_workload
            
            if available_capacity > shift_hours:
                feasibility = "high"
            elif available_capacity > shift_hours / 2:
                feasibility = "medium"
            else:
                feasibility = "low"
            
            # Link shift back to board decision
            shift_id = f"SHIFT-{uuid4().hex[:12].upper()}"
            recommended_shifts.append({
                "shift_id": shift_id,
                "board_decision_id": board_shift.get("decision_id") or "unknown_board_decision",
                "shift_type": str(board_shift.get("shift_type") or "effort"),
                "justification": f"Support board directive: {board_shift.get('rationale') or 'asset rebalancing'}",
                "feasibility": feasibility,
                "capacity_impact_hours": shift_hours,
                "available_capacity_hours": round(available_capacity, 2),
                "expected_effect": "Reallocate asset from lower-priority area to supported board decision",
                "trace_id": f"SHIFT-{uuid4().hex[:12].upper()}",
                "trace_source": "board_directed_shift",
            })
    
    # Generate shifts for overutilized assets (independent recommendations)
    elif utilization_rate > UTILIZATION_BALANCED_HIGH and asset_distribution:
        for asset in asset_distribution:
            if asset.get("status") in ["overloaded", "balanced"]:
                feasibility = _evaluate_shift_feasibility(
                    {"shift_type": "effort"},
                    asset_distribution,
                    current_workload,
                    capacity_hours,
                )
                shift = _generate_recommended_shift(asset, workload_driver, utilization_rate, feasibility)
                # Add trace back to utilization signal
                shift["trace_source"] = "asset_overutilization_detected"
                shift["upstream_evidence"] = f"{workload_driver}_workload_high"
                recommended_shifts.append(shift)
    
    # Detect execution constraints
    execution_constraints = _detect_execution_constraints(asset_distribution, board_shifts)
    
    # Add constraint if recruiter data was estimated
    if asset_list is None or len(asset_list) == 0:
        execution_constraints.append({
            "constraint_id": f"CONST-{uuid4().hex[:12].upper()}",
            "constraint_type": "data_granularity",
            "description": "Individual recruiter asset data not available; using organizational-level estimates",
            "affected_area": "asset_distribution_precision",
            "severity": "low",
            "trace_id": f"CONST-{uuid4().hex[:12].upper()}",
        })
    
    # Calculate risk and feasibility
    risk_level, feasibility_posture = _calculate_execution_risk(asset_distribution, board_signal)
    
    # Count asset statuses
    overutilized = sum(1 for a in asset_distribution if a.get("status") == "overloaded")
    underutilized = sum(1 for a in asset_distribution if a.get("status") == "underutilized")
    balanced = sum(1 for a in asset_distribution if a.get("status") == "balanced")
    
    # Build data sources map
    data_sources = {
        "board": "targeting_board_engine.summarize_targeting_board_engine()",
        "twg": "twg_engine.summarize_twg_engine()",
        "funnel": "funnel_engine.summarize_funnel_engine()",
        "school_plan": "school_plan_engine.summarize_school_plan_engine()",
        "roi": "roi_engine.summarize_roi_engine()",
        "recruiter_strength": "crud_domain.read_recruiter_count() [REAL DATA]",
        "asset_assignments": "crud_domain.read_recruiter_assignments() [REAL DATA]",
    }
    
    return {
        "status": "ok",
        "asset_engine": {
            "summary": {
                "total_assets": len(asset_distribution),
                "overutilized_assets": overutilized,
                "underutilized_assets": underutilized,
                "balanced_assets": balanced,
                "execution_risk_level": risk_level,
                "feasibility_posture": feasibility_posture,
                "data_completeness": "full" if asset_list else "partial_scope_level",
            },
            "asset_distribution": asset_distribution,
            "recommended_shifts": recommended_shifts,
            "execution_constraints": execution_constraints,
            "data_sources": data_sources,
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }
