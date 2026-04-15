from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

REQUIRED_SCOPE_TYPES = {"USAREC", "BDE", "BN", "CO", "STN"}


def ensure_outcome_learning_schema(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS controlled_learning_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id TEXT NOT NULL,
                source_engine TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_value TEXT NOT NULL,
                target_object TEXT,
                recommendation_kind TEXT,
                rationale_snapshot TEXT,
                expected_kpi_json TEXT,
                expected_effect TEXT,
                expected_horizon TEXT,
                actual_kpi_json TEXT,
                actual_effect TEXT,
                observed_state TEXT,
                pattern_type TEXT,
                pattern_value TEXT,
                period_start TEXT,
                period_end TEXT,
                generated_at TEXT,
                measured_at TEXT,
                trace_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    db.commit()


def _as_json(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return fallback
    return fallback


def _normalize_scope(scope_type: str, scope_value: str) -> Tuple[str, str]:
    st = (scope_type or "USAREC").upper().strip()
    sv = (scope_value or "USAREC").strip()
    if st not in REQUIRED_SCOPE_TYPES:
        return "USAREC", "USAREC"
    return st, sv


def record_outcome(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_outcome_learning_schema(db)

    recommendation_id = str(payload.get("recommendation_id") or "").strip()
    source_engine = str(payload.get("source_engine") or payload.get("engine") or "").strip()
    scope_type, scope_value = _normalize_scope(str(payload.get("scope_type") or "USAREC"), str(payload.get("scope_value") or "USAREC"))

    if not recommendation_id or not source_engine:
        return {
            "status": "invalid",
            "message": "recommendation_id and source_engine are required",
        }

    trace_id = str(payload.get("trace_id") or f"trace-{uuid4().hex[:16]}")
    now = datetime.utcnow().isoformat() + "Z"

    db.execute(
        text(
            """
            INSERT INTO controlled_learning_outcomes (
                recommendation_id, source_engine, scope_type, scope_value, target_object,
                recommendation_kind, rationale_snapshot, expected_kpi_json, expected_effect,
                expected_horizon, actual_kpi_json, actual_effect, observed_state,
                pattern_type, pattern_value, period_start, period_end, generated_at,
                measured_at, trace_id, created_at
            ) VALUES (
                :recommendation_id, :source_engine, :scope_type, :scope_value, :target_object,
                :recommendation_kind, :rationale_snapshot, :expected_kpi_json, :expected_effect,
                :expected_horizon, :actual_kpi_json, :actual_effect, :observed_state,
                :pattern_type, :pattern_value, :period_start, :period_end, :generated_at,
                :measured_at, :trace_id, :created_at
            )
            """
        ),
        {
            "recommendation_id": recommendation_id,
            "source_engine": source_engine,
            "scope_type": scope_type,
            "scope_value": scope_value,
            "target_object": payload.get("target_object"),
            "recommendation_kind": payload.get("recommendation_kind"),
            "rationale_snapshot": payload.get("rationale_snapshot"),
            "expected_kpi_json": json.dumps(payload.get("expected_kpi") or {}, default=str),
            "expected_effect": payload.get("expected_effect"),
            "expected_horizon": payload.get("expected_horizon"),
            "actual_kpi_json": json.dumps(payload.get("actual_kpi") or {}, default=str),
            "actual_effect": payload.get("actual_effect"),
            "observed_state": payload.get("observed_state"),
            "pattern_type": payload.get("pattern_type"),
            "pattern_value": payload.get("pattern_value"),
            "period_start": payload.get("period_start"),
            "period_end": payload.get("period_end"),
            "generated_at": payload.get("generated_at"),
            "measured_at": payload.get("measured_at"),
            "trace_id": trace_id,
            "created_at": now,
        },
    )
    db.commit()
    return {"status": "ok", "trace_id": trace_id}


def _extract_numeric_values(payload: Dict[str, Any]) -> List[float]:
    values: List[float] = []
    for value in (payload or {}).values():
        try:
            values.append(float(value))
        except Exception:
            continue
    return values


def _classify_outcome(expected_kpi: Dict[str, Any], actual_kpi: Dict[str, Any], observed_state: str) -> Tuple[str, Dict[str, float]]:
    expected_values = _extract_numeric_values(expected_kpi)
    actual_values = _extract_numeric_values(actual_kpi)

    if not expected_values or not actual_values:
        return "insufficient_data", {"delta_abs": 0.0, "delta_pct": 0.0}

    expected_avg = sum(expected_values) / float(len(expected_values))
    actual_avg = sum(actual_values) / float(len(actual_values))
    delta_abs = actual_avg - expected_avg
    delta_pct = (delta_abs / expected_avg) if expected_avg else 0.0

    observed_state_norm = (observed_state or "").strip().lower()
    if observed_state_norm in {"failed", "blocked"}:
        return "failed", {"delta_abs": round(delta_abs, 6), "delta_pct": round(delta_pct, 6)}

    if delta_pct >= 0.15:
        return "exceeded", {"delta_abs": round(delta_abs, 6), "delta_pct": round(delta_pct, 6)}
    if delta_pct >= -0.05:
        return "met", {"delta_abs": round(delta_abs, 6), "delta_pct": round(delta_pct, 6)}
    if delta_pct >= -0.30:
        return "underperformed", {"delta_abs": round(delta_abs, 6), "delta_pct": round(delta_pct, 6)}
    return "failed", {"delta_abs": round(delta_abs, 6), "delta_pct": round(delta_pct, 6)}


def _confidence_adjustment_for(classification: str, delta_pct: float) -> Dict[str, str]:
    c = (classification or "insufficient_data").lower()
    if c == "exceeded":
        magnitude = "significant" if delta_pct >= 0.25 else "moderate"
        return {
            "direction": "increase",
            "magnitude": magnitude,
            "rationale": "Observed effect exceeded expectation within the measured horizon.",
        }
    if c == "met":
        return {
            "direction": "hold",
            "magnitude": "minor",
            "rationale": "Observed effect met expectation; keep current confidence.",
        }
    if c == "underperformed":
        return {
            "direction": "decrease",
            "magnitude": "moderate",
            "rationale": "Observed effect underperformed expected KPI trajectory.",
        }
    if c == "failed":
        return {
            "direction": "decrease",
            "magnitude": "significant",
            "rationale": "Observed state failed or KPI variance exceeded tolerated bounds.",
        }
    return {
        "direction": "hold",
        "magnitude": "minor",
        "rationale": "Insufficient comparable KPI evidence to justify confidence change.",
    }


def _learning_confidence(summary: Dict[str, int]) -> str:
    evaluated = int(summary.get("recommendations_evaluated") or 0)
    met_or_exceeded = int(summary.get("met_or_exceeded") or 0)
    if evaluated >= 25 and (met_or_exceeded / float(max(1, evaluated))) >= 0.65:
        return "high"
    if evaluated >= 8:
        return "medium"
    return "low"


def _pattern_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[str]] = {}
    for row in rows:
        p_type = str(row.get("pattern_type") or "targeting_strategy")
        p_value = str(row.get("pattern_value") or row.get("recommendation_kind") or "unknown")
        key = (p_type, p_value)
        grouped.setdefault(key, []).append(str(row.get("outcome_classification") or "insufficient_data"))

    out: List[Dict[str, Any]] = []
    for (p_type, p_value), outcomes in grouped.items():
        success_count = sum(1 for item in outcomes if item in {"exceeded", "met"})
        success_rate = success_count / float(len(outcomes))
        recommendation = "monitor"
        if success_rate >= 0.70:
            recommendation = "promote"
        elif success_rate < 0.45:
            recommendation = "de-emphasize"
        out.append(
            {
                "pattern_id": f"pattern-{p_type}-{p_value}".replace(" ", "_").lower(),
                "pattern_type": p_type,
                "pattern_value": p_value,
                "evaluations": len(outcomes),
                "success_rate": round(success_rate, 4),
                "recommendation": recommendation,
                "trace_id": f"trace-pattern-{abs(hash((p_type, p_value))) % 10_000_000}",
            }
        )

    out.sort(key=lambda item: (-float(item.get("success_rate") or 0.0), item.get("pattern_id") or ""))
    return out


def evaluate_outcomes(db: Session, scope_type: str = "USAREC", scope_value: str = "USAREC", limit: int = 200) -> Dict[str, Any]:
    ensure_outcome_learning_schema(db)
    st, sv = _normalize_scope(scope_type, scope_value)

    rows = (
        db.execute(
            text(
                """
                SELECT *
                FROM controlled_learning_outcomes
                WHERE (:scope_type='USAREC' OR (scope_type=:scope_type AND scope_value=:scope_value))
                ORDER BY measured_at DESC, created_at DESC
                LIMIT :limit
                """
            ),
            {"scope_type": st, "scope_value": sv, "limit": int(limit)},
        )
        .mappings()
        .all()
    )

    if not rows:
        return {
            "status": "no_data",
            "outcome_learning_engine": {
                "summary": {
                    "recommendations_evaluated": 0,
                    "met_or_exceeded": 0,
                    "underperformed": 0,
                    "failed": 0,
                    "insufficient_data": 0,
                    "learning_confidence": "low",
                },
                "outcome_evaluations": [],
                "pattern_performance": [],
                "data_sources": {
                    "source_table": "controlled_learning_outcomes",
                    "scope_type": st,
                    "scope_value": sv,
                },
            },
        }

    evaluations: List[Dict[str, Any]] = []
    summary_counts = {
        "recommendations_evaluated": len(rows),
        "met_or_exceeded": 0,
        "underperformed": 0,
        "failed": 0,
        "insufficient_data": 0,
    }

    for idx, row in enumerate(rows, start=1):
        expected_kpi = _as_json(row.get("expected_kpi_json"), {})
        actual_kpi = _as_json(row.get("actual_kpi_json"), {})
        classification, delta = _classify_outcome(expected_kpi, actual_kpi, str(row.get("observed_state") or ""))
        adjustment = _confidence_adjustment_for(classification, float(delta.get("delta_pct") or 0.0))

        if classification in {"exceeded", "met"}:
            summary_counts["met_or_exceeded"] += 1
        elif classification == "underperformed":
            summary_counts["underperformed"] += 1
        elif classification == "failed":
            summary_counts["failed"] += 1
        else:
            summary_counts["insufficient_data"] += 1

        evaluations.append(
            {
                "evaluation_id": f"eval-{idx}-{row.get('recommendation_id')}",
                "recommendation_id": row.get("recommendation_id"),
                "scope_type": row.get("scope_type"),
                "scope_value": row.get("scope_value"),
                "recommendation_kind": row.get("recommendation_kind"),
                "target": row.get("target_object"),
                "expected_kpi": expected_kpi,
                "actual_kpi": actual_kpi,
                "outcome_classification": classification,
                "performance_delta": delta,
                "confidence_adjustment_suggestion": adjustment,
                "trace_id": row.get("trace_id") or f"trace-eval-{idx}",
                "source_engine": row.get("source_engine"),
                "expected_effect": row.get("expected_effect"),
                "actual_effect": row.get("actual_effect"),
                "observed_state": row.get("observed_state"),
                "period_start": row.get("period_start"),
                "period_end": row.get("period_end"),
                "generated_at": row.get("generated_at"),
                "measured_at": row.get("measured_at"),
            }
        )

    learning_confidence = _learning_confidence(summary_counts)
    pattern_performance = _pattern_rows(evaluations)

    return {
        "status": "ok",
        "outcome_learning_engine": {
            "summary": {
                **summary_counts,
                "learning_confidence": learning_confidence,
            },
            "outcome_evaluations": evaluations,
            "pattern_performance": pattern_performance,
            "data_sources": {
                "source_table": "controlled_learning_outcomes",
                "scope_type": st,
                "scope_value": sv,
                "evaluated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    }
