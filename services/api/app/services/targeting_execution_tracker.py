from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
import re
from typing import Dict, List, Optional, Tuple

from starlette.exceptions import HTTPException

from services.api.app.services import (
    asset_engine,
    funnel_engine,
    roi_engine,
    school_plan_engine,
    targeting_board_engine,
    twg_engine,
)


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


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join([prefix] + [str(p or "") for p in parts])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def _parse_due_date(value: str) -> Optional[date]:
    v = str(value or "").strip()
    if not v:
        return None
    try:
        # ISO date format from board engine
        return datetime.fromisoformat(v).date()
    except Exception:
        pass
    return None


def _normalize_status(raw_status: str) -> Optional[str]:
    s = str(raw_status or "").strip().lower()
    if s in {"not_started", "not started", "todo"}:
        return "not_started"
    if s in {"in_progress", "in progress", "active", "working"}:
        return "in_progress"
    if s in {"completed", "complete", "done", "closed"}:
        return "completed"
    if s in {"blocked", "on_hold", "on hold"}:
        return "blocked"
    return None


def _infer_task_status(
    explicit_status: Optional[str],
    progress_pct: Optional[float],
    has_asset_shift_signal: bool,
    has_due_out_signal: bool,
    is_blocked: bool,
) -> Tuple[str, float]:
    normalized = _normalize_status(explicit_status or "")
    if normalized is not None:
        if normalized == "completed":
            return "completed", 100.0
        if normalized == "in_progress":
            return "in_progress", max(1.0, min(99.0, float(progress_pct or 50.0)))
        if normalized == "blocked":
            return "blocked", max(0.0, min(99.0, float(progress_pct or 25.0)))
        return "not_started", max(0.0, min(99.0, float(progress_pct or 0.0)))

    if is_blocked:
        return "blocked", 25.0
    if has_asset_shift_signal or has_due_out_signal:
        return "in_progress", 50.0
    return "not_started", 0.0


def _extract_expected_numeric(expected_effect: str) -> Optional[float]:
    txt = str(expected_effect or "")
    # Only parse explicit numeric targets in authoritative text (e.g., "10%", "0.2").
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", txt)
    if m:
        return float(m.group(1)) / 100.0
    m2 = re.search(r"(-?\d+(?:\.\d+)?)", txt)
    if m2 and any(k in txt.lower() for k in ["rate", "ratio", "score", "effect"]):
        return float(m2.group(1))
    return None


def _actual_effect_for_category(
    category: str,
    funnel_signal: Dict,
    school_signal: Dict,
    roi_signal: Dict,
    mission_signal: Optional[Dict],
) -> Tuple[str, Optional[float], Optional[str]]:
    c = str(category or "").lower()

    if c == "funnel":
        v = (((funnel_signal.get("funnel_engine") or {}).get("summary") or {}).get("lead_to_contract_rate"))
        if v is None:
            return "", None, "funnel_actual_effect_unavailable"
        return f"lead_to_contract_rate={v}", float(v), None

    if c == "school":
        v = (((school_signal.get("school_plan_engine") or {}).get("summary") or {}).get("engagement_rate"))
        if v is None:
            return "", None, "school_actual_effect_unavailable"
        return f"engagement_rate={v}", float(v), None

    if c == "roi":
        v = (((roi_signal.get("roi_engine") or {}).get("summary") or {}).get("avg_roi_score"))
        if v is None:
            return "", None, "roi_actual_effect_unavailable"
        return f"avg_roi_score={v}", float(v), None

    if c in {"targeting", "market"}:
        # No direct targeting effect metric in required authoritative list for this tracker.
        return "", None, "targeting_actual_effect_unavailable"

    if c == "mission":
        delta_pct = (((mission_signal or {}).get("mission_delta_summary") or {}).get("delta_pct"))
        if delta_pct is None:
            return "", None, "mission_actual_effect_unavailable"
        return f"mission_delta_pct={delta_pct}", float(delta_pct), None

    return "", None, "actual_effect_unavailable"


def _effect_material_miss(effect_gap: Optional[float]) -> bool:
    if effect_gap is None:
        return False
    return effect_gap > 0.15


def _resolve_owner_level(value: str) -> str:
    v = str(value or "").upper().strip()
    if v in {"BN", "CO", "STN"}:
        return v
    return "CO"


def _posture(total: int, blocked: int, off_track: int, effect_realization_rate: float, measurable_count: int) -> str:
    if total <= 0:
        return "unknown"
    blocked_rate = blocked / float(total)
    off_track_rate = off_track / float(total)

    if blocked_rate >= 0.35 or off_track_rate >= 0.40:
        return "failing"
    if measurable_count > 0 and effect_realization_rate < 0.40:
        return "failing"
    if blocked_rate >= 0.15 or off_track_rate >= 0.20:
        return "watch"
    return "on_track"


def _today_utc() -> date:
    return datetime.utcnow().date()


def summarize_targeting_execution_tracker(
    db,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    actor_scope_type: Optional[str] = None,
    actor_scope_value: Optional[str] = None,
    top_n: int = 30,
    mission_signal: Optional[Dict] = None,
    include_mission_signal: bool = True,
) -> Dict:
    """
    Execution and status layer for board-directed actions.

    Consumes authoritative outputs only:
    - targeting_board_engine
    - twg_engine
    - asset_engine
    - mission_decrease_justification (optional input or fetched when allowed)
    - funnel_engine
    - school_plan_engine
    - roi_engine
    """
    try:
        enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)
    except HTTPException:
        return {
            "status": "invalid",
            "targeting_execution_tracker": {
                "summary": {
                    "total_tasks": 0,
                    "not_started": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "blocked": 0,
                    "off_track": 0,
                    "execution_posture": "unknown",
                },
                "execution_items": [],
                "blocked_items": [],
                "off_track_items": [],
                "escalations": [],
                "execution_scorecard": {
                    "completion_rate": 0.0,
                    "blocked_rate": 0.0,
                    "on_time_rate": 0.0,
                    "effect_realization_rate": 0.0,
                },
                "data_sources": {
                    "board": "invalid_scope",
                    "twg": "invalid_scope",
                    "asset": "invalid_scope",
                    "mission": "invalid_scope",
                    "funnel": "invalid_scope",
                    "school_plan": "invalid_scope",
                    "roi": "invalid_scope",
                },
                "execution_constraints": [
                    {
                        "constraint_id": _stable_id("CONST", "invalid_scope", scope_type or "", scope_value or ""),
                        "constraint_type": "invalid_scope",
                        "description": "Requested scope is outside actor permissions.",
                        "severity": "high",
                    }
                ],
            },
        }

    st = scope_type or "USAREC"
    sv = scope_value or "USAREC"
    ast = actor_scope_type or st
    asv = actor_scope_value or sv

    board_signal = targeting_board_engine.summarize_targeting_board_engine(db, st, sv, ast, asv, top_n=top_n)
    twg_signal = twg_engine.summarize_twg_engine(db, st, sv, ast, asv, top_n=top_n)
    asset_signal = asset_engine.summarize_asset_engine(db, st, sv, ast, asv, top_n=top_n)
    funnel_signal = funnel_engine.summarize_funnel_engine(db, st, sv, ast, asv, top_n=top_n)
    school_signal = school_plan_engine.summarize_school_plan_engine(db, st, sv, ast, asv, top_n=top_n)
    roi_signal = roi_engine.summarize_roi_engine(db, st, sv, ast, asv, top_n=top_n)

    mission_source = "provided"
    if mission_signal is None and include_mission_signal:
        try:
            from services.api.app.services import mission_decrease_justification as _mdj

            end = _today_utc()
            start = end - timedelta(days=29)
            baseline_end = start - timedelta(days=1)
            baseline_start = baseline_end - timedelta(days=29)
            org_id = (sv or "USAREC").upper()
            if (st or "USAREC").upper() == "USAREC":
                org_id = "USAREC"
            mission_signal = _mdj.generate_mission_decrease_justification(
                db,
                org_id=org_id,
                period_start=start,
                period_end=end,
                baseline_start=baseline_start,
                baseline_end=baseline_end,
                include_evidence=False,
            )
            mission_source = "mission_decrease_justification.generate_mission_decrease_justification()"
        except Exception:
            mission_signal = None
            mission_source = "unavailable"
    elif mission_signal is None:
        mission_source = "not_included"

    board_data = board_signal.get("targeting_board_engine") or {}
    twg_data = twg_signal.get("twg_engine") or {}
    asset_data = asset_signal.get("asset_engine") or {}

    downstream_tasks = list(board_data.get("downstream_twg_tasks") or [])
    board_decisions = list(board_data.get("board_decisions") or [])
    directed_shifts = list(board_data.get("directed_shifts") or [])
    twg_due_outs = list(twg_data.get("due_outs") or [])
    prioritized_items = list(twg_data.get("prioritized_items") or [])
    asset_shifts = list(asset_data.get("recommended_shifts") or [])
    asset_constraints = list(asset_data.get("execution_constraints") or [])

    if not downstream_tasks and not board_decisions:
        return {
            "status": "no_data",
            "targeting_execution_tracker": {
                "summary": {
                    "total_tasks": 0,
                    "not_started": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "blocked": 0,
                    "off_track": 0,
                    "execution_posture": "unknown",
                },
                "execution_items": [],
                "blocked_items": [],
                "off_track_items": [],
                "escalations": [],
                "execution_scorecard": {
                    "completion_rate": 0.0,
                    "blocked_rate": 0.0,
                    "on_time_rate": 0.0,
                    "effect_realization_rate": 0.0,
                },
                "data_sources": {
                    "board": board_signal.get("status") or "unknown",
                    "twg": twg_signal.get("status") or "unknown",
                    "asset": asset_signal.get("status") or "unknown",
                    "mission": mission_source,
                    "funnel": funnel_signal.get("status") or "unknown",
                    "school_plan": school_signal.get("status") or "unknown",
                    "roi": roi_signal.get("status") or "unknown",
                },
                "execution_constraints": [
                    {
                        "constraint_id": _stable_id("CONST", "no_tasks", st, sv),
                        "constraint_type": "no_execution_items",
                        "description": "No board downstream tasks were available for execution tracking.",
                        "severity": "medium",
                    }
                ],
            },
        }

    decision_by_id: Dict[str, Dict] = {}
    for d in board_decisions:
        did = str(d.get("decision_id") or "")
        if did:
            decision_by_id[did] = d

    # Fallback when downstream tasks are unavailable: project one task per board decision.
    if not downstream_tasks:
        downstream_tasks = [
            {
                "task_id": _stable_id("TASK", str(d.get("decision_id") or ""), str(d.get("action") or "")),
                "source_board_decision_id": str(d.get("decision_id") or ""),
                "owner_level": _resolve_owner_level(str(d.get("owner_level") or "CO")),
                "action": str(d.get("action") or ""),
                "due_out": str(d.get("time_horizon") or ""),
                "expected_effect": str(d.get("expected_effect") or ""),
                "trace_id": str(d.get("trace_id") or _stable_id("TRACE", str(d.get("decision_id") or ""))),
            }
            for d in board_decisions
            if str(d.get("decision_type") or "").lower() in {"approve", "modify"}
        ]

    execution_items: List[Dict] = []
    execution_constraints: List[Dict] = []
    today = _today_utc()

    for idx, task in enumerate(sorted(downstream_tasks, key=lambda x: str(x.get("task_id") or ""))[:top_n]):
        task_id = str(task.get("task_id") or _stable_id("TASK", str(idx), str(task.get("action") or "")))
        decision_id = str(task.get("source_board_decision_id") or "")
        decision = decision_by_id.get(decision_id) or {}
        action = str(task.get("action") or decision.get("action") or "")
        expected_effect = str(task.get("expected_effect") or decision.get("expected_effect") or "")
        owner_level = _resolve_owner_level(str(task.get("owner_level") or decision.get("owner_level") or "CO"))
        due_out = str(task.get("due_out") or decision.get("time_horizon") or "")
        due_date = _parse_due_date(due_out)

        has_due_out_signal = any(str(x.get("action") or "") == action for x in twg_due_outs)
        has_asset_shift_signal = len(directed_shifts) > 0 or len(asset_shifts) > 0

        linked_constraint = None
        if asset_constraints:
            linked_constraint = asset_constraints[0]

        blocker_reason = ""
        is_blocked = False
        if linked_constraint is not None:
            is_blocked = True
            blocker_reason = str(linked_constraint.get("description") or "execution_constraint_present")

        explicit_status = task.get("status")
        progress_raw = task.get("progress_pct")
        status, progress_pct = _infer_task_status(
            explicit_status=explicit_status,
            progress_pct=float(progress_raw) if progress_raw is not None else None,
            has_asset_shift_signal=has_asset_shift_signal,
            has_due_out_signal=has_due_out_signal,
            is_blocked=is_blocked,
        )

        category = ""
        if action:
            action_l = action.lower()
            if "funnel" in action_l:
                category = "funnel"
            elif "school" in action_l:
                category = "school"
            elif "roi" in action_l or "event" in action_l:
                category = "roi"
            elif "target" in action_l or "zip" in action_l:
                category = "targeting"
            elif "market" in action_l:
                category = "market"
            elif "mission" in action_l:
                category = "mission"

        actual_effect, actual_numeric, actual_limitation = _actual_effect_for_category(
            category=category,
            funnel_signal=funnel_signal,
            school_signal=school_signal,
            roi_signal=roi_signal,
            mission_signal=mission_signal,
        )
        expected_numeric = _extract_expected_numeric(expected_effect)
        effect_gap = None
        if expected_numeric is not None and actual_numeric is not None:
            effect_gap = round(expected_numeric - actual_numeric, 6)

        overdue_not_complete = bool(due_date is not None and due_date < today and status != "completed")
        effect_miss = _effect_material_miss(effect_gap)
        off_track = bool(overdue_not_complete or status == "blocked" or effect_miss)

        if actual_limitation is not None:
            execution_constraints.append(
                {
                    "constraint_id": _stable_id("CONST", task_id, "actual_effect"),
                    "constraint_type": "partial_data",
                    "description": f"Actual effect unavailable for task {task_id}: {actual_limitation}",
                    "severity": "medium",
                }
            )

        execution_items.append(
            {
                "task_id": task_id,
                "source_board_decision_id": decision_id,
                "owner_level": owner_level,
                "status": status,
                "progress_pct": round(float(progress_pct), 2),
                "due_out": due_out,
                "expected_effect": expected_effect,
                "actual_effect": actual_effect,
                "effect_gap": effect_gap,
                "blocker_reason": blocker_reason,
                "trace_id": str(task.get("trace_id") or _stable_id("TRACE", task_id)),
                "_off_track": off_track,
            }
        )

    execution_items.sort(key=lambda x: (str(x.get("task_id") or ""), str(x.get("source_board_decision_id") or "")))

    blocked_items = [x for x in execution_items if x.get("status") == "blocked"]
    off_track_items = [x for x in execution_items if bool(x.get("_off_track"))]

    # Escalation model: operational blockers to TWG; policy/resource/tradeoff misses to BOARD.
    escalations: List[Dict] = []
    for item in off_track_items:
        reason = []
        if item.get("status") == "blocked":
            reason.append("task_blocked")
        if item.get("status") != "completed" and _parse_due_date(str(item.get("due_out") or "")) and _parse_due_date(str(item.get("due_out") or "")) < today:
            reason.append("overdue_not_completed")
        if _effect_material_miss(item.get("effect_gap")):
            reason.append("effect_material_miss")

        blocker_txt = str(item.get("blocker_reason") or "").lower()
        board_reason = any(k in blocker_txt for k in ["resource", "policy", "tradeoff", "personnel", "workload"])
        board_reason = board_reason or ("effect_material_miss" in reason)
        escalate_to = "BOARD" if board_reason else "TWG"

        rec_action = "Resolve task-level execution friction and republish due-out status in next TWG cycle."
        if escalate_to == "BOARD":
            rec_action = "Board review required for resource/policy tradeoff and directive adjustment."

        escalations.append(
            {
                "escalation_id": _stable_id("ESC", str(item.get("task_id") or ""), escalate_to),
                "task_id": str(item.get("task_id") or ""),
                "escalate_to": escalate_to,
                "reason": ",".join(reason) if reason else "execution_risk",
                "recommended_action": rec_action,
                "trace_id": _stable_id("TRACE", "ESC", str(item.get("task_id") or "")),
            }
        )

    total = len(execution_items)
    not_started = sum(1 for x in execution_items if x.get("status") == "not_started")
    in_progress = sum(1 for x in execution_items if x.get("status") == "in_progress")
    completed = sum(1 for x in execution_items if x.get("status") == "completed")
    blocked = sum(1 for x in execution_items if x.get("status") == "blocked")
    off_track = len(off_track_items)

    completion_rate = round((completed / float(total)) if total else 0.0, 6)
    blocked_rate = round((blocked / float(total)) if total else 0.0, 6)

    on_schedule_count = 0
    for x in execution_items:
        d = _parse_due_date(str(x.get("due_out") or ""))
        if d is None:
            on_schedule_count += 1
        elif x.get("status") == "completed":
            on_schedule_count += 1
        elif d >= today:
            on_schedule_count += 1
    on_time_rate = round((on_schedule_count / float(total)) if total else 0.0, 6)

    measurable = [x for x in execution_items if x.get("effect_gap") is not None]
    realized = [x for x in measurable if float(x.get("effect_gap") or 0.0) <= 0.0]
    effect_realization_rate = round((len(realized) / float(len(measurable))) if measurable else 0.0, 6)

    posture = _posture(total, blocked, off_track, effect_realization_rate, len(measurable))

    # remove internal marker before return
    for x in execution_items:
        x.pop("_off_track", None)

    return {
        "status": "ok",
        "targeting_execution_tracker": {
            "summary": {
                "total_tasks": total,
                "not_started": not_started,
                "in_progress": in_progress,
                "completed": completed,
                "blocked": blocked,
                "off_track": off_track,
                "execution_posture": posture,
            },
            "execution_items": execution_items,
            "blocked_items": blocked_items,
            "off_track_items": off_track_items,
            "escalations": sorted(escalations, key=lambda x: str(x.get("task_id") or "")),
            "execution_scorecard": {
                "completion_rate": completion_rate,
                "blocked_rate": blocked_rate,
                "on_time_rate": on_time_rate,
                "effect_realization_rate": effect_realization_rate,
            },
            "data_sources": {
                "board": "targeting_board_engine.summarize_targeting_board_engine()",
                "twg": "twg_engine.summarize_twg_engine()",
                "asset": "asset_engine.summarize_asset_engine()",
                "mission": mission_source,
                "funnel": "funnel_engine.summarize_funnel_engine()",
                "school_plan": "school_plan_engine.summarize_school_plan_engine()",
                "roi": "roi_engine.summarize_roi_engine()",
            },
            "execution_constraints": sorted(
                execution_constraints,
                key=lambda x: (str(x.get("constraint_type") or ""), str(x.get("constraint_id") or "")),
            ),
        },
    }
