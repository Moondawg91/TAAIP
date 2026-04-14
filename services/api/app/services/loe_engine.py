from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import text

VALID_SCOPE_TYPES = {"USAREC", "BDE", "BN", "CO", "STN"}


def _empty_loe_summary(total_loes: int = 0) -> Dict:
    return {
        "total_loes": int(total_loes or 0),
        "total_metrics": 0,
        "status_counts": {"met": 0, "at_risk": 0, "not_met": 0, "unknown": 0},
    }


def validate_scope(scope_type: str, scope_value: str) -> None:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()
    if st not in VALID_SCOPE_TYPES:
        raise HTTPException(status_code=400, detail="invalid scope_type")
    if st != "USAREC" and not sv:
        raise HTTPException(status_code=400, detail="scope_value is required")


def can_user_manage_loe(user, scope_type: str, scope_value: str) -> None:
    role_name = getattr(getattr(user, "role", None), "name", str(getattr(user, "role", "")))
    scope = (getattr(user, "scope", "") or "").strip()
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()

    if role_name == "STATION_VIEW" or role_name.endswith("_VIEW"):
        raise HTTPException(status_code=403, detail="role not permitted to write LOE")

    if role_name == "COMPANY_CMD":
        # Company commanders are read-only unless policy flag is enabled.
        import os

        if os.getenv("ALLOW_COMPANY_LOE_WRITE", "0").lower() not in {"1", "true", "yes"}:
            raise HTTPException(status_code=403, detail="company commander LOE write disabled by policy")
        if st not in {"CO", "STN"}:
            raise HTTPException(status_code=403, detail="company commander may only create CO/STN LOEs")
        if scope and not sv.startswith(scope[:3]):
            raise HTTPException(status_code=403, detail="scope outside company commander authority")


def scope_match(scope_type: str, scope_value: str, loe_scope_value: str) -> bool:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()
    lv = (loe_scope_value or "").strip()
    if st == "USAREC":
        return True
    if st == "BDE":
        return lv.startswith(sv[:1])
    if st == "BN":
        return lv.startswith(sv[:2])
    if st == "CO":
        return lv.startswith(sv[:3])
    if st == "STN":
        return lv.startswith(sv[:4])
    return False


def evaluate_metric_status(metric) -> Tuple[str, str]:
    current = metric.current_value
    target = metric.target_value
    warn = metric.warn_threshold
    fail = metric.fail_threshold

    if current is None:
        return "unknown", "current value is missing"

    # Higher is better for LOE metrics by default.
    if fail is not None and current <= fail:
        return "not_met", f"current {current:.2f} <= fail threshold {fail:.2f}"
    if warn is not None and current <= warn:
        return "at_risk", f"current {current:.2f} <= warning threshold {warn:.2f}"
    if target is not None:
        if current >= target:
            return "met", f"current {current:.2f} >= target {target:.2f}"
        return "at_risk", f"current {current:.2f} below target {target:.2f}"
    return "unknown", "target and thresholds are not configured"


def evaluate_loe(db, loe_id: str) -> Dict:
    from services.api.app import models_domain as domain

    metrics = db.query(domain.LoeMetric).filter(domain.LoeMetric.loe_id == loe_id).all()
    counts = {"met": 0, "at_risk": 0, "not_met": 0, "unknown": 0}
    now = datetime.utcnow()

    for metric in metrics:
        status, rationale = evaluate_metric_status(metric)
        metric.status = status
        metric.rationale = rationale
        metric.last_evaluated_at = now
        counts[status] = counts.get(status, 0) + 1

    # Persist trend snapshot for commander trend review.
    try:
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS loe_evaluation_history (
                    id TEXT PRIMARY KEY,
                    loe_id TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL,
                    met_count INTEGER DEFAULT 0,
                    at_risk_count INTEGER DEFAULT 0,
                    not_met_count INTEGER DEFAULT 0,
                    unknown_count INTEGER DEFAULT 0
                )
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO loe_evaluation_history(
                    id, loe_id, evaluated_at, met_count, at_risk_count, not_met_count, unknown_count
                ) VALUES(:id, :loe_id, :evaluated_at, :met_count, :at_risk_count, :not_met_count, :unknown_count)
                """
            ),
            {
                "id": f"leh-{loe_id}-{int(now.timestamp())}",
                "loe_id": loe_id,
                "evaluated_at": now.isoformat() + "Z",
                "met_count": int(counts.get("met", 0)),
                "at_risk_count": int(counts.get("at_risk", 0)),
                "not_met_count": int(counts.get("not_met", 0)),
                "unknown_count": int(counts.get("unknown", 0)),
            },
        )
    except Exception:
        pass

    db.commit()
    return {
        "evaluated": len(metrics),
        "status_counts": counts,
    }


def loe_blockers(db, scope_type: str, scope_value: str, market_summary: Dict, school_summary: Dict, execution_summary: Dict) -> Dict:
    summary = summarize_loes(db, scope_type, scope_value)
    blocked_by = []

    if (market_summary or {}).get("overall_market_status") in {"market_constrained", "no_active_dataset"}:
        blocked_by.append("market")
    if (school_summary or {}).get("overall_access_status") in {"access_constrained", "no_active_dataset"}:
        blocked_by.append("access")
    if (execution_summary or {}).get("overall_execution_status") in {"execution_degraded", "no_active_dataset"}:
        blocked_by.append("execution")

    return {
        "total_loes": summary.get("total_loes", 0),
        "status_counts": summary.get("status_counts", {}),
        "blocked_by": blocked_by,
    }


def list_loes_for_scope(db, scope_type: str, scope_value: str) -> List[Dict]:
    from services.api.app import models_domain as domain

    try:
        loes = db.query(domain.Loe).all()
    except Exception:
        return []

    out = []
    for loe in loes:
        if not scope_match(scope_type, scope_value, loe.scope_value):
            continue
        try:
            metric_count = (
                db.query(domain.LoeMetric)
                .filter(domain.LoeMetric.loe_id == loe.id)
                .count()
            )
        except Exception:
            metric_count = 0
        out.append(
            {
                "id": loe.id,
                "scope_type": loe.scope_type,
                "scope_value": loe.scope_value,
                "title": loe.title,
                "description": loe.description,
                "created_by": loe.created_by,
                "metrics_count": metric_count,
                "created_at": loe.created_at,
            }
        )
    return out


def summarize_loes(db, scope_type: str, scope_value: str) -> Dict:
    from services.api.app import models_domain as domain

    loes = list_loes_for_scope(db, scope_type, scope_value)
    loe_ids = [x["id"] for x in loes]
    if not loe_ids:
        return _empty_loe_summary()

    try:
        metrics = db.query(domain.LoeMetric).filter(domain.LoeMetric.loe_id.in_(loe_ids)).all()
    except Exception:
        return _empty_loe_summary(total_loes=len(loes))

    status_counts = {"met": 0, "at_risk": 0, "not_met": 0, "unknown": 0}
    for m in metrics:
        status = m.status or "unknown"
        if status not in status_counts:
            status = "unknown"
        status_counts[status] += 1

    return {
        "total_loes": len(loes),
        "total_metrics": len(metrics),
        "status_counts": status_counts,
    }
