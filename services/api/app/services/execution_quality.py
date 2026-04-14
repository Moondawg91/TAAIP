from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app.services import execution_quality_contract


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()
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


def enforce_scope(actor_scope_type: str, actor_scope_value: str, request_scope_type: str, request_scope_value: str) -> None:
    a_type = (actor_scope_type or "USAREC").upper().strip()
    r_type = (request_scope_type or "USAREC").upper().strip()
    a_val = (actor_scope_value or "USAREC").strip()
    r_val = (request_scope_value or "USAREC").strip()
    if a_type == "USAREC":
        return
    if r_type == "USAREC":
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")
    a_prefix = _scope_prefix(a_type, a_val)
    r_prefix = _scope_prefix(r_type, r_val)
    if a_prefix and not r_prefix.startswith(a_prefix):
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")


def _safe_table_exists(db, table_name: str) -> bool:
    q = text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n")
    return bool(db.execute(q, {"n": table_name}).first())


def _table_columns(db, table_name: str) -> List[str]:
    rows = db.execute(text(f"PRAGMA table_info('{table_name}')")).mappings().all()
    return [str(r.get("name")) for r in rows]


def _load_rows(db, scope_type: str, scope_value: str) -> Tuple[str, List[Dict], str, str]:
    if not _safe_table_exists(db, "funnel_transitions"):
        return "no_active_dataset", [], "", ""

    cols = _table_columns(db, "funnel_transitions")
    valid, schema_errors = execution_quality_contract.validate_schema_columns(cols)
    if not valid:
        return "invalid_dataset_schema", [], "", "; ".join(schema_errors)

    prefix = _scope_prefix(scope_type, scope_value)
    if prefix:
        src_rows = db.execute(
            text("SELECT * FROM funnel_transitions WHERE station_rsid LIKE :pfx"),
            {"pfx": f"{prefix}%"},
        ).mappings().all()
    else:
        src_rows = db.execute(text("SELECT * FROM funnel_transitions")).mappings().all()

    if not src_rows:
        return "no_active_dataset", [], "", ""

    grouped: Dict[str, List[Dict]] = {}
    as_of_values: List[str] = []
    for r in src_rows:
        lead_key = str(r.get("lead_key") or "")
        if not lead_key:
            continue
        grouped.setdefault(lead_key, []).append(r)

    out: List[Dict] = []
    for lead_key, events in grouped.items():
        events_sorted = sorted(events, key=lambda x: str(x.get("transitioned_at") or x.get("created_at") or ""))
        first = events_sorted[0]
        last = events_sorted[-1]
        station = str(first.get("station_rsid") or "")

        ts_first = str(first.get("transitioned_at") or first.get("created_at") or "")
        ts_last = str(last.get("transitioned_at") or last.get("created_at") or "")
        if ts_first:
            as_of_values.append(ts_first)
        if ts_last:
            as_of_values.append(ts_last)

        flash_to_bang = 0.0
        avg_stage_age = 0.0
        try:
            d1 = datetime.fromisoformat(ts_first.replace("Z", "+00:00"))
            d2 = datetime.fromisoformat(ts_last.replace("Z", "+00:00"))
            flash_to_bang = max(0.0, (d2 - d1).total_seconds() / 86400.0)
            if len(events_sorted) > 1:
                avg_stage_age = flash_to_bang / (len(events_sorted) - 1)
            else:
                avg_stage_age = flash_to_bang
        except Exception:
            pass

        last_stage = str(last.get("to_stage") or "").lower()
        stall = avg_stage_age >= 21.0 or flash_to_bang >= 90.0
        processing_bottleneck = "test" in last_stage or "physical" in last_stage

        out.append(
            {
                "lead_key": lead_key,
                "station_rsid": station,
                "flash_to_bang_days": round(flash_to_bang, 2),
                "avg_stage_age_days": round(avg_stage_age, 2),
                "stall_flag": stall,
                "processing_bottleneck_flag": processing_bottleneck,
                "prospecting_problem": len(events_sorted) <= 1,
                "engagement_problem": len(events_sorted) > 1 and last_stage in {"lead", "prospect"},
                "processing_problem": processing_bottleneck or (last_stage in {"appointment_conducted", "test", "physical"} and flash_to_bang > 45),
                "future_soldier_management_problem": last_stage in {"enlist", "dep", "future_soldier"} and flash_to_bang > 120,
                "data_as_of": ts_last or ts_first,
                "source_dataset_name": "funnel_transitions",
            }
        )

    ok, errors, normalized = execution_quality_contract.validate_rows(out)
    if not ok:
        return "invalid_dataset_schema", [], "", "; ".join(errors[:10])

    latest = max(as_of_values) if as_of_values else ""
    return "ok", normalized, latest, ""


def _rollup(rows: List[Dict], key_name: str, key_fn) -> List[Dict]:
    groups: Dict[str, List[Dict]] = {}
    for row in rows:
        k = key_fn(row)
        groups.setdefault(k, []).append(row)

    out: List[Dict] = []
    for k, vals in groups.items():
        if not k:
            continue
        n = len(vals)
        flash = sum(float(v.get("flash_to_bang_days") or 0.0) for v in vals) / n if n else 0.0
        stage_age = sum(float(v.get("avg_stage_age_days") or 0.0) for v in vals) / n if n else 0.0
        stalls = sum(1 for v in vals if v.get("stall_flag"))
        processing = sum(1 for v in vals if v.get("processing_bottleneck_flag"))
        out.append(
            {
                key_name: k,
                "lead_count": n,
                "avg_flash_to_bang": round(flash, 2),
                "avg_stage_age_days": round(stage_age, 2),
                "stall_count": stalls,
                "processing_bottleneck_count": processing,
                "execution_status": "execution_degraded" if (stalls / n if n else 0.0) >= 0.4 else "execution_stable",
            }
        )
    out.sort(key=lambda x: x.get("stall_count", 0), reverse=True)
    return out


def summarize_execution_quality(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    status, rows, data_as_of, schema_error = _load_rows(db, scope_type, scope_value)
    if status != "ok":
        return {
            "status": status,
            "execution_quality": {
                "summary": {
                    "overall_execution_status": status,
                    "avg_flash_to_bang": 0.0,
                    "stall_count": 0,
                    "processing_bottleneck_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "root_cause_breakdown": [],
                "data_as_of": data_as_of or None,
                "last_refresh": datetime.utcnow().isoformat() + "Z",
                "source_dataset_name": None,
                "schema_error": schema_error or None,
            },
        }

    n = len(rows)
    avg_flash = sum(float(r.get("flash_to_bang_days") or 0.0) for r in rows) / n if n else 0.0
    stall_count = sum(1 for r in rows if r.get("stall_flag"))
    processing_count = sum(1 for r in rows if r.get("processing_bottleneck_flag"))

    root = {
        "prospecting_problem": sum(1 for r in rows if r.get("prospecting_problem")),
        "engagement_problem": sum(1 for r in rows if r.get("engagement_problem")),
        "processing_problem": sum(1 for r in rows if r.get("processing_problem")),
        "future_soldier_management_problem": sum(1 for r in rows if r.get("future_soldier_management_problem")),
    }
    root_breakdown = [{"cause": k, "count": v} for k, v in sorted(root.items(), key=lambda x: x[1], reverse=True)]

    source_dataset_name = rows[0].get("source_dataset_name") if rows else None

    overall = "execution_degraded" if (stall_count / n if n else 0.0) >= 0.35 else "execution_stable"

    return {
        "status": "ok",
        "execution_quality": {
            "summary": {
                "overall_execution_status": overall,
                "avg_flash_to_bang": round(avg_flash, 2),
                "stall_count": stall_count,
                "processing_bottleneck_count": processing_count,
            },
            "by_scope": {
                "bde": _rollup(rows, "brigade_prefix", lambda r: str(r.get("station_rsid") or "")[:1]),
                "bn": _rollup(rows, "battalion_prefix", lambda r: str(r.get("station_rsid") or "")[:2]),
                "company": _rollup(rows, "company_prefix", lambda r: str(r.get("station_rsid") or "")[:3]),
                "station": _rollup(rows, "station_rsid", lambda r: str(r.get("station_rsid") or "")),
            },
            "root_cause_breakdown": root_breakdown,
            "data_as_of": data_as_of or None,
            "last_refresh": datetime.utcnow().isoformat() + "Z",
            "source_dataset_name": source_dataset_name,
        },
    }
