from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.api.app.services import live_context_engine, outcome_learning_engine

APPROVAL_STATES = {"draft", "pending_review", "approved", "rejected", "superseded"}


def ensure_adaptive_update_schema(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS controlled_learning_adaptive_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                proposal_type TEXT NOT NULL,
                target_engine TEXT NOT NULL,
                target_rule TEXT,
                scope_type TEXT NOT NULL,
                scope_value TEXT NOT NULL,
                current_state_json TEXT,
                proposed_state_json TEXT,
                reason TEXT,
                evidence_refs_json TEXT,
                risk_level TEXT,
                approval_required INTEGER NOT NULL,
                approval_state TEXT NOT NULL,
                rollback_plan TEXT,
                config_version_from TEXT,
                config_version_to TEXT,
                trace_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS controlled_learning_config_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_version TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    existing = db.execute(text("SELECT COUNT(*) AS c FROM controlled_learning_config_version")).mappings().first() or {"c": 0}
    if int(existing.get("c") or 0) == 0:
        db.execute(
            text(
                "INSERT INTO controlled_learning_config_version(config_version, state, created_at) VALUES (:v, 'active', :ts)"
            ),
            {"v": "controlled-learning-v1", "ts": datetime.utcnow().isoformat() + "Z"},
        )
    db.commit()


def _current_config_version(db: Session) -> str:
    row = (
        db.execute(
            text(
                "SELECT config_version FROM controlled_learning_config_version ORDER BY id DESC LIMIT 1"
            )
        )
        .mappings()
        .first()
    )
    return str((row or {}).get("config_version") or "controlled-learning-v1")


def _proposal_order_key(item: Dict[str, Any]) -> tuple:
    risk_rank = {"high": 0, "medium": 1, "low": 2}
    return (risk_rank.get(str(item.get("risk_level") or "low"), 3), str(item.get("target_engine") or ""), str(item.get("proposal_type") or ""), str(item.get("proposal_id") or ""))


def _risk_for_magnitude(magnitude: str) -> str:
    mag = (magnitude or "minor").lower()
    if mag == "significant":
        return "high"
    if mag == "moderate":
        return "medium"
    return "low"


def _build_outcome_proposals(scope_type: str, scope_value: str, evaluations: List[Dict[str, Any]], current_version: str) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    for evaluation in evaluations:
        suggestion = evaluation.get("confidence_adjustment_suggestion") or {}
        if not suggestion:
            continue
        magnitude = str(suggestion.get("magnitude") or "minor")
        proposal_id = f"prop-outcome-{uuid4().hex[:12]}"
        proposals.append(
            {
                "proposal_id": proposal_id,
                "proposal_type": "confidence_rule",
                "target_engine": str(evaluation.get("source_engine") or "mission_decrease_justification"),
                "target_rule": f"recommendation_kind:{evaluation.get('recommendation_kind')}",
                "scope_type": scope_type,
                "scope_value": scope_value,
                "current_state": {
                    "confidence_direction": "hold",
                    "classification": evaluation.get("outcome_classification"),
                },
                "proposed_state": {
                    "direction": suggestion.get("direction"),
                    "magnitude": magnitude,
                    "bounded": True,
                },
                "reason": str(suggestion.get("rationale") or "Outcome evaluation generated bounded confidence adjustment suggestion."),
                "evidence_refs": [evaluation.get("trace_id"), evaluation.get("recommendation_id")],
                "risk_level": _risk_for_magnitude(magnitude),
                "approval_required": True,
                "approval_state": "draft",
                "rollback_plan": "Restore previous confidence-rule mapping and re-run outcome evaluation snapshot.",
                "trace_id": f"trace-{proposal_id}",
                "config_version_from": current_version,
                "config_version_to": f"{current_version}-proposal",
            }
        )
    return proposals


def _build_context_proposals(scope_type: str, scope_value: str, signals: List[Dict[str, Any]], current_version: str) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    for signal in signals:
        modifier = signal.get("recommended_modifier") or {}
        magnitude = str(modifier.get("magnitude") or "minor")
        proposal_id = f"prop-context-{uuid4().hex[:12]}"
        proposals.append(
            {
                "proposal_id": proposal_id,
                "proposal_type": "context_modifier",
                "target_engine": str(modifier.get("target_engine") or "mission_decrease_justification"),
                "target_rule": f"context:{signal.get('category')}:{signal.get('subcategory')}",
                "scope_type": scope_type,
                "scope_value": scope_value,
                "current_state": {
                    "modifier_type": "hold",
                    "signal_id": signal.get("signal_id"),
                },
                "proposed_state": {
                    "modifier_type": modifier.get("modifier_type"),
                    "direction": modifier.get("direction"),
                    "magnitude": magnitude,
                    "bounded": True,
                },
                "reason": f"Context signal suggests {modifier.get('modifier_type')} with {modifier.get('direction')} direction.",
                "evidence_refs": [signal.get("trace_id"), signal.get("signal_id")],
                "risk_level": _risk_for_magnitude(magnitude),
                "approval_required": True,
                "approval_state": "draft",
                "rollback_plan": "Revert context modifier proposal and restore prior context weighting baseline.",
                "trace_id": f"trace-{proposal_id}",
                "config_version_from": current_version,
                "config_version_to": f"{current_version}-proposal",
            }
        )
    return proposals


def _persist_proposals(db: Session, proposals: List[Dict[str, Any]]) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    for proposal in proposals:
        db.execute(
            text(
                """
                INSERT INTO controlled_learning_adaptive_proposals (
                    proposal_id, proposal_type, target_engine, target_rule, scope_type, scope_value,
                    current_state_json, proposed_state_json, reason, evidence_refs_json, risk_level,
                    approval_required, approval_state, rollback_plan, config_version_from,
                    config_version_to, trace_id, created_at, updated_at
                ) VALUES (
                    :proposal_id, :proposal_type, :target_engine, :target_rule, :scope_type, :scope_value,
                    :current_state_json, :proposed_state_json, :reason, :evidence_refs_json, :risk_level,
                    :approval_required, :approval_state, :rollback_plan, :config_version_from,
                    :config_version_to, :trace_id, :created_at, :updated_at
                )
                """
            ),
            {
                "proposal_id": proposal.get("proposal_id"),
                "proposal_type": proposal.get("proposal_type"),
                "target_engine": proposal.get("target_engine"),
                "target_rule": proposal.get("target_rule"),
                "scope_type": proposal.get("scope_type"),
                "scope_value": proposal.get("scope_value"),
                "current_state_json": json.dumps(proposal.get("current_state") or {}, default=str),
                "proposed_state_json": json.dumps(proposal.get("proposed_state") or {}, default=str),
                "reason": proposal.get("reason"),
                "evidence_refs_json": json.dumps(proposal.get("evidence_refs") or [], default=str),
                "risk_level": proposal.get("risk_level"),
                "approval_required": 1 if bool(proposal.get("approval_required", True)) else 0,
                "approval_state": proposal.get("approval_state") or "draft",
                "rollback_plan": proposal.get("rollback_plan"),
                "config_version_from": proposal.get("config_version_from"),
                "config_version_to": proposal.get("config_version_to"),
                "trace_id": proposal.get("trace_id"),
                "created_at": now,
                "updated_at": now,
            },
        )
    db.commit()


def update_proposal_state(db: Session, proposal_id: str, new_state: str) -> Dict[str, Any]:
    ensure_adaptive_update_schema(db)
    state = str(new_state or "").strip().lower()
    if state not in APPROVAL_STATES:
        return {"status": "invalid", "message": f"Unsupported state: {new_state}"}

    now = datetime.utcnow().isoformat() + "Z"
    updated = db.execute(
        text(
            """
            UPDATE controlled_learning_adaptive_proposals
            SET approval_state=:state, updated_at=:updated_at
            WHERE proposal_id=:proposal_id
            """
        ),
        {"state": state, "updated_at": now, "proposal_id": proposal_id},
    )
    db.commit()
    if int(updated.rowcount or 0) == 0:
        return {"status": "no_data", "message": "proposal_id not found"}
    return {"status": "ok", "proposal_id": proposal_id, "approval_state": state}


def list_proposals(db: Session, scope_type: str = "USAREC", scope_value: str = "USAREC", approval_state: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_adaptive_update_schema(db)
    st = (scope_type or "USAREC").upper().strip()
    sv = (scope_value or "USAREC").strip()
    state = (approval_state or "").strip().lower()

    sql = """
        SELECT * FROM controlled_learning_adaptive_proposals
        WHERE (:scope_type='USAREC' OR (scope_type=:scope_type AND scope_value=:scope_value))
    """
    params: Dict[str, Any] = {"scope_type": st, "scope_value": sv, "limit": int(limit)}
    if state:
        sql += " AND approval_state=:approval_state"
        params["approval_state"] = state
    sql += " ORDER BY created_at DESC, proposal_id ASC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()
    proposals: List[Dict[str, Any]] = []
    for row in rows:
        proposals.append(
            {
                "proposal_id": row.get("proposal_id"),
                "proposal_type": row.get("proposal_type"),
                "target_engine": row.get("target_engine"),
                "target_rule": row.get("target_rule"),
                "current_state": json.loads(row.get("current_state_json") or "{}"),
                "proposed_state": json.loads(row.get("proposed_state_json") or "{}"),
                "reason": row.get("reason"),
                "evidence_refs": json.loads(row.get("evidence_refs_json") or "[]"),
                "risk_level": row.get("risk_level"),
                "approval_required": bool(int(row.get("approval_required") or 0)),
                "approval_state": row.get("approval_state"),
                "rollback_plan": row.get("rollback_plan"),
                "trace_id": row.get("trace_id"),
                "config_version_from": row.get("config_version_from"),
                "config_version_to": row.get("config_version_to"),
            }
        )

    proposals.sort(key=_proposal_order_key)
    return {"status": "ok", "items": proposals}


def generate_update_proposals(db: Session, scope_type: str = "USAREC", scope_value: str = "USAREC", persist: bool = False, limit: int = 200) -> Dict[str, Any]:
    ensure_adaptive_update_schema(db)
    st = (scope_type or "USAREC").upper().strip()
    sv = (scope_value or "USAREC").strip()
    current_version = _current_config_version(db)

    outcome = outcome_learning_engine.evaluate_outcomes(db, st, sv, limit=limit)
    context = live_context_engine.summarize_context_signals(db, st, sv, limit=limit)

    evaluations = ((outcome.get("outcome_learning_engine") or {}).get("outcome_evaluations") or [])
    signals = ((context.get("live_context_engine") or {}).get("context_signals") or [])

    proposals = _build_outcome_proposals(st, sv, evaluations, current_version)
    proposals.extend(_build_context_proposals(st, sv, signals, current_version))
    proposals.sort(key=_proposal_order_key)

    if persist and proposals:
        _persist_proposals(db, proposals)

    high_priority = sum(1 for p in proposals if str(p.get("risk_level") or "").lower() == "high")
    approval_required = sum(1 for p in proposals if bool(p.get("approval_required", True)))

    return {
        "status": "ok" if proposals else "no_data",
        "adaptive_update_engine": {
            "summary": {
                "proposals_generated": len(proposals),
                "high_priority_proposals": high_priority,
                "approval_required": approval_required,
                "auto_applicable": 0,
            },
            "update_proposals": proposals,
            "versioning": {
                "current_config_version": current_version,
                "proposed_config_version": f"{current_version}-proposal",
            },
        },
    }
