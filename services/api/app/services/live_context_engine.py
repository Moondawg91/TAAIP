from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

CATEGORY_KEYWORDS = {
    "Political": ["policy", "election", "legislation", "governor", "city council"],
    "Military": ["training", "force", "deployment", "readiness", "recruiting"],
    "Economic": ["employment", "unemployment", "inflation", "housing", "wage"],
    "Social": ["school", "community", "demographic", "family", "youth"],
    "Information": ["media", "social media", "narrative", "misinformation", "campaign"],
    "Infrastructure": ["transport", "road", "internet", "facility", "power"],
    "Physical Environment": ["weather", "storm", "flood", "wildfire", "terrain"],
    "Time": ["holiday", "season", "quarter", "timeline", "deadline"],
    "Area": ["district", "county", "zip", "region"],
    "Structure": ["school district", "board", "institution"],
    "Capability": ["capacity", "throughput", "staffing"],
    "Organization": ["agency", "nonprofit", "business", "unit"],
    "People": ["population", "students", "families", "workers"],
    "Events": ["festival", "event", "competition", "meeting"],
}


def ensure_live_context_schema(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS controlled_learning_context_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                scope_hint TEXT,
                scope_type TEXT,
                scope_value TEXT,
                source TEXT NOT NULL,
                source_type TEXT,
                published_at TEXT,
                ingested_at TEXT NOT NULL,
                confidence REAL,
                trust_label TEXT,
                signal_summary TEXT,
                operational_implication TEXT,
                recommended_modifier_json TEXT,
                approval_required INTEGER NOT NULL,
                trace_id TEXT,
                stale_after_hours INTEGER DEFAULT 72
            )
            """
        )
    )
    db.commit()


def _normalize_category(category: str, summary: str) -> str:
    raw = (category or "").strip()
    if raw:
        return raw
    text_blob = f"{summary or ''}".lower()
    for mapped, keywords in CATEGORY_KEYWORDS.items():
        if any(word in text_blob for word in keywords):
            return mapped
    return "Information"


def _trust_label(source_type: str, confidence: float) -> str:
    st = (source_type or "").strip().lower()
    if st in {"official", "government", "military", "validated_feed"} and confidence >= 0.70:
        return "high"
    if confidence >= 0.55:
        return "medium"
    return "low"


def _modifier_template(signal: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(signal.get("confidence") or 0.0)
    implication = str(signal.get("operational_implication") or "").lower()
    modifier_type = "context_weight"
    direction = "hold"
    magnitude = "minor"
    target_engine = str(signal.get("target_engine") or "market_engine")

    if "risk" in implication or "constraint" in implication:
        modifier_type = "confidence_reduction"
        direction = "decrease"
        magnitude = "moderate" if confidence >= 0.65 else "minor"
    elif "opportunity" in implication or "favorable" in implication:
        modifier_type = "opportunity_boost"
        direction = "increase"
        magnitude = "moderate" if confidence >= 0.75 else "minor"
    elif "caution" in implication:
        modifier_type = "caution_flag"

    if confidence >= 0.85:
        magnitude = "significant"

    return {
        "target_engine": target_engine,
        "modifier_type": modifier_type,
        "direction": direction,
        "magnitude": magnitude,
    }


def ingest_context_signals(db: Session, signals: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ensure_live_context_schema(db)
    now = datetime.utcnow().isoformat() + "Z"
    inserted = 0

    for index, signal in enumerate(signals or [], start=1):
        confidence = float(signal.get("confidence") or 0.0)
        summary = str(signal.get("signal_summary") or "").strip()
        source = str(signal.get("source") or "").strip()
        if not source or not summary:
            continue

        category = _normalize_category(str(signal.get("category") or ""), summary)
        source_type = str(signal.get("source_type") or "external").strip()
        trust = _trust_label(source_type, confidence)
        modifier = signal.get("recommended_modifier") or _modifier_template(signal)
        approval_required = bool(signal.get("approval_required", True))

        db.execute(
            text(
                """
                INSERT INTO controlled_learning_context_signals (
                    signal_id, category, subcategory, scope_hint, scope_type, scope_value,
                    source, source_type, published_at, ingested_at, confidence, trust_label,
                    signal_summary, operational_implication, recommended_modifier_json,
                    approval_required, trace_id, stale_after_hours
                ) VALUES (
                    :signal_id, :category, :subcategory, :scope_hint, :scope_type, :scope_value,
                    :source, :source_type, :published_at, :ingested_at, :confidence, :trust_label,
                    :signal_summary, :operational_implication, :recommended_modifier_json,
                    :approval_required, :trace_id, :stale_after_hours
                )
                """
            ),
            {
                "signal_id": signal.get("signal_id") or f"signal-{uuid4().hex[:16]}",
                "category": category,
                "subcategory": signal.get("subcategory"),
                "scope_hint": signal.get("scope_hint"),
                "scope_type": signal.get("scope_type") or "USAREC",
                "scope_value": signal.get("scope_value") or "USAREC",
                "source": source,
                "source_type": source_type,
                "published_at": signal.get("published_at") or now,
                "ingested_at": now,
                "confidence": confidence,
                "trust_label": trust,
                "signal_summary": summary,
                "operational_implication": signal.get("operational_implication") or "No explicit implication provided.",
                "recommended_modifier_json": json.dumps(modifier, default=str),
                "approval_required": 1 if approval_required else 0,
                "trace_id": signal.get("trace_id") or f"trace-context-{index}",
                "stale_after_hours": int(signal.get("stale_after_hours") or 72),
            },
        )
        inserted += 1

    db.commit()
    return {"status": "ok", "signals_ingested": inserted}


def _is_stale(published_at: str, stale_after_hours: int) -> bool:
    try:
        ts = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
    except Exception:
        return True
    return datetime.utcnow() - ts.replace(tzinfo=None) > timedelta(hours=max(1, int(stale_after_hours or 72)))


def summarize_context_signals(db: Session, scope_type: str = "USAREC", scope_value: str = "USAREC", limit: int = 200) -> Dict[str, Any]:
    ensure_live_context_schema(db)
    st = (scope_type or "USAREC").upper().strip()
    sv = (scope_value or "USAREC").strip()

    rows = (
        db.execute(
            text(
                """
                SELECT *
                FROM controlled_learning_context_signals
                WHERE (:scope_type='USAREC' OR (scope_type=:scope_type AND scope_value=:scope_value))
                ORDER BY published_at DESC, ingested_at DESC
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
            "live_context_engine": {
                "summary": {
                    "signals_ingested": 0,
                    "high_confidence_signals": 0,
                    "approval_required_signals": 0,
                    "stale_signals": 0,
                },
                "context_signals": [],
                "data_sources": {
                    "source_table": "controlled_learning_context_signals",
                    "scope_type": st,
                    "scope_value": sv,
                },
            },
        }

    context_signals: List[Dict[str, Any]] = []
    high_conf = 0
    approval_required = 0
    stale = 0

    for row in rows:
        confidence = float(row.get("confidence") or 0.0)
        modifier = row.get("recommended_modifier_json")
        if isinstance(modifier, str):
            try:
                modifier = json.loads(modifier)
            except Exception:
                modifier = {}
        stale_signal = _is_stale(str(row.get("published_at") or ""), int(row.get("stale_after_hours") or 72))

        if confidence >= 0.75:
            high_conf += 1
        if int(row.get("approval_required") or 0) == 1:
            approval_required += 1
        if stale_signal:
            stale += 1

        context_signals.append(
            {
                "signal_id": row.get("signal_id"),
                "category": row.get("category"),
                "subcategory": row.get("subcategory"),
                "scope_hint": row.get("scope_hint"),
                "source": row.get("source"),
                "source_type": row.get("source_type"),
                "published_at": row.get("published_at"),
                "confidence": round(confidence, 4),
                "trust_label": row.get("trust_label") or _trust_label(str(row.get("source_type") or ""), confidence),
                "signal_summary": row.get("signal_summary"),
                "operational_implication": row.get("operational_implication"),
                "recommended_modifier": modifier or {},
                "approval_required": bool(int(row.get("approval_required") or 0)),
                "trace_id": row.get("trace_id") or f"trace-context-{row.get('signal_id')}",
            }
        )

    # deterministic ordering: newest confidence first then signal id
    context_signals.sort(key=lambda item: (-float(item.get("confidence") or 0.0), str(item.get("signal_id") or "")))

    return {
        "status": "ok",
        "live_context_engine": {
            "summary": {
                "signals_ingested": len(rows),
                "high_confidence_signals": high_conf,
                "approval_required_signals": approval_required,
                "stale_signals": stale,
            },
            "context_signals": context_signals,
            "data_sources": {
                "source_table": "controlled_learning_context_signals",
                "scope_type": st,
                "scope_value": sv,
                "evaluated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    }
