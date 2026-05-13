from datetime import datetime
from typing import Dict
from uuid import uuid4

from services.api.app import models_domain as domain


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def writeback_change(
    db,
    actor: str,
    scope_type: str,
    scope_value: str,
    decision_type: str,
    summary: str,
    before_json: Dict,
    after_json: Dict,
) -> Dict:
    did = f"decision-{uuid4().hex[:16]}"
    aid = f"audit-{uuid4().hex[:16]}"

    d = domain.Decision(
        id=did,
        scope_type=scope_type,
        scope_value=scope_value,
        decision_type=decision_type,
        summary=summary,
        details_json={"before": before_json, "after": after_json, "written_at": _now_iso()},
        created_by=actor,
    )
    a = domain.AuditLog(
        id=aid,
        actor=actor,
        action="writeback_decision",
        entity_type="decision",
        entity_id=did,
        scope_type=scope_type,
        scope_value=scope_value,
        before_json=before_json,
        after_json=after_json,
    )

    db.add(d)
    db.add(a)
    db.commit()

    return {
        "decision_id": did,
        "audit_id": aid,
        "status": "ok",
    }
