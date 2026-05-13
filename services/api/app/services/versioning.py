from typing import Any, Dict, List, Optional
import hashlib
import json
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models_intelligence as mi
from .runtime_cache import bucket
from .intelligence_observability import emit_event


def _period_to_fy_quarter_rsm(period_type: Optional[str], period_value: Optional[str]) -> Dict[str, Optional[str]]:
    normalized_type = str(period_type or "").upper().strip()
    value = None if period_value is None else str(period_value)

    if normalized_type == "RSM":
        return {"fy": None, "quarter": None, "rsm": value}
    if normalized_type == "QTR":
        return {"fy": None, "quarter": value, "rsm": None}
    if normalized_type == "FY":
        return {"fy": value, "quarter": None, "rsm": None}
    return {"fy": None, "quarter": None, "rsm": None}


def _normalize_unit_scope(content: Dict[str, Any], rsid: Optional[str], metadata: Dict[str, Any]) -> List[str]:
    candidate = (
        content.get("unit_scope")
        or (content.get("scope") or {}).get("unit_scope")
        or metadata.get("unit_scope")
        or []
    )
    if not isinstance(candidate, list):
        candidate = []

    normalized: List[str] = []
    seen = set()
    if rsid:
        normalized.append(rsid)
        seen.add(rsid)
    for value in candidate:
        if value is None:
            continue
        item = str(value)
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    return normalized


def _explanation_summary(entity_type: str, content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    if entity_type == "analytics_snapshot":
        stype = metadata.get("snapshot_type") or "analytics"
        return f"Analytics snapshot version for {stype}"
    if entity_type == "recommendation_record":
        rtype = metadata.get("recommendation_type") or content.get("recommendation_type") or "recommendation"
        return f"Recommendation snapshot version for {rtype}"
    if entity_type == "frago_order":
        return str(content.get("summary") or "FRAGO snapshot version")
    return "Version snapshot"


def _explanation_key_drivers(entity_type: str, content: Dict[str, Any], metadata: Dict[str, Any]) -> List[str]:
    drivers: List[str] = []

    if entity_type == "analytics_snapshot":
        summary_metrics = content.get("summary_metrics") if isinstance(content, dict) else None
        if isinstance(summary_metrics, dict):
            for key in sorted(summary_metrics.keys())[:3]:
                drivers.append(f"summary_metrics.{key}")
    elif entity_type == "recommendation_record":
        payload = content if isinstance(content, dict) else {}
        for key in ["recommendation_type", "priority", "status", "recommendation_count"]:
            if key in payload:
                drivers.append(key)
    elif entity_type == "frago_order":
        detail = content.get("recommendation") if isinstance(content, dict) else None
        if isinstance(detail, dict):
            for key in ["recommendation_type", "priority", "summary"]:
                if detail.get(key) is not None:
                    drivers.append(f"recommendation.{key}")

    if not drivers:
        for key in sorted((content or {}).keys())[:3]:
            drivers.append(str(key))
    return drivers


def create_explanation_object(
    entity_type: str,
    entity_id: str,
    version_number: int,
    content: Dict[str, Any],
    rsid: Optional[str],
    period_type: Optional[str],
    period_value: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    content_fingerprint = hashlib.sha256(
        json.dumps(content or {}, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    meta_fingerprint = hashlib.sha256(
        json.dumps(metadata or {}, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    cache_key = ":".join(
        [
            str(entity_type),
            str(entity_id),
            str(version_number),
            str(rsid),
            str(period_type),
            str(period_value),
            content_fingerprint,
            meta_fingerprint,
        ]
    )
    cache = bucket("explanation")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    meta = metadata or {}
    result = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "version_number": int(version_number),
        "rsid": rsid,
        "period_type": period_type,
        "period_value": period_value,
        "unit_scope": _normalize_unit_scope(content or {}, rsid, meta),
        "summary": _explanation_summary(entity_type, content or {}, meta),
        "key_drivers": _explanation_key_drivers(entity_type, content or {}, meta),
        "confidence": float(meta.get("confidence", 0.8)),
        "metadata": meta,
    }
    cache.set(cache_key, result)
    emit_event(
        "explanation.created",
        rsid=rsid,
        period=f"{period_type}:{period_value}" if period_type or period_value else None,
        entity_type=entity_type,
        entity_id=entity_id,
        version_number=int(version_number),
    )
    return result


def create_version_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    content: Dict[str, Any],
    rsid: Optional[str],
    period_type: Optional[str],
    period_value: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create one append-only version row.

    This function never updates prior version rows.
    """
    bind = db.get_bind()
    mi.AnalyticsSnapshotVersion.__table__.create(bind=bind, checkfirst=True)
    mi.RecommendationRecordVersion.__table__.create(bind=bind, checkfirst=True)
    mi.FragoOrderVersion.__table__.create(bind=bind, checkfirst=True)

    period = _period_to_fy_quarter_rsm(period_type, period_value)

    if entity_type == "analytics_snapshot":
        current_max = db.query(func.max(mi.AnalyticsSnapshotVersion.version_number)).filter(
            mi.AnalyticsSnapshotVersion.snapshot_id == entity_id
        ).scalar()
        next_version = int(current_max or 0) + 1
        version_row = mi.AnalyticsSnapshotVersion(
            id=f"snapshot_ver_{uuid.uuid4().hex[:8]}",
            snapshot_id=entity_id,
            version_number=next_version,
            payload=content,
            period_analyzed=(metadata or {}).get("period_analyzed"),
            is_current=True,
        )
    elif entity_type == "recommendation_record":
        current_max = db.query(func.max(mi.RecommendationRecordVersion.version_number)).filter(
            mi.RecommendationRecordVersion.record_id == entity_id
        ).scalar()
        next_version = int(current_max or 0) + 1
        version_row = mi.RecommendationRecordVersion(
            id=f"rec_ver_{uuid.uuid4().hex[:8]}",
            record_id=entity_id,
            version_number=next_version,
            payload=content,
            explanation_objects=(metadata or {}).get("explanation_objects") or {},
            analytics_snapshot_id=(metadata or {}).get("analytics_snapshot_id"),
            is_current=True,
        )
    elif entity_type == "frago_order":
        current_max = db.query(func.max(mi.FragoOrderVersion.version_number)).filter(
            mi.FragoOrderVersion.frago_id == entity_id
        ).scalar()
        next_version = int(current_max or 0) + 1
        version_row = mi.FragoOrderVersion(
            id=f"frago_ver_{uuid.uuid4().hex[:8]}",
            frago_id=entity_id,
            version_number=next_version,
            content=content,
            generated_from_recommendation_id=(metadata or {}).get("generated_from_recommendation_id"),
            rop_version_id=(metadata or {}).get("rop_version_id"),
            srp_version_id=(metadata or {}).get("srp_version_id"),
            analytics_snapshot_id=(metadata or {}).get("analytics_snapshot_id"),
            recommendation_record_version_id=(metadata or {}).get("recommendation_record_version_id"),
            analytics_snapshot_version_id=(metadata or {}).get("analytics_snapshot_version_id"),
            effective_start=(metadata or {}).get("effective_start"),
            effective_end=(metadata or {}).get("effective_end"),
            is_current=True,
        )
    else:
        raise ValueError(f"Unsupported entity_type: {entity_type}")

    db.add(version_row)
    db.flush()

    for prefix in (
        f"version_list:{entity_type}:{entity_id}",
        f"version:{entity_type}:{entity_id}:{next_version}",
    ):
        bucket("version_list").delete(prefix)
    emit_event(
        "version.created",
        rsid=rsid,
        period=f"{period_type}:{period_value}" if period_type or period_value else None,
        entity_type=entity_type,
        entity_id=entity_id,
        version_number=int(next_version),
    )

    return version_row


def create_archive_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    version_id: str,
    version_number: int,
    content: Dict[str, Any],
    rsid: Optional[str],
    period_type: Optional[str],
    period_value: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create one append-only archive ledger event for a version row."""
    bind = db.get_bind()
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)

    period = _period_to_fy_quarter_rsm(period_type, period_value)
    meta = dict(metadata or {})
    explanation_metadata = dict(meta)
    explanation_metadata.pop("explanation", None)
    meta["explanation"] = create_explanation_object(
        entity_type=entity_type,
        entity_id=entity_id,
        version_number=int(version_number),
        content=content or {},
        rsid=rsid,
        period_type=period_type,
        period_value=period_value,
        metadata=explanation_metadata,
    )

    payload_hash = hashlib.sha256(
        json.dumps(content or {}, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    event = mi.VersionArchiveEvent(
        id=f"varch_{uuid.uuid4().hex[:8]}",
        entity_type=entity_type,
        entity_id=entity_id,
        version_id=version_id,
        version_number=int(version_number),
        station_rsid=rsid,
        fy=period.get("fy"),
        quarter=period.get("quarter"),
        rsm=period.get("rsm"),
        event_type="version_created",
        payload_hash=payload_hash,
        event_metadata=meta,
    )
    db.add(event)
    db.flush()
    bucket("archive_event").delete(f"archive:{entity_type}:{entity_id}:{version_number}")
    emit_event(
        "archive.created",
        rsid=rsid,
        period=f"{period_type}:{period_value}" if period_type or period_value else None,
        entity_type=entity_type,
        entity_id=entity_id,
        version_number=int(version_number),
    )
    return event


def list_versions(db: Session, entity_type: str, entity_id: str) -> List[Any]:
    cache_key = f"version_list:{entity_type}:{entity_id}"
    cached = bucket("version_list").get(cache_key)
    if cached is not None:
        return cached

    if entity_type == "analytics_snapshot":
        rows = db.query(mi.AnalyticsSnapshotVersion).filter_by(snapshot_id=entity_id).order_by(
            mi.AnalyticsSnapshotVersion.version_number.asc()
        ).all()
    elif entity_type == "recommendation_record":
        rows = db.query(mi.RecommendationRecordVersion).filter_by(record_id=entity_id).order_by(
            mi.RecommendationRecordVersion.version_number.asc()
        ).all()
    elif entity_type == "frago_order":
        rows = db.query(mi.FragoOrderVersion).filter_by(frago_id=entity_id).order_by(
            mi.FragoOrderVersion.version_number.asc()
        ).all()
    else:
        raise ValueError(f"Unsupported entity_type: {entity_type}")

    bucket("version_list").set(cache_key, rows)
    return rows


def get_version(db: Session, entity_type: str, entity_id: str, version_number: int) -> Optional[Any]:
    cache_key = f"version:{entity_type}:{entity_id}:{int(version_number)}"
    cached = bucket("version_list").get(cache_key)
    if cached is not None:
        return cached

    if entity_type == "analytics_snapshot":
        row = db.query(mi.AnalyticsSnapshotVersion).filter(
            mi.AnalyticsSnapshotVersion.snapshot_id == entity_id,
            mi.AnalyticsSnapshotVersion.version_number == version_number,
        ).first()
    elif entity_type == "recommendation_record":
        row = db.query(mi.RecommendationRecordVersion).filter(
            mi.RecommendationRecordVersion.record_id == entity_id,
            mi.RecommendationRecordVersion.version_number == version_number,
        ).first()
    elif entity_type == "frago_order":
        row = db.query(mi.FragoOrderVersion).filter(
            mi.FragoOrderVersion.frago_id == entity_id,
            mi.FragoOrderVersion.version_number == version_number,
        ).first()
    else:
        raise ValueError(f"Unsupported entity_type: {entity_type}")

    if row is not None:
        bucket("version_list").set(cache_key, row)
    return row


def get_archive_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    version_number: int,
) -> Optional[Any]:
    cache_key = f"archive:{entity_type}:{entity_id}:{int(version_number)}"
    cached = bucket("archive_event").get(cache_key)
    if cached is not None:
        return cached

    row = db.query(mi.VersionArchiveEvent).filter(
        mi.VersionArchiveEvent.entity_type == entity_type,
        mi.VersionArchiveEvent.entity_id == entity_id,
        mi.VersionArchiveEvent.version_number == int(version_number),
    ).order_by(mi.VersionArchiveEvent.created_at.desc()).first()
    if row is not None:
        bucket("archive_event").set(cache_key, row)
    return row
